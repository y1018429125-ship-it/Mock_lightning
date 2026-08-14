# Task：特高压线路故障诊断 API Mock 测试平台

> 每次派任务时，按以下格式填写。减少理解偏差，对齐交付预期。

---

## Context（背景）

- 仓库定位：Python 独立项目，桌面 `特高压/` 目录
- 相关模块/文件：txt 解析、Pydantic 模型生成、FastAPI 端点生成、Token 管理、入参匹配逻辑
- 已知限制：
  - 数据源为 `接口/` 目录下 13 个 txt 文件，非 Excel
  - 每个 txt 为标准三段式结构（完整 curl + 简化 curl + JSON 响应），解析时跳过第一部分冗余 curl，只看第二部分简化 curl 和第三部分 JSON 响应
  - 登录接口必须生成随机 token，其他接口必须校验该 token
  - 单 token 覆盖式：重新登录后旧 token 失效
  - 内网远程 API（10.238.0.5:31269）不可用，服务为纯 Mock，不发起任何 HTTP 请求
  - 项目从零开始，无参考代码可用

---

## Goal（目标）

基于 `接口/` 目录下 13 个 txt 文件中记录的特高压输电线路监测与故障诊断 API 接口信息，构建一个 **纯 Mock 测试平台**。

系统核心能力：
1. **强制认证流程**：必须先调用登录接口获取 token，否则所有业务接口返回未登录错误
2. **严格入参匹配**：登录后调用业务接口，如果入参与 txt 中记录的示例完全匹配，则返回对应的 JSON 响应；否则返回参数错误
3. **单记录接口**：每个接口仅 1 条入参/出参记录

**支持场景**：
- **未登录访问**：任何非登录接口 → 返回 `{"code": 1002, "message": "未登录或token已过期"}`
- **登录成功**：入参匹配 txt 示例 → 生成随机 token → 返回响应
- **登录后访问**：携带有效 token 调用业务接口 → 入参匹配 → 返回 JSON 响应
- **重新登录**：再次调用登录接口 → 旧 token 失效，新 token 生效
- **token 错误**：携带无效/过期 token → 返回未登录错误

**关键设计原则**：
- 强制 Token 认证：登录接口生成随机 token，业务接口全局校验
- 严格入参匹配：入参必须与 txt 示例完全匹配（字段名、类型、值一致）
- 不调用远程 API：纯 Mock，完全离线可用
- 代码自动生成：从 txt 解析后直接生成 FastAPI 代码

---

## Acceptance criteria（验收标准）

- [ ] 13 个 API 接口均被正确解析，每个接口的 URL、入参、出参均正确提取
- [ ] `getTripRipple` 超大响应（约 390KB）完整保留，无截断
- [ ] `getTripInfo` 返回的 `image[].path` 字段已替换为 `/images/<filename>.jpg`（映射到本地静态文件服务）
- [ ] 浏览器直接访问 `http://localhost:8000/images/xxx.jpg` 可正常加载图片（HTTP 200）
- [ ] 每个接口生成独立的 Pydantic 请求模型，字段类型推断正确（str/int/bool/float/None）
- [ ] Swagger UI 上列出 13 个接口，Summary 与 txt 文件名一一对应
- [ ] Swagger UI Try it out 默认填充 txt 中的示例值，其中 `access_token` 根据当前认证状态动态变化（未登录时空，登录后**自动刷新页面**填入当前 token）
- [ ] **未登录时**：调用任意业务接口返回 `{"code": 1002, "message": "未登录或token已过期"}`
- [ ] **登录接口**：入参匹配 txt 示例 → 返回 `{"code": 1001, "data": {"access_token": "<随机生成的token>", ...}}` → 页面**自动刷新**
- [ ] **自动刷新后验证**：登录成功自动刷新页面后，任意业务接口的 `access_token` 默认值已自动填入当前有效 token
- [ ] **登录后**：携带登录返回的 token 调用业务接口 → 入参匹配 → 返回对应 JSON 响应
- [ ] **错误 token**：携带错误 token 调用业务接口 → 返回 1002 未登录错误
- [ ] **重新登录**：再次调用登录接口后，旧 token 失效，新 token 可正常访问业务接口
- [ ] **入参不匹配**：登录后修改入参为不匹配值 → 返回 `{"code": "400003", "message": "参数错误"}`
- [ ] 登录接口是唯一不校验 token 的接口
- [ ] 一键启动脚本 `setup.py` 可用：解析 txt → 生成代码 → 启动服务

**验证命令**：
```bash
# 一键启动
python setup.py

# 或分步验证
python txt_parser.py      # 检查 api_schema.json 生成是否正确
python api_generator.py   # 检查 generated/*.py 生成是否正确
uvicorn app:app --reload  # 启动后访问 http://localhost:8000/docs
```

---

## Constraints（约束）

- [ ] 不泄露 secrets（.env、key、token、credentials）
- [ ] 最小化改动，不重构无关代码
- [ ] 改动不超过 5 个文件时直接修改；超过 5 个需停下说明理由
- [ ] 连续 2 次排错失败找不到原因必须停下报告
- [ ] **源码目录**：所有源代码存放于 `src/` 目录下

---

## Delivery（必须交付）

1. **计划**：3-7 步执行计划，每步含验证方式
2. **代码改动**：实际新建/修改的文件和内容
3. **关键 diff**：影响最大的改动对比
4. **验证输出**：测试命令的实际运行结果

---

## 附加说明

### 编码规范
- 严格遵守 `skills/coding-protocol.md` 的质量流程（Scout → Builder → Verifier）
- 长任务按 `skills/ulw-loop.md` 切成多轮，每轮只改 1 个改动点
- 每轮结束必须有验证日志，否则不得进入下一轮

### 技术栈
- 语言：Python 3.12
- 依赖管理：pip（requirements.txt）
- Web 框架：FastAPI 0.115+
- 服务器：Uvicorn
- txt 解析：Python 标准库（re, pathlib）
- 数据验证：Pydantic 2.x
- API 文档：FastAPI 自带 Swagger UI（`http://localhost:8000/docs`）

### 数据来源
- **主要数据源**：`/Users/yfzx/Desktop/特高压/接口/*.txt`
  - 13 个 txt 文件，每个含标准三段式结构（完整 curl + 简化 curl + JSON 响应）
  - 每个接口包含：请求地址、入参 key=value 对、出参 JSON
  - **解析时跳过第一部分冗余 curl**，只看第二部分（简化 curl）和第三部分（JSON 响应）
- **字段说明参考**：`/Users/yfzx/Desktop/特高压/特高压接口.xlsx`
  - 包含 7 个接口（getWeather、getTripInfo、tripDiagnosis、getTripDiagnosis、getTripSolution、getPredictMessage、getTripRipple）的返回字段说明，共 115 行
  - 可作为生成 Pydantic 模型字段 `description` 的参考来源（非强制）

### 项目目录结构

```
/Users/yfzx/Desktop/特高压/
├── requirements.md                 # 需求分析（本文档同级）
├── task.md                         # 任务说明（本文档）
├── 接口/                            # txt 数据源目录
│   ├── login.txt
│   ├── getProvinceInfo.txt
│   ├── getWorkPressureLineGroupList.txt
│   ├── getPressureFilter.txt
│   ├── getTripFilter.txt
│   ├── getTripInfoData.txt
│   ├── getTripInfo.txt
│   ├── getTripRipple.txt
│   ├── tripDiagnosis.txt
│   ├── getTripDiagnosis.txt
│   ├── getTripSolution.txt
│   ├── getWeather.txt
│   └── getPredictMessage.txt
├── 可视化监拍图片/                   # getTripInfo 监拍图片源目录（6张 .jpg）
│   └── *.jpg
├── 密集通道信息数据表.xlsx
├── 三大直流-数据接口规范（WMS）_20191218.docx
├── 三大直流-数据接口规范（雷电）_20191218.docx
├── 三大直流-数据接口规范（密集通道）_20200524.docx
├── 特高压接口.xlsx
└── src/                            # 【本项目的源码目录】
    ├── requirements.txt            # 依赖：fastapi, uvicorn, pydantic
    ├── txt_parser.py               # txt 解析器 -> api_schema.json
    ├── api_generator.py            # 代码生成器 -> generated/*.py
    ├── token_manager.py            # Token 生成与校验
    ├── app.py                      # FastAPI 入口（含 /images 静态文件挂载）
    ├── setup.py                    # 一键脚本：解析+生成+启动
    ├── api_schema.json             # 解析后的结构化数据（中间产物）
    └── generated/                  # 生成的 API 模块
        ├── __init__.py
        └── {slug}_api.py           # 每个接口一个模块（13 个）
```

### 接口清单

| # | 文件名 | 端点路径 | 需 Token 校验 |
|---|--------|---------|-------------|
| 1 | login.txt | `/tgyApiservice/userservice/login` | ❌ 否（生成 token） |
| 2 | getProvinceInfo.txt | `/tgyApiservice/patrollineservice/getProvinceInfo` | ✅ 是 |
| 3 | getWorkPressureLineGroupList.txt | `/tgyApiservice/flashqueryservice/getWorkPressureLineGroupList` | ✅ 是 |
| 4 | getPressureFilter.txt | `/tgyApiservice/reportdataservice/getPressureFilter` | ✅ 是 |
| 5 | getTripFilter.txt | `/tgyApiservice/devicedataservice/getTripFilter` | ✅ 是 |
| 6 | getTripInfoData.txt | `/tgyApiservice/devicedataservice/getTripInfoData` | ✅ 是 |
| 7 | getTripInfo.txt | `/tgyApiservice/lineflashtripservice/getTripInfo` | ✅ 是 |
| 8 | getTripRipple.txt | `/tgyApiservice/lineflashtripservice/getTripRipple` | ✅ 是 |
| 9 | tripDiagnosis.txt | `/tgyApiservice/tripdiagnosisservice/tripDiagnosis` | ✅ 是 |
| 10 | getTripDiagnosis.txt | `/tgyApiservice/tripdiagnosisservice/getTripDiagnosis` | ✅ 是 |
| 11 | getTripSolution.txt | `/tgyApiservice/tripdiagnosisservice/getTripSolution` | ✅ 是 |
| 12 | getWeather.txt | `/tgyApiservice/tripdiagnosisservice/getWeather` | ✅ 是 |
| 13 | getPredictMessage.txt | `/tgyApiservice/predictservice/getPredictMessage` | ✅ 是 |

### 类型推断规则

| 原始值 | Python 类型 |
|--------|------------|
| `"string"` | `str` |
| `123` | `int` |
| `true`/`false` | `bool` |
| `null` | `Any \| None` |
| `123.45` | `float` |

> 注：简化 curl 的 `-d` 参数值在 HTTP 层面均为字符串，需通过尝试解析判断真实类型。

### 认证状态机

```
初始状态（_current_token = None）
    |
    v
[调用登录接口]
    | 入参匹配成功
    v
生成新 token → _current_token = "<随机token>"
    |
    v
[调用业务接口] → 校验 token → 通过 → 入参匹配 → 返回响应
    |                                     |
    | 校验失败                             | 不匹配
    v                                     v
返回 1002 未登录                      返回 400003 参数错误
    |
    v
[再次调用登录接口]
    |
    v
生成新 token → 覆盖 _current_token
    |
    v
旧 token 失效，新 token 可用
```

### 协作规范（AI 助手执行约束）

**代码生成前必须确认**

由于本项目涉及从 txt 自动生成代码文件（约 13 个模块），在开始代码生成前必须确认：
- txt 解析结果（`api_schema.json`）已人工检查通过
- Slug 映射表（`SLUG_MAP`）已确认无误

**验证优先级**

日常代码改动后的验证应优先使用轻量级方式：
- 语法检查：`python3 -m py_compile txt_parser.py api_generator.py app.py token_manager.py`
- 解析验证：检查 `api_schema.json` 的接口数量和字段提取正确性
- 单接口验证：测试登录接口 + 1-2 个业务接口

**端到端测试**

完整的 13 个接口端到端验证在代码稳定后执行，日常改动不需要全量验证。
