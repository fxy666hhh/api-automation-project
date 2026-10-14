import pytest
@pytest.mark.smoke

def test_login_success(client):
    response = client.login()

    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert isinstance(response.json()["access_token"], str)


@pytest.mark.parametrize(
    ("username", "password"),
    [("tester", "wrong"), ("unknown", "secret123")],
)
def test_login_rejects_wrong_credentials(client, username, password):
    response = client.login(username, password)

    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_login_requires_both_fields(client):
    response = client.login(password="")

    assert response.status_code == 400
    assert response.json()["code"] == "MISSING_CREDENTIALS"
