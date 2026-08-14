from fastapi import FastAPI

app = FastAPI(
    title="特高压线路故障诊断 API Mock 测试平台",
    docs_url=None,  # 禁用默认 /docs，由 app.py 自定义
)
