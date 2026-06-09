
class ParsingError(Exception):
    ...
    
    
class Map:
    def __init__(self):
        self.nb_drones = 0
        self.start_hub = None
        self.end_hub = None
        self.hubs = []
        self.connections = []

    def add_hub(self, line, start_hub, end_hub):
        try:
            name = line.split(" ")[1]
            x = int(line.split(" ")[2])
            y = int(line.split(" ")[3])
            hub = Hub(name, x, y, start_hub, end_hub)
            self.hubs.append(hub)
        except ValueError:
            raise ParsingError("Invvalid type on hub")


class Hub:
    def __init__(self, name, x, y, start, end):
        self.name = name
        self.x = x
        self.y = y
        self.start_hub = start
        self.end_hub = end


class Connection:
    def __init__(self):
        self.name = ""
        self.x = 0
        self.y = 0

def parse_input(path):

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().split("\n")

        first_line = True
        map = Map()

        for line in content:

            if line == "" or line[0] == "#":
                continue
            line = line.split("#")[0]

            type = line.split(":")[0]
            match type:

                case "nb_drones":
                    if not first_line:
                        raise ParsingError("The first line must contain the number of drones (format: nb_drones: 5)")
                    nb_drones = int(line.split(" ")[1])
                    if nb_drones <= 0:
                        raise ParsingError("Number of drones must be an positive integer")
                    map.nb_drones = nb_drones
                    first_line = False

                case "start_hub":
                    if first_line:
                        raise ParsingError("The first line must contain the number of drones (format: nb_drones: 5)")
                    if map.start_hub != None:
                        raise ParsingError("The map must have only one start_hub")
                    map.start_hub = map.add_hub(line, True, False)
                    first_line = False

                case "end_hub":
                    if first_line:
                        raise ParsingError("The first line must contain the number of drones (format: nb_drones: 5)")
                    if map.end_hub != None:
                        raise ParsingError("The map must have only one end_hub")
                    map.end_hub = map.add_hub(line, False, True)
                    first_line = False

                case "hub":
                    if first_line:
                        raise ParsingError("The first line must contain the number of drones (format: nb_drones: 5)")
                    map.add_hub(line, False, False)
                    first_line = False

                case "connection":
                    pass

                case _:
                    raise ParsingError("The types must be part of nb_drones, start_hub, hub, end_hub or connection")

    except Exception as e:
        print("[ERROR]", e)

parse_input("maps/easy/01_linear_path.txt")