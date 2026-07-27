"""
3D visualization layer built on raylib (pyray).

Draws the map (hubs as colored spheres, connections as cylinders)
and interpolates each drone's on-screen position between the hubs
of its reserved path, so the simulation can be watched turn by turn
(subject VII.1's "graphical interface" visual-representation option).
"""

from pyray import (
    WHITE,
    Vector3,
    draw_cylinder_ex,
    draw_model_ex,
    draw_sphere,
)

from .models import Connection, Hub, Map, ModelManager
from .pathfinding import PathStep

_COLOR_MAP = {
    "red": (230, 41, 55, 255),
    "green": (0, 228, 48, 255),
    "blue": (0, 121, 241, 255),
    "yellow": (253, 249, 0, 255),
    "gray": (130, 130, 130, 255),
    "grey": (130, 130, 130, 255),
    "orange": (255, 161, 0, 255),
    "purple": (200, 122, 255, 255),
    "cyan": (0, 247, 247, 255),
    "white": (255, 255, 255, 255),
    "black": (20, 20, 20, 255),
    "maroon": (112, 31, 22, 255),
    "brown": (127, 95, 0, 255),
    "gold": (255, 203, 0, 255),
    "violet": (135, 60, 190, 255),
    "crimson": (220, 20, 60, 255),
}
_DEFAULT_COLOR = (0, 121, 241, 255)
_START_COLOR = (0, 228, 48, 255)
_END_COLOR = (253, 249, 0, 255)
_CONN_COLOR = (130, 130, 130, 255)
_DRONE_MODEL_KEY = "drone"

_SCALE = 3.0


class Graphic:
    """Stateless helper drawing a :class:`Map` and its drones."""

    def __init__(self) -> None:
        """Create a stateless graphic renderer instance."""

    def hub_color(self, hub: Hub) -> tuple[int, int, int, int]:
        """
        Resolve the RGBA color a hub should be drawn with.

        Args:
            hub: The hub to color.

        Returns:
            An RGBA tuple: the hub's explicit ``color`` metadata if
            set, otherwise a default based on whether it is the
            start/end hub.
        """
        if hub.is_start and hub.color is None:
            return _START_COLOR
        if hub.is_end and hub.color is None:
            return _END_COLOR
        if hub.color is not None:
            return _COLOR_MAP.get(hub.color.lower(), _DEFAULT_COLOR)
        return _DEFAULT_COLOR

    def _lerp(self, a: float, b: float, t: float) -> float:
        """Linearly interpolate between ``a`` and ``b`` by ``t``."""
        return a + (b - a) * t

    def _hub_pos(self, hub: Hub) -> Vector3:
        """World-space position of a hub, scaled for the 3D scene."""
        return Vector3(hub.x * _SCALE, 1.5, hub.y * _SCALE)

    def drone_position(
        self, steps: list[PathStep], start_hub: Hub, turn: float
    ) -> Vector3:
        """
        Interpolate a drone's on-screen position at a given turn.

        Args:
            steps: The drone's reserved path.
            start_hub: Hub the drone started from.
            turn: Fractional turn value (allows smooth animation
                between two integer turns).

        Returns:
            The drone's interpolated world-space position.
        """
        prev_hub, prev_turn = start_hub, 0.0
        for step_hub, step_turn in steps:
            if step_turn <= turn:
                prev_hub, prev_turn = step_hub, float(step_turn)
                continue
            span = step_turn - prev_turn
            t = (turn - prev_turn) / span if span > 0 else 1.0
            p0, p1 = self._hub_pos(prev_hub), self._hub_pos(step_hub)
            return Vector3(
                self._lerp(p0.x, p1.x, t),
                self._lerp(p0.y, p1.y, t),
                self._lerp(p0.z, p1.z, t),
            )
        return self._hub_pos(prev_hub)

    def draw_drone_at(self, pos: Vector3) -> None:
        """
        Draw the drone model at a given world-space position.

        Args:
            pos: World-space position to draw the drone at.
        """
        model = ModelManager.get(_DRONE_MODEL_KEY)
        draw_model_ex(
            model, pos,
            Vector3(0.0, 1.0, 0.0), -90.0,
            Vector3(1.0, 1.0, 1.0), WHITE,
        )

    def draw_drones_at_turn(
        self,
        paths: list[list[PathStep]],
        start_hub: Hub,
        turn: float,
    ) -> None:
        """
        Draw every drone at its interpolated position for a turn.

        Args:
            paths: Every drone's reserved path.
            start_hub: Hub every drone started from.
            turn: Fractional turn value to render.
        """
        for steps in paths:
            if not steps:
                continue
            self.draw_drone_at(self.drone_position(steps, start_hub, turn))

    def draw_connection(self, connection: Connection) -> None:
        """
        Draw a connection as a thin cylinder between its hubs.

        Args:
            connection: The connection to draw.
        """
        p1 = Vector3(
            connection.hub1.x * _SCALE, 0.5, connection.hub1.y * _SCALE
        )
        p2 = Vector3(
            connection.hub2.x * _SCALE, 0.5, connection.hub2.y * _SCALE
        )
        draw_cylinder_ex(p1, p2, 0.1, 0.1, 8, _CONN_COLOR)

    def draw_hub(self, hub: Hub) -> None:
        """
        Draw a hub as a colored sphere.

        Args:
            hub: The hub to draw.
        """
        pos = Vector3(hub.x * _SCALE, 0.5, hub.y * _SCALE)
        draw_sphere(pos, 0.5, self.hub_color(hub))

    def draw_map(self, game_map: Map) -> None:
        """
        Draw every connection and hub of a map.

        Args:
            game_map: The map to draw.
        """
        for connection in game_map.connections:
            self.draw_connection(connection)
        for hub in game_map.hubs:
            self.draw_hub(hub)
