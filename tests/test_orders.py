import pytest


@pytest.mark.smoke
def test_create_order_and_check_inventory(authorized_client):
    before = authorized_client.products().json()["products"][0]["stock"]

    created = authorized_client.create_order(quantity=2)

    assert created.status_code == 201
    order = created.json()
    assert order["product_id"] == 101
    assert order["quantity"] == 2
    assert order["status"] == "created"

    fetched = authorized_client.get_order(order["id"])
    assert fetched.status_code == 200
    assert fetched.json() == order

    after = authorized_client.products().json()["products"][0]["stock"]
    assert after == before - 2


def test_repeated_get_order_does_not_change_inventory(authorized_client):
    created = authorized_client.create_order(quantity=2)
    assert created.status_code == 201
    order = created.json()

    stock_before = authorized_client.products().json()["products"][0]["stock"]

    first = authorized_client.get_order(order["id"])
    second = authorized_client.get_order(order["id"])

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json() == order

    stock_after = authorized_client.products().json()["products"][0]["stock"]
    assert stock_after == stock_before


def test_two_orders_have_unique_ids_and_cumulative_inventory_change(authorized_client):
    stock_before = authorized_client.products().json()["products"][0]["stock"]

    first = authorized_client.create_order(quantity=2)
    second = authorized_client.create_order(quantity=1)
    assert first.status_code == 201
    assert second.status_code == 201

    first_order = first.json()
    second_order = second.json()
    assert first_order["id"] != second_order["id"]

    for order in (first_order, second_order):
        fetched = authorized_client.get_order(order["id"])
        assert fetched.status_code == 200
        assert fetched.json() == order

    stock_after = authorized_client.products().json()["products"][0]["stock"]
    assert stock_after == stock_before - 3


def test_order_requires_login(client):
    response = client.create_order()

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize("quantity", [0, -1, "2", None])
def test_order_rejects_invalid_quantity(authorized_client, quantity):
    before = authorized_client.products().json()["products"][0]["stock"]
    response = authorized_client.create_order(quantity=quantity)

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_QUANTITY"
    after = authorized_client.products().json()["products"][0]["stock"]
    assert after == before


def test_order_rejects_unknown_product(authorized_client):
    before = authorized_client.products().json()["products"][0]["stock"]
    response = authorized_client.create_order(product_id=999)

    assert response.status_code == 404
    assert response.json()["code"] == "PRODUCT_NOT_FOUND"
    after = authorized_client.products().json()["products"][0]["stock"]
    assert after == before


def test_order_rejects_insufficient_stock_without_changing_inventory(authorized_client):
    before = authorized_client.products().json()["products"][0]["stock"]

    response = authorized_client.create_order(quantity=before + 1)

    assert response.status_code == 409
    assert response.json()["code"] == "INSUFFICIENT_STOCK"
    after = authorized_client.products().json()["products"][0]["stock"]
    assert after == before


def test_get_unknown_order(authorized_client):
    response = authorized_client.get_order("not-here")

    assert response.status_code == 404
    assert response.json()["code"] == "ORDER_NOT_FOUND"


@pytest.mark.parametrize(
    "token",
    [None, "wrong-token", ""],
    ids=["missing", "invalid", "empty"],
)
def test_get_existing_order_requires_valid_token(authorized_client, token):
    created = authorized_client.create_order()
    assert created.status_code == 201

    if token is None:
        authorized_client.session.headers.pop("Authorization", None)
    else:
        authorized_client.use_token(token)

    response = authorized_client.get_order(created.json()["id"])
    assert response.status_code == 401
    assert response.json() == {"code": "UNAUTHORIZED"}


def test_order_uses_all_stock(authorized_client):
    response = authorized_client.create_order(product_id=101, quantity=5)

    assert response.status_code == 201
    assert response.json()["quantity"] == 5

    products = authorized_client.products().json()["products"]
    assert products[0]["stock"] == 0


def test_second_order_fails_when_stock_is_insufficient(authorized_client):
    first = authorized_client.create_order(quantity=3)
    assert first.status_code == 201

    second = authorized_client.create_order(quantity=3)
    assert second.status_code == 409
    assert second.json()["code"] == "INSUFFICIENT_STOCK"

    products = authorized_client.products().json()["products"]
    assert products[0]["stock"] == 2

@pytest.mark.parametrize(
    "payload",
    ["{", "", "[]", "null"],
    ids=["truncated", "empty", "array", "null"],
)
def test_order_rejects_malformed_json(authorized_client, payload):
    before = authorized_client.products().json()["products"][0]["stock"]

    response = authorized_client.session.post(
        f"{authorized_client.base_url}/orders",
        data=payload,
        headers={"Content-Type": "application/json"},
        timeout=3,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_JSON"

    after = authorized_client.products().json()["products"][0]["stock"]
    assert after == before


@pytest.mark.parametrize("token", ["wrong-token", ""])
def test_order_rejects_invalid_token(client, token):
    client.use_token(token)
    response = client.create_order()
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"
