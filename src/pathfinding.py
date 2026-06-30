import heapq
from typing import Optional
from .models import Hub, Map


_ZONE_COST: dict[str, float] = {
    "normal":     1.0,
    "priority":   0.9,
    "restricted": 2.0,
    "blocked":    float("inf"),
}


def entry_cost(hub: Hub) -> float:
    return _ZONE_COST.get(hub.zone, 1.0)


def real_zone_cost(hub: Hub) -> int:
    if hub.zone == "restricted":
        return 2
    return 1


def find_path(game_map: Map, start: Hub, end: Hub) -> list[Hub]:

    distances: dict[str, float] = {start.name: 0.0}

    came_from: dict[str, Optional[Hub]] = {start.name: None}

    counter = 0
    heap: list[tuple[float, int, Hub]] = [(0.0, counter, start)]

    while heap:
        cost, _, current = heapq.heappop(heap)
        if cost > distances.get(current.name, float("inf")):
            continue

        if current is end:
            return _rebuild_path(came_from, end)

        for neighbor in game_map.get_neighbors(current):
            step_cost = entry_cost(neighbor)

            if step_cost == float("inf"):
                continue

            new_cost = cost + step_cost

            if new_cost < distances.get(neighbor.name, float("inf")):
                distances[neighbor.name] = new_cost
                came_from[neighbor.name] = current
                counter += 1
                heapq.heappush(heap, (new_cost, counter, neighbor))

    return []


def _rebuild_path(
    came_from: dict[str, Optional[Hub]],
    end: Hub
) -> list[Hub]:
    path: list[Hub] = []
    current: Optional[Hub] = end

    while current is not None:
        path.append(current)
        current = came_from.get(current.name)

    path.reverse()
    return path


def path_cost(path: list[Hub]) -> int:
    if len(path) <= 1:
        return 0
    return sum(real_zone_cost(hub) for hub in path[1:])