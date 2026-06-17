from typing import Optional
from .models import Hub, Connection, Map, ParsingError

_HUB_METADATA_KEYS = {"zone", "color", "max_drones"}

_CONNECTION_METADATA_KEYS = {"max_link_capacity"}

_VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}


def _parse_metadata(
    raw: str,
    allowed_keys: set[str],
    line_number: int
) -> dict[str, str]:
    metadata: dict[str, str] = {}

    if raw == "":
        return metadata

    for item in raw.split():
        if "=" not in item:
            raise ParsingError(
                f"Line {line_number}: Invalid metadata format '{item}'"
            )

        key, value = item.split("=", 1)

        if key not in allowed_keys:
            raise ParsingError(
                f"Line {line_number}: Unknown metadata key '{key}'"
                f" (allowed: {sorted(allowed_keys)})"
            )

        if key in metadata:
            raise ParsingError(
                f"Line {line_number}: Duplicate metadata key '{key}'"
            )

        metadata[key] = value

    return metadata


def _parse_hub_line(param: str, is_start: bool, is_end: bool, game_map: Map, line_number: int) -> Hub:
    line = param.strip()
    metadata: dict[str, str] = {}

    if "[" in line:
        if not line.endswith("]"):
            raise ParsingError(
                f"Line {line_number}: Metadata block is not properly closed"
            )
        line, metadata_raw = line.split("[", 1)
        metadata_raw = metadata_raw[:-1].strip()
        metadata = _parse_metadata(metadata_raw, _HUB_METADATA_KEYS, line_number)

    parts = line.split()

    if len(parts) != 3:
        raise ParsingError(
            f"Line {line_number}: Hub definition expects 'name x y'"
            f", got {len(parts)} token(s)"
        )

    name = parts[0]

    # Zone names must not contain dashes (connection syntax relies on them)
    if "-" in name:
        raise ParsingError(
            f"Line {line_number}: Hub name '{name}' must not contain dashes"
        )

    if game_map.get_hub(name) is not None:
        raise ParsingError(
            f"Line {line_number}: Duplicate hub name '{name}'"
        )

    try:
        x = int(parts[1])
        y = int(parts[2])
    except ValueError:
        raise ParsingError(
            f"Line {line_number}: Hub coordinates must be integers"
        )

    hub = Hub(name, x, y, is_start, is_end)

    if "zone" in metadata:
        if metadata["zone"] not in _VALID_ZONE_TYPES:
            raise ParsingError(
                f"Line {line_number}: Invalid zone type '{metadata['zone']}'"
                f" (must be one of {sorted(_VALID_ZONE_TYPES)})"
            )
        hub.zone = metadata["zone"]

    if "color" in metadata:
        color = metadata["color"]
        if " " in color:
            raise ParsingError(
                f"Line {line_number}: Color must be a single word, got '{color}'"
            )
        hub.color = color

    if "max_drones" in metadata:
        try:
            max_drones = int(metadata["max_drones"])
        except ValueError:
            raise ParsingError(
                f"Line {line_number}: max_drones must be an integer"
            )
        if max_drones <= 0:
            raise ParsingError(
                f"Line {line_number}: max_drones must be a positive integer"
            )
        hub.max_drones = max_drones

    game_map.hubs.append(hub)
    return hub


def _parse_connection_line(
    param: str, game_map: Map, line_number: int) -> Connection:
    line = param.strip()
    metadata: dict[str, str] = {}

    if "[" in line:
        if not line.endswith("]"):
            raise ParsingError(
                f"Line {line_number}: Metadata block is not properly closed"
            )
        line, metadata_raw = line.split("[", 1)
        metadata_raw = metadata_raw[:-1].strip()
        metadata = _parse_metadata(
            metadata_raw, _CONNECTION_METADATA_KEYS, line_number
        )

    line = line.strip()

    if line.count("-") != 1:
        raise ParsingError(
            f"Line {line_number}: Connection must be in format 'zone1-zone2'"
        )

    name1, name2 = line.split("-")
    name1 = name1.strip()
    name2 = name2.strip()

    if not name1 or not name2:
        raise ParsingError(
            f"Line {line_number}: Connection hub names must not be empty"
        )

    hub1 = game_map.get_hub(name1)
    hub2 = game_map.get_hub(name2)

    if hub1 is None:
        raise ParsingError(
            f"Line {line_number}: Unknown hub '{name1}' in connection"
        )
    if hub2 is None:
        raise ParsingError(
            f"Line {line_number}: Unknown hub '{name2}' in connection"
        )

    if game_map.get_connection(hub1, hub2) is not None:
        raise ParsingError(
            f"Line {line_number}: Duplicate connection '{name1}-{name2}'"
        )

    max_link_capacity = 1

    if "max_link_capacity" in metadata:
        try:
            max_link_capacity = int(metadata["max_link_capacity"])
        except ValueError:
            raise ParsingError(
                f"Line {line_number}: max_link_capacity must be an integer"
            )
        if max_link_capacity <= 0:
            raise ParsingError(
                f"Line {line_number}: max_link_capacity must be a positive integer"
            )

    connection = Connection(hub1, hub2, max_link_capacity)
    game_map.connections.append(connection)
    return connection


def parse_input(path: str) -> Optional[Map]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().splitlines()
    except OSError as e:
        print(f"[ERROR] Cannot open file '{path}': {e}")
        return None

    game_map = Map()
    nb_drones_seen = False

    for line_number, raw_line in enumerate(content, start=1):
        line = raw_line.strip()

        if line == "" or line.startswith("#"):
            continue

        if ":" not in line:
            print(f"[ERROR] Line {line_number}: Missing ':' separator")
            return None

        line_type, _, param = line.partition(":")
        line_type = line_type.strip()
        param = param.strip()

        try:
            match line_type:

                case "nb_drones":
                    if nb_drones_seen:
                        raise ParsingError(
                            f"Line {line_number}: 'nb_drones' defined more than once"
                        )
                    if not nb_drones_seen and game_map.start_hub is not None:
                        raise ParsingError(
                            f"Line {line_number}: 'nb_drones' must be the first line"
                        )
                    try:
                        nb_drones = int(param)
                    except ValueError:
                        raise ParsingError(
                            f"Line {line_number}: nb_drones must be an integer"
                        )
                    if nb_drones <= 0:
                        raise ParsingError(
                            f"Line {line_number}: nb_drones must be a positive integer"
                        )
                    game_map.nb_drones = nb_drones
                    nb_drones_seen = True

                case "start_hub":
                    if not nb_drones_seen:
                        raise ParsingError(
                            f"Line {line_number}: 'nb_drones' must appear first"
                        )
                    if game_map.start_hub is not None:
                        raise ParsingError(
                            f"Line {line_number}: Only one 'start_hub' is allowed"
                        )
                    hub = _parse_hub_line(param, True, False, game_map, line_number)
                    game_map.start_hub = hub

                case "end_hub":
                    if not nb_drones_seen:
                        raise ParsingError(
                            f"Line {line_number}: 'nb_drones' must appear first"
                        )
                    if game_map.end_hub is not None:
                        raise ParsingError(
                            f"Line {line_number}: Only one 'end_hub' is allowed"
                        )
                    hub = _parse_hub_line(param, False, True, game_map, line_number)
                    game_map.end_hub = hub

                case "hub":
                    if not nb_drones_seen:
                        raise ParsingError(
                            f"Line {line_number}: 'nb_drones' must appear first"
                        )
                    _parse_hub_line(param, False, False, game_map, line_number)

                case "connection":
                    if not nb_drones_seen:
                        raise ParsingError(
                            f"Line {line_number}: 'nb_drones' must appear first"
                        )
                    _parse_connection_line(param, game_map, line_number)

                case _:
                    raise ParsingError(
                        f"Line {line_number}: Unknown line type '{line_type}'"
                    )

        except ParsingError as e:
            print(f"[ERROR] {e}")
            return None

    if not nb_drones_seen:
        print("[ERROR] Missing 'nb_drones' declaration")
        return None

    if game_map.start_hub is None:
        print("[ERROR] Missing 'start_hub' declaration")
        return None

    if game_map.end_hub is None:
        print("[ERROR] Missing 'end_hub' declaration")
        return None

    return game_map