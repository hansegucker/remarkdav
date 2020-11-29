from typing import List
from uuid import uuid4


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


def get_filename(path: str):
    return path.split("/")[-1]


def get_extension(path: str):
    return path.split(".")[-1]


def make_unique_filename(filename: str):
    return f"{uuid4()}_filename"


def has_extension(filename: str, extensions: List[str]):
    return get_extension(filename) in extensions
