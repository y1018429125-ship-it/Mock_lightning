from main_app import app
from fastapi import Form
import token_manager

import json

_RECORD = {
    "request": json.loads(r'''{"tripId": "S_Y202505080552", "access_token": "04B438E8DF9540BEC86F549165B45ADDCCF85606BF4D5B5CC4C636C9627C60A2483458B2EF769B976EA09FC456ACC6BFD3299E9CCA77FE95438E4FBF8581ACC347679AF49A63CF988629DFC10770743A3C8852D8F7C79F0ACA74B86FEE06C77ABAE157E76D1F20F4C5BA169BFF0985EDE5F6F6"}'''),
    "response": json.loads(r'''{"code": 1001, "data": {"image": [{"equipmentID": "18002120211016268", "TOWERID": "3522", "path": "/v3/image/2025/5/8/18002120211016268_20250508101915.jpg", "create_time": "2025-05-08 10:08:58"}, {"equipmentID": "18002120211016268", "TOWERID": "3522", "path": "/v4/image/2025/5/8/18002120211016123_20250508101529.jpg", "create_time": "2025-05-08 10:11:58"}, {"equipmentID": "18002120211016268", "TOWERID": "3522", "path": "/v4/image/2025/5/8/18002120211016006_20250508101532.jpg", "create_time": "2025-05-08 10:13:56"}, {"equipmentID": "18002120211016268", "TOWERID": "3522", "path": "/v4/image/2025/5/8/18002120211016268_20250508152129.jpg", "create_time": "2025-05-08 15:09:15"}, {"equipmentID": "18002120211016268", "TOWERID": "3522", "path": "/v3/image/2025/5/8/18002120211016016_20250508152436.jpg", "create_time": "2025-05-08 15:17:12"}, {"equipmentID": "18002120211016268", "TOWERID": "3522", "path": "/v4/image/2025/5/8/18002120211016151_20250508152430.jpg", "create_time": "2025-05-08 15:19:23"}], "trip": {"id": null, "linename": "雅湖线", "lineid": 410201, "milliSecond": 56, "timedate": "2025-05-08 19:46:30", "towerId": "3522", "longitude": 116.03716, "latitude": 27.833884, "tripId": "S_Y202505080552", "chzFlag": 3, "flashFlag": 1, "tripCause": "雷击", "tripDescription": "2025-05-08 19:46:30 056毫秒±800kV雅湖线线路发生雷击故障，重合闸未知，故障相别为极Ⅱ，故障点位于3365号杆塔和3638号杆塔之间，(湖南省)，距离3365号杆塔大号方向81.011km，故障点位于3522号杆塔附近，所属局是国网湖南省电力有限公司输电检修分公司。", "pressure": "±800", "region": "江西抚州市", "length": 1697.15, "tripPhase": "极Ⅱ", "tripStation1": "特高压雅砻江站", "tripDiaelepo1": "3365号杆塔", "tripStation2": "特高压鄱阳湖站", "tripDiaelepo2": "3638号杆塔", "viewStatus": "0", "tripClass": "雷击", "elevation": null, "tripInfo": null}, "weather": null, "alarmImage": [], "flash": [{"sequence": 1, "peakCurrent": -18.7, "longitude": 115.931072, "latitude": 27.719433, "timedate": "2025-05-08 19:46:28.371", "hostId": 1, "tdfsum": 12, "multiplicity": 3, "strMltiplicity": "主放电(含2次后续回击)", "tdfString": "怀宁数字站,黄梅（新）,黄石,宜春上高,上饶玉山,赣西/新余(新),赣东北/乐平,广昌(新),吉安县(新),南昌(新),抚州乐安,宜春石市", "distance": 4265, "tower": "3490", "bothEnds": null, "towerRange": null}, {"sequence": 2, "peakCurrent": -18.4, "longitude": 115.931639, "latitude": 27.720047, "timedate": "2025-05-08 19:46:28.459", "hostId": 1, "tdfsum": 7, "multiplicity": -1, "strMltiplicity": "后续第1次回击", "tdfString": "宜春上高,赣西/新余(新),广昌(新),吉安县(新),南昌(新),抚州乐安,宜春石市", "distance": 4244, "tower": "3491", "bothEnds": null, "towerRange": null}, {"sequence": 3, "peakCurrent": -17.0, "longitude": 115.944755, "latitude": 27.736032, "timedate": "2025-05-08 19:46:28.459", "hostId": 1, "tdfsum": 7, "multiplicity": -2, "strMltiplicity": "后续第2次回击", "tdfString": "怀宁数字站,黄梅（新）,黄石,上饶玉山,赣东北/乐平,九江湖口(新),抚州乐安", "distance": 3482, "tower": "3495", "bothEnds": null, "towerRange": null}, {"sequence": 4, "peakCurrent": -18.3, "longitude": 115.850261, "latitude": 27.687508, "timedate": "2025-05-08 19:46:29.400", "hostId": 1, "tdfsum": 16, "multiplicity": 1, "strMltiplicity": "单次回击", "tdfString": "怀宁数字站,黄梅（新）,黄石,宜春上高,上饶玉山,赣西/新余(新),赣东北/乐平,广昌(新),九江湖口(新),吉安县(新),南昌(新),吉安井冈山,上饶铅山,抚州乐安,宜春石市,衢州电力园区", "distance": 3817, "tower": "3470", "bothEnds": null, "towerRange": null}, {"sequence": 5, "peakCurrent": -11.1, "longitude": 116.000472, "latitude": 27.809218, "timedate": "2025-05-08 19:46:29.951", "hostId": 1, "tdfsum": 4, "multiplicity": 1, "strMltiplicity": "单次回击", "tdfString": "赣西/新余(新),广昌(新),南昌(新),抚州乐安", "distance": 109, "tower": "3513", "bothEnds": null, "towerRange": null}, {"sequence": 6, "peakCurrent": 19.6, "longitude": 116.038658, "latitude": 27.835283, "timedate": "2025-05-08 19:46:30.056", "hostId": 1, "tdfsum": 11, "multiplicity": 1, "strMltiplicity": "单次回击", "tdfString": "怀宁数字站,黄梅（新）,黄石,黄冈桐梓,上饶玉山,赣西/新余(新),九江湖口(新),上饶铅山,抚州乐安,宜春石市,茶陵", "distance": 204, "tower": "3522", "bothEnds": null, "towerRange": null}, {"sequence": 7, "peakCurrent": 12.6, "longitude": 115.077726, "latitude": 27.454555, "timedate": "2025-05-08 19:46:39.526", "hostId": 1, "tdfsum": 2, "multiplicity": 1, "strMltiplicity": "单次回击", "tdfString": "吉安井冈山,宜春石市", "distance": 1519, "tower": "3311", "bothEnds": null, "towerRange": null}, {"sequence": 8, "peakCurrent": -7.6, "longitude": 115.097066, "latitude": 27.448552, "timedate": "2025-05-08 19:46:39.561", "hostId": 1, "tdfsum": 4, "multiplicity": 8, "strMltiplicity": "主放电(含7次后续回击)", "tdfString": "赣西/新余(新),吉安县(新),南昌(新),抚州乐安", "distance": 2156, "tower": "3315", "bothEnds": null, "towerRange": null}], "desc": null}}'''),
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

@app.post("/tgyApiservice/lineflashtripservice/getTripInfo", summary="getTripInfo")
async def getTripInfo(
    tripId: str = Form(default='S_Y202505080552'),
    access_token: str = Form(default='04B438E8DF9540BEC86F549165B45ADDCCF85606BF4D5B5CC4C636C9627C60A2483458B2EF769B976EA09FC456ACC6BFD3299E9CCA77FE95438E4FBF8581ACC347679AF49A63CF988629DFC10770743A3C8852D8F7C79F0ACA74B86FEE06C77ABAE157E76D1F20F4C5BA169BFF0985EDE5F6F6'),
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