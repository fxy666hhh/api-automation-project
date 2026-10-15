import json

import pytest

from tests.assertions import assert_error


@pytest.mark.parametrize(
    "product_id",
    [None, 0, -1, True, 1.5, "101", [], {}],
    ids=["null", "zero", "negative", "boolean", "decimal", "string", "array", "object"],
)
def test_order_rejects_invalid_product_id_without_changing_inventory(
    authorized_client, product_id
):
    before = authorized_client.products().json()
    response = authorized_client.create_order(product_id=product_id)

    assert_error(response, 400, "INVALID_PRODUCT_ID")
    assert authorized_client.products().json() == before


@pytest.mark.parametrize(
    "quantity",
    [True, 1.5, [], {}, ""],
    ids=["boolean", "decimal", "array", "object", "empty-string"],
)
def test_order_rejects_more_invalid_quantity_types(authorized_client, quantity):
    before = authorized_client.products().json()
    assert_error(authorized_client.create_order(quantity=quantity), 400, "INVALID_QUANTITY")
    assert authorized_client.products().json() == before


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        ({"quantity": 1}, "INVALID_PRODUCT_ID"),
        ({"product_id": 101}, "INVALID_QUANTITY"),
        ({}, "INVALID_PRODUCT_ID"),
    ],
    ids=["missing-product", "missing-quantity", "empty-object"],
)
def test_order_rejects_missing_required_fields(authorized_client, payload, expected_code):
    before = authorized_client.products().json()
    response = authorized_client.session.post(
        f"{authorized_client.base_url}/orders", json=payload, timeout=3
    )
    assert_error(response, 400, expected_code)
    assert authorized_client.products().json() == before


@pytest.mark.parametrize(
    "payload",
    [
        {"username": 0, "password": "secret123"},
        {"username": [], "password": "secret123"},
        {"username": "tester", "password": False},
        {"username": "tester", "password": {}},
    ],
    ids=["numeric-username", "array-username", "boolean-password", "object-password"],
)
def test_login_rejects_non_string_credentials(client, payload):
    response = client.session.post(f"{client.base_url}/login", json=payload, timeout=3)
    assert_error(response, 400, "INVALID_CREDENTIALS_FORMAT")


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "   ", "password": "secret123"},
        {"username": "tester", "password": "   "},
    ],
    ids=["blank-username", "blank-password"],
)
def test_login_rejects_whitespace_only_credentials(client, payload):
    response = client.session.post(f"{client.base_url}/login", json=payload, timeout=3)
    assert_error(response, 400, "MISSING_CREDENTIALS")


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/login", {"username": "tester", "password": "secret123", "otp": "1"}),
        ("/orders", {"product_id": 101, "quantity": 1, "coupon": "X"}),
    ],
    ids=["login", "order"],
)
def test_post_rejects_unknown_fields(authorized_client, path, payload):
    before = authorized_client.products().json()
    response = authorized_client.session.post(
        f"{authorized_client.base_url}{path}", json=payload, timeout=3
    )
    assert_error(response, 400, "INVALID_FIELDS")
    assert authorized_client.products().json() == before


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/login", {"username": "tester", "password": "secret123"}),
        ("/orders", {"product_id": 101, "quantity": 1}),
    ],
    ids=["login", "order"],
)
@pytest.mark.parametrize("media_type", [None, "text/plain"], ids=["missing", "wrong"])
def test_post_rejects_unsupported_media_type(
    authorized_client, path, payload, media_type
):
    before = authorized_client.products().json()
    headers = {} if media_type is None else {"Content-Type": media_type}
    response = authorized_client.session.post(
        f"{authorized_client.base_url}{path}",
        data=json.dumps(payload),
        headers=headers,
        timeout=3,
    )
    assert_error(response, 415, "UNSUPPORTED_MEDIA_TYPE")
    assert authorized_client.products().json() == before


@pytest.mark.parametrize(
    ("path", "payload", "expected_status"),
    [
        ("/login", {"username": "tester", "password": "secret123"}, 200),
        ("/orders", {"product_id": 101, "quantity": 1}, 201),
    ],
    ids=["login", "order"],
)
def test_post_accepts_json_media_type_with_charset(
    authorized_client, path, payload, expected_status
):
    response = authorized_client.session.post(
        f"{authorized_client.base_url}{path}",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=3,
    )
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "header",
    ["bearer demo-token", "Bearer", "Token demo-token", "Bearer demo-token "],
    ids=["wrong-case", "missing-value", "wrong-scheme", "trailing-space"],
)
def test_order_rejects_malformed_authorization_header(authorized_client, header):
    before = authorized_client.products().json()
    authorized_client.session.headers["Authorization"] = header
    assert_error(authorized_client.create_order(), 401, "UNAUTHORIZED")
    assert authorized_client.products().json() == before


@pytest.mark.parametrize(
    ("body", "media_type"),
    [("{", "application/json"), ('{"product_id":101,"quantity":1}', "text/plain")],
    ids=["malformed-json", "wrong-media-type"],
)
def test_unauthorized_order_request_rejects_before_body_validation(
    client, body, media_type
):
    response = client.session.post(
        f"{client.base_url}/orders",
        data=body,
        headers={"Content-Type": media_type},
        timeout=3,
    )
    assert_error(response, 401, "UNAUTHORIZED")
    assert client.product(101).json()["stock"] == 5


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE"])
def test_unsupported_methods_return_json_405(client, method):
    response = client.session.request(method, f"{client.base_url}/orders", timeout=3)
    assert_error(response, 405, "METHOD_NOT_ALLOWED")
