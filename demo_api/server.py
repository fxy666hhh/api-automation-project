"""Local order API used as the system under test.

Run manually with ``python -m demo_api.server``. Pytest starts a fresh server
for every test, so orders and inventory never leak between cases.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse


def make_handler():
    products = {
        101: {"id": 101, "name": "测试鼠标", "stock": 5},
        102: {"id": 102, "name": "测试键盘", "stock": 8},
    }
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

        def read_body(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 0 or size > 65536:
                    return None
                return self.rfile.read(size)
            except ValueError:
                return None

        def read_json_object(self, body):
            try:
                data = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                return None
            return data if isinstance(data, dict) else None

        def accepts_json(self):
            media_type = self.headers.get("Content-Type", "").partition(";")[0]
            return media_type.strip().lower() == "application/json"

        def authorized(self):
            return self.headers.get("Authorization") == "Bearer demo-token"

        def require_authorization(self):
            if self.authorized():
                return True
            self.send_json(401, {"code": "UNAUTHORIZED"})
            return False

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/products":
                self.send_json(200, {"products": list(products.values())})
                return

            if path.startswith("/products/"):
                product_id_text = path.removeprefix("/products/")
                if not product_id_text.isascii() or not product_id_text.isdecimal():
                    self.send_json(400, {"code": "INVALID_PRODUCT_ID"})
                    return
                product_id = int(product_id_text)
                if product_id < 1:
                    self.send_json(400, {"code": "INVALID_PRODUCT_ID"})
                elif product_id not in products:
                    self.send_json(404, {"code": "PRODUCT_NOT_FOUND"})
                else:
                    self.send_json(200, products[product_id])
                return

            if path == "/orders":
                if not self.require_authorization():
                    return
                params = parse_qs(parsed.query, keep_blank_values=True)
                if set(params) - {"status", "offset", "limit"} or any(
                    len(values) != 1 for values in params.values()
                ):
                    self.send_json(400, {"code": "INVALID_QUERY"})
                    return
                status = params.get("status", [None])[0]
                if status not in (None, "created", "cancelled"):
                    self.send_json(400, {"code": "INVALID_STATUS"})
                    return
                offset_text = params.get("offset", ["0"])[0]
                limit_text = params.get("limit", ["20"])[0]
                if not offset_text.isascii() or not offset_text.isdecimal():
                    self.send_json(400, {"code": "INVALID_PAGINATION"})
                    return
                if not limit_text.isascii() or not limit_text.isdecimal():
                    self.send_json(400, {"code": "INVALID_PAGINATION"})
                    return
                offset, limit = int(offset_text), int(limit_text)
                if limit < 1 or limit > 100:
                    self.send_json(400, {"code": "INVALID_PAGINATION"})
                    return
                selected = [
                    order for order in orders.values()
                    if status is None or order["status"] == status
                ]
                self.send_json(200, {
                    "orders": selected[offset:offset + limit],
                    "total": len(selected),
                    "offset": offset,
                    "limit": limit,
                })
                return

            if path.startswith("/orders/"):
                if not self.require_authorization():
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

            # Consume the body before responding. Unread request bytes can make
            # Windows abort the connection rather than deliver the HTTP status.
            body = self.read_body()
            if body is None:
                self.send_json(400, {"code": "INVALID_JSON"})
                return

            if path.startswith("/orders/") and path.endswith("/cancel"):
                if not self.require_authorization():
                    return
                if body:
                    self.send_json(400, {"code": "UNEXPECTED_BODY"})
                    return
                order_id = path[len("/orders/"):-len("/cancel")]
                order = orders.get(order_id)
                if order is None:
                    self.send_json(404, {"code": "ORDER_NOT_FOUND"})
                elif order["status"] == "cancelled":
                    self.send_json(409, {"code": "ORDER_ALREADY_CANCELLED"})
                else:
                    order["status"] = "cancelled"
                    products[order["product_id"]]["stock"] += order["quantity"]
                    self.send_json(200, order)
                return

            if path not in ("/login", "/orders"):
                self.send_json(404, {"code": "NOT_FOUND"})
                return
            if path == "/orders" and not self.require_authorization():
                return
            if not self.accepts_json():
                self.send_json(415, {"code": "UNSUPPORTED_MEDIA_TYPE"})
                return
            data = self.read_json_object(body)
            if data is None:
                self.send_json(400, {"code": "INVALID_JSON"})
                return

            if path == "/login":
                if set(data) - {"username", "password"}:
                    self.send_json(400, {"code": "INVALID_FIELDS"})
                    return
                username, password = data.get("username"), data.get("password")
                if username is None or password is None or username == "" or password == "":
                    self.send_json(400, {"code": "MISSING_CREDENTIALS"})
                elif not isinstance(username, str) or not isinstance(password, str):
                    self.send_json(400, {"code": "INVALID_CREDENTIALS_FORMAT"})
                elif not username.strip() or not password.strip():
                    self.send_json(400, {"code": "MISSING_CREDENTIALS"})
                elif username == "tester" and password == "secret123":
                    self.send_json(200, {"access_token": "demo-token"})
                else:
                    self.send_json(401, {"code": "INVALID_CREDENTIALS"})
                return

            if set(data) - {"product_id", "quantity"}:
                self.send_json(400, {"code": "INVALID_FIELDS"})
                return
            product_id, quantity = data.get("product_id"), data.get("quantity")
            if type(product_id) is not int or product_id < 1:
                self.send_json(400, {"code": "INVALID_PRODUCT_ID"})
            elif type(quantity) is not int or quantity < 1:
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

        def method_not_allowed(self):
            self.read_body()
            self.send_json(405, {"code": "METHOD_NOT_ALLOWED"})

        do_PUT = method_not_allowed
        do_PATCH = method_not_allowed
        do_DELETE = method_not_allowed

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
