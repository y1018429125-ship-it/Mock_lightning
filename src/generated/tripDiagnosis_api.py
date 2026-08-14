from main_app import app
from fastapi import Form
import token_manager

import json

_RECORD = {
    "request": json.loads(r'''{"tripId": "S_Y202505080552", "access_token": "0488A454FAC7E498A6107A27334F0367108861FE93CD9AD6D94435FDADD1C260E641CFBB59128A345D21106CAAE25BC1EF245C75F0ED1AAA8013C472839BAD68722C5B6ABE5FE33029FD0005F85531B0092CC867FBB3C7ABD524CBDA796DB734B1C58D0AFC642D7A7F49BCD24B798C59CAEF98"}'''),
    "response": json.loads(r'''{"code": 1001, "data": {"typhoon": {}, "trip": {"tripId": "S_Y202505080552", "tripTime": "2025-05-08 19:46:30", "tripMillisecond": 56, "tripLineName": "雅湖线", "tripTowerNo": "3522", "chzFlag": 3, "flashFlag": 1, "recordTime": "2025-08-01 11:11:34", "tripCause": "雷击", "tripClass": "雷击", "tripInfo": null, "tripDescription": "2025-05-08 19:46:30 056毫秒±800kV雅湖线线路发生雷击故障，重合闸未知，故障相别为极Ⅱ，故障点位于3365号杆塔和3638号杆塔之间，(湖南省)，距离3365号杆塔大号方向81.011km，故障点位于3522号杆塔附近，所属局是国网湖南省电力有限公司输电检修分公司。", "tripPhase": "极Ⅱ", "tripStation1": "特高压雅砻江站", "tripDiaelepo1": "3365号杆塔", "tripStation2": "特高压鄱阳湖站", "tripDiaelepo2": "3638号杆塔", "id": 2042, "province": "江西", "viewStatus": 0, "tripPressure": "±800", "tripEleoffName": "国网湖南省电力有限公司输电检修分公司"}, "weather": {}, "result": "雷击-绕击。", "historyIce": {}, "report1": "  分布式监测系统诊断故障原因为雷击，雷电定位系统查得3522塔附近5000m范围，前后一分钟内有2次雷电，其中序号为2的雷电时间为2025-05-08 19:46:30.056，距离3522杆塔214m，与分布式监测系统诊断的情况一致，雷电流幅值为19.6kA，可判断故障原因为雷击-绕击。", "fire": {}, "ice": {}, "L1": {"ret": "雷击", "flashList": {"km": 214.0, "coode": "1001", "latitude": "27.835283", "strMltiplicity": "单次回击", "tdfString": "怀宁数字站,黄梅（新）,黄石,黄冈桐梓,上饶玉山,赣西/新余(新),九江湖口(新),上饶铅山,抚州乐安,宜春石市,茶陵", "type": "绕击", "peakCurrent": 19.6, "linFlash": {"linFlash": [{"sequence": "1", "km": 4537.0, "tdfsum": 4, "latitude": "27.809218", "strMltiplicity": "单次回击", "tdfString": "赣西/新余(新),广昌(新),南昌(新),抚州乐安", "timeDate": "2025-05-08 19:46:29.951", "peakCurrent": 11.1, "longitude": "116.000472"}, {"sequence": "2", "km": 214.0, "tdfsum": 11, "latitude": "27.835283", "strMltiplicity": "单次回击", "tdfString": "怀宁数字站,黄梅（新）,黄石,黄冈桐梓,上饶玉山,赣西/新余(新),九江湖口(新),上饶铅山,抚州乐安,宜春石市,茶陵", "timeDate": "2025-05-08 19:46:30.056", "peakCurrent": 19.6, "longitude": "116.038658"}]}, "sequence": "2", "flashNum": "  分布式监测系统诊断故障原因为雷击，雷电定位系统查得3522塔附近5000m范围，前后一分钟内有2次雷电，其中序号为2的雷电时间为2025-05-08 19:46:30.056，距离3522杆塔214m，与分布式监测系统诊断的情况一致，雷电流幅值为19.6kA，可判断故障原因为雷击-绕击。", "tdfsum": 11, "timeDate": "2025-05-08 19:46:30.056", "longitude": "116.038658"}}, "wave": {}}}'''),
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

@app.post("/tgyApiservice/tripdiagnosisservice/tripDiagnosis", summary="tripDiagnosis")
async def tripDiagnosis(
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