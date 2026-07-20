from .models import Drone, Hub, Map
from .pathfinding import (find_path, register_path, real_zone_cost, PathStep, State, LinkKey)


class Monitor:

    def __init__(self, game_map: Map) -> None:
        self.map: Map = game_map
        self.drones: list[Drone] = []
        self.turn: int = 0
        self.output_lines: list[str] = []
        self._paths: list[list[PathStep]] = []

    def init_drones(self) -> None:
        if self.map.start_hub is None:
            raise ValueError("Map has no start_hub")
        if self.map.end_hub is None:
            raise ValueError("Map has no end_hub")

        start_name = self.map.start_hub.name

        reservation: dict[State, int] = {}
        link_reservation: dict[tuple[LinkKey, int], int] = {}

        for i in range(self.map.nb_drones):
            drone = Drone(i + 1, self.map.start_hub)
            steps = find_path(
                self.map,
                self.map.start_hub,
                self.map.end_hub,
                reservation,
                link_reservation,
            )
            if steps:
                register_path(steps, start_name, reservation, link_reservation)
                self._paths.append(steps)
            else:
                self._paths.append([])
            self.drones.append(drone)

    @property
    def all_arrived(self) -> bool:
        return all(d.is_arrived for d in self.drones)

    def run(self, max_turns: int = 1000) -> None:
        if self.map.end_hub is None:
            raise ValueError("Map has no end_hub")
        if not self._paths:
            return

        last_turns = [
            steps[-1][1] for steps in self._paths if steps
        ]
        if not last_turns:
            return
        total_turns = min(max(last_turns), max_turns)

        turns: list[list[str]] = [[] for _ in range(total_turns)]

        for drone_id, steps in enumerate(self._paths):
            if not steps:
                continue
            pos = self.map.start_hub.name
            pos_turn = 0

            for hub, turn in steps:
                if hub.name == pos:
                    pos_turn = turn
                    continue

                if real_zone_cost(hub) == 2:
                    turns[pos_turn].append(
                        f"D{drone_id + 1}-{pos}-{hub.name}"
                    )

                pos = hub.name
                pos_turn = turn
                if turn - 1 < total_turns:
                    turns[turn - 1].append(f"D{drone_id + 1}-{pos}")

            self.drones[drone_id].state = "arrived"
            if steps:
                self.drones[drone_id].current_hub = steps[-1][0]

        for turn_list in turns:
            line = " ".join(turn_list)
            if line:
                self.output_lines.append(line)

        self.turn = total_turns

    def print_output(self) -> None:
        for line in self.output_lines:
            print(line)

    def print_summary(self) -> None:
        arrived = sum(1 for d in self.drones if d.is_arrived)
        print(f"Turns          : {self.turn}")
        print(f"Drones arrived : {arrived} / {len(self.drones)}")