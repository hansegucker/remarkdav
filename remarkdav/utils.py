from typing import List

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError


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


def has_extension(filename: str, extensions: List[str]):
    return get_extension(filename) in extensions


def check_pdf_file(path: str) -> bool:
    """Check if a file is a valid PDF file."""
    try:
        PdfFileReader(open(path, "rb"))
    except PdfReadError:
        return False
    return True
