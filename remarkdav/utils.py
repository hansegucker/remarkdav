def clean_path(path: str) -> str:
    if path[-1] != "/":
        path += "/"
    return path


def simple_path(path: str) -> str:
    return path.replace("/", "")


def last_part_of_path(path: str) -> str:
    if path[-1] == "/":
        path = path[:-1]
    return path.split("/")[-1].replace("/", "")
