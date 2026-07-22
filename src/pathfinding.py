import heapq
from typing import Optional
from .models import Hub, Map



_REAL_COST: dict[str, int] = {
    "normal":     1,
    "priority":   1,
    "restricted": 2,
    "blocked":    0,
}

_MAX_TURNS = 200

State = tuple[str, int]
LinkKey = tuple[str, str]
BestScore = tuple[int, float, int]
PathStep = tuple[Hub, int]


class PathFinder:

    def __init__(self):
        pass

    def real_zone_cost(self, hub: Hub):
        return _REAL_COST.get(hub.zone, 1)


    def path_cost(self, steps: list[PathStep]):
        if not steps:
            return 0
        return steps[-1][1]


    def _link_key(self, a: str, b: str):
        return (a, b) if a < b else (b, a)


    def _hub_capacity(self, hub: Hub) -> int:
        if hub.is_start or hub.is_end:
            return 10 ** 9
        return hub.max_drones


    def _congestion_cost(self, current: Hub, neighbor: Hub, arrival: int, dep_turn: int, reservation: dict[State, int], link_reservation: dict[tuple[LinkKey, int], int], conn_cap: int):
        node_cap = max(self._hub_capacity(neighbor), 1)
        node_load = reservation.get((neighbor.name, arrival), 0)

        lk = self._link_key(current.name, neighbor.name)
        link_load = link_reservation.get((lk, dep_turn + 1), 0)

        return (node_load / node_cap) + (link_load / max(conn_cap, 1))


    def _movement_penalty(self, current_state: State, came_from: dict[State, Optional[State]], next_name: str):
        prev = came_from.get(current_state)
        if prev is None:
            return 0

        penalty = 0
        prev_name, _ = prev
        if next_name == prev_name:
            penalty += 2

        ancestor: Optional[State] = prev
        while ancestor is not None:
            anc_name, _ = ancestor
            if anc_name == next_name:
                penalty += 1
                break
            ancestor = came_from.get(ancestor)

        return penalty


    def find_path(self, game_map: Map, start: Hub, end: Hub, reservation: dict[State, int], link_reservation: dict[tuple[LinkKey, int], int]):
        hub_map: dict[str, Hub] = {h.name: h for h in game_map.hubs}

        counter = 0
        start_priority = 1 if start.zone == "priority" else 0
        start_state: State = (start.name, 0)

        heap: list[tuple[int, int, float, int, int, Hub]] = [(0, 0, 0.0, -start_priority, counter, start)]

        best: dict[State, BestScore] = {start_state: (0, 0.0, start_priority)}
        came_from: dict[State, Optional[State]] = {start_state: None}

        while heap:
            turn, detour, cong, neg_prio, _, current = heapq.heappop(heap)
            prio = -neg_prio
            current_state: State = (current.name, turn)

            known_d, known_c, known_p = best.get(current_state, (10 ** 9, float("inf"), -1))
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
                conn_cap = conn.max_link_capacity if conn is not None else 1
                lk = self._link_key(current.name, neighbor.name)
                if link_reservation.get((lk, turn + 1), 0) >= conn_cap:
                    continue

                next_state: State = (neighbor.name, arrival)
                next_detour = (
                    detour +
                    self._movement_penalty(current_state, came_from, neighbor.name)
                )
                next_cong = (
                    cong +
                    self._congestion_cost(
                        current, neighbor, arrival, turn,
                        reservation, link_reservation, conn_cap,
                    )
                )
                next_prio = prio + (1 if neighbor.zone == "priority" else 0)

                known_d2, known_c2, known_p2 = best.get(
                    next_state, (10 ** 9, float("inf"), -1)
                )
                if (
                    next_detour > known_d2 or (
                        next_detour == known_d2 and (
                            next_cong > known_c2 or (
                                next_cong == known_c2 and next_prio <= known_p2
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
                                wait_cong == known_c2 and prio > known_p2
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


    def _rebuild(self, came_from: dict[State, Optional[State]], hub_map: dict[str, Hub], end: Hub, end_turn: int):
        states: list[State] = []
        entry: Optional[State] = (end.name, end_turn)

        while entry is not None:
            states.append(entry)
            entry = came_from.get(entry)

        states.reverse()
        return [(hub_map[name], turn) for name, turn in states[1:]]


    def register_path(self, steps: list[PathStep], start_name: str, reservation: dict[State, int], link_reservation: dict[tuple[LinkKey, int], int]):

        reservation[(start_name, 0)] = reservation.get((start_name, 0), 0) + 1
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
            link_state = (lk, prev_turn + 1)
            link_reservation[link_state] = (
                link_reservation.get(link_state, 0) + 1
            )
            prev_name = hub.name
            prev_turn = turn