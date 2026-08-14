from main_app import app
from fastapi import Form
import token_manager

import json

_RECORD = {
    "request": json.loads(r'''{"access_token": "0488A454FAC7E498A6107A27334F0367108861FE93CD9AD6D94435FDADD1C260E641CFBB59128A345D21106CAAE25BC1EF245C75F0ED1AAA8013C472839BAD68722C5B6ABE5FE33029FD0005F85531B0092CC867FBB3C7ABD524CBDA796DB734B1C58D0AFC642D7A7F49BCD24B798C59CAEF98"}'''),
    "response": json.loads(r'''{"code": 1001, "data": [{"id": 17, "name": "天津", "patrolDay": 15, "patrolSection": 2}, {"id": 13, "name": "河北", "patrolDay": 15, "patrolSection": 2}, {"id": 16, "name": "冀北", "patrolDay": 15, "patrolSection": 2}, {"id": 15, "name": "山东", "patrolDay": 15, "patrolSection": 2}, {"id": 12, "name": "山西", "patrolDay": 15, "patrolSection": 2}, {"id": 22, "name": "上海", "patrolDay": 15, "patrolSection": 2}, {"id": 23, "name": "江苏", "patrolDay": 15, "patrolSection": 2}, {"id": 25, "name": "浙江", "patrolDay": 15, "patrolSection": 2}, {"id": 24, "name": "安徽", "patrolDay": 15, "patrolSection": 2}, {"id": 31, "name": "湖北", "patrolDay": 15, "patrolSection": 2}, {"id": 33, "name": "湖南", "patrolDay": 15, "patrolSection": 2}, {"id": 34, "name": "河南", "patrolDay": 15, "patrolSection": 2}, {"id": 32, "name": "江西", "patrolDay": 15, "patrolSection": 2}, {"id": 75, "name": "四川", "patrolDay": 15, "patrolSection": 2}, {"id": 71, "name": "重庆", "patrolDay": 15, "patrolSection": 2}, {"id": 66, "name": "蒙东", "patrolDay": 15, "patrolSection": 2}, {"id": 91, "name": "陕西", "patrolDay": 15, "patrolSection": 2}, {"id": 93, "name": "甘肃", "patrolDay": 15, "patrolSection": 2}, {"id": 92, "name": "宁夏", "patrolDay": 15, "patrolSection": 2}, {"id": 97, "name": "新疆", "patrolDay": 15, "patrolSection": 2}, {"id": 94, "name": "青海", "patrolDay": 15, "patrolSection": 2}, {"id": 41, "name": "福建", "patrolDay": 15, "patrolSection": 2}]}'''),
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

@app.post("/tgyApiservice/patrollineservice/getProvinceInfo", summary="getProvinceInfo")
async def getProvinceInfo(
    access_token: str = Form(default='0488A454FAC7E498A6107A27334F0367108861FE93CD9AD6D94435FDADD1C260E641CFBB59128A345D21106CAAE25BC1EF245C75F0ED1AAA8013C472839BAD68722C5B6ABE5FE33029FD0005F85531B0092CC867FBB3C7ABD524CBDA796DB734B1C58D0AFC642D7A7F49BCD24B798C59CAEF98'),
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