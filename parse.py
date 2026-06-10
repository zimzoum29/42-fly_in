class ParsingError(Exception):
    pass


class Hub:
    def __init__(self, name, x, y, start, end):
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone: str = "normal"
        self.color: str = None
        self.max_drones: int = 1
        self.start_hub: bool = start
        self.end_hub: bool = end


class Connection:
    def __init__(self, hub1, hub2, max_link_capacity):
        self.hub1: Hub = hub1
        self.hub2: Hub = hub2
        self.max_link_capacity: int = max_link_capacity


class Map:
    def __init__(self):
        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.hubs = []
        self.connections = []

    def get_hub(self, name):
        for hub in self.hubs:
            if hub.name == name:
                return hub
        return None

    def parse_metadata(self, raw):
        metadata = {}

        allowed_keys = {"zone", "color", "max_drones"}
        if raw == "":
            return metadata

        for item in raw.split():
            if "=" not in item:
                raise ParsingError("Invalid metadata format")

            key, value = item.split("=", 1)

            if key not in allowed_keys:
                raise ParsingError(f"Unknown metadata: {key}")

            if key in metadata:
                raise ParsingError(f"Duplicate metadata: {key}")

            metadata[key] = value

        return metadata

    def add_hub(self, line, start_hub, end_hub):
        try:
            line = line.strip()
            metadata = {}

            if "[" in line:
                if not line.endswith("]"):
                    raise ParsingError("Invalid metadata block on hub")

                line, metadata_raw = line.split("[", 1)
                metadata_raw = metadata_raw[:-1].strip()
                metadata = self.parse_metadata(metadata_raw)

            param = line.split()

            if len(param) != 3:
                raise ParsingError("Invalid format on hub")

            name = param[0]

            if "#" in name:
                raise ParsingError("Invalid hub name")

            if self.get_hub(name) is not None:
                raise ParsingError(f"Duplicate hub name: {name}")

            x = int(param[1])
            y = int(param[2])

            hub = Hub(name, x, y, start_hub, end_hub)

            if "zone" in metadata:
                if metadata["zone"] not in {"normal", "blocked", "restricted", "priority"}:
                    raise ParsingError("Invalid zone type")
                hub.zone = metadata["zone"]

            if "color" in metadata:
                if " " in metadata["color"]:
                    raise ParsingError("Invalid color")
                hub.color = metadata["color"]

            if "max_drones" in metadata:
                hub.max_drones = int(metadata["max_drones"])
                if hub.max_drones <= 0:
                    raise ParsingError("max_drones must be positive")

            self.hubs.append(hub)
            return hub

        except ValueError:
            raise ParsingError("Invalid numeric value on hub")

    def add_connection(self, line):
        try:
            line = line.strip()
            metadata = {}

            if "[" in line:
                if not line.endswith("]"):
                    raise ParsingError("Invalid metadata block on connection")

                line, metadata_raw = line.split("[", 1)
                metadata_raw = metadata_raw[:-1].strip()
                metadata = self.parse_metadata(metadata_raw,{"max_link_capacity"}
                )

            if line.count("-") != 1:
                raise ParsingError("Invalid connection format")

            name1, name2 = line.split("-")

            if name1 == "" or name2 == "":
                raise ParsingError("Invalid connection format")

            hub1 = self.get_hub(name1)
            hub2 = self.get_hub(name2)

            if hub1 is None or hub2 is None:
                raise ParsingError("Connection uses unknown hub")

            for connection in self.connections:
                same_order = (connection.hub1.name == name1 and connection.hub2.name == name2)
                reverse_order = (connection.hub1.name == name2 and connection.hub2.name == name1)

                if same_order or reverse_order:
                    raise ParsingError("Duplicate connection")

            max_link_capacity = 1

            if "max_link_capacity" in metadata:
                max_link_capacity = int(metadata["max_link_capacity"])
                if max_link_capacity <= 0:
                    raise ParsingError("max_link_capacity must be positive")

            connection = Connection(hub1, hub2, max_link_capacity)
            self.connections.append(connection)
            return connection

        except ValueError:
            raise ParsingError("Invalid numeric value on connection")


def parse_input(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().splitlines()

        first_line = True
        map = Map()

        for line_number, line in enumerate(content, start=1):
            line = line.strip()

            if line == "" or line.startswith("#"):
                continue

            if ":" not in line:
                raise ParsingError("Missing ':'")

            split_line = line.split(":", 1)
            line_type = split_line[0].strip()
            param = split_line[1].strip()

            try:

                match line_type:

                    case "nb_drones":
                        if not first_line:
                            raise ParsingError("The first line must contain nb_drones")

                        nb_drones = int(param)

                        if nb_drones <= 0:
                            raise ParsingError("Number of drones must be positive")

                        map.nb_drones = nb_drones
                        first_line = False

                    case "start_hub":
                        if first_line:
                            raise ParsingError("The first line must contain nb_drones")
                        
                        if map.start_hub is not None:
                            raise ParsingError("The map must have only one start_hub")

                        map.start_hub = map.add_hub(param, True, False)

                    case "end_hub":
                        if first_line:
                            raise ParsingError("The first line must contain nb_drones")

                        if map.end_hub is not None:
                            raise ParsingError("The map must have only one end_hub")

                        map.end_hub = map.add_hub(param, False, True)

                    case "hub":
                        if first_line:
                            raise ParsingError(
                                "The first line must contain nb_drones"
                            )

                        map.add_hub(param, False, False)

                    case "connection":
                        if first_line:
                            raise ParsingError("The first line must contain nb_drones")

                        map.add_connection(param)

                    case _:
                        raise ParsingError(f"Unknown line type: {line_type}")

            except ParsingError as e:
                raise ParsingError(f"Line {line_number}: {e}")

        if map.nb_drones <= 0:
            raise ParsingError("Missing nb_drones")

        if map.start_hub is None:
            raise ParsingError("Missing start_hub")

        if map.end_hub is None:
            raise ParsingError("Missing end_hub")

        return map

    except ParsingError as e:
        print("[ERROR]", e)
        return None
    
parse_input("map.txt")