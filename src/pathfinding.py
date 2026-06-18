from .models import Hub

def path_cost(path: list[Hub]):
    cost = 0

    for hub in path:
        if hub.is_start:
            continue

        match (hub.zone):
            
            case "restricted":
                cost += 2.0

            case "priority":
                cost += 1.0
            
            case "normal":
                cost += 0.9

            case "blocked":
                cost += float("inf")

    return cost
