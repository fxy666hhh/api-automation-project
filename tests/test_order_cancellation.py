import pytest

from tests.assertions import assert_error, assert_matches_schema


@pytest.mark.parametrize(("product_id", "quantity"), [(101, 2), (102, 3)])
@pytest.mark.smoke
def test_cancel_order_restores_selected_product_stock(
    authorized_client, product_id, quantity
):
    initial_stock = authorized_client.product(product_id).json()["stock"]
    created = authorized_client.create_order(product_id=product_id, quantity=quantity)
    assert created.status_code == 201
    order_id = created.json()["id"]
    assert authorized_client.product(product_id).json()["stock"] == initial_stock - quantity

    cancelled = authorized_client.cancel_order(order_id)
    assert cancelled.status_code == 200
    assert cancelled.json() == {**created.json(), "status": "cancelled"}
    assert_matches_schema(cancelled.json(), "order.json")
    assert authorized_client.product(product_id).json()["stock"] == initial_stock

    fetched = authorized_client.get_order(order_id)
    assert fetched.status_code == 200
    assert fetched.json() == cancelled.json()


def test_second_cancellation_is_rejected_without_double_restock(authorized_client):
    initial_stock = authorized_client.product(101).json()["stock"]
    created = authorized_client.create_order(quantity=2)
    assert created.status_code == 201

    first = authorized_client.cancel_order(created.json()["id"])
    assert first.status_code == 200
    second = authorized_client.cancel_order(created.json()["id"])
    assert_error(second, 409, "ORDER_ALREADY_CANCELLED")
    assert authorized_client.product(101).json()["stock"] == initial_stock


def test_cancel_unknown_order_returns_404(authorized_client):
    assert_error(authorized_client.cancel_order("not-here"), 404, "ORDER_NOT_FOUND")


@pytest.mark.parametrize("token", [None, "wrong-token", ""], ids=["missing", "invalid", "empty"])
def test_cancel_order_requires_valid_token(authorized_client, token):
    created = authorized_client.create_order()
    assert created.status_code == 201
    valid_header = authorized_client.session.headers["Authorization"]
    stock_before = authorized_client.product(101).json()["stock"]

    if token is None:
        authorized_client.session.headers.pop("Authorization")
    else:
        authorized_client.use_token(token)
    assert_error(authorized_client.cancel_order(created.json()["id"]), 401, "UNAUTHORIZED")

    authorized_client.session.headers["Authorization"] = valid_header
    assert authorized_client.get_order(created.json()["id"]).json()["status"] == "created"
    assert authorized_client.product(101).json()["stock"] == stock_before


@pytest.mark.parametrize(
    ("body", "headers"),
    [
        ({"reason": "changed mind"}, None),
        ("unexpected", {"Content-Type": "text/plain"}),
    ],
)
def test_cancel_order_rejects_request_body_without_changing_state(
    authorized_client, body, headers
):
    created = authorized_client.create_order(quantity=2)
    assert created.status_code == 201
    stock_before = authorized_client.product(101).json()["stock"]
    url = f"{authorized_client.base_url}/orders/{created.json()['id']}/cancel"
    if isinstance(body, dict):
        response = authorized_client.session.post(url, json=body, timeout=3)
    else:
        response = authorized_client.session.post(url, data=body, headers=headers, timeout=3)

    assert_error(response, 400, "UNEXPECTED_BODY")
    assert authorized_client.get_order(created.json()["id"]).json()["status"] == "created"
    assert authorized_client.product(101).json()["stock"] == stock_before


def test_cancellation_makes_out_of_stock_product_orderable_again(authorized_client):
    first = authorized_client.create_order(quantity=5)
    assert first.status_code == 201
    assert authorized_client.product(101).json()["stock"] == 0

    cancelled = authorized_client.cancel_order(first.json()["id"])
    assert cancelled.status_code == 200
    assert authorized_client.product(101).json()["stock"] == 5

    replacement = authorized_client.create_order(quantity=5)
    assert replacement.status_code == 201
    assert replacement.json()["id"] != first.json()["id"]
    assert authorized_client.product(101).json()["stock"] == 0


def test_cancelling_one_order_preserves_another_order(authorized_client):
    first = authorized_client.create_order(quantity=2)
    second = authorized_client.create_order(quantity=1)
    assert first.status_code == second.status_code == 201
    assert authorized_client.product(101).json()["stock"] == 2

    assert authorized_client.cancel_order(first.json()["id"]).status_code == 200
    assert authorized_client.product(101).json()["stock"] == 4
    assert authorized_client.get_order(second.json()["id"]).json() == second.json()


def test_cancelling_keyboard_order_does_not_change_mouse_stock(authorized_client):
    mouse_before = authorized_client.product(101).json()["stock"]
    created = authorized_client.create_order(product_id=102, quantity=4)
    assert created.status_code == 201

    assert authorized_client.cancel_order(created.json()["id"]).status_code == 200
    assert authorized_client.product(101).json()["stock"] == mouse_before
    assert authorized_client.product(102).json()["stock"] == 8
