import pytest

from mcp_tdo.tdo_client import TdoClient


@pytest.fixture
def tdo_server():
    return TdoClient(tdo_path="tdo")
