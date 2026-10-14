import json
from pathlib import Path

from jsonschema import validate


def test_created_order_matches_schema(authorized_client):
    response = authorized_client.create_order()
    assert response.status_code == 201

    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "order.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validate(instance=response.json(), schema=schema)


def test_products_match_schema(client):
    response = client.products()
    assert response.status_code == 200

    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "products.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validate(instance=response.json(), schema=schema)
