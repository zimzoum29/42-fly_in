from .models import Drone, Hub, Map
from .pathfinding import find_path


class Monitor:

    def __init__(self, game_map: Map) -> None:
        self.map: Map = game_map
        self.drones: list[Drone] = []
        self.turn: int = 0
        self.output_lines: list[str] = []


    def init_drones(self) -> None:

        if self.map.start_hub is None:
            raise ValueError("Cannot init drones: map has no start_hub")
        if self.map.end_hub is None:
            raise ValueError("Cannot init drones: map has no end_hub")

        path = find_path(self.map, self.map.start_hub, self.map.end_hub)

        for i in range(self.map.nb_drones):
            drone = Drone(i + 1, self.map.start_hub)
            if path:
                drone.assign_path(list(path))
            self.drones.append(drone)


    @property
    def all_arrived(self) -> bool:
        return all(d.is_arrived for d in self.drones)

    def _active_drones(self) -> list[Drone]:
        return [d for d in self.drones if not d.is_arrived]

    def _drones_staying_at(self, hub: Hub) -> int:
        return sum(
            1 for d in self.drones
            if not d.is_arrived and d.current_hub is hub
        )

    def _hub_free_capacity(self, hub: Hub, claimed: list[Hub]) -> int:

        if hub.is_start or hub.is_end:
            return 10 ** 9

        occupied = self._drones_staying_at(hub)
        reserved = claimed.count(hub)
        return max(0, hub.max_drones - occupied - reserved)

    def _link_free_capacity(self, from_hub: Hub, to_hub: Hub, claimed_links: list[tuple[Hub, Hub]]) -> int:
        
        connection = self.map.get_connection(from_hub, to_hub)
        if connection is None:
            return 0

        used = sum(
            1 for f, t in claimed_links
            if (f is from_hub and t is to_hub) or (f is to_hub and t is from_hub)
        )
        return max(0, connection.max_link_capacity - used)

    def next_turn(self) -> None:

        if self.all_arrived:
            return

        self.turn += 1
        movements: list[str] = []
        claimed_hubs: list[Hub] = []
        claimed_links: list[tuple[Hub, Hub]] = []

        active = self._active_drones()

        for drone in active:
            if drone.state != "in_transit":
                continue

            target = drone.transit_target
            if target is None:
                raise RuntimeError(
                    f"Invariant broken: D{drone.index} is in_transit "
                    f"but has no transit_target"
                )

            if self._hub_free_capacity(target, claimed_hubs) > 0:
                claimed_hubs.append(target)
                drone.step_forward()
                if not drone.is_arrived:
                    drone.state = "moving"
                drone.transit_target = None
                movements.append(f"D{drone.index}-{target.name}")

        moving = sorted((d for d in active if d.state == "moving"), key=lambda d: d.index)

        for drone in moving:
            target = drone.next_hub
            if target is None:
                drone.state = "arrived"
                continue

            zone_ok = self._hub_free_capacity(target, claimed_hubs) > 0
            link_ok = self._link_free_capacity(
                drone.current_hub, target, claimed_links
            ) > 0

            if not (zone_ok and link_ok):
                continue

            claimed_hubs.append(target)
            claimed_links.append((drone.current_hub, target))

            if target.zone == "restricted":
                drone.state = "in_transit"
                drone.transit_target = target
                connection = self.map.get_connection(drone.current_hub, target)
                label = (
                    f"{drone.current_hub.name}-{target.name}"
                    if connection is not None
                    else target.name
                )
                movements.append(f"D{drone.index}-{label}")
            else:
                drone.step_forward()
                movements.append(f"D{drone.index}-{target.name}")

        if movements:
            line = " ".join(movements)
            self.output_lines.append(line)

    def run(self, max_turns: int = 1000) -> None:
        while not self.all_arrived and self.turn < max_turns:
            self.next_turn()

    def print_output(self) -> None:
        for line in self.output_lines:
            print(line)

    def print_summary(self) -> None:
        arrived = sum(1 for d in self.drones if d.is_arrived)
        print(f"Turns          : {self.turn}")
        print(f"Drones arrived : {arrived} / {len(self.drones)}")