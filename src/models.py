"""Domain models for the Fly-in drone routing simulator.

This module defines the core data structures shared across the
project: map zones (:class:`Hub`), links between zones
(:class:`Connection`), drones (:class:`Drone`), the full map graph
(:class:`Map`), and a small cache for loaded 3D models
(:class:`ModelManager`).
"""

import pyray as rl


class ParsingError(Exception):
    """Raised when an input map file violates the expected format."""


class Hub:
    """A single zone (node) of the drone routing graph."""

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        is_start: bool,
        is_end: bool,
    ) -> None:
        """Create a hub.

        Args:
            name: Unique identifier of the zone.
            x: Integer x coordinate.
            y: Integer y coordinate.
            is_start: Whether this hub is the map's start zone.
            is_end: Whether this hub is the map's end zone.
        """
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone: str = "normal"
        self.color: str | None = None
        self.max_drones: int = 1
        self.is_start: bool = is_start
        self.is_end: bool = is_end


class Connection:
    """A bidirectional link between two hubs."""

    def __init__(
        self, hub1: Hub, hub2: Hub, max_link_capacity: int
    ) -> None:
        """
        Create a connection.

        Args:
            hub1: One endpoint of the connection.
            hub2: The other endpoint of the connection.
            max_link_capacity: Maximum number of drones that may
                traverse this connection during the same turn.
        """
        self.hub1: Hub = hub1
        self.hub2: Hub = hub2
        self.max_link_capacity: int = max_link_capacity

    def connects(self, hub: Hub) -> Hub | None:
        """
        Return the hub on the other side of ``hub``, if any.

        Args:
            hub: The hub to look up.

        Returns:
            The neighboring hub if ``hub`` is one of this
            connection's endpoints, otherwise ``None``.
        """
        if self.hub1 is hub:
            return self.hub2
        if self.hub2 is hub:
            return self.hub1
        return None


class Drone:
    """A single drone travelling from the start hub to the end hub."""

    def __init__(self, index: int, start_hub: Hub) -> None:
        """
        Create a drone positioned at the start hub.

        Args:
            index: 1-based identifier of the drone (used as D<index>
                in the simulation output).
            start_hub: The hub the drone begins its journey at.
        """
        self.index: int = index
        self.current_hub: Hub = start_hub
        self.path: list[Hub] = []
        self.path_index: int = 0
        self.state: str = "waiting"
        self.transit_target: Hub | None = None

    @property
    def is_arrived(self) -> bool:
        """Whether the drone has reached the end zone."""
        return self.state == "arrived"

    @property
    def next_hub(self) -> Hub | None:
        """The next hub on this drone's assigned path, if any."""
        if not self.path:
            return None
        next_index = self.path_index + 1
        if next_index >= len(self.path):
            return None
        return self.path[next_index]

    def assign_path(self, path: list[Hub]) -> None:
        """
        Assign a full path to this drone and reset its cursor.

        Args:
            path: Ordered list of hubs the drone will visit.
        """
        self.path = path
        self.path_index = 0
        if len(path) <= 1:
            self.state = "arrived" if path and path[0].is_end else "waiting"
        else:
            self.state = "moving"

    def step_forward(self) -> None:
        """Advance the drone to the next hub on its assigned path."""
        self.path_index += 1
        self.current_hub = self.path[self.path_index]
        if self.current_hub.is_end:
            self.state = "arrived"


class Map:
    """The full graph of hubs and connections for one simulation."""

    def __init__(self) -> None:
        """Create an empty map."""
        self.nb_drones: int = 0
        self.start_hub: Hub | None = None
        self.end_hub: Hub | None = None
        self.hubs: list[Hub] = []
        self.connections: list[Connection] = []

    def get_hub(self, name: str) -> Hub | None:
        """
        Look up a hub by name.

        Args:
            name: Name of the hub to find.

        Returns:
            The matching hub, or ``None`` if no hub has that name.
        """
        for hub in self.hubs:
            if hub.name == name:
                return hub
        return None

    def get_neighbors(self, hub: Hub) -> list[Hub]:
        """
        List all hubs directly connected to ``hub``.

        Args:
            hub: The hub whose neighbors are requested.

        Returns:
            The list of hubs reachable through a single connection.
        """
        neighbors: list[Hub] = []
        for connection in self.connections:
            other = connection.connects(hub)
            if other is not None:
                neighbors.append(other)
        return neighbors

    def get_connection(
        self, hub1: Hub, hub2: Hub
    ) -> Connection | None:
        """
        Find the connection between two hubs, in either order.

        Args:
            hub1: One endpoint.
            hub2: The other endpoint.

        Returns:
            The matching connection, or ``None`` if the hubs are not
            directly connected.
        """
        for connection in self.connections:
            if (
                (connection.hub1 is hub1 and connection.hub2 is hub2)
                or (connection.hub1 is hub2 and connection.hub2 is hub1)
            ):
                return connection
        return None


class ModelManager:
    """Small cache so each 3D model is loaded from disk only once."""

    _models: dict[str, rl.Model] = {}

    @classmethod
    def load(cls, key: str, path: str) -> rl.Model:
        """
        Load (or fetch from cache) the model stored at ``path``.

        Args:
            key: Cache key to store the model under.
            path: Filesystem path to the model asset.

        Returns:
            The loaded raylib model.
        """
        if key not in cls._models:
            cls._models[key] = rl.load_model(path)
        return cls._models[key]

    @classmethod
    def get(cls, key: str) -> rl.Model:
        """
        Fetch a previously loaded model.

        Args:
            key: Cache key the model was loaded under.

        Returns:
            The cached raylib model.

        Raises:
            KeyError: If ``load`` was never called for this key.
        """
        if key not in cls._models:
            raise KeyError(
                f"Model '{key}' was never loaded — call "
                f"ModelManager.load('{key}', <path>) before get()"
            )
        return cls._models[key]

    @classmethod
    def unload_all(cls) -> None:
        """Unload every cached model and clear the cache."""
        for model in cls._models.values():
            rl.unload_model(model)
        cls._models.clear()
