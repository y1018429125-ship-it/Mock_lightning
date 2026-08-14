# 雷电故障诊断 MCP Tool — 需求分析 v1.0

---

## 第一部分：概念指南 (User-Facing Conceptual Layer)

### 1. 项目概述

**雷电故障诊断 MCP Tool** 是一个基于 Model Context Protocol (MCP) 的智能诊断工具，连接本地运行的特高压 API Mock 测试平台，为特高压输电线路的雷击故障提供多源交叉验证的诊断结论。

**核心使用场景**：

用户（运维人员/分析人员）面对一条特高压线路跳闸记录，需要快速判断故障是否为雷击、是绕击还是反击。传统方式需要逐个登录系统、查看多个模块的数据，人工综合分析。本工具将这一过程自动化：

1. **输入日期和线路名** → 自动完成认证 → 查询 getTripInfoData 获取 tripId → 拉取全部相关数据
2. **多源交叉验证** → 独立计算各证据的置信度 → 加权合成最终结论
3. **输出结构化诊断报告** → 包含结论、置信度、各项证据明细

**关键特性**：
- **模块化多源验证**：将诊断拆分为"故障波形分析"、"分布式监测判定"、"雷电定位系统分析"、"气象条件"四个独立模块，每个模块独立贡献置信度
- **基于日期和线路名查询**：用户输入日期和线路名，Tool 自动通过 `getTripInfoData` 查询对应 `tripId`，无需手动输入 tripId
- **不依赖单一结论**：不直接使用 tripDiagnosis 的 "雷击-绕击" 结果作为判断，而是将 getTripDiagnosis 的概率输出作为"故障波形分析"模块的证据之一
- **独立地理计算**：不依赖 tripDiagnosis 接口的距离字段，直接使用 getTripInfo 的落雷点经纬度和故障杆塔经纬度计算 haversine 距离，避免数据未同步问题
- **置信度透明**：每项证据的权重、原始数据、支撑逻辑对用户可见，可审计、可解释
- **波形随诊断绘制**：每次诊断均调用 getTripRipple 生成故障波形图，作为模块一 故障波形分析的完整链路输出

### 数据获取原则

**所有数据必须通过本地 Mock 测试平台的 HTTP 接口获取，禁止直接读取 txt 文件或本地文件。**
- 认证：调用 `POST /tgyApiservice/userservice/login`
- 查询 tripId：调用 `POST /tgyApiservice/devicedataservice/getTripInfoData`
- 诊断数据：调用 `getTripDiagnosis`、`getTripInfo`、`getTripRipple`、`getWeather`

### 2. 证据链设计

诊断结论基于 **5 个证据条目** 的加权投票：

| 模块 | 证据来源 | 置信度 | 说明 |
|------|---------|--------|------|
| **模块一：故障波形分析** | getTripRipple + getTripDiagnosis | 0.30 | 绘制波形图 → 提取 eigenvalue → 基于 process 判定规则 → 输出 data 概率 → 结论"雷击-绕击" |
| **模块二：分布式监测判定** | getTripInfo.trip.tripCause/tripClass | 0.15 | 分布式监测系统独立判定为"雷击" |
| **模块三 3.1 雷电活动规模** | getTripInfo.flash[] 雷电总条数 | 0.15 | 统计故障时刻前后雷电记录总条数，判断雷电活动强度 |
| **模块三 3.2 雷电与故障杆塔地理关联** | getTripInfo.flash[] + 自算 haversine 距离 | 0.30 | 落雷点经纬度与故障杆塔经纬度计算距离，按 500m/5000m 阈值判定 |
| **模块四：气象条件** | getWeather.real.hum | 0.10 | 仅使用湿度参数，按 40%/70% 阈值判定是否有利于雷暴形成 |
| | tripDiagnosis 接口 | **不使用** | 无独立信息，距离可由自算替代，result/report1 与 getTripDiagnosis 重复 |
| | **合计** | **1.00** | |

### 模块一：故障波形分析

**输入接口**：getTripRipple + getTripDiagnosis

**分析流程**：

1. **绘制波形图**：调用 getTripRipple 获取三组波形数据（行波×2 + 工频×1），生成与 Mock 前端 SVG 样式一致的波形图。三个波形图分别作为三张独立的 PNG 返回，每张画布尺寸均为 600×280 px。
2. **提取特征值**：从 getTripDiagnosis 的 eigenvalue 字段获取：
   - `amplitude: -2262.5898` — 行波幅值
   - `halfPeakTime: 0.000564` — 半峰值时间
3. **判定分析**：从 `getTripDiagnosis.process` 字段中提取关键判定条件，结合 `getTripInfo.trip.pressure` 和 `data` 概率输出，生成可读判定结论。

   **提取规则**：
   - 从 `process` 中提取"半峰值时间"后的比较条件（比较词 + 数值），如"小于等于40" → "≤ 40"
   - 从 `process` 中提取"幅值"后的比较条件（比较词 + 数值），忽略 `process` 中自带的电压等级描述
   - 实际电压等级使用 `getTripInfo.trip.pressure`，不使用 `process` 中的电压等级阈值
   - 比较词映射：小于→<、小于等于→≤、大于→>、大于等于→≥、远远大于→>>、远远小于→<<

   **结论词规则**：
   - 雷击 vs 非雷击：由 `data.isLightning` 和 `data.noLightning` 比较决定
     - `isLightning >= noLightning` → "雷击"
     - `isLightning < noLightning` → "非雷击"
   - 绕击 vs 反击：由 `data.roundPass` 和 `data.backPass` 比较决定（仅雷击时输出）
     - `roundPass > backPass` → "绕击"
     - `roundPass < backPass` → "反击"
     - `roundPass == backPass` → 不输出绕击/反击结论句

   **process 字段示例**（tripId=S_Y202505080552）：
   
   ```
   雅湖线是分布式故障雷电定位小于5isLightning += 0.1;半峰值时间小于等于40isLightning += 0.15;电压等级大于220或小于等于500并且幅值小于等于50绕反击roundPass += 0.9;backPass += 0.1;...
   ```
   
   **提取后的判定分析输出示例**（`trip.pressure=±800`，`isLightning=0.95 >= noLightning=0.05`，`roundPass=0.86 > backPass=0.10`）：
   
   > 半峰值时间 ≤ 40，符合雷击判定条件；电压等级为 ±800kV 且幅值 ≤ 50，符合绕击判定条件。
   
   **泛化示例**：
   
   | process 原文 | 提取的半峰值条件 | 提取的幅值条件 |
   |---|---|---|
   | 半峰值时间小于等于40 | 半峰值时间 ≤ 40 | — |
   | 半峰值时间大于100 | 半峰值时间 > 100 | — |
   | 电压等级大于220或小于等于500并且幅值小于等于50 | — | 幅值 ≤ 50 |
   | 电压等级为1100并且幅值远远大于80 | — | 幅值 >> 80 |
   
   若 `roundPass == backPass`，则不输出"电压等级为 ... 且幅值 ..."这一句。
4. **输出概率**：data 字段给出最终概率：

| 故障类型 | 总概率 | 雷击类型 | 雷击类型概率 |
|---------|--------|---------|-------------|
| 雷击 | 0.95 | 绕击 | 0.86 |
| 雷击 | 0.95 | 反击 | 0.10 |
| 非雷击 | 0.05 | — | — |

5. **判定逻辑**：
   - 第一层（雷击 vs 非雷击）：
     - 若 `isLightning >= noLightning`，判定为雷击，模块一 支撑度为 `isLightning`，置信度贡献为 `isLightning × 0.30`
     - 若 `isLightning < noLightning`，判定为非雷击，模块一 支撑度为 `0`，置信度贡献为 `0`
   - 第二层（仅雷击时细分绕击/反击）：
     - 若 `roundPass > backPass`，结论为"雷击-绕击"
     - 若 `roundPass < backPass`，结论为"雷击-反击"
     - 若 `roundPass == backPass`，结论为"雷击"

6. **模块结论示例**："基于故障波形分析，输电线路故障类型为雷击-绕击。"

7. **置信度贡献**：模块用于判断"雷击"还是"非雷击"。当前数据 `isLightning=0.95 >= noLightning=0.05`，判定为雷击，支撑度 0.95，贡献 `0.95 × 0.30 = **0.285**`

8. **模块一 MCP 输出**：以 `CallToolResult.content` 数组形式返回，包含一段 Markdown 文本和三张独立的波形图（行波×2 + 工频×1）。每张波形图画布尺寸均为 600×280 px，与 Mock 前端 SVG 样式一致。Markdown 文本模板如下（数值根据接口返回值动态填充）：

```markdown
## 模块一：故障波形分析

基于波形图分析得出，半峰值时间是 {eigenvalue.halfPeakTime}，行波幅值是 {eigenvalue.amplitude}。判定分析：半峰值时间 {half_peak_condition}，符合{lightning_conclusion}判定条件；电压等级为 {trip.pressure}kV 且幅值 {amplitude_condition}，符合{stroke_type_conclusion}判定条件。

### 概率分布

| 故障类型 | 总概率 | 雷击类型 | 雷击类型概率 |
| -------- | ------ | -------- | ------------ |
| 雷击     | {data.isLightning} | 绕击     | {data.roundPass} |
| 雷击     | {data.isLightning} | 反击     | {data.backPass} |
| 非雷击   | {data.noLightning} |          |             |

### 故障波形分析结论

基于故障波形分析，输电线路故障类型为{模块一细分结论}。

### 置信度贡献

权重 0.30 × 支撑度 {data.isLightning} = {data.isLightning × 0.30}
```

当前数据填充后示例（`trip.pressure=±800`，`half_peak_condition=≤ 40`，`amplitude_condition=≤ 50`，`lightning_conclusion=雷击`，`stroke_type_conclusion=绕击`）：

```json
{
  "content": [
    {
      "type": "text",
      "text": "## 模块一：故障波形分析\n\n基于波形图分析得出，半峰值时间是 0.000564，行波幅值是 -2262.5898。判定分析：半峰值时间 ≤ 40，符合雷击判定条件；电压等级为 ±800kV 且幅值 ≤ 50，符合绕击判定条件。\n\n### 概率分布\n\n| 故障类型 | 总概率 | 雷击类型 | 雷击类型概率 |\n| -------- | ------ | -------- | ------------ |\n| 雷击     | 0.95   | 绕击     | 0.86         |\n| 雷击     | 0.95   | 反击     | 0.10         |\n| 非雷击   | 0.05   |          |              |\n\n### 故障波形分析结论\n\n基于故障波形分析，输电线路故障类型为雷击-绕击。\n\n### 置信度贡献\n\n权重 0.30 × 支撑度 0.95 = 0.285\n"
    },
    {
      "type": "image",
      "data": "<base64-encoded PNG 行波图1>",
      "mimeType": "image/png"
    },
    {
      "type": "image",
      "data": "<base64-encoded PNG 行波图2>",
      "mimeType": "image/png"
    },
    {
      "type": "image",
      "data": "<base64-encoded PNG 工频图>",
      "mimeType": "image/png"
    }
  ]
}
```

**为什么 getTripRipple 和 getTripDiagnosis 合并为一个模块？**

getTripRipple 是原始波形数据，getTripDiagnosis 是基于原始波形提取特征（eigenvalue）并应用规则模型后输出的概率结论。两者是"原始数据 → 分析结论"的因果关系，不应拆分为两个独立证据（否则会重复计算 eigenvalue 与 data 之间的信息）。本模块的核心价值是呈现"波形 → 特征 → 规则 → 结论"的完整分析链路，使用户理解系统是如何从波形图得出雷击-绕击判断的。

**为什么 30% 权重只取决于 isLightning 而不是 roundPass？**

模块一 的 30% 权重回答的是"雷击还是非雷击"这个大类问题，isLightning: 0.95 直接对应这个判断。roundPass/backPass 是在"已判定为雷击"的前提下进一步细分绕击/反击，属于下一层结论，不应重复计入整体置信度。

### 模块二：分布式监测判定

**输入接口**：getTripInfo.trip

**分析流程**：

1. **故障类型判断**：读取 `tripCause` 和 `tripClass`：
   - 若任一值为"雷击"，则模块二支撑度为 1.0，继续分析
   - 若均为非雷击（如金属性接地、高阻性接地等），该模块支撑度为 0

2. **故障基本信息输出**：

| 字段 | 示例值 | 输出项 |
|------|--------|--------|
| `timedate` | 2025-05-08 19:46:30 | 故障时间 |
| `pressure` | ±800 | 电压等级 |
| `linename` | 雅湖线 | 线路名称 |
| `tripStation1` / `tripDiaelepo1` | 特高压雅砻江站 / 3365号杆塔 | 起始站点及杆塔 |
| `tripStation2` / `tripDiaelepo2` | 特高压鄱阳湖站 / 3638号杆塔 | 终止站点及杆塔 |
| `towerId` | 3522 | 故障杆塔号 |
| `tripDescription` | （长文本） | 故障详细描述 |
| `tripPhase` | 极Ⅱ | 故障相别 |

3. **Markdown 输出模板**（数值根据接口返回值动态填充）：

```markdown
## 模块二：分布式监测判定

### 1、故障基本信息
- 故障时间：{trip.timedate}
- 线路名称：{trip.linename}
- 电压等级：{trip.pressure} kV
- 故障相别：{trip.tripPhase}
- 故障杆塔位置：{trip.tripStation1} 的 {trip.tripDiaelepo1} 到 {trip.tripStation2} 的 {trip.tripDiaelepo2} 之间的 {trip.towerId}号杆塔
- 故障描述：{trip.tripDescription}

### 2、分布式监测结论
基于分布式监测系统，输电线路故障类型为{tripCause/tripClass 结论}，故障相别为{trip.tripPhase}。

### 置信度贡献
权重 0.15 × 支撑度 {support_score} = {contribution}
```

当前数据填充后示例：

```markdown
## 模块二：分布式监测判定

### 1、故障基本信息
- 故障时间：2025-05-08 19:46:30
- 线路名称：雅湖线
- 电压等级：±800 kV
- 故障相别：极Ⅱ
- 故障杆塔位置：特高压雅砻江站 的 3365号杆塔 到 特高压鄱阳湖站 的 3638号杆塔 之间的 3522号杆塔
- 故障描述：2025-05-08 19:46:30 056毫秒±800kV雅湖线线路发生雷击故障，重合闸未知，故障相别为极Ⅱ，故障点位于3365号杆塔和3638号杆塔之间，(湖南省)，距离3365号杆塔大号方向81.011km，故障点位于3522号杆塔附近，所属局是国网湖南省电力有限公司输电检修分公司。

### 2、分布式监测结论
基于分布式监测系统，输电线路故障类型为雷击，故障相别为极Ⅱ。

### 置信度贡献
权重 0.15 × 支撑度 1.0 = 0.15
```

4. **支撑度计算**：

```python
support_score = 1.0 if trip.tripCause == "雷击" or trip.tripClass == "雷击" else 0.0
contribution = support_score * 0.15
```

**为什么 tripCause 和 tripClass 可视为一个证据？**

`tripCause` 和 `tripClass` 在当前数据中完全一致（均为"雷击"），两者本质上都是分布式监测系统对故障类型的输出，不应拆分为两个独立证据。模块二的整体支撑度由两者是否至少有一个为"雷击"决定。

### 模块三：雷电定位系统分析

**输入接口**：getTripInfo.flash[]

**模块三 由两个子项组成**：

| 子项 | 权重 | 说明 |
|------|------|------|
| 3.1 雷电活动规模 | 0.15 | 统计故障时刻前后雷电记录总条数，判断该区域雷电活动强度 |
| 3.2 雷电与故障杆塔地理关联 | 0.30 | 自算落雷点与故障杆塔的 haversine 距离，按 500m/5000m 阈值判定关联强度 |

**3.1 雷电活动规模**

分析流程：

1. 读取 getTripInfo.flash[] 所有雷电记录
2. 以表格形式展示所有记录：

| 序号 | 时间 | 电流（kA） | 回击 | 最近杆塔 | 距离（m） | 站数 | 参与定位的探测站 |
|------|------|-----------|------|---------|----------|------|----------------|
| 1 | 2025-05-08 19:46:28.371 | -18.7 | 主放电(含2次后续回击) | 3490 | 4265 | 12 | 怀宁数字站,黄梅（新）,黄石,... |
| 2 | 2025-05-08 19:46:28.459 | -18.4 | 后续第1次回击 | 3491 | 4244 | 7 | 宜春上高,赣西/新余(新),... |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 8 | 2025-05-08 19:46:39.561 | -7.6 | 主放电(含7次后续回击) | 3315 | 2156 | 4 | 赣西/新余(新),吉安县(新),南昌(新),抚州乐安 |

3. **Markdown 输出模板**（数值根据接口返回值动态填充，大括号内为占位符，括号后注明来源）：

```markdown
## 模块三：雷电定位系统分析

### 3.1 雷电活动规模

雷电定位系统探测到，故障时刻前后一共有 {flash_count} 条雷电记录（来自 `len(data.flash)`），表明该区域当时有 {activity_intensity} 的雷电活动（来自总条数判定规则）。

| 序号 | 时间 | 电流（kA） | 回击 | 最近杆塔 | 距离（m） | 站数 | 参与定位的探测站 |
|------|------|-----------|------|---------|----------|------|----------------|
| {flash[i].sequence} | {flash[i].timedate} | {flash[i].peakCurrent} | {flash[i].strMltiplicity} | {flash[i].tower} | {flash[i].distance} | {flash[i].tdfsum} | {flash[i].tdfString} |
| ... | ... | ... | ... | ... | ... | ... | ... |

### 3.2 雷电与故障杆塔地理关联

雷电定位系统探测到，{trip.towerId}号 故障杆塔附近 5000m 内一共有 {nearby_5000m_count} 条雷电记录（来自对 `data.flash` 按 haversine 距离 ≤ 5000m 筛选后的计数）。

其中，雷电时间为 {nearest_record.timedate}，距离 {trip.towerId}号 故障杆塔 {nearest_record.calculated_distance}m，雷电流幅值为 {nearest_record.peakCurrent} kA。

{trip.towerId}号 故障杆塔附近当时有 {association_intensity} 的雷电活动（来自 500m/5000m 阈值判定规则）。

| 时间 | 电流（kA） | 回击 | 故障杆塔 | 距离（m） | 站数 | 参与定位的探测站 |
|------|-----------|------|---------|----------|------|----------------|
| {nearby_records[i].timedate} | {nearby_records[i].peakCurrent} | {nearby_records[i].strMltiplicity} | {trip.towerId}号 | {nearby_records[i].calculated_distance} | {nearby_records[i].tdfsum} | {nearby_records[i].tdfString} |
| ... | ... | ... | ... | ... | ... | ... |

### 置信度贡献

- 3.1 雷电活动规模：权重 0.15 × 支撑度 {score_31}（来自总条数判定规则） = {contribution_31}
- 3.2 雷电与故障杆塔地理关联：权重 0.30 × 支撑度 {score_32}（来自 500m/5000m 阈值判定规则） = {contribution_32}
- 模块三合计贡献：{contribution_31 + contribution_32}
```

当前数据填充后示例：

```markdown
## 模块三：雷电定位系统分析

### 3.1 雷电活动规模

雷电定位系统探测到，故障时刻前后一共有 8 条雷电记录，表明该区域当时有高强度的雷电活动。

| 序号 | 时间 | 电流（kA） | 回击 | 最近杆塔 | 距离（m） | 站数 | 参与定位的探测站 |
|------|------|-----------|------|---------|----------|------|----------------|
| 1 | 2025-05-08 19:46:28.371 | -18.7 | 主放电(含2次后续回击) | 3490 | 4265 | 12 | 怀宁数字站,黄梅（新）,黄石,... |
| 2 | 2025-05-08 19:46:28.459 | -18.4 | 后续第1次回击 | 3491 | 4244 | 7 | 宜春上高,赣西/新余(新),... |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 8 | 2025-05-08 19:46:39.561 | -7.6 | 主放电(含7次后续回击) | 3315 | 2156 | 4 | 赣西/新余(新),吉安县(新),南昌(新),抚州乐安 |

### 3.2 雷电与故障杆塔地理关联

雷电定位系统探测到，3522号 故障杆塔附近 5000m 内一共有 2 条雷电记录。

其中，雷电时间为 2025-05-08 19:46:30.056，距离 3522号 故障杆塔 214m，雷电流幅值为 19.6 kA。

3522号 故障杆塔附近当时有高强度的雷电活动。

| 时间 | 电流（kA） | 回击 | 故障杆塔 | 距离（m） | 站数 | 参与定位的探测站 |
|------|-----------|------|---------|----------|------|----------------|
| 2025-05-08 19:46:30.056 | 19.6 | 单次回击 | 3522号 | 214 | 11 | 怀宁数字站,黄梅（新）,黄石,... |
| 2025-05-08 19:46:29.951 | -11.1 | 单次回击 | 3522号 | 4532 | 4 | 赣西/新余(新),广昌(新),南昌(新),抚州乐安 |

### 置信度贡献

- 3.1 雷电活动规模：权重 0.15 × 支撑度 1.0 = 0.15
- 3.2 雷电与故障杆塔地理关联：权重 0.30 × 支撑度 1.0 = 0.30
- 模块三合计贡献：0.45
```

| 距离范围 | 关联强度 | 支撑度 | 置信度贡献 |
|---------|---------|--------|-----------|
| 500m 内 ≥1 条 | 强关联 | 1.0 | 30% |
| 500m 内 0 条，且 5000m 内 ≥1 条 | 较强关联 | 0.8 | 24% |
| 5000m 内 0 条 | 无关联 | 0.0 | 0% |

**模块三 总置信度贡献**：

```
3.1 贡献：0.15 × 支撑度_31
3.2 贡献：0.30 × 支撑度_32
模块三 合计 = 0.15 × 支撑度_31 + 0.30 × 支撑度_32
```

以当前数据为例：
- 3.1 支撑度 = 1.0（8 条 > 3 条）→ 贡献 0.15
- 3.2 支撑度 = 1.0（500m 内有 1 条）→ 贡献 0.30
- **模块三 合计贡献 = 0.45**

**数据来源**：本地 FastAPI Mock 服务（`http://localhost:8000`）

| 接口 | 端点 | 是否参与诊断推理 | 是否展示 |
|------|------|----------------|---------|
| login | `/tgyApiservice/userservice/login` | 认证前置 | 否 |
| getTripInfoData | `/tgyApiservice/devicedataservice/getTripInfoData` | 是（查询 tripId） | 否 |
| getTripDiagnosis | `/tgyApiservice/tripdiagnosisservice/getTripDiagnosis` | 是（模块一 故障波形分析） | 输出模块一 明细 |
| getTripInfo | `/tgyApiservice/lineflashtripservice/getTripInfo` | 是（模块二 + 模块三） | 输出故障概况 + 雷电记录 |
| getTripRipple | `/tgyApiservice/lineflashtripservice/getTripRipple` | 是（模块一 绘制波形图） | 每次诊断生成波形图 |
| getWeather | `/tgyApiservice/tripdiagnosisservice/getWeather` | 是（模块四 气象条件） | 输出气象数据 |
| tripDiagnosis | `/tgyApiservice/tripdiagnosisservice/tripDiagnosis` | **不使用** | 否 |

### 4. 核心设计思想

**4.1 置信度透明**

诊断报告不是黑箱输出，而是逐项展示：
- 每个证据维度给了多少置信度
- 该维度的原始数据是什么
- 原始数据对结论的支撑逻辑是什么

**4.2 独立计算优先**

任何可以独立计算的数据（如地理距离），不依赖外部系统的现成字段。这样即使某个接口数据丢失或未同步，诊断流程仍可继续，仅该证据维度的置信度降为 0。

### 4.3 数据缺失降级规则

当任一接口返回 `code != 1001`，或该模块的**关键参数为空/缺失**时，该模块的置信度贡献计为 0，报告中对应位置显示"XX接口数据同步异常"，其他模块继续诊断。各模块关键参数定义如下：

| 模块 | 关键参数 | 说明 |
|------|---------|------|
| 模块一（故障波形分析） | `data.isLightning`、`data.noLightning`、`eigenvalue.amplitude`、`eigenvalue.halfPeakTime` | 缺少任一则无法计算雷击概率和提取特征值 |
| 模块二（分布式监测判定） | `trip.tripCause`、`trip.tripClass` | 缺少或均为空则无法判定分布式监测结论 |
| 模块三 3.1（雷电活动规模） | `data.flash[]` | 雷电记录列表缺失则无法统计雷电活动规模 |
| 模块三 3.2（雷电与故障杆塔地理关联） | `trip.longitude`、`trip.latitude`、`flash[].longitude`、`flash[].latitude` | 缺少任一则无法计算 haversine 距离 |
| 模块四（气象条件） | `data.real.hum` | 湿度缺失则无法判定雷暴条件 |

---

## 第二部分：技术实现指南 (Agent-Facing Technical Layer)

### 数据获取原则

**所有数据必须通过本地 Mock 测试平台的 HTTP 接口获取，禁止直接读取 txt 文件、api_schema.json 或其他本地文件。**

包括：
- 认证：调用 `POST /tgyApiservice/userservice/login`
- tripId 查询：调用 `POST /tgyApiservice/devicedataservice/getTripInfoData`
- 诊断数据：调用 `getTripDiagnosis`、`getTripInfo`、`getTripRipple`、`getWeather`

MCP Tool 运行时仅允许与 `http://localhost:8000`（或 config.py 中配置的 base URL）进行 HTTP 交互。

### 1. 系统架构总览

```
用户输入 query_date + line_name
    |
[login] → 获取 access_token
    |
[getTripInfoData] → 按日期范围 + 线路名查询 → 匹配第一条记录 → 获取 tripId
    |
并行拉取：
├── [getTripDiagnosis] → eigenvalue + process + data（模块一）
├── [getTripInfo] → trip + flash + image（模块二 + 模块三）
├── [getTripRipple] → 三组波形数据（模块一 绘制波形图）
└── [getWeather] → 实时气象数据（模块四）
    |
诊断引擎：
├── 模块一：getTripRipple 波形图 + getTripDiagnosis → 雷击概率 0.95 → 置信度 0.30
├── 模块二：解析 trip.tripCause → 雷击判定 → 置信度 0.15
├── 模块三：雷电定位系统分析
│   ├── 3.1 统计 flash[] 总条数 → 判定雷电活动规模 → 置信度 0.15
│   └── 3.2 haversine 计算落雷点-杆塔距离 → 按 500m/5000m 阈值判定 → 置信度 0.30
└── 模块四：解析 weather.hum → 按 40%/70% 阈值判定 → 置信度 0.10
    |
加权合成 → 综合置信度 → 诊断结论
    |
输出结构化诊断报告
```

### 2. MCP Server 项目结构

```
/Users/yfzx/Desktop/特高压/MCP src/
├── requirements.txt              # 依赖：mcp[cli], httpx, matplotlib
├── server.py                     # MCP 服务器入口（FastMCP）
├── config.py                     # 配置：API Mock base URL, login credentials
├── client.py                     # HTTP 客户端：封装 login + getTripInfoData + 业务接口调用
├── diagnosis_engine.py           # 诊断引擎：置信度计算核心
├── wave_plotter.py               # 波形图生成器（matplotlib）
└── models.py                     # Pydantic 模型：诊断报告结构
```

### 3. MCP Tool 定义

**Tool 名称**: `diagnose_lightning_tool`

**参数**: 
- `query_date: str` — 查询日期，支持格式 `"2025-05-08"` 或 `"2025年5月8日"`
- `line_name: str` — 线路名称，如 `"雅湖线"`，需与 `getTripInfoData` 返回的 `tripLineName` 精确匹配

**返回值**: `CallToolResult`，`content` 数组包含：
- `content[0]`：`text` 类型，Markdown 格式的完整诊断报告（含模块一-4 的所有输出内容）
- `content[1]`-`content[3]`：`image` 类型，三张独立的故障波形图 PNG（base64 编码），分别为行波图 1、行波图 2、工频图

> 注：每张波形图画布尺寸均为 600×280 px，与 Mock 前端 SVG 样式一致。

**调用流程**:
1. 调用 `login` 获取 `access_token`
2. 调用 `getTripInfoData`，参数：
   - `timeOrderBy=1`
   - `startTime={query_date} 00:00:00`
   - `endTime={query_date} 23:59:59`
   - `pressureType=1`
   - `page=0`
   - `pageSize=999`
   - `access_token={token}`
3. 遍历 `data.data`，精确匹配 `tripLineName == line_name`
4. 取第一条匹配记录，获取 `tripId`
5. 若未匹配到记录，返回错误："未找到 {query_date} {line_name} 的跳闸记录"
6. 并行调用 `getTripDiagnosis`、`getTripInfo`、`getTripRipple`、`getWeather` 进行诊断

```python
# 返回结构示意（非 TypedDict 模型）
{
    "content": [
        {
            "type": "text",
            "text": "## 雷电故障诊断报告\n\n### 模块一：故障波形分析\n...\n### 模块二：分布式监测判定\n...\n### 模块三：雷电定位系统分析\n...\n### 模块四：气象条件\n...\n### 综合诊断结论\n..."
        },
        {
            "type": "image",
            "data": "<base64-encoded PNG>",
            "mimeType": "image/png"
        }
    ],
    "isError": false
}
```

模块一 的 Markdown 文本输出模板及示例参见上文。

### 4. 接口调用流程

**4.1 认证**

```python
async def login() -> str:
    """调用 /tgyApiservice/userservice/login，返回 access_token"""
    # account=yfzx, password=123456, access_token=""
    # 返回 data.access_token
```

**4.2 并行拉取**

```python
async def fetch_all(token: str, trip_id: str) -> tuple:
    # 使用 asyncio.gather 并行调用：
    # getTripDiagnosis(trip_id, token)
    # getTripInfo(trip_id, token)
    # getWeather(trip_id, token)

async def query_trip_id(token: str, query_date: str, line_name: str) -> str:
    """调用 getTripInfoData 查询指定日期和线路名的 tripId"""
    # startTime=f"{query_date} 00:00:00"
    # endTime=f"{query_date} 23:59:59"
    # timeOrderBy=1, pressureType=1, page=0, pageSize=999
    # 精确匹配 tripLineName == line_name，返回第一条匹配记录的 tripId
    # 未匹配到时抛出异常
```

**4.3 距离计算**

```python
def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """计算两点间地球表面距离（米）"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def filter_nearby_lightning(flash_list: list, tower_lon: float, tower_lat: float, max_distance: float = 5000) -> list:
    """筛选距离故障杆塔 max_distance 米以内的雷电记录"""
    result = []
    for record in flash_list:
        dist = haversine(record['longitude'], record['latitude'], tower_lon, tower_lat)
        record['_calculated_distance'] = dist  # 附加自算距离字段
        if dist <= max_distance:
            result.append(record)
    return result
```

### 5. 置信度计算逻辑

**5.1 各模块支撑度计算**

| 模块 | 支撑度计算 | 支撑度公式 |
|------|-----------|-----------|
| 模块一 故障波形分析 | 雷击判定：`isLightning >= noLightning` 则支撑度为 `isLightning`，否则为 `0` | 雷击时：`isLightning × 0.30`；非雷击时：`0` |
| 模块二 分布式判定 | tripCause == "雷击" | 是→1.0，否→0.0 |
| 模块三 雷电定位系统分析 | 见下表 3.1 + 3.2 | — |
| 模块四：气象条件 | 见下表湿度阈值 | — |

**模块三 子项支撑度**：

| 子项 | 规则 | 支撑度 |
|------|------|--------|
| 3.1 雷电活动规模 | 总条数 0 条 | 0.0 |
| | 总条数 1-3 条 | 0.8 |
| | 总条数 > 3 条 | 1.0 |
| 3.2 雷电与故障杆塔地理关联 | 500m 内 ≥1 条 | 1.0 |
| | 500m 内 0 条，且 5000m 内 ≥1 条 | 0.8 |
| | 5000m 内 0 条 | 0.0 |

**模块四 气象条件支撑度**：

| 湿度范围 | 结论 | 支撑度 |
|---------|------|--------|
| hum < 40% | 空气干燥，不符合雷暴形成条件 | 0.0 |
| 40% < hum ≤ 70% | 空气较为潮湿，符合雷暴形成条件 | 0.8 |
| hum > 70% | 空气极为潮湿，有利于雷暴形成条件 | 1.0 |

**模块三 总贡献**：

```python
module3_contribution = 0.15 * score_31 + 0.30 * score_32
```

### 模块四：气象条件

**输入接口**：getWeather.real

**分析流程**：

1. 读取故障时刻气象数据，展示关键参数：

| 参数 | 示例值 |
|------|--------|
| 温度 | 26.13 °C |
| 风速 | 3.41 m/s |
| 湿度 | 80.16% |

2. **仅使用湿度参数**进行雷暴条件判定：

| 湿度范围 | 支撑度 | 结论 | 整体置信度贡献 |
|---------|--------|------|--------------|
| hum < 40% | 0.0 | 该区域故障时刻湿度为 **X%**，空气干燥，不符合雷暴形成条件 | 0 |
| 40% < hum ≤ 70% | 0.8 | 该区域故障时刻湿度为 **X%**，空气较为潮湿，符合雷暴形成条件 | 0.08 |
| hum > 70% | 1.0 | 该区域故障时刻湿度为 **X%**，空气极为潮湿，有利于雷暴形成条件 | 0.10 |

3. 输出示例（当前数据 humidity = 80.16%）：

> **故障时刻气象信息**
> - 温度：26.13 °C
> - 风速：3.41 m/s
> - 湿度：80.16%
> 
> **气象条件分析**
> 该区域故障时刻湿度为 **80.16%**，空气极为潮湿，有利于雷暴形成条件。
> 
> **置信度贡献**
> 该模块权重为 0.10，湿度 > 70%，支撑度为 1.0，因此模块四 对整体诊断结论的置信度贡献为：1.0 × 0.10 = **0.10**

**为什么只使用湿度？**

getWeather 接口返回的温度、风速、风向、气压、能见度等参数对雷击故障没有直接可解释的判定规则。其中只有湿度与雷暴形成有明确的正相关关系：空气越潮湿，越有利于雷暴云的发展，从而提升雷击概率。因此模块四 仅使用湿度作为判定依据。

**5.2 综合诊断结论**

综合诊断结论采用模块一的细分结论（雷击-绕击 / 雷击-反击 / 雷击 / 非雷击），并总结各模块支撑情况：

```markdown
### 综合诊断结论

基于 5 个证据条目的交叉验证，最终诊断结论为：**{模块一细分结论}**。

- 模块一（故障波形分析）：{结论}，置信度贡献 {contribution_1}
- 模块二（分布式监测判定）：{结论}，置信度贡献 {contribution_2}
- 模块三 3.1（雷电活动规模）：{结论}，置信度贡献 {contribution_31}
- 模块三 3.2（雷电与故障杆塔地理关联）：{结论}，置信度贡献 {contribution_32}
- 模块四（气象条件）：{结论}，置信度贡献 {contribution_4}

综合置信度为 {total_confidence}，{结论说明}。
```

**5.3 综合置信度计算**

```python
def calculate_confidence(evidence_scores: list[float], weights: list[float]) -> float:
    """加权求和"""
    return sum(s * w for s, w in zip(evidence_scores, weights))
```

### 6. 波形图绘制规范

**6.1 数据**

调用 getTripRipple 返回 `data` 下 3 个 key，每个 key 对应一个 dict，含 `waveType`（"行波"或"工频"）和 `items[]`（x,y 坐标列表）。实际数据示例如下：

| # | data key | waveType | 数据点数 | items x 范围 | 映射后 X 轴范围 | Y 轴范围 | X 轴单位 |
|---|----------|----------|---------|-------------|----------------|---------|---------|
| 1 | 长字符串 ID | 行波 | 6500 | 0 - 6499 | 0 - 7000 | -2000~1000 | 微秒 |
| 2 | 长字符串 ID | 行波 | 6500 | 0 - 6499 | 0 - 7000 | -3000~2000 | 微秒 |
| 3 | 长字符串 ID | 工频 | 4800 | 0 - 1199.75 | 0 - 1200 | -2000~5000 | 毫秒 |

**6.2 绘图参数**

与 Mock 测试平台前端（`app.py` custom Swagger UI）中 getTripRipple 波形图样式完全一致：
- 布局: 三个波形图分别作为三张独立的 PNG 返回，每张图为一个单独的子图
- 画布: 每张图均为 600 x 280 px
- 采样: 按像素宽度降采样（避免 6500 点过密）
- 波形线: `#2196F3` 蓝色，1.5px
- 网格: 灰色 `#e0e0e0`
- 坐标轴: `#333`，线宽 2px
- X轴标签: 工频"时间（毫秒）"，行波"时间（微秒）"
- Y轴标签: "电流（安培）"
- 子图标题: "故障波形：{waveType}波形"
- 刻度字体大小: 10px
- 标签字体大小: 12px

**6.3 生成 PNG**

```python
async def plot_waveforms(trip_id: str, token: str) -> list[bytes]:
    # 调用 getTripRipple 获取数据
    # matplotlib 生成三张独立的 PNG（每张 600x280 px），样式与 Mock 前端 /docs 中 getTripRipple 波形图完全一致
    # 返回 list[bytes]，顺序为 [行波图1, 行波图2, 工频图]
```

> **字体依赖说明**：波形图标题、坐标轴标签包含中文。macOS 默认使用 `/System/Library/Fonts/STHeiti Medium.ttc`；Linux 需安装 `wqy-zenhei`（路径 `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`）。若找不到中文字体，中文标签将显示为方框。

### 7. 错误处理

| 场景 | 处理 |
|------|------|
| Mock 服务未启动 | 返回错误："API Mock 服务未运行，请先执行 `python setup.py`" |
| 登录失败 | 返回错误："认证失败，请检查 Mock 服务配置" |
| 任意接口返回非 1001 或关键参数为空 | 该模块置信度贡献为 0，报告中显示"XX接口数据同步异常"，其他模块继续诊断 |
| getTripRipple 超大响应 | 流式读取，按需采样，避免内存溢出 |
| haversine 计算异常 | 跳过该条记录，继续处理其他记录 |

### 8. 部署方式

- **Transport**: stdio（本地接入 Claude Desktop / Claude Code）
- **安装**: `uv run mcp install server.py`
- **开发测试**: `uv run mcp dev server.py`
- **端到端测试**: 在 MCP Inspector 中调用 `diagnose_lightning_tool(query_date="2025-05-08", line_name="雅湖线")`

### 9. 验证协议

| 验证项 | 方法 |
|--------|------|
| 登录正常 | 调用 login 返回有效 token |
| 诊断结论正确 | `query_date="2025-05-08", line_name="雅湖线"` → 结论为"雷击-绕击"，综合置信度 > 0.6 |
| 置信度透明 | 报告中 evidence 列表包含 5 个条目，权重之和为 1.00 |
| 自算距离准确 | flash[5] → 故障杆塔距离 ≈ 4532m，与 tripDiagnosis 报告 4537m 差异 < 10m |
| 波形图一致 | diagnose_lightning_tool 输出的波形图与 Mock 前端 /docs 中 getTripRipple 波形图样式完全一致（布局、颜色、坐标轴范围、标题、标签） |
| 独立运行 | 断开 tripDiagnosis 数据源后，诊断仍可完成，仅该模块证据缺失 |

---

## 第三部分：附录

### A. 各证据维度与原始接口的字段映射

| 模块 | 原始接口 | 原始字段 | 说明 |
|------|---------|---------|------|
| 模块一 故障波形分析 | getTripRipple + getTripDiagnosis | `eigenvalue.amplitude`, `eigenvalue.halfPeakTime`, `data.isLightning/roundPass/backPass`, `process` | getTripRipple 提供原始波形用于绘图，getTripDiagnosis 提供特征值、判定规则、概率结论 |
| 模块二 分布式判定 | getTripInfo | `trip.tripCause`, `trip.tripClass` | 字符串匹配 |
| 模块三 雷电定位系统分析 | getTripInfo | `flash[].longitude`, `flash[].latitude`, `trip.longitude`, `trip.latitude` | 自算 haversine 距离（含 3.1 雷电活动规模 + 3.2 地理关联） |
| 模块四 气象条件 | getWeather | `real.hum` | 直接读取 |

### B. 为什么抛弃 tripDiagnosis

| 接口字段 | 是否可被替代 | 替代方式 |
|---------|-------------|---------|
| `result: "雷击-绕击。"` | 是 | 与 getTripDiagnosis.data 结论重复 |
| `report1` / `flashNum` | 是 | 与 getTripDiagnosis.process 推理逻辑重复 |
| `L1.linFlash[].km` | 是 | 可由 haversine 自算，已验证误差 < 10m |
| `L1.linFlash[]` 其他字段 | 是 | 与 getTripInfo.flash[] 是同一条雷电记录，字段一一对应 |

**结论：tripDiagnosis 接口的所有信息都已被其他接口覆盖，且不存在独立的新信息。**
