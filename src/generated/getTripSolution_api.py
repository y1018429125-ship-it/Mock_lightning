from main_app import app
from fastapi import Form
import token_manager

import json

_RECORD = {
    "request": json.loads(r'''{"tripType": "雷击故障", "access_token": "0488A454FAC7E498A6107A27334F0367108861FE93CD9AD6D94435FDADD1C260E641CFBB59128A345D21106CAAE25BC1EF245C75F0ED1AAA8013C472839BAD68722C5B6ABE5FE33029FD0005F85531B0092CC867FBB3C7ABD524CBDA796DB734B1C58D0AFC642D7A7F49BCD24B798C59CAEF98"}'''),
    "response": json.loads(r'''{"code": 1001, "data": "现场巡视：1、了解故障区段故障时气象条件；2、绝缘子是否有放电痕迹；3、线路地线放电间隙是否有烧伤痕迹；4、接地引下线连接板是否有烧伤痕迹；5、绝缘子是否有掉串、破损、自爆。\r\n运维建议：开展线路差异化雷害风险评估，针对雷害高风险及雷击跳闸杆塔开展防雷改造工作。"}'''),
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

@app.post("/tgyApiservice/tripdiagnosisservice/getTripSolution", summary="getTripSolution")
async def getTripSolution(
    tripType: str = Form(default='雷击故障'),
    access_token: str = Form(default='0488A454FAC7E498A6107A27334F0367108861FE93CD9AD6D94435FDADD1C260E641CFBB59128A345D21106CAAE25BC1EF245C75F0ED1AAA8013C472839BAD68722C5B6ABE5FE33029FD0005F85531B0092CC867FBB3C7ABD524CBDA796DB734B1C58D0AFC642D7A7F49BCD24B798C59CAEF98'),
):
    body = {
        "tripType": tripType,
        "access_token": access_token,
    }
    token = body.get("access_token", "")
    if not token_manager.validate_token(token):
        return {"code": 1002, "message": "未登录或token已过期"}
    if not _match_request(body, _RECORD["request"]):
        return {"code": "400003", "message": "参数错误"}
    return _RECORD["response"]