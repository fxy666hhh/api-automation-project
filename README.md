# 接口自动化测试实战：订单 API

这是一个可以在本机运行的练习项目。`demo_api/` 是待测服务，`tests/` 是接口自动化测试。测试会自动启动服务，每条用例使用独立的初始数据，不需要注册账号或连接外网。

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

只运行核心冒烟用例，或同时生成供 CI 读取的 JUnit XML 与可直接打开的 HTML 报告：

```powershell
.\.venv\Scripts\python.exe -m pytest -m smoke -v
.\.venv\Scripts\python.exe -m pytest -q --junitxml=reports/results.xml --html=reports/results.html --self-contained-html
```

`smoke` 标记在项目根目录的 `pytest.ini` 中注册。运行报告保存在 `reports/`；其中 `results.html` 可以直接用浏览器打开。该目录和 `.venv/` 均由 `.gitignore` 排除。

## 2. 接口清单

| 方法 | 路径 | 用途 | 关键状态码 |
| --- | --- | --- | --- |
| POST | `/login` | 登录，获取 token | 200、400、401 |
| GET | `/products` | 查询商品和库存 | 200 |
| POST | `/orders` | 创建订单，需 Bearer token | 201、400、401、404、409 |
| GET | `/orders/{id}` | 查询订单，需 Bearer token | 200、401、404 |

登录账号是 `tester`，密码是 `secret123`。这是本地练习数据。商品 101 的初始库存为 5。

## 3. 先看这三处

1. `tests/test_orders.py`：业务场景和断言。成功下单同时检查订单详情和库存变化；失败下单检查库存不变。
2. `tests/conftest.py`：pytest fixture 启动独立服务，准备客户端和登录状态。
3. `tests/api_client.py`：封装 HTTP 请求，统一设置超时；断言仍保留在测试里。

`demo_api/server.py` 是被测系统。初次阅读时，先按接口清单写出你认为需要测的场景，再看服务实现。

## 4. 已覆盖的场景

- 登录成功、凭据错误和缺少凭据；
- 登录后创建订单、读取订单，并验证库存变化；
- 缺少或使用无效 token 时拒绝下单；
- 已存在的订单在缺少、无效或空 token 时也不能被读取；
- 数量非法、商品不存在、库存不足时返回对应错误；
- 库存刚好够用，以及连续下单后的库存边界；
- 请求体不完整、为空或不是 JSON 对象时拒绝下单，库存保持不变。
- 创建订单的响应符合 `schemas/order.json` 定义的字段、类型和取值约束；对应测试在 `tests/test_contract.py`。
- 商品列表响应符合 `schemas/products.json` 定义的商品 ID、名称与非负库存约束。

## 5. CI

`.github/workflows/api-tests.yml` 定义了 GitHub Actions 工作流。推送代码、创建 Pull Request 或手动触发时会安装依赖、运行全部测试，并把 XML 和 HTML 文件一起上传为 `pytest-results`。在 GitHub Actions 运行页面的 Artifacts 区域可以下载报告。

## 6. 接入真实项目时改哪里

把 `base_url` fixture 改为测试环境地址，并删除本地服务的启动逻辑；在 `APIClient` 中按真实接口调整路径、请求头和数据。账号密码应从环境变量或团队的密钥管理系统读取。真实系统还需要测试数据创建与清理，避免用例之间互相影响。
