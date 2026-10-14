from http.server import HTTPServer
from threading import Thread

import pytest

from demo_api.server import make_handler
from tests.api_client import APIClient


@pytest.fixture
def base_url():
    # A fresh server per test gives each case the same initial inventory.
    server = HTTPServer(("127.0.0.1", 0), make_handler())
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


@pytest.fixture
def client(base_url):
    api = APIClient(base_url)
    try:
        yield api
    finally:
        api.close()


@pytest.fixture
def authorized_client(client):
    response = client.login()
    assert response.status_code == 200
    client.use_token(response.json()["access_token"])
    return client
