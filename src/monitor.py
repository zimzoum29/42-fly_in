"""
Turn-by-turn simulation runner for the Fly-in project.

The :class:`Monitor` routes every drone (via :class:`PathFinder`),
then replays all the resulting paths together to build the
turn-by-turn textual output described in subject VII.5.
"""

from .models import Drone, Map
from .pathfinding import LinkKey, PathFinder, PathStep, State


class Monitor:
    """Owns the simulation state: drones, paths, turns and output."""

    def __init__(self, game_map: Map) -> None:
        """
        Create a monitor for a given map.

        Args:
            game_map: The parsed map to simulate drones on.
        """
        self.map: Map = game_map
        self.drones: list[Drone] = []
        self.turn: int = 0
        self.output_lines: list[str] = []
        self._paths: list[list[PathStep]] = []
        self.pathfinder = PathFinder()

    def init_drones(self) -> None:
        """
        Create every drone and compute its reserved path.

        Drones are routed one at a time: each new path avoids the
        hub/connection capacity already reserved by previously
        routed drones.

        Raises:
            ValueError: If the map has no start or end hub.
        """
        if self.map.start_hub is None:
            raise ValueError("Map has no start_hub")
        if self.map.end_hub is None:
            raise ValueError("Map has no end_hub")

        start_name = self.map.start_hub.name

        reservation: dict[State, int] = {}
        link_reservation: dict[tuple[LinkKey, int], int] = {}

        for i in range(self.map.nb_drones):
            drone = Drone(i + 1, self.map.start_hub)
            steps = self.pathfinder.find_path(
                self.map,
                self.map.start_hub,
                self.map.end_hub,
                reservation,
                link_reservation,
            )
            if steps:
                self.pathfinder.register_path(
                    steps, start_name, reservation, link_reservation
                )
                self._paths.append(steps)
            else:
                self._paths.append([])
            self.drones.append(drone)

    @property
    def all_arrived(self) -> bool:
        """Whether every drone has reached the end zone."""
        return all(d.is_arrived for d in self.drones)

    def run(self, max_turns: int = 1000) -> None:
        """
        Replay every drone's path and build the output lines.

        Args:
            max_turns: Safety cap on the number of simulated turns.

        Raises:
            ValueError: If the map has no start or end hub.
        """
        if self.map.start_hub is None:
            raise ValueError("Map has no start_hub")
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

                if self.pathfinder.real_zone_cost(hub) == 2:
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
        """Print the simulation's turn-by-turn output lines."""
        for line in self.output_lines:
            print(line)

    def print_summary(self) -> None:
        """Print a short summary of the simulation result."""
        arrived = sum(1 for d in self.drones if d.is_arrived)
        print(f"Turns          : {self.turn}")
        print(f"Drones arrived : {arrived} / {len(self.drones)}")
