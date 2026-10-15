import pytest

from tests.assertions import assert_error, assert_matches_schema


@pytest.fixture
def three_orders(authorized_client):
    orders = []
    for _ in range(3):
        response = authorized_client.create_order(quantity=1)
        assert response.status_code == 201
        orders.append(response.json())
    return orders


@pytest.mark.parametrize("token", [None, "wrong-token", ""], ids=["missing", "invalid", "empty"])
def test_order_list_requires_valid_token(client, token):
    if token is not None:
        client.use_token(token)
    assert_error(client.list_orders(), 401, "UNAUTHORIZED")


def test_order_list_starts_empty(authorized_client):
    response = authorized_client.list_orders()
    assert response.status_code == 200
    assert response.json() == {"orders": [], "total": 0, "offset": 0, "limit": 20}
    assert_matches_schema(response.json(), "orders.json")


def test_order_list_contains_new_orders_in_creation_order(authorized_client, three_orders):
    response = authorized_client.list_orders()
    assert response.status_code == 200
    assert response.json()["orders"] == three_orders
    assert response.json()["total"] == len(three_orders)
    assert_matches_schema(response.json(), "orders.json")


def test_order_list_filters_created_and_cancelled(authorized_client):
    first = authorized_client.create_order().json()
    second = authorized_client.create_order().json()
    cancelled = authorized_client.cancel_order(first["id"])
    assert cancelled.status_code == 200

    created = authorized_client.list_orders(status="created")
    assert created.status_code == 200
    assert created.json()["orders"] == [second]
    assert created.json()["total"] == 1

    cancelled_list = authorized_client.list_orders(status="cancelled")
    assert cancelled_list.status_code == 200
    assert cancelled_list.json()["orders"] == [cancelled.json()]
    assert cancelled_list.json()["total"] == 1
    assert_matches_schema(cancelled_list.json(), "orders.json")


@pytest.mark.parametrize(
    ("offset", "limit"),
    [(0, 1), (1, 1), (2, 1), (3, 1), (0, 100)],
)
def test_order_list_pagination(authorized_client, three_orders, offset, limit):
    response = authorized_client.list_orders(offset=offset, limit=limit)
    assert response.status_code == 200
    assert response.json() == {
        "orders": three_orders[offset:offset + limit],
        "total": 3,
        "offset": offset,
        "limit": limit,
    }


def test_order_list_filters_before_paginating(authorized_client):
    first = authorized_client.create_order().json()
    second = authorized_client.create_order().json()
    third = authorized_client.create_order().json()
    assert authorized_client.cancel_order(second["id"]).status_code == 200

    response = authorized_client.list_orders(status="created", offset=1, limit=1)
    assert response.status_code == 200
    assert response.json()["orders"] == [third]
    assert response.json()["total"] == 2
    assert first["id"] != third["id"]


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("offset", ""), ("offset", "-1"), ("offset", "1.5"), ("offset", "abc"),
        ("limit", ""), ("limit", "0"), ("limit", "-1"),
        ("limit", "101"), ("limit", "1.5"), ("limit", "abc"),
    ],
)
def test_order_list_rejects_invalid_pagination(authorized_client, parameter, value):
    response = authorized_client.list_orders(**{parameter: value})
    assert_error(response, 400, "INVALID_PAGINATION")


@pytest.mark.parametrize("status", ["", "pending", "CREATED"])
def test_order_list_rejects_invalid_status(authorized_client, status):
    assert_error(authorized_client.list_orders(status=status), 400, "INVALID_STATUS")


@pytest.mark.parametrize(
    "params",
    [
        [("unknown", "1")],
        [("status", "created"), ("status", "cancelled")],
        [("limit", "1"), ("limit", "2")],
    ],
    ids=["unknown-field", "duplicate-status", "duplicate-limit"],
)
def test_order_list_rejects_unknown_or_duplicate_query(authorized_client, params):
    response = authorized_client.session.get(
        f"{authorized_client.base_url}/orders", params=params, timeout=3
    )
    assert_error(response, 400, "INVALID_QUERY")


def test_repeated_order_list_does_not_change_inventory(authorized_client, three_orders):
    stock_before = authorized_client.product(101).json()["stock"]
    first = authorized_client.list_orders()
    second = authorized_client.list_orders()

    assert first.status_code == second.status_code == 200
    assert first.json()["orders"] == second.json()["orders"] == three_orders
    assert authorized_client.product(101).json()["stock"] == stock_before
