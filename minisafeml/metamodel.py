from pathlib import Path
from textx import metamodel_from_file


def grammar_path() -> Path:
    return Path(__file__).parent / "grammar" / "minisafeml.tx"


def build_metamodel():
    return metamodel_from_file(str(grammar_path()))
