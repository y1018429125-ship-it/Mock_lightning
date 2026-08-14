from main_app import app
from fastapi import Form
import token_manager

import json

_RECORD = {
    "request": json.loads(r'''{"account": "YFZX-1", "password": 123456, "accsess_token": ""}'''),
    "response": json.loads(r'''{"code": 1001, "data": {"access_token": "0491F62EF83447D242FB257E0F68A70BF859E4D115AB46697D96CA7D942C0FC54F773E19D6DF1BD6D9A773CC809BC9B9C78899CBEDC437F815C97C6A1E035EA98E06402EF54E873521C96E0AA9399033103E230AAB095BD89FCFA6B97CFF0D422A64FFD185BD05C6E14692DDE8CF1F9AD606CD", "organizationId": -1, "province": "全国", "userName": "武汉南瑞", "expires_in": 3600}}'''),
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

@app.post("/tgyApiservice/userservice/login", summary="login")
async def login(
    account: str = Form(default='YFZX-1'),
    password: int = Form(default=123456),
    accsess_token: str = Form(default=''),
):
    body = {
        "account": account,
        "password": password,
        "accsess_token": accsess_token,
    }
    token = token_manager.login(account, password)
    if token is None:
        return {"code": "400003", "message": "参数错误"}
    resp = dict(_RECORD["response"])
    resp["data"] = dict(resp["data"])
    resp["data"]["access_token"] = token
    return resp