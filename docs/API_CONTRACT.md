# 订单演示 API 契约

本文件记录当前演示服务的测试契约。请求和响应示例只使用本地练习数据；接口规则变更时，应同步更新测试用例。

下表列出的接口响应均为 JSON。错误响应统一为 `{"code": "错误码"}`，没有其他字段。订单 ID 是非空字符串；商品 ID 和库存是整数。

| 接口 | 成功响应 | 已定义错误 |
| --- | --- | --- |
| `POST /login` | `200`，`{"access_token": "非空字符串"}`。 | 缺少或空用户名/密码：`400 MISSING_CREDENTIALS`；字段不是字符串：`400 INVALID_CREDENTIALS_FORMAT`；错误凭据：`401 INVALID_CREDENTIALS`；无法解析为 JSON 对象：`400 INVALID_JSON`。 |
| `GET /products` | `200`，`{"products": [...]}`，商品包含正整数 `id`、非空 `name`、非负整数 `stock`。 | 公开接口，不要求 token。 |
| `GET /products/{id}` | 已有商品返回 `200` 和商品对象。 | ID 不是正整数路径：`400 INVALID_PRODUCT_ID`；未知正整数 ID：`404 PRODUCT_NOT_FOUND`。 |
| `POST /orders` | 有效 Bearer token、商品存在且库存足够时返回 `201`，字段为 `id`、`product_id`、`quantity`、`status`；状态为 `created`，库存扣减数量。 | 无效或缺少 token：`401 UNAUTHORIZED`；无法解析为 JSON 对象：`400 INVALID_JSON`；`product_id` 不是正整数：`400 INVALID_PRODUCT_ID`；`quantity` 不是正整数：`400 INVALID_QUANTITY`；未知商品：`404 PRODUCT_NOT_FOUND`；库存不足：`409 INSUFFICIENT_STOCK`。 |
| `GET /orders` | 有效 token 时返回 `200`，结构为 `{"orders": [...], "total": 0, "offset": 0, "limit": 20}`。支持 `status=created|cancelled`、非负整数 `offset`、`1..100` 的整数 `limit`；先筛选再分页，`total` 是筛选后总数。 | 无效或缺少 token：`401 UNAUTHORIZED`；非法状态：`400 INVALID_STATUS`；非法分页值：`400 INVALID_PAGINATION`；未知或重复查询参数：`400 INVALID_QUERY`。 |
| `GET /orders/{id}` | 有效 Bearer token 且订单存在时返回 `200` 和对应订单，重复读取不修改库存。 | 无效或缺少 token：`401 UNAUTHORIZED`；订单不存在：`404 ORDER_NOT_FOUND`。 |
| `POST /orders/{id}/cancel` | 有效 token、已有且未取消订单、空请求体时返回 `200` 和状态为 `cancelled` 的订单；对应商品库存返还订单数量。 | 无效或缺少 token：`401 UNAUTHORIZED`；请求体非空：`400 UNEXPECTED_BODY`；未知订单：`404 ORDER_NOT_FOUND`；重复取消：`409 ORDER_ALREADY_CANCELLED`，不得重复返还库存。 |

`POST /login` 与 `POST /orders` 只接受 JSON 对象，Content-Type 必须是 `application/json`，可带 `charset` 参数；其他媒体类型返回 `415 UNSUPPORTED_MEDIA_TYPE`。两者只接受规定字段，额外字段返回 `400 INVALID_FIELDS`。受保护接口在请求体校验前检查 token。固定演示 token 必须以 `Bearer demo-token` 原样传入。

未知路径返回 `404 NOT_FOUND`；PUT、PATCH、DELETE 返回 JSON 格式的 `405 METHOD_NOT_ALLOWED`。每条自动化用例使用独立服务实例；初始商品为 `101`（测试鼠标、库存 `5`）和 `102`（测试键盘、库存 `8`）；练习账号为 `tester` / `secret123`。这些数据只适用于本地演示，不作为真实环境凭据。

请求和响应的具体形状由 `schemas/` 中的 JSON Schema 及 `tests/` 中的状态码和业务断言共同校验。若接口行为要调整，应先更新本契约，再修改服务和用例。
