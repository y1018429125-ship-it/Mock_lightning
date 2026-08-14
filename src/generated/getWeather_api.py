from main_app import app
from fastapi import Form
import token_manager

import json

_RECORD = {
    "request": json.loads(r'''{"tripId": "S_Y202505080552", "access_token": "04052C403DECF923A569BEB814A860EC8F1B7B15D41B470C1C3B89B78E90EBB6A895E5716E926F1100B0AD482326201BAE50EA7DFB32D727F5ABB59AB32D78476258F5B40E00EAD8DB4E1AF4AC3BF95AB82DAA678443F0EFFAAC175E09FCB86CF3822DE2EA99BC0AE5EF0FD6C7BB1B934501EB"}'''),
    "response": json.loads(r'''{"code": 1001, "data": {"predict": {"48h": [], "24h": [], "72h": []}, "real": {"id": 45, "tripId": "S_Y202505080552", "ws": 3.40831, "wd": 298.877, "tmp": 26.1303, "hum": 80.1612, "pre": 1.1108, "vis": 23763.0, "atm": -999.0}}}'''),
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

@app.post("/tgyApiservice/tripdiagnosisservice/getWeather", summary="getWeather")
async def getWeather(
    tripId: str = Form(default='S_Y202505080552'),
    access_token: str = Form(default='04052C403DECF923A569BEB814A860EC8F1B7B15D41B470C1C3B89B78E90EBB6A895E5716E926F1100B0AD482326201BAE50EA7DFB32D727F5ABB59AB32D78476258F5B40E00EAD8DB4E1AF4AC3BF95AB82DAA678443F0EFFAAC175E09FCB86CF3822DE2EA99BC0AE5EF0FD6C7BB1B934501EB'),
):
    body = {
        "tripId": tripId,
        "access_token": access_token,
    }
    token = body.get("access_token", "")
    if not token_manager.validate_token(token):
        return {"code": 1002, "message": "未登录或token已过期"}
    if not _match_request(body, _RECORD["request"]):
        return {"code": "400003", "message": "参数错误"}
    return _RECORD["response"]