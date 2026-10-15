# 订单 API 测试用例清单

本清单把 [测试计划](TEST_PLAN.md) 的测试项映射到可执行 pytest 用例。每条用例由 fixture 启动独立服务：商品 `101` 初始库存 `5`，订单初始为空。`authorized_client` 会先登录，`client` 不带 token。方括号中的数据由 `pytest.mark.parametrize` 分别运行。

| 编号 | 操作与测试数据 | 关键预期 | 自动化用例 |
| --- | --- | --- | --- |
| AUTH-01 | 用正确账号密码调用 `POST /login`。 | `200`、JSON 响应、非空字符串 token。 | `tests/test_auth.py::test_login_success` |
| AUTH-02 | 分别提交错误密码、未知账号、缺少用户名、缺少密码、空用户名、空密码。 | 错误凭据为 `401 INVALID_CREDENTIALS`；缺少或空字段为 `400 MISSING_CREDENTIALS`。 | `tests/test_auth.py::test_login_rejects_wrong_credentials`；`test_login_requires_both_fields` |
| AUTH-03 | 登录请求体依次为 `{`、空串、`[]`、`null`；每次再正常登录。 | 首次请求为 `400 INVALID_JSON`；后续正常登录仍返回 `200`。 | `tests/test_auth.py::test_login_rejects_malformed_json_and_remains_available` |
| PROD-01 | 未登录调用 `GET /products`。 | `200`，商品数组符合 `schemas/products.json`。 | `tests/test_contract.py::test_products_match_schema` |
| ORD-01 | 登录后下单 2 件，再按返回 ID 查询商品订单与库存。 | `201`，订单详情一致，库存减少 2。 | `tests/test_orders.py::test_create_order_and_check_inventory` |
| ORD-02 | 下单用完全部库存；另一次用例请求超过当前库存的数量。 | 前者成功且库存为 0；后者 `409 INSUFFICIENT_STOCK` 且库存不变。 | `tests/test_orders.py::test_order_uses_all_stock`；`test_order_rejects_insufficient_stock_without_changing_inventory` |
| ORD-03 | 先下单 3 件再下单 3 件；另一次用例连续读取同一已有订单。 | 第二单因库存不足被拒绝且剩余 2；重复 GET 内容一致且库存不变。 | `tests/test_orders.py::test_second_order_fails_when_stock_is_insufficient`；`test_repeated_get_order_does_not_change_inventory` |
| ORD-04 | 不带、带错误或空 token 创建订单；先创建真实订单，再用上述 token 查询。 | 均返回 `401 UNAUTHORIZED`，查询响应不含订单内容。 | `tests/test_orders.py::test_order_requires_login`；`test_order_rejects_invalid_token`；`test_get_existing_order_requires_valid_token` |
| ORD-05 | 数量设为 `0`、`-1`、`"2"`、`null`；另一次请求未知商品 `999`。 | 非法数量为 `400 INVALID_QUANTITY`，未知商品为 `404 PRODUCT_NOT_FOUND`；库存不变。 | `tests/test_orders.py::test_order_rejects_invalid_quantity`；`test_order_rejects_unknown_product` |
| ORD-06 | 下单请求体依次为 `{`、空串、`[]`、`null`。 | `400 INVALID_JSON`，库存不变。 | `tests/test_orders.py::test_order_rejects_malformed_json` |
| ORD-07 | 创建订单并校验响应；查询不存在的订单 ID。 | 成功响应符合 `schemas/order.json`；未知 ID 为 `404 ORDER_NOT_FOUND`。 | `tests/test_contract.py::test_created_order_matches_schema`；`tests/test_orders.py::test_get_unknown_order` |
| ORD-08 | 连续成功下单 2 件与 1 件，按各自 ID 查询。 | 两个 ID 不同，订单分别可查，库存累计减少 3。 | `tests/test_orders.py::test_two_orders_have_unique_ids_and_cumulative_inventory_change` |
| ERR-01 | 分别触发缺少凭据、错误凭据、未授权下单、非法数量、未知商品、库存不足、未知订单。 | HTTP 状态与错误码符合 [接口契约](API_CONTRACT.md)，响应符合 `schemas/error.json`；库存不变。 | `tests/test_contract.py::test_error_responses_match_schema` |
| ROUTE-01 | 用 GET、POST 请求 `/does-not-exist`。 | `404 NOT_FOUND`，响应类型为 JSON。 | `tests/test_routes.py::test_unknown_path_returns_json_404` |
| INPUT-01 | `product_id` 类型、额外字段和 Content-Type 的规则尚未约定。 | 待接口契约明确后填写，不预设结果。 | 尚未自动化 |

## 运行方式

在项目根目录运行 `python -m pytest -q` 执行全部用例。单独运行某一测试函数时使用 `python -m pytest tests/test_orders.py::test_two_orders_have_unique_ids_and_cumulative_inventory_change -v`。Windows 虚拟环境中可把命令开头的 `python` 替换为 `.\.venv\Scripts\python.exe`。
