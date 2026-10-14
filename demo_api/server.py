"""Local order API for practicing black-box interface tests.

Run it manually with: python -m demo_api.server
The pytest fixtures also start an isolated copy automatically for each test.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse


def make_handler():
    products = {101: {"id": 101, "name": "测试鼠标", "stock": 5}}
    orders = {}
    next_order_id = 1

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def send_json(self, status, data):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def read_json(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("JSON body must be an object")
                return data
            except (ValueError, json.JSONDecodeError):
                return None

        def authorized(self):
            return self.headers.get("Authorization") == "Bearer demo-token"

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/products":
                self.send_json(200, {"products": list(products.values())})
                return
            if path.startswith("/orders/"):
                if not self.authorized():
                    self.send_json(401, {"code": "UNAUTHORIZED"})
                    return
                order_id = path.removeprefix("/orders/")
                order = orders.get(order_id)
                if order is None:
                    self.send_json(404, {"code": "ORDER_NOT_FOUND"})
                else:
                    self.send_json(200, order)
                return
            self.send_json(404, {"code": "NOT_FOUND"})

        def do_POST(self):
            nonlocal next_order_id
            path = urlparse(self.path).path
            if path not in ("/login", "/orders"):
                self.send_json(404, {"code": "NOT_FOUND"})
                return
            # Consume the POST body before sending an error response. Closing a
            # socket with unread request bytes can abort the client connection
            # on Windows instead of delivering the intended HTTP status.
            data = self.read_json()
            if path == "/orders" and not self.authorized():
                self.send_json(401, {"code": "UNAUTHORIZED"})
                return
            if data is None:
                self.send_json(400, {"code": "INVALID_JSON"})
                return
            if path == "/login":
                if not data.get("username") or not data.get("password"):
                    self.send_json(400, {"code": "MISSING_CREDENTIALS"})
                elif data == {"username": "tester", "password": "secret123"}:
                    self.send_json(200, {"access_token": "demo-token"})
                else:
                    self.send_json(401, {"code": "INVALID_CREDENTIALS"})
                return

            product_id = data.get("product_id")
            quantity = data.get("quantity")
            if type(quantity) is not int or quantity <= 0:
                self.send_json(400, {"code": "INVALID_QUANTITY"})
            elif product_id not in products:
                self.send_json(404, {"code": "PRODUCT_NOT_FOUND"})
            elif quantity > products[product_id]["stock"]:
                self.send_json(409, {"code": "INSUFFICIENT_STOCK"})
            else:
                products[product_id]["stock"] -= quantity
                order = {
                    "id": str(next_order_id),
                    "product_id": product_id,
                    "quantity": quantity,
                    "status": "created",
                }
                orders[order["id"]] = order
                next_order_id += 1
                self.send_json(201, order)

    return Handler


def main():
    server = HTTPServer(("127.0.0.1", 8000), make_handler())
    print("Demo API running at http://127.0.0.1:8000", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
