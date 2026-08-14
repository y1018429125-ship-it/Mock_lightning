# Mock_lightning — 特高压线路故障诊断 API Mock 测试平台

模拟特高压线路故障诊断系统的后端接口（登录、故障查询、气象、电压等），用于本地开发测试，无需连接真实系统。

## 环境要求

- Python 3.10+
- 无需联网访问真实系统，所有数据为内置模拟数据

## 部署启动

```bash
# 1. 安装依赖
pip install -r src/requirements.txt

# 2. 启动前需要修改两处本机路径（见下方"必改项"）

# 3. 一键启动（解析接口定义 -> 生成代码 -> 启动服务）
python src/setup.py
```

启动成功后访问 Swagger 文档：http://127.0.0.1:8000/docs

## ⚠️ 必改项（两处硬编码路径）

仓库中有两处路径指向原作者电脑，克隆后必须先修改，否则无法启动：

1. **`src/txt_parser.py` 第 8 行**
   ```python
   # 原值
   TXT_DIR = Path("/Users/yfzx/Desktop/特高压/接口")
   # 改为你本地仓库下的"接口"目录，例如使用相对路径：
   TXT_DIR = Path(__file__).parent.parent / "接口"
   ```

2. **`src/app.py` 第 18 行**
   ```python
   # 原值（挂载图片目录，目录不存在会导致启动崩溃）
   app.mount("/images", StaticFiles(directory="/Users/yfzx/Desktop/特高压/可视化监拍图片"), name="images")
   ```
   二选一：
   - 在项目根目录新建空目录 `可视化监拍图片`，并把路径改为 `"可视化监拍图片"`
   - 或直接注释掉这一行（不影响接口测试，仅无法访问图片）

## 目录说明

| 目录/文件 | 说明 |
|---|---|
| `src/setup.py` | 一键启动脚本 |
| `src/api_schema.json` | 接口定义（由 txt 解析生成，已提交） |
| `src/generated/` | 自动生成的接口实现 |
| `接口/` | 接口 curl 定义原始文件 |
| `lightning-service/` | 雷电诊断 MCP 服务（独立运行：`pip install -r lightning-service/requirements.txt` 后 `python lightning-service/main.py`，端口 8001） |
| `MCP src/` | MCP 服务开发版本（uv 管理，见其中 README） |

## 测试账号

- 账号：`YFZX-1` 密码：`123456`（模拟账号，仅供测试）
