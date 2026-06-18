from typing import Optional


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


class Drone:

    def __init__(self, index, start_hub: Hub, path):

        self.index = index
        self.current_hub = start_hub
        self.path: list[Hub] = path
