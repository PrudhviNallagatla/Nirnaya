import os
import pytest

from nirnaya.core.parser import HeaderParser


@pytest.fixture
def parser() -> HeaderParser:
    return HeaderParser()


@pytest.fixture
def fixtures_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))
