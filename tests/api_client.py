"""Thin HTTP client: keep request details separate from test assertions."""

import requests


class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def close(self):
        self.session.close()

    def login(self, username="tester", password="secret123"):
        return self.session.post(
            f"{self.base_url}/login",
            json={"username": username, "password": password},
            timeout=3,
        )

    def use_token(self, token):
        self.session.headers["Authorization"] = f"Bearer {token}"

    def products(self):
        return self.session.get(f"{self.base_url}/products", timeout=3)

    def create_order(self, product_id=101, quantity=1):
        return self.session.post(
            f"{self.base_url}/orders",
            json={"product_id": product_id, "quantity": quantity},
            timeout=3,
        )

    def get_order(self, order_id):
        return self.session.get(f"{self.base_url}/orders/{order_id}", timeout=3)
