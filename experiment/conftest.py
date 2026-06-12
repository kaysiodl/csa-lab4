import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "translator"))


def pytest_addoption(parser):
    parser.addoption("--regen", action="store_true", default=False)
