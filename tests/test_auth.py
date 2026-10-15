import pytest


@pytest.mark.smoke
def test_login_success(client):
    response = client.login()

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    token = response.json()["access_token"]
    assert isinstance(token, str)
    assert token


@pytest.mark.parametrize(
    ("username", "password"),
    [("tester", "wrong"), ("unknown", "secret123")],
)
def test_login_rejects_wrong_credentials(client, username, password):
    response = client.login(username, password)

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"password": "secret123"}, id="missing-username"),
        pytest.param({"username": "tester"}, id="missing-password"),
        pytest.param({"username": "", "password": "secret123"}, id="empty-username"),
        pytest.param({"username": "tester", "password": ""}, id="empty-password"),
    ],
)
def test_login_requires_both_fields(client, payload):
    response = client.session.post(f"{client.base_url}/login", json=payload, timeout=3)

    assert response.status_code == 400
    assert response.json()["code"] == "MISSING_CREDENTIALS"


@pytest.mark.parametrize(
    "payload",
    ["{", "", "[]", "null"],
    ids=["truncated", "empty", "array", "null"],
)
def test_login_rejects_malformed_json_and_remains_available(client, payload):
    response = client.session.post(
        f"{client.base_url}/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        timeout=3,
    )

    assert response.status_code == 400
    assert response.json() == {"code": "INVALID_JSON"}

    healthy = client.login()
    assert healthy.status_code == 200
    assert healthy.json()["access_token"]
