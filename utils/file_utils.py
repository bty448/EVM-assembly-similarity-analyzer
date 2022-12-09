import os
from typing import IO


def read_text(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


def read_binary(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    with make_dirs_and_open(path, 'w', newline='') as f:
        f.write(content)


def write_binary(path: str, content: bytes) -> None:
    with make_dirs_and_open(path, 'wb') as f:
        f.write(content)


def make_dirs_and_open(path: str, mode: str, **kwargs) -> IO:
    """
    Creates the directory for the given path and opens the file
    :param path: The path to the file
    :param mode: The mode to open the file
    :return: The opened file
    """
    output_dir = os.path.dirname(path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return open(path, mode, **kwargs)
