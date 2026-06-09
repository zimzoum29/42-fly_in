

class ParsingError(Exception):
    ...

def parse_input(path):

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            