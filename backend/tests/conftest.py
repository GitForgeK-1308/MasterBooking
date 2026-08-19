import pytest

pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.client",
    "tests.fixtures.users",
]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"