import pytest

from solawi.app import app


@pytest.fixture
def app_ctx():
    with app.app_context():
        yield
