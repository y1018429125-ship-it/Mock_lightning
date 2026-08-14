from main_app import app
from fastapi import Form
import token_manager

import json

_RECORD = {
    "request": json.loads(r'''{"tripId": "S_Y202505080552", "access_token": "0488A454FAC7E498A6107A27334F0367108861FE93CD9AD6D94435FDADD1C260E641CFBB59128A345D21106CAAE25BC1EF245C75F0ED1AAA8013C472839BAD68722C5B6ABE5FE33029FD0005F85531B0092CC867FBB3C7ABD524CBDA796DB734B1C58D0AFC642D7A7F49BCD24B798C59CAEF98"}'''),
    "response": json.loads(r'''{"msg": "可视化数据暂无,", "process": "雅湖线是分布式故障雷电定位小于5isLightning += 0.1;半峰值时间小于等于40isLightning += 0.15;电压等级大于220或小于等于500并且幅值小于等于50绕反击roundPass += 0.9;backPass += 0.1;组合因子总数1.0绕击四舍五入取整保留2位小数0.86组合因子总数1.0反击四舍五入取整保留2位小数0.1组合因子总数1.0金属性四舍五入取整保留2位小数0.03组合因子总数1.0高阻性四舍五入取整保留2位小数0.03", "code": 1001, "data": {"isLightning": 0.95, "roundPass": 0.86, "backPass": 0.1, "noLightning": 0.05, "king": 0.03, "high": 0.03, "bh": 0.0, "sxwp": 0.0, "btdxdc": 0.0, "fp": 0.0, "ywwp": 0.0, "sgwp": 0.0, "nh": 0.0, "shwp": 0.0, "ws": 0.0}, "eigenvalue": {"amplitude": -2262.5898, "halfPeakTime": 0.000564}}'''),
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

@app.post("/tgyApiservice/tripdiagnosisservice/getTripDiagnosis", summary="getTripDiagnosis")
async def getTripDiagnosis(
    tripId: str = Form(default='S_Y202505080552'),
    access_token: str = Form(default='0488A454FAC7E498A6107A27334F0367108861FE93CD9AD6D94435FDADD1C260E641CFBB59128A345D21106CAAE25BC1EF245C75F0ED1AAA8013C472839BAD68722C5B6ABE5FE33029FD0005F85531B0092CC867FBB3C7ABD524CBDA796DB734B1C58D0AFC642D7A7F49BCD24B798C59CAEF98'),
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