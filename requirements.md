# 特高压线路故障诊断 API Mock 测试平台 — 需求分析 v1.0

---

## 第一部分：概念指南 (User-Facing Conceptual Layer)

### 1. 项目概述

**特高压线路故障诊断 API Mock 测试平台**是一个基于 FastAPI 的纯 Mock 服务器，用于将 13 个 txt 文件中记录的特高压输电线路监测与故障诊断接口信息转换为可直接交互测试的 API 端点。

**核心使用场景**：

用户收到一份内网特高压监测系统的接口抓包数据（13 个 txt 文件，每个包含 curl 请求、简化参数、JSON 响应）。用户需要：

1. **快速复现接口行为**：启动服务后通过 Swagger UI 一览所有接口，模拟真实系统的请求/响应
2. **验证接口定义一致性**：填写入参调用接口，如果入参与 txt 中记录的示例完全匹配，则返回对应的 JSON 响应；如果不匹配，返回参数错误
3. **离线演示与联调**：无需连接内网远程服务器（10.238.0.5:31269），完全离线可用，方便前端联调或向他人展示接口定义
4. **模拟认证流程**：必须先调用登录接口获取 token，后续所有接口必须携带该 token 才能访问

**关键特性**：
- **会话级 Token 认证**：登录接口生成随机 token，所有业务接口强制校验 token 有效性，未登录则拒绝访问
- **严格入参匹配**：不是随意返回 mock 数据，而是严格匹配 txt 中的入参示例
- **单记录接口**：每个接口仅含 1 条入参/出参记录，匹配即返回唯一响应

### 2. 数据源特征

数据源为 `接口/` 目录下的 **13 个 txt 文件**。

**每个 txt 文件的标准三段式结构**：
1. **第一部分**：完整的 curl 命令（含所有浏览器 header、data-raw、compressed、insecure 等参数）—— **冗余信息，解析时跳过**
2. **第二部分**：简化版 curl（仅 `-X POST` 和 `-d` 传参）—— **解析入参和 URL 的来源**
3. **第三部分**：JSON 响应数据（`{"code":1001, "data":...}`）—— **解析响应数据的来源**

> **为什么跳过第一部分？** 对比两个 curl 命令行可见，第一部分仅多了浏览器相关的 HTTP header（`User-Agent`、`Origin`、`Referer`、`Accept-Language` 等）和 `--compressed`、`--insecure` 标志，请求的数据内容与第二部分完全一致。第一部分是从浏览器抓包的完整请求，第二部分是手动简化后的等效命令，两者在业务层面没有本质区别。

**提取规则**：
- **请求地址**：从**第二部分**简化 curl 中提取 URL（如 `http://10.238.0.5:31269/tgyApiservice/userservice/login`）
- **入参参数**：从**第二部分**简化 curl 的 `-d` 参数中提取（key=value 格式）
- **出参 JSON**：**第三部分**完整的 JSON 响应字符串
- **端点路径**：从 URL 中提取服务路径（如 `/userservice/login`）

**字段说明参考**：
`特高压接口.xlsx`（位于项目根目录）包含 7 个接口的返回字段说明文档（getWeather、getTripInfo、tripDiagnosis、getTripDiagnosis、getTripSolution、getPredictMessage、getTripRipple），共 115 行。可作为生成 Pydantic 模型字段 `description` 的参考来源（非强制，解析器优先从 txt 出参 JSON 推断字段结构）。

**接口分类**（13 个）：

| 接口名称 | 端点路径 | 说明 |
|---------|---------|------|
| 登录 | `/userservice/login` | 认证入口，生成随机 token |
| 省份信息 | `/patrollineservice/getProvinceInfo` | 获取省份/单位巡检配置 |
| 线路分组列表 | `/flashqueryservice/getWorkPressureLineGroupList` | 按电压等级分组获取线路列表 |
| 电压筛选 | `/reportdataservice/getPressureFilter` | 获取电压等级筛选选项 |
| 跳闸筛选 | `/devicedataservice/getTripFilter` | 获取跳闸筛选条件（省公司、线路名、故障类型） |
| 跳闸数据列表 | `/devicedataservice/getTripInfoData` | 分页查询跳闸记录 |
| 跳闸详情 | `/lineflashtripservice/getTripInfo` | 获取单条跳闸详情（含可视化监拍图片，图片路径映射到本地静态文件服务） |
| 行波数据 | `/lineflashtripservice/getTripRipple` | 获取行波数据（响应体最大） |
| 跳闸综合诊断 | `/tripdiagnosisservice/tripDiagnosis` | 综合诊断（含雷电、气象、历史覆冰等） |
| 可视化诊断 | `/tripdiagnosisservice/getTripDiagnosis` | 可视化诊断（绕击/反击概率等） |
| 处置建议 | `/tripdiagnosisservice/getTripSolution` | 根据故障类型返回运维建议 |
| 气象信息 | `/tripdiagnosisservice/getWeather` | 获取故障点实时气象及预测预警 |
| 预测消息 | `/predictservice/getPredictMessage` | 获取预测消息统计 |

### 3. 核心设计思想

**3.1 会话级 Token 认证（强制）**

与故障数据项目不同，本项目包含真实的登录接口，且认证是强制性的：

- **登录前**：调用任何非登录接口 → 返回 `{"code": 1002, "message": "未登录或token已过期"}`
- **登录接口**：接收 `account` + `password`，验证后生成随机 token 存入内存，返回给客户端
- **登录后**：客户端在所有后续请求中携带 `access_token`，服务端校验通过后才执行业务逻辑
- **重新登录**：再次调用登录接口生成新 token，旧 token 被覆盖失效（单 token 模式）

**3.2 严格入参匹配（非宽松 Mock）**

- 用户提交的入参必须与 txt 中记录的入参示例 **深度匹配**（字段名、类型、值完全一致）
- 匹配成功 → 返回 txt 中记录的 JSON 响应
- 匹配失败 → 返回 `{"code": "400003", "message": "参数错误"}`

**3.3 代码自动生成**

从 txt 文件直接解析生成 FastAPI 代码，而非手写：
- 解析 txt 中的简化 curl 参数，提取字段名、类型、默认值
- 解析 txt 中的 JSON 响应，作为硬编码的 mock 响应数据
- 自动生成 Pydantic 请求模型、匹配逻辑、端点定义
- 修改 txt 后重新生成即可更新接口

---

## 第二部分：技术实现指南 (Agent-Facing Technical Layer)

### 1. 系统架构总览

```
接口/ 目录（13 个 txt 文件）
    |
[txt_parser.py] -> 解析三段式结构 -> api_schema.json
    |
[api_generator.py] -> 读取 api_schema.json -> generated/*.py
    |
[app.py] -> FastAPI 入口 -> 自动导入 generated/*.py
    |
Swagger UI (http://localhost:8000/docs)
    |
用户填写入参 -> 调用接口 -> Token 校验 -> 入参匹配 -> 返回响应或错误
```

### 2. txt 解析策略

**2.1 解析模式**

遍历 `接口/` 目录下所有 `.txt` 文件，对每个文件执行解析：

```python
def parse_txt(filepath):
    content = read_file(filepath)
    # 提取第二个 curl 命令（简化版）
    simple_curl = extract_second_curl(content)
    # 提取 JSON 响应（最后一个 { 开头的段落）
    response_json = extract_last_json(content)
```

> **跳过第一部分**：第一部分完整 curl 仅包含浏览器 header 和传输标志，业务数据与第二部分完全一致，无需解析。

**2.2 URL 与端点路径提取**

从**第二部分**简化 curl 的 URL 中提取：
- **完整 URL**：`http://10.238.0.5:31269/tgyApiservice/xxx/yyy`
- **端点路径**：`/xxx/yyy`

**2.3 入参提取**

从第二部分简化 curl 的 `-d` 参数中提取：
- 格式为 `key=value`，多个 `-d` 参数合并为字典
- 如果简化 curl 使用 `--data-raw`（如 `tripId=xxx&access_token=yyy`），按 `&` 分割为 key=value 对

**2.4 响应 JSON 提取**

从第三部分提取以 `{` 开头的完整 JSON 字符串。对于超大响应（如 `getTripRipple.txt`，约 390KB），需完整保留。

### 3. 类型推断 Schema

从入参值中推断字段类型：

| 参数值示例 | 推断 Python 类型 | Pydantic 字段定义 |
|-----------|-----------------|------------------|
| `"value"` | `str` | `field: str = Field(default="value")` |
| `123` | `int` | `field: int = Field(default=123)` |
| `true`/`false` | `bool` | `field: bool = Field(default=True)` |
| `null` | `Any \| None` | `field: Any \| None = Field(default=None)` |
| `123.45` | `float` | `field: float = Field(default=123.45)` |

> 注意：简化 curl 的 `-d` 参数值均为字符串（HTTP 表单传输特性）。需通过尝试解析来判断真实类型：先尝试 `int()`，再尝试 `float()`，再尝试 `json.loads()`（判断 bool/null），失败则保持为 `str`。

### 4. Token 生成与校验机制

**4.1 Token 存储**

使用全局变量存储当前有效 token：

```python
# token_manager.py
_current_token: str | None = None

def generate_token() -> str:
    """生成随机 token（如 UUID 或随机字符串），存入内存"""
    global _current_token
    _current_token = secrets.token_hex(128)  # 256 字符随机 hex
    return _current_token

def validate_token(token: str) -> bool:
    """校验 token 是否有效"""
    return _current_token is not None and _current_token == token

def get_token() -> str | None:
    return _current_token
```

**4.2 登录接口特殊处理**

登录接口是唯一**不校验 token** 的接口。其行为：
1. 接收 `account` 和 `password`
2. 与 txt 中记录的示例值进行匹配（如 `account=YFZX`, `password=123456`）
3. 匹配成功 → 调用 `generate_token()` 生成新 token → 返回响应（响应体中 `data.access_token` 使用新生成的随机 token，而非 txt 中的原始值）
4. 匹配失败 → 返回账号密码错误

> 原始 txt 中的 token 值仅作占位参考，实际响应中的 `access_token` 必须由 `token_manager.generate_token()` 生成。

**4.3 全局 Token 校验依赖**

所有非登录接口使用 FastAPI `Depends` 注入 token 校验：

```python
from fastapi import Depends, HTTPException
from token_manager import validate_token

def verify_token(request: Request):
    # 从请求体或查询参数中提取 access_token
    body = request.json()
    token = body.get("access_token", "")
    if not validate_token(token):
        raise HTTPException(
            status_code=401,
            detail={"code": 1002, "message": "未登录或token已过期"}
        )

# 在业务接口端点中使用
@app.post("/xxx/yyy")
async def some_endpoint(req: SomeRequest, _=Depends(verify_token)):
    ...
```

**4.4 未登录状态**

如果没有先调用登录接口，内存中 `_current_token = None`。此时调用任何业务接口：
- token 校验失败 → 返回 `{"code": 1002, "message": "未登录或token已过期"}`
- 不会进入入参匹配逻辑

### 5. Swagger UI 动态默认值

**5.1 设计目标**

Swagger UI 的 "Try it out" 界面中，每个接口的默认入参应保留 txt 中的原始示例值，但 `access_token` 字段的值需根据当前认证状态动态变化：

- **未登录时**：`access_token` 默认值为空字符串 `""`
- **已登录后**：`access_token` 默认值为当前内存中存储的有效 token

这样用户只需点击 "Execute" 即可直接测试接口，无需手动复制粘贴 token。

**5.2 实现方式**

通过自定义 `app.openapi()` 方法，在生成 OpenAPI schema 时动态注入当前 token：

```python
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    openapi_schema = get_openapi(
        title="特高压 API Mock",
        version="1.0",
        routes=app.routes,
    )
    token = token_manager.get_token() or ""
    # 遍历所有路径，修改 requestBody 中 access_token 字段的默认值
    for path_data in openapi_schema.get("paths", {}).values():
        for operation in path_data.values():
            request_body = operation.get("requestBody", {})
            for media_type in request_body.get("content", {}).values():
                schema = media_type.get("schema", {})
                properties = schema.get("properties", {})
                if "access_token" in properties:
                    properties["access_token"]["default"] = token
    return openapi_schema

app.openapi = custom_openapi
```

**5.3 自动刷新页面机制**

Swagger UI 是静态前端应用，只在页面加载时获取一次 OpenAPI schema。为解决登录后 schema 不更新的问题，通过**自定义 Swagger UI HTML** 注入 JS 拦截器，实现登录成功后**自动刷新页面**：

```python
# app.py 中覆盖 Swagger UI HTML
from fastapi.openapi.docs import get_swagger_ui_html

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="特高压 Mock API",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
    )
    # 注入 JS：登录成功后自动刷新页面
    custom_js = """
    <script>
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const response = await originalFetch.apply(this, args);
        if (args[0].includes('/userservice/login')) {
            const clone = response.clone();
            const data = await clone.json();
            if (data.code === 1001) {
                setTimeout(() => location.reload(), 500);
            }
        }
        return response;
    };
    </script>
    """
    return html.replace("</body>", custom_js + "</body>")
```

**效果**：
1. 用户首次打开 `/docs` → `access_token` 默认值为空（未登录状态）
2. 用户填写登录参数 → 点击 Execute → 后端生成 token 存入内存 → 返回成功响应
3. 前端 JS 拦截器检测到登录成功 → 自动执行 `location.reload()` → 页面刷新
4. 页面重新加载后 → 重新获取 schema → 此时 schema 中 `access_token` 默认值已更新为有效 token
5. 用户直接点击任意业务接口的 "Execute" → 自动携带有效 token → 成功调用

> **注意**：token 存储在**后端内存**中，页面刷新不会导致 token 丢失。只有再次调用登录接口或重启服务，token 才会被覆盖或清空。

**5.4 兜底方案：请求拦截器**

作为第二道保障，在自定义 Swagger UI 中同时注入 `requestInterceptor`，确保即使 schema 默认值未更新（如用户手动阻止了页面刷新），实际发送的请求也会被自动注入当前 token：

```javascript
requestInterceptor: (req) => {
    if (req.body) {
        const body = JSON.parse(req.body);
        if (!body.access_token) {
            body.access_token = getCurrentToken();  // 从页面全局变量读取
            req.body = JSON.stringify(body);
        }
    }
    return req;
}
```

这样即使用户不刷新页面，实际发送的请求也会携带正确的 token（但输入框中显示的默认值不会变化）。

### 6. 入参匹配规则

**6.1 匹配算法**

```python
def match_request(received_body: dict, expected_body: dict) -> bool:
    for key, expected_val in expected_body.items():
        if key not in received_body:
            return False
        if received_body[key] != expected_val:
            return False
    return True
```

**6.2 匹配原则**
- 精确匹配：类型和值都必须一致
- 所有在 expected 中的字段都必须在 received 中存在且值相同
- received 中可以有额外字段

**6.3 匹配数据源**

与故障数据项目一致：**入参匹配必须基于原始请求体**（FastAPI `Request` 对象 `.json()`），而非 Pydantic 解析后的模型实例。Pydantic 模型仅用于 Swagger UI 展示和格式校验。

**6.4 匹配失败响应**

```json
{
    "code": "400003",
    "message": "参数错误"
}
```

### 7. 代码生成策略

**7.1 生成内容**

每个接口生成一个 Python 模块，包含：

1. **Pydantic 请求模型**：字段来自入参的 key=value 对，默认值取 txt 中的示例值
2. **记录字典**：硬编码的 `_RECORD`（单条记录，包含 `request` 和 `response`）
3. **匹配函数**：`_match_request()`，深度比较入参
4. **POST 端点**：`@app.post()` 装饰的异步函数，非登录接口带 `Depends(verify_token)`

**7.2 Slug 映射**

基于接口名称关键词生成 slug 和端点路径：

| 接口名称 | slug | 端点路径 |
|---------|------|---------|
| login | login | `/tgyApiservice/userservice/login` |
| getProvinceInfo | province_info | `/tgyApiservice/patrollineservice/getProvinceInfo` |
| getWorkPressureLineGroupList | line_group_list | `/tgyApiservice/flashqueryservice/getWorkPressureLineGroupList` |
| getPressureFilter | pressure_filter | `/tgyApiservice/reportdataservice/getPressureFilter` |
| getTripFilter | trip_filter | `/tgyApiservice/devicedataservice/getTripFilter` |
| getTripInfoData | trip_info_data | `/tgyApiservice/devicedataservice/getTripInfoData` |
| getTripInfo | trip_info | `/tgyApiservice/lineflashtripservice/getTripInfo` |
| getTripRipple | trip_ripple | `/tgyApiservice/lineflashtripservice/getTripRipple` |
| tripDiagnosis | trip_diagnosis_full | `/tgyApiservice/tripdiagnosisservice/tripDiagnosis` |
| getTripDiagnosis | trip_diagnosis_visual | `/tgyApiservice/tripdiagnosisservice/getTripDiagnosis` |
| getTripSolution | trip_solution | `/tgyApiservice/tripdiagnosisservice/getTripSolution` |
| getWeather | trip_weather | `/tgyApiservice/tripdiagnosisservice/getWeather` |
| getPredictMessage | predict_message | `/tgyApiservice/predictservice/getPredictMessage` |

### 8. FastAPI 入口与静态文件服务

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="特高压线路故障诊断 API Mock 测试平台")

# 挂载监拍图片静态文件服务
app.mount("/images", StaticFiles(directory="/Users/yfzx/Desktop/特高压/可视化监拍图片"), name="images")

# 自动扫描并导入 generated/ 目录下所有 *_api.py 模块
import importlib, pkgutil, generated
for _, name, _ in pkgutil.iter_modules(generated.__path__):
    if name.endswith('_api'):
        importlib.import_module(f'generated.{name}')
```

**静态文件服务**：
- `getTripInfo` 接口返回的 `image[].path` 已替换为 `/images/<filename>.jpg`
- FastAPI `StaticFiles` 将 `/images` 路由映射到本地图片目录，Swagger UI 上可直接点击预览
- 其他设备通过局域网访问时（如 `http://<你的IP>:8000/images/xxx.jpg`）也能正常加载图片

启动后访问 `http://localhost:8000/docs`：
- 列出 13 个接口
- 登录接口无需 token，其他接口自动带 token 校验
- Try it out 默认已填充 txt 中的示例值，其中 `access_token` 根据当前认证状态动态变化（未登录时空，登录后刷新页面自动填入当前 token）

### 9. 扩展性设计

**9.1 txt 更新后重新生成**

当 txt 文件内容更新时：
```bash
python txt_parser.py     # 重新解析 txt -> api_schema.json
python api_generator.py  # 重新生成 generated/*.py
# 重启 uvicorn 即可生效
```

**9.2 新增接口**

在 `接口/` 目录下新增标准三段式 txt 文件后，重新运行解析和生成脚本即可自动创建新接口。

### 10. 验证协议

**10.1 解析验证**

检查 `api_schema.json` 的完整性：
- 确认 13 个接口均被解析
- 确认每个接口的 URL、入参、出参均正确提取
- 确认 `getTripRipple` 超大响应已完整保留

**10.2 端点验证**

启动服务后访问 Swagger UI：

| 验证项 | 方法 |
|--------|------|
| 接口列表完整性 | 访问 `/docs`，确认 13 个接口全部列出 |
| 接口名称对应 | 检查每个接口的 Summary 是否与 txt 文件名一致 |
| 默认值填充 | 点击 Try it out，确认参数默认值已填充 txt 示例值 |
| 动态 token 默认值（未登录） | 首次打开 `/docs`，确认业务接口 `access_token` 默认值为空 `""` |
| 动态 token 默认值（已登录） | 登录后刷新 `/docs` 页面，确认业务接口 `access_token` 默认值为新生成的 token |
| 未登录访问 | 不调用登录接口，直接调用业务接口 → 返回 1002 未登录错误 |
| 登录成功 | 调用登录接口，确认返回响应中包含新生成的随机 token |
| 登录后访问 | 使用登录返回的 token 调用业务接口 → 返回正确 JSON |
| token 错误 | 使用错误 token 调用业务接口 → 返回 1002 未登录错误 |
| 入参匹配 | 不修改参数直接 Execute，确认返回对应出参 JSON |
| 入参不匹配 | 修改入参为不匹配的值 → 返回 400003 参数错误 |
| 图片路径映射 | 调用 getTripInfo，检查 data.image[].path 是否以 `/images/` 开头 | 是 |
| 静态文件访问 | 浏览器直接访问 `http://localhost:8000/images/xxx.jpg` | 返回图片文件（HTTP 200） |
| 重新登录 | 再次调用登录接口 → 旧 token 失效，新 token 生效 |

**10.3 端到端测试用例**

| 测试场景 | 测试步骤 | 期望结果 |
|---------|---------|---------|
| 未登录访问业务接口 | 直接 POST `/tgyApiservice/devicedataservice/getTripFilter` | `{"code": 1002, "message": "未登录或token已过期"}` |
| 动态默认值（未登录） | 首次打开 `/docs`，查看任意业务接口 Try it out 中的 `access_token` | 默认值为空字符串 `""` |
| 登录成功 | POST `/tgyApiservice/userservice/login`，入参为 txt 示例值 | `{"code": 1001, "data": {"access_token": "<随机token>", ...}}` |
| 动态默认值（已登录） | 登录成功后**刷新 `/docs` 页面**，查看业务接口 Try it out | `access_token` 默认值为新生成的 token |
| 登录后访问 | 携带登录返回的 token 调用 `/tgyApiservice/devicedataservice/getTripFilter` | 返回 txt 中记录的 JSON 响应 |
| 错误 token | 携带错误 token 调用任意业务接口 | `{"code": 1002, "message": "未登录或token已过期"}` |
| 旧 token 失效 | 重新登录生成新 token，再用旧 token 调用业务接口 | 返回 1002 未登录错误 |
| 入参不匹配 | 登录后，修改某字段值调用接口 | `{"code": "400003", "message": "参数错误"}` |
| 图片路径验证 | 调用 getTripInfo，检查返回的 path 字段 | 格式为 `/images/<filename>.jpg`，可直接通过 `http://localhost:8000/images/<filename>.jpg` 访问 |

### 11. 已知问题与注意事项

**11.1 超大响应文件**

`getTripRipple.txt` 约 390KB，生成代码时作为硬编码字典可能导致 `.py` 文件过大。不影响功能，但会增加代码生成时间。可考虑将超大响应存入单独的 `.json` 文件，运行时动态加载。

**11.2 入参类型推断限制**

简化 curl 的 `-d` 参数在 HTTP 层面均为字符串。类型推断通过尝试解析实现：
- `json.loads(value)` 成功 → 可能是 bool / null / 嵌套对象
- `int(value)` 成功 → int
- `float(value)` 成功 → float
- 否则 → str

对于明确应为数字但被引号包裹的值（如 `"001"`），推断为 `str` 是正确的。

**11.3 Token 生命周期**

当前为纯内存存储，服务重启后 token 丢失，需重新登录。这是 Mock 服务器的预期行为。
