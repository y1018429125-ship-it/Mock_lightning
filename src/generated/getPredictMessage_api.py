from main_app import app
from fastapi import Form
import token_manager

import json

_RECORD = {
    "request": json.loads(r'''{"access_token": "046DE70F35C417A82BE1D1D102BE1CE5D097E751CF9D1A7F0699C1C090957E989BBD588DCD9859977C7A04140CF8E8F44F1EAFA495AAD369C6627C175B98B77C2C0B1A5065CF70486BC95F4E76ECCEA121DFE42DADA55FAFF1C9CF5F9948B1AA9F8D6B3C845495CE12B70F3EEF676FFA074923"}'''),
    "response": json.loads(r'''{"code": 1001, "data": [{"name": "30分钟雷电", "ct": 57}, {"name": "分布式故障", "ct": 0}, {"name": "可视化告警", "ct": 13}]}'''),
}

def _match_request(received: dict, expected: dict) -> bool:
    skip = {"access_token", "accsess_token"}
    for key, expected_val in expected.items():
        if key in skip:
            continue
        if key not in received:
            return False
        if received[key] != expected_val:
            return False
    return True

@app.post("/tgyApiservice/predictservice/getPredictMessage", summary="getPredictMessage")
async def getPredictMessage(
    access_token: str = Form(default='046DE70F35C417A82BE1D1D102BE1CE5D097E751CF9D1A7F0699C1C090957E989BBD588DCD9859977C7A04140CF8E8F44F1EAFA495AAD369C6627C175B98B77C2C0B1A5065CF70486BC95F4E76ECCEA121DFE42DADA55FAFF1C9CF5F9948B1AA9F8D6B3C845495CE12B70F3EEF676FFA074923'),
):
    body = {
        "access_token": access_token,
    }
    token = body.get("access_token", "")
    if not token_manager.validate_token(token):
        return {"code": 1002, "message": "未登录或token已过期"}
    if not _match_request(body, _RECORD["request"]):
        return {"code": "400003", "message": "参数错误"}
    return _RECORD["response"]