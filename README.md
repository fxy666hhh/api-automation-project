# 接口自动化测试实战：订单 API

这是一个可以在本机运行的练习项目。`demo_api/` 是待测服务，`tests/` 是接口自动化测试。测试会自动启动服务，每条用例使用独立的初始数据，不需要注册账号或连接外网。

完整的测试范围、待补场景和验收标准见 [测试计划](docs/TEST_PLAN.md)；逐项操作、预期和自动化用例见 [测试用例清单](docs/TEST_CASES.md)；接口状态码和响应字段见 [接口契约](docs/API_CONTRACT.md)。

## 1. 运行

需要 Python 3.10 或更新版本。在本目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
```

想看每条用例名称：

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

只运行核心冒烟用例，或生成 JUnit XML、HTML 与覆盖率报告：

```powershell
.\.venv\Scripts\python.exe -m pytest -m smoke -v
.\.venv\Scripts\python.exe -m pytest -q --cov=demo_api --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml:reports/coverage.xml --junitxml=reports/results.xml --html=reports/results.html --self-contained-html
```

`smoke` 标记在项目根目录的 `pytest.ini` 中注册。运行报告保存在 `reports/`；其中 `results.html` 可以直接用浏览器打开，`coverage.xml` 记录被测服务覆盖率。该目录和 `.venv/` 均由 `.gitignore` 排除。

## 2. 接口清单

| 方法 | 路径 | 用途 | 关键状态码 |
| --- | --- | --- | --- |
| POST | `/login` | 登录，获取 token | 200、400、401、415 |
| GET | `/products` | 查询商品和库存 | 200 |
| GET | `/products/{id}` | 查询商品详情 | 200、400、404 |
| POST | `/orders` | 创建订单，需 Bearer token | 201、400、401、404、409、415 |
| GET | `/orders` | 查询、筛选和分页订单 | 200、400、401 |
| GET | `/orders/{id}` | 查询订单，需 Bearer token | 200、401、404 |
| POST | `/orders/{id}/cancel` | 取消订单并返还库存 | 200、400、401、404、409 |

登录账号是 `tester`，密码是 `secret123`。这是本地练习数据。商品 101（测试鼠标）的初始库存为 5，商品 102（测试键盘）的初始库存为 8。

## 3. 先看这三处

1. `tests/test_orders.py`：业务场景和断言。成功下单同时检查订单详情和库存变化；失败下单检查库存不变。
2. `tests/conftest.py`：pytest fixture 启动独立服务，准备客户端和登录状态。
3. `tests/api_client.py`：封装 HTTP 请求，统一设置超时；断言仍保留在测试里。

`demo_api/server.py` 是被测系统。初次阅读时，先按接口清单写出你认为需要测的场景，再看服务实现。

## 4. 已覆盖的场景

- 登录成功、凭据错误和缺少凭据；
- 非法登录请求返回错误后，服务仍可正常登录；
- 登录后创建订单、读取订单，并验证库存变化；
- 两次成功下单得到不同订单 ID，订单均可查询，库存累计扣减；
- 连续读取同一订单时，返回内容一致，库存保持不变；
- 缺少或使用无效 token 时拒绝下单；
- 已存在的订单在缺少、无效或空 token 时也不能被读取；
- 数量非法、商品不存在、库存不足时返回对应错误；
- 库存刚好够用，以及连续下单后的库存边界；
- 请求体不完整、为空或不是 JSON 对象时拒绝下单，库存保持不变。
- 创建订单的响应符合 `schemas/order.json` 定义的字段、类型和取值约束；对应测试在 `tests/test_contract.py`。
- 商品列表响应符合 `schemas/products.json` 定义的商品 ID、名称与非负库存约束。
- 错误响应符合 `schemas/error.json`，未知路径返回 JSON 格式的 404。
- 商品详情与列表一致；两个商品的库存互不影响。
- 订单列表支持认证、状态筛选、分页和参数校验；取消订单返还库存，重复取消不会重复返还。
- 请求字段类型、缺失与额外字段、Content-Type 和 Authorization 格式均有边界用例。

## 5. CI

`.github/workflows/api-tests.yml` 定义了 GitHub Actions 工作流。推送代码、创建 Pull Request 或手动触发时会安装依赖、运行全部测试，检查被测服务覆盖率不低于 90%，并把 JUnit XML、HTML 和覆盖率 XML 一起上传为 `pytest-results`。在 GitHub Actions 运行页面的 Artifacts 区域可以下载报告。

## 6. 接入真实项目时改哪里

把 `base_url` fixture 改为测试环境地址，并删除本地服务的启动逻辑；在 `APIClient` 中按真实接口调整路径、请求头和数据。账号密码应从环境变量或团队的密钥管理系统读取。真实系统还需要测试数据创建与清理，避免用例之间互相影响。
