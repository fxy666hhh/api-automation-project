import pytest

from tests.assertions import assert_error, assert_matches_schema


@pytest.mark.parametrize(
    ("product_id", "name", "initial_stock"),
    [(101, "测试鼠标", 5), (102, "测试键盘", 8)],
)
def test_get_product_detail(client, product_id, name, initial_stock):
    response = client.product(product_id)

    assert response.status_code == 200
    assert response.json() == {
        "id": product_id,
        "name": name,
        "stock": initial_stock,
    }
    assert_matches_schema(response.json(), "product.json")


def test_product_list_matches_individual_details(client):
    catalog = client.products()
    assert catalog.status_code == 200
    assert {item["id"] for item in catalog.json()["products"]} == {101, 102}

    for item in catalog.json()["products"]:
        detail = client.product(item["id"])
        assert detail.status_code == 200
        assert detail.json() == item


def test_product_detail_is_public_even_with_invalid_token(client):
    client.use_token("wrong-token")
    response = client.product(101)
    assert response.status_code == 200
    assert response.json()["id"] == 101


@pytest.mark.parametrize("product_id", ["", "abc", "1.5", "-1", "0", "101/extra"])
def test_product_detail_rejects_invalid_id(client, product_id):
    response = client.product(product_id)
    assert_error(response, 400, "INVALID_PRODUCT_ID")


def test_product_detail_returns_404_for_unknown_positive_id(client):
    assert_error(client.product(999), 404, "PRODUCT_NOT_FOUND")


def test_order_changes_only_selected_product_stock(authorized_client):
    before_mouse = authorized_client.product(101).json()["stock"]
    before_keyboard = authorized_client.product(102).json()["stock"]

    created = authorized_client.create_order(product_id=102, quantity=3)
    assert created.status_code == 201
    assert created.json()["product_id"] == 102

    assert authorized_client.product(101).json()["stock"] == before_mouse
    assert authorized_client.product(102).json()["stock"] == before_keyboard - 3
