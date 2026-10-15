import pytest


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_unknown_path_returns_json_404(client, method):
    response = client.session.request(
        method,
        f"{client.base_url}/does-not-exist",
        timeout=3,
    )

    assert response.status_code == 404
    assert response.headers["Content-Type"].startswith("application/json")
    assert response.json() == {"code": "NOT_FOUND"}
