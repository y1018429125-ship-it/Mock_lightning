# Task：雷电故障诊断 MCP Tool

> 每次派任务时，按以下格式填写。减少理解偏差，对齐交付预期。

---

## Context（背景）

- 仓库定位：Python MCP Server 项目，源码目录 `特高压/MCP src/`
- 依赖服务：本地 FastAPI Mock 服务（`http://localhost:8000`），源码位于 `特高压/src/`
- 相关模块/文件：MCP Tool 定义、HTTP 客户端、诊断引擎、波形图生成器
- 已知限制：
  - 数据源为 Mock 服务，非真实内网 API
  - 当前仅有单条测试数据（query_date=2025-05-08, line_name=雅湖线 → tripId=S_Y202505080552），所有接口均为单记录
  - 波形数据超大（getTripRipple 约 390KB），绘图时需降采样
  - 认证采用单 token 覆盖模式，登录后旧 token 失效
  - 波形图绘制需与 Mock 前端 SVG 样式一致

---

## Goal（目标）

基于本地运行的特高压 API Mock 测试平台，构建一个 **雷电故障诊断 MCP Tool**。

系统核心能力：
1. **用户输入日期和线路名** → 自动完成认证 → 查询 `getTripInfoData` 获取 tripId → 拉取全部相关数据
2. **多源交叉验证诊断** → 4 个独立模块加权投票 → 输出诊断结论和置信度
3. **诊断时生成波形图** → 每次诊断自动在模块一 中绘制故障波形图

**支持场景**：
- **正常诊断**：输入日期 + 线路名 → 自动认证并查询 tripId → 拉取全部相关数据 → 生成故障波形图 → 返回 Markdown 格式诊断报告（含文本 + 波形图）
- **服务未启动**：Mock 服务未运行 → 返回友好错误提示
- **数据缺失**：某接口数据丢失 → 该维度置信度降为 0，其他维度继续诊断
- **未找到记录**：`getTripInfoData` 未查询到匹配的跳闸记录 → 返回"未找到 {query_date} {line_name} 的跳闸记录"

**关键设计原则**：
- **模块化多源验证**：诊断拆分为"故障波形分析"、"分布式监测判定"、"雷电定位系统分析"、"气象条件"四个独立模块
- **不依赖 tripDiagnosis 接口**：所有信息可被其他接口 + 自算替代
- **独立地理计算**：haversine 自算落雷点与故障杆塔距离，不依赖外部距离字段
- **故障波形分析**：getTripRipple 波形图 + getTripDiagnosis 概率结论合并为一个 30% 权重的模块，每次诊断都绘制波形图

---

## Acceptance criteria（验收标准）

- [ ] MCP Server 可通过 `uv run mcp dev server.py` 正常启动
- [ ] `diagnose_lightning_tool(query_date="2025-05-08", line_name="雅湖线")` 返回 `CallToolResult`，`content[0]` 为 Markdown 诊断报告，`content[1..3]` 为三张独立波形图，结论为"雷击-绕击"，综合置信度为 **0.985**（保留三位小数）
- [ ] 诊断报告 Markdown 中包含 5 个证据条目（模块一、模块二、模块 3.1、模块 3.2、模块四），权重之和为 1.00
- [ ] 最终诊断结论采用模块一细分结论（雷击-绕击 / 雷击-反击 / 雷击 / 非雷击），并在结论中总结各模块支撑情况
- [ ] 任意接口返回非 1001 或关键参数为空时，该模块置信度贡献为 0，报告中显示"XX接口数据同步异常"，其他模块继续诊断
- [ ] 模块一 输出以 Markdown 文本展示：基于波形图分析得出半峰值时间和行波幅值、从 `process` 提取半峰值时间和幅值条件（比较词和数值）并结合 `data.isLightning/noLightning` 和 `data.roundPass/backPass` 输出雷击/非雷击、绕击/反击判定结论、概率分布表格、故障波形分析结论及置信度贡献；并作为单独 image content 返回三张模块一波形图（行波×2、工频×1）
- [ ] 模块二 输出以 Markdown 文本展示：故障基本信息（故障时间、线路名称、电压等级、故障相别、故障杆塔位置、故障描述）、分布式监测结论及置信度贡献
- [ ] 模块一 的置信度贡献计算为 isLightning × 0.30 = 0.95 × 0.30 = 0.285
- [ ] 模块二 的置信度贡献计算为 support_score × 0.15，当前数据 support_score=1.0，贡献 0.15
- [ ] 模块三 输出包含 3.1 雷电活动规模表格（含序号列）和 3.2 雷电与故障杆塔地理关联表格（不含序号列，按距离升序）
- [ ] 模块 3.1 置信度贡献为 15%，模块 3.2 置信度贡献为 30%，模块三 合计贡献 0.45
- [ ] 模块 3.2 距离阈值规则：优先判断 500m 内是否有雷电记录；500m 内 ≥1 条得 30%，500m 内 0 条但 5000m 内 ≥1 条得 24%，否则 0%
- [ ] diagnose_lightning_tool 在模块一 中生成三张独立的 PNG 波形图（行波×2、工频×1），每张图尺寸 600×280 px，与 Mock 前端 `/docs` 中 getTripRipple 波形图样式完全一致
- [ ] 每张波形图画布尺寸 600×280 px，按像素宽度降采样，波形线颜色 `#2196F3`，线宽 1.5px，背景网格 `#e0e0e0`，坐标轴颜色 `#333`
- [ ] 三张子图坐标轴范围与 Mock 前端一致：两个行波 X 轴 0-7000μs / Y 轴分别为 -2000~1000A 和 -3000~2000A，工频 X 轴 0-1200ms / Y 轴 -2000~5000A
- [ ] 每个子图标题为"故障波形：{waveType}波形"，X 轴标签为"时间（微秒）"或"时间（毫秒）"，Y 轴标签为"电流（安培）"
- [ ] Mock 服务未启动时返回清晰错误提示
- [ ] 模块四 输出包含温度、风速、湿度，并基于湿度 40%/70% 阈值给出雷暴条件结论
- [ ] 模块四 的置信度贡献按湿度阈值计算：>70% 得 0.10，40%-70% 得 0.08，<40% 得 0
- [ ] `diagnose_lightning_tool(query_date="2025-05-08", line_name="雅湖线")` 调用流程：login → getTripInfoData → 匹配 tripLineName="雅湖线" 的第一条记录 → 获取 tripId → 并行调用 getTripDiagnosis/getTripInfo/getTripRipple/getWeather
- [ ] 日期格式支持 `"2025-05-08"` 和 `"2025年5月8日"` 两种
- [ ] `getTripInfoData` 入参固定：`timeOrderBy=1`、`pressureType=1`、`page=0`、`pageSize=999`，`startTime` 和 `endTime` 基于 `query_date` 动态生成
- [ ] `tripLineName` 与 `line_name` 精确匹配，只诊断第一条匹配记录
- [ ] 未找到匹配记录时返回清晰错误："未找到 {query_date} {line_name} 的跳闸记录"
- [ ] 诊断报告中不显示 tripId
- [ ] 综合置信度 = 模块一 + 模块二 + 模块三 + 模块四，`query_date="2025-05-08", line_name="雅湖线"` 时综合置信度为 0.985
- [ ] 所有 Tool 函数带完整类型提示和 docstring
- [ ] 代码通过 `python3 -m py_compile` 语法检查
- [ ] **数据来源约束**：所有数据必须通过 Mock 测试平台 HTTP 接口获取，禁止直接读取 txt 文件或本地文件
- [ ] **不使用 tripDiagnosis 接口**：所有信息由其他接口 + 自算替代
- [ ] **置信度透明**：诊断报告中必须包含每项证据的权重、原始数据、支撑逻辑
- [ ] 所有 Tool 函数带完整类型提示和 docstring
- [ ] 代码通过 `python3 -m py_compile` 语法检查

**验证命令**：
```bash
# 进入 MCP 源码目录
cd "/Users/yfzx/Desktop/特高压/MCP src"

# 安装依赖（含 pydantic）
uv add "mcp[cli]" httpx matplotlib pydantic

# 启动 MCP Inspector 测试
uv run mcp dev server.py

# 安装到 Claude Desktop
uv run mcp install server.py

# 语法检查
python3 -m py_compile server.py client.py diagnosis_engine.py wave_plotter.py models.py config.py

# 端到端验证（需先启动 Mock 服务：cd ../src && uvicorn app:app --host 127.0.0.1 --port 8000）
uv run python -c "
import asyncio
from server import diagnose_lightning_tool
async def main():
    result = await diagnose_lightning_tool('2025-05-08', '雅湖线')
    print('isError:', result.isError)
    print('content count:', len(result.content))
asyncio.run(main())
"
```

---

## Constraints（约束）

- [ ] 不泄露 secrets（.env、key、token、credentials）
- [ ] 最小化改动，不重构无关代码
- [ ] 改动不超过 5 个文件时直接修改；超过 5 个需停下说明理由
- [ ] 连续 2 次排错失败找不到原因必须停下报告
- [ ] **源码目录**：所有源代码存放于 `MCP src/` 目录下
- [ ] **数据来源约束**：所有数据必须通过 Mock 测试平台 HTTP 接口获取，禁止直接读取 txt 文件或本地文件
- [ ] **不使用 tripDiagnosis 接口**：所有信息由其他接口 + 自算替代
- [ ] **置信度透明**：诊断报告中必须包含每项证据的权重、原始数据、支撑逻辑
- [ ] **关键参数定义**：影响模块置信度计算的核心输入参数为空/缺失时，该模块置信度贡献为 0（详见 mcp_requirements.md 4.3 节）
- [ ] **波形图输出**：模块一返回三张独立的 600×280 px PNG 波形图
- [ ] **小数精度**：报告中所有置信度、支撑度、贡献值统一保留三位小数
- [ ] **中文字体依赖**：波形图标签依赖系统字体，macOS 需 STHeiti，Linux 需 wqy-zenhei

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
- 依赖管理：uv
- MCP SDK：mcp[cli]
- HTTP 客户端：httpx
- 波形图绘制：matplotlib
- 数据验证：Pydantic

### 项目目录结构

```
/Users/yfzx/Desktop/特高压/
├── requirements.md                 # API Mock 需求分析
├── task.md                         # API Mock 任务说明
├── mcp_requirements.md             # MCP 需求分析（本文档同级）
├── mcp_task.md                     # MCP 任务说明（本文档）
├── src/                            # 【API Mock 源码目录（已有）】
│   ├── requirements.txt
│   ├── txt_parser.py
│   ├── api_generator.py
│   ├── token_manager.py
│   ├── app.py
│   ├── setup.py
│   ├── api_schema.json
│   └── generated/
│       ├── __init__.py
│       └── *_api.py
├── MCP src/                        # 【MCP Tool 源码目录（空）】
│   ├── requirements.txt            # 依赖：mcp[cli], httpx, matplotlib
│   ├── server.py                   # MCP 服务器入口
│   ├── config.py                   # 配置
│   ├── client.py                   # HTTP 客户端
│   ├── diagnosis_engine.py         # 诊断引擎
│   ├── wave_plotter.py             # 波形图生成器
│   └── models.py                   # Pydantic 模型
├── 接口/                            # txt 数据源目录
├── 可视化监拍图片/                   # 监拍图片源目录
└── ...
```

### 证据链与置信度汇总

| 模块 | 证据来源 | 权重 | 原始接口 | 原始字段 |
|------|---------|------|---------|---------|
| 模块一：故障波形分析 | getTripRipple + getTripDiagnosis | 0.30 | getTripRipple + getTripDiagnosis | `eigenvalue.amplitude`, `eigenvalue.halfPeakTime`, `data.isLightning/roundPass/backPass`, `process` |
| 模块二：分布式监测判定 | getTripInfo.trip.tripCause/tripClass | 0.15 | getTripInfo | `trip.tripCause`, `trip.tripClass` |
| 模块三 3.1 雷电活动规模 | getTripInfo.flash[] 雷电总条数 | 0.15 | getTripInfo | `flash[]` 全部字段 |
| 模块三 3.2 雷电与故障杆塔地理关联 | getTripInfo.flash[] + 自算 haversine 距离 | 0.30 | getTripInfo | `flash[].longitude`, `flash[].latitude`, `trip.longitude`, `trip.latitude` |
| 模块四：气象条件 | getWeather.real.hum | 0.10 | getWeather | `real.hum` |
| — | tripDiagnosis | **不使用** | — | — |
| | **合计** | **1.00** | | |

### 诊断结论分类

```
大类1：雷击（isLightning >= noLightning）
    └── 小类1：绕击（roundPass > backPass）→ 雷击-绕击
    └── 小类2：反击（roundPass < backPass）→ 雷击-反击
    └── 小类3：roundPass == backPass → 雷击

大类2：非雷击（isLightning < noLightning）
    └── 金属性接地 / 高阻性接地 / 其他
```

### 接口清单（本 Tool 使用）

| # | 接口 | 端点 | 用途 | 诊断推理 | 展示输出 |
|---|------|------|------|---------|---------|
| 1 | login | `/tgyApiservice/userservice/login` | 认证 | — | — |
| 2 | getTripInfoData | `/tgyApiservice/devicedataservice/getTripInfoData` | 查询 tripId | — | 否 |
| 3 | getTripDiagnosis | `/tgyApiservice/tripdiagnosisservice/getTripDiagnosis` | 故障波形分析结论 | 模块一 | 输出模块一 明细 |
| 4 | getTripInfo | `/tgyApiservice/lineflashtripservice/getTripInfo` | 分布式判定 + 雷电定位数据 + 图片 | 模块二 + 模块三 | 输出概况 |
| 5 | getTripRipple | `/tgyApiservice/lineflashtripservice/getTripRipple` | 原始波形数据 | 模块一（绘制波形图） | 每次诊断生成波形图 |
| 6 | getWeather | `/tgyApiservice/tripdiagnosisservice/getWeather` | 气象数据 | 模块四 | 输出数据 |

### Tool 参数

```python
async def diagnose_lightning_tool(query_date: str, line_name: str) -> CallToolResult:
    """
    基于日期和线路名查询雷击故障诊断结果。

    Args:
        query_date: 查询日期，支持 "2025-05-08" 或 "2025年5月8日"
        line_name: 线路名称，如 "雅湖线"，需与 getTripInfoData 返回的 tripLineName 精确匹配
    """
```

### 波形图绘制规范

与 Mock 测试平台前端（`app.py` custom Swagger UI）完全一致：

| 参数 | 值 |
|------|-----|
| 画布 | 600 x 280 px |
| 采样 | 按像素宽度降采样 |
| 波形线颜色 | `#2196F3` |
| 波形线宽 | 1.5px |
| 网格颜色 | `#e0e0e0` |
| X轴标签（行波） | 时间（微秒） |
| X轴标签（工频） | 时间（毫秒） |
| Y轴标签 | 电流（安培） |
| 坐标轴颜色 | `#333` |
| 刻度字体大小 | 10px |
| 标签字体大小 | 12px |

**坐标轴范围**：

| # | waveType | X轴范围 | Y轴范围 |
|---|----------|---------|---------|
| 1 | 行波 | 0 - 7000 μs | -2000 ~ 1000 A |
| 2 | 行波 | 0 - 7000 μs | -3000 ~ 2000 A |
| 3 | 工频 | 0 - 1200 ms | -2000 ~ 5000 A |

### 验证优先级

- 语法检查：`python3 -m py_compile server.py client.py diagnosis_engine.py wave_plotter.py models.py config.py`
- MCP Inspector 测试：`uv run mcp dev server.py`
- 端到端验证：测试 diagnose_lightning_tool Tool
