# 订单演示 API 契约

本文件记录当前演示服务已明确、可用于测试断言的行为。测试计划中的 `INPUT-01` 尚未约定，因此不在这里猜测 `product_id` 类型、额外字段或 Content-Type 校验规则。

下表列出的接口响应均为 JSON。错误响应统一为 `{"code": "错误码"}`，没有其他字段。订单 ID 是非空字符串；商品 ID 和库存是整数。

| 接口 | 成功响应 | 已定义错误 |
| --- | --- | --- |
| `POST /login` | `200`，`{"access_token": "非空字符串"}` | 缺少或空用户名/密码：`400 MISSING_CREDENTIALS`；错误凭据：`401 INVALID_CREDENTIALS`；无法解析为 JSON 对象：`400 INVALID_JSON`。 |
| `GET /products` | `200`，`{"products": [{"id": 101, "name": "测试鼠标", "stock": 5}]}`；库存随下单变化，可为 `0`。 | 当前没有需要认证或其他已定义业务错误。 |
| `POST /orders` | 有效 Bearer token、商品存在且库存足够时返回 `201`，字段为 `id`、`product_id`、`quantity`、`status`；`status` 为 `created`，库存扣减数量。 | 无效或缺少 token：`401 UNAUTHORIZED`；无法解析为 JSON 对象：`400 INVALID_JSON`；数量不是正整数：`400 INVALID_QUANTITY`；未知商品：`404 PRODUCT_NOT_FOUND`；库存不足：`409 INSUFFICIENT_STOCK`。 |
| `GET /orders/{id}` | 有效 Bearer token 且订单存在时返回 `200` 和对应订单，重复读取不修改库存。 | 无效或缺少 token：`401 UNAUTHORIZED`；订单不存在：`404 ORDER_NOT_FOUND`。 |

未知路径返回 `404` 和 `{"code": "NOT_FOUND"}`。每条自动化用例使用独立服务实例，初始商品 ID 为 `101`、库存为 `5`；练习账号为 `tester` / `secret123`。这些数据只适用于本地演示，不作为真实环境凭据。

请求和响应的具体形状由 `schemas/` 中的 JSON Schema 及 `tests/` 中的状态码和业务断言共同校验。若接口行为要调整，应先更新本契约，再修改服务和用例。
