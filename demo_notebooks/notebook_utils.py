import sys
from pathlib import Path


def initialize_environment():
    BASE_DIR = str(Path("./../").resolve())
    if BASE_DIR not in sys.path:
        sys.path.append(BASE_DIR)


def print_heading(text: str):
    print("###############################\n")
    print(text)
    print("\n###############################")


class Color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
