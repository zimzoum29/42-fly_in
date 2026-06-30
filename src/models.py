from typing import Optional
import pyray as rl


class ParsingError(Exception):
    pass


class Hub:

    def __init__(self, name: str, x: int, y: int, is_start: bool, is_end: bool) -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone: str = "normal"
        self.color: Optional[str] = None
        self.max_drones: int = 1
        self.is_start: bool = is_start
        self.is_end: bool = is_end


class Connection:

    def __init__(self, hub1: Hub, hub2: Hub, max_link_capacity: int) -> None:
        self.hub1: Hub = hub1
        self.hub2: Hub = hub2
        self.max_link_capacity: int = max_link_capacity

    def connects(self, hub: Hub) -> Optional["Hub"]:
        if self.hub1 is hub:
            return self.hub2
        if self.hub2 is hub:
            return self.hub1
        return None


class Drone:

    def __init__(self, index: int, start_hub: Hub) -> None:
        self.index: int = index
        self.current_hub: Hub = start_hub
        self.path: list[Hub] = []
        self.path_index: int = 0
        self.state: str = "waiting"
        self.transit_target: Optional[Hub] = None

    @property
    def is_arrived(self) -> bool:
        return self.state == "arrived"

    @property
    def next_hub(self) -> Optional[Hub]:
        if not self.path:
            return None
        next_index = self.path_index + 1
        if next_index >= len(self.path):
            return None
        return self.path[next_index]

    def assign_path(self, path: list[Hub]) -> None:
        self.path = path
        self.path_index = 0
        if len(path) <= 1:
            self.state = "arrived" if path and path[0].is_end else "waiting"
        else:
            self.state = "moving"

    def step_forward(self) -> None:
        self.path_index += 1
        self.current_hub = self.path[self.path_index]
        if self.current_hub.is_end:
            self.state = "arrived"


class Map:

    def __init__(self) -> None:
        self.nb_drones: int = 0
        self.start_hub: Optional[Hub] = None
        self.end_hub: Optional[Hub] = None
        self.hubs: list[Hub] = []
        self.connections: list[Connection] = []

    def get_hub(self, name: str) -> Optional[Hub]:
        for hub in self.hubs:
            if hub.name == name:
                return hub
        return None

    def get_neighbors(self, hub: Hub) -> list[Hub]:
        neighbors: list[Hub] = []
        for connection in self.connections:
            other = connection.connects(hub)
            if other is not None:
                neighbors.append(other)
        return neighbors

    def get_connection(self, hub1: Hub, hub2: Hub) -> Optional[Connection]:
        for connection in self.connections:
            if (
                (connection.hub1 is hub1 and connection.hub2 is hub2)
                or (connection.hub1 is hub2 and connection.hub2 is hub1)
            ):
                return connection
        return None



class ModelManager:

    _models: dict[str, rl.Model] = {}

    @classmethod
    def load(cls, key: str, path: str) -> rl.Model:
        if key not in cls._models:
            cls._models[key] = rl.load_model(path)
        return cls._models[key]

    @classmethod
    def get(cls, key: str) -> rl.Model:
        if key not in cls._models:
            raise KeyError(
                f"Model '{key}' was never loaded — call "
                f"ModelManager.load('{key}', <path>) before get()"
            )
        return cls._models[key]

    @classmethod
    def unload_all(cls) -> None:
        for model in cls._models.values():
            rl.unload_model(model)
        cls._models.clear()