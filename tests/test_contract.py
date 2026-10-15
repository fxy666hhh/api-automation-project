import json
from pathlib import Path

import pytest
from jsonschema import validate


def assert_matches_schema(data, schema_name):
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validate(instance=data, schema=schema)


def test_created_order_matches_schema(authorized_client):
    response = authorized_client.create_order()
    assert response.status_code == 201
    assert_matches_schema(response.json(), "order.json")


def test_products_match_schema(client):
    response = client.products()
    assert response.status_code == 200
    assert_matches_schema(response.json(), "products.json")


def request_order_with_invalid_token(client):
    client.use_token("wrong-token")
    return client.create_order()


@pytest.mark.parametrize(
    ("call_api", "expected_status", "expected_code"),
    [
        pytest.param(
            lambda client: client.login(password=""),
            400,
            "MISSING_CREDENTIALS",
            id="missing-credentials",
        ),
        pytest.param(
            lambda client: client.login(password="wrong"),
            401,
            "INVALID_CREDENTIALS",
            id="invalid-credentials",
        ),
        pytest.param(
            request_order_with_invalid_token,
            401,
            "UNAUTHORIZED",
            id="unauthorized-order",
        ),
        pytest.param(
            lambda client: client.create_order(quantity=0),
            400,
            "INVALID_QUANTITY",
            id="invalid-quantity",
        ),
        pytest.param(
            lambda client: client.create_order(product_id=999),
            404,
            "PRODUCT_NOT_FOUND",
            id="unknown-product",
        ),
        pytest.param(
            lambda client: client.create_order(
                quantity=client.products().json()["products"][0]["stock"] + 1
            ),
            409,
            "INSUFFICIENT_STOCK",
            id="insufficient-stock",
        ),
        pytest.param(
            lambda client: client.get_order("not-here"),
            404,
            "ORDER_NOT_FOUND",
            id="unknown-order",
        ),
    ],
)
def test_error_responses_match_schema(
    authorized_client, call_api, expected_status, expected_code
):
    stock_before = authorized_client.products().json()["products"][0]["stock"]
    response = call_api(authorized_client)

    assert response.status_code == expected_status
    body = response.json()
    assert body["code"] == expected_code
    assert_matches_schema(body, "error.json")

    stock_after = authorized_client.products().json()["products"][0]["stock"]
    assert stock_after == stock_before
