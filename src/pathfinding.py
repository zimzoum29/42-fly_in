"""
Turn-aware pathfinding for the Fly-in drone routing simulator.

Implements a Dijkstra-style search over ``(hub, turn)`` states. Each
drone is routed one at a time: the path found for a drone is
"reserved" (hub occupancy per turn, and connection usage per turn)
before the next drone is routed, so later drones automatically avoid
capacity conflicts with earlier ones.
"""

import heapq

from .models import Hub, Map

_REAL_COST: dict[str, int] = {
    "normal": 1,
    "priority": 1,
    "restricted": 2,
    "blocked": 0,
}

_MAX_TURNS = 200

State = tuple[str, int]
LinkKey = tuple[str, str]
BestScore = tuple[int, float, int]
PathStep = tuple[Hub, int]


class PathFinder:
    """Finds and reserves conflict-free paths for individual drones."""

    def __init__(self) -> None:
        """Create a stateless pathfinder instance."""

    def real_zone_cost(self, hub: Hub) -> int:
        """
        Return the turn cost of moving onto ``hub``.

        Args:
            hub: Destination hub of the move.

        Returns:
            The number of turns the move takes, based on the hub's
            zone type (see subject VII.3).
        """
        return _REAL_COST.get(hub.zone, 1)

    def path_cost(self, steps: list[PathStep]) -> int:
        """
        Return the total turn cost of a computed path.

        Args:
            steps: Path as returned by :meth:`find_path`.

        Returns:
            The turn at which the path's last step lands, or ``0``
            for an empty path.
        """
        if not steps:
            return 0
        return steps[-1][1]

    def _link_key(self, a: str, b: str) -> LinkKey:
        """Build an order-independent key identifying a connection."""
        return (a, b) if a < b else (b, a)

    def _hub_capacity(self, hub: Hub) -> int:
        """
        Return the effective drone capacity of a hub.

        The start and end hubs are exempt from capacity limits, per
        subject VII.2.
        """
        if hub.is_start or hub.is_end:
            return 10 ** 9
        return hub.max_drones

    def _link_capacity_ok(
        self,
        lk: LinkKey,
        dep_turn: int,
        arrival: int,
        link_reservation: dict[tuple[LinkKey, int], int],
        conn_cap: int,
    ) -> bool:
        """
        Check a connection has free capacity for a whole transit.

        A move from ``dep_turn`` to ``arrival`` occupies the
        connection for every turn in between (this matters for
        2-turn moves into ``restricted`` zones, which occupy the
        connection during both turns of their transit, per subject
        VII.3).

        Args:
            lk: Order-independent key of the connection.
            dep_turn: Turn the drone departs from the current hub.
            arrival: Turn the drone will land on the neighbor hub.
            link_reservation: Per-(connection, turn) occupancy count.
            conn_cap: Maximum simultaneous occupancy of the
                connection.

        Returns:
            ``True`` if every turn of the transit has free capacity.
        """
        for t in range(dep_turn + 1, arrival + 1):
            if link_reservation.get((lk, t), 0) >= conn_cap:
                return False
        return True

    def _congestion_cost(
        self,
        current: Hub,
        neighbor: Hub,
        arrival: int,
        dep_turn: int,
        reservation: dict[State, int],
        link_reservation: dict[tuple[LinkKey, int], int],
        conn_cap: int,
    ) -> float:
        """
        Soft heuristic penalizing already-crowded hubs/links.

        This only influences which of several equally-short paths is
        preferred; hard capacity limits are enforced separately in
        :meth:`find_path` and :meth:`_link_capacity_ok`.
        """
        node_cap = max(self._hub_capacity(neighbor), 1)
        node_load = reservation.get((neighbor.name, arrival), 0)

        lk = self._link_key(current.name, neighbor.name)
        link_load = link_reservation.get((lk, dep_turn + 1), 0)

        return (node_load / node_cap) + (link_load / max(conn_cap, 1))

    def _movement_penalty(
        self,
        current_state: State,
        came_from: dict[State, State | None],
        next_name: str,
    ) -> int:
        """Soft heuristic discouraging back-and-forth detours."""
        prev = came_from.get(current_state)
        if prev is None:
            return 0

        penalty = 0
        prev_name, _ = prev
        if next_name == prev_name:
            penalty += 2

        ancestor: State | None = prev
        while ancestor is not None:
            anc_name, _ = ancestor
            if anc_name == next_name:
                penalty += 1
                break
            ancestor = came_from.get(ancestor)

        return penalty

    def find_path(
        self,
        game_map: Map,
        start: Hub,
        end: Hub,
        reservation: dict[State, int],
        link_reservation: dict[tuple[LinkKey, int], int],
    ) -> list[PathStep]:
        """
        Find the best conflict-free path from ``start`` to ``end``.

        Args:
            game_map: Graph to search.
            start: Hub the drone departs from.
            end: Hub the drone must reach.
            reservation: Per-(hub, turn) occupancy already committed
                by previously routed drones.
            link_reservation: Per-(connection, turn) occupancy
                already committed by previously routed drones.

        Returns:
            An ordered list of ``(hub, turn)`` steps (excluding the
            starting position), or an empty list if no valid path
            exists within the turn budget.
        """
        hub_map: dict[str, Hub] = {h.name: h for h in game_map.hubs}

        counter = 0
        start_priority = 1 if start.zone == "priority" else 0
        start_state: State = (start.name, 0)

        heap: list[tuple[int, int, float, int, int, Hub]] = [
            (0, 0, 0.0, -start_priority, counter, start)
        ]

        best: dict[State, BestScore] = {
            start_state: (0, 0.0, start_priority)
        }
        came_from: dict[State, State | None] = {start_state: None}

        while heap:
            turn, detour, cong, neg_prio, _, current = heapq.heappop(
                heap
            )
            prio = -neg_prio
            current_state: State = (current.name, turn)

            known_d, known_c, known_p = best.get(
                current_state, (10 ** 9, float("inf"), -1)
            )
            if (
                detour > known_d or (
                    detour == known_d and (
                        cong > known_c or (
                            cong == known_c and prio < known_p
                        )
                    )
                )
            ):
                continue

            if current is end:
                return self._rebuild(came_from, hub_map, end, turn)

            if turn >= _MAX_TURNS:
                continue

            for neighbor in game_map.get_neighbors(current):
                if neighbor.zone == "blocked":
                    continue

                step_real = self.real_zone_cost(neighbor)
                arrival = turn + step_real
                cap = self._hub_capacity(neighbor)

                if reservation.get((neighbor.name, arrival), 0) >= cap:
                    continue

                conn = game_map.get_connection(current, neighbor)
                conn_cap = (
                    conn.max_link_capacity if conn is not None else 1
                )
                lk = self._link_key(current.name, neighbor.name)
                if not self._link_capacity_ok(
                    lk, turn, arrival, link_reservation, conn_cap
                ):
                    continue

                next_state: State = (neighbor.name, arrival)
                next_detour = detour + self._movement_penalty(
                    current_state, came_from, neighbor.name
                )
                next_cong = cong + self._congestion_cost(
                    current, neighbor, arrival, turn,
                    reservation, link_reservation, conn_cap,
                )
                next_prio = prio + (
                    1 if neighbor.zone == "priority" else 0
                )

                known_d2, known_c2, known_p2 = best.get(
                    next_state, (10 ** 9, float("inf"), -1)
                )
                if (
                    next_detour > known_d2 or (
                        next_detour == known_d2 and (
                            next_cong > known_c2 or (
                                next_cong == known_c2
                                and next_prio <= known_p2
                            )
                        )
                    )
                ):
                    continue

                best[next_state] = (next_detour, next_cong, next_prio)
                came_from[next_state] = current_state
                counter += 1
                heapq.heappush(heap, (
                    arrival, next_detour, next_cong,
                    -next_prio, counter, neighbor,
                ))

            wait_turn = turn + 1
            cap_w = self._hub_capacity(current)
            wait_occ = reservation.get((current.name, wait_turn), 0)

            if wait_occ < cap_w:
                wait_state: State = (current.name, wait_turn)
                wait_cong = cong + (wait_occ / max(cap_w, 1))

                known_d2, known_c2, known_p2 = best.get(
                    wait_state, (10 ** 9, float("inf"), -1)
                )
                if (
                    detour < known_d2 or (
                        detour == known_d2 and (
                            wait_cong < known_c2 or (
                                wait_cong == known_c2
                                and prio > known_p2
                            )
                        )
                    )
                ):
                    best[wait_state] = (detour, wait_cong, prio)
                    came_from[wait_state] = current_state
                    counter += 1
                    heapq.heappush(heap, (
                        wait_turn, detour, wait_cong,
                        -prio, counter, current,
                    ))

        return []

    def _rebuild(
        self,
        came_from: dict[State, State | None],
        hub_map: dict[str, Hub],
        end: Hub,
        end_turn: int,
    ) -> list[PathStep]:
        """
        Walk ``came_from`` back to the start and reverse it.

        Args:
            came_from: Predecessor map built during the search.
            hub_map: Lookup from hub name to :class:`Hub`.
            end: Hub the search terminated on.
            end_turn: Turn at which ``end`` was reached.

        Returns:
            The ordered list of ``(hub, turn)`` steps, excluding the
            starting position.
        """
        states: list[State] = []
        entry: State | None = (end.name, end_turn)

        while entry is not None:
            states.append(entry)
            entry = came_from.get(entry)

        states.reverse()
        return [(hub_map[name], turn) for name, turn in states[1:]]

    def register_path(
        self,
        steps: list[PathStep],
        start_name: str,
        reservation: dict[State, int],
        link_reservation: dict[tuple[LinkKey, int], int],
    ) -> None:
        """
        Commit a drone's path into the shared reservation tables.

        Every hub visited (including the start) reserves one unit of
        capacity for the turn it is occupied. Every connection
        traversed reserves one unit of capacity for *each* turn of
        its transit — not just the departure turn — so that a
        2-turn move into a ``restricted`` zone correctly blocks the
        connection for both turns, per subject VII.3.

        Args:
            steps: Path as returned by :meth:`find_path`.
            start_name: Name of the hub the drone started from.
            reservation: Per-(hub, turn) occupancy table to update.
            link_reservation: Per-(connection, turn) occupancy table
                to update.
        """
        reservation[(start_name, 0)] = (
            reservation.get((start_name, 0), 0) + 1
        )
        for hub, turn in steps:
            key: State = (hub.name, turn)
            reservation[key] = reservation.get(key, 0) + 1

        prev_name = start_name
        prev_turn = 0
        for hub, turn in steps:
            if hub.name == prev_name:
                prev_turn = turn
                continue
            lk = self._link_key(prev_name, hub.name)
            for occupied_turn in range(prev_turn + 1, turn + 1):
                link_state = (lk, occupied_turn)
                link_reservation[link_state] = (
                    link_reservation.get(link_state, 0) + 1
                )
            prev_name = hub.name
            prev_turn = turn
