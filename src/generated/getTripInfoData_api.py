from main_app import app
from fastapi import Form
import token_manager

import json

_RECORD = {
    "request": json.loads(r'''{"timeOrderBy": 1, "startTime": "2025-05-08 00:00:00", "endTime": "2025-05-08 23:59:59", "pressureType": 1, "page": 0, "pageSize": 999, "access_token": "046794F8885BAB6CBA42C79A4C220089D152D9417F65983DFF3930851D18F922DC30727B89A32D2D03741921EE89D70D5D1F8BB43304C65DE568CEDA5DDE59B448A3E1829CA67377A2FC5443488D76CB34CE939F406EF06E635EED5554512E4E588CE3ED55045F365066C00A50A6C5E5A099D8"}'''),
    "response": json.loads(r'''{"code": 1001, "data": {"data": [{"year": "2025", "province": "江西", "voltage": "±800kV", "tripLineName": "雅湖线", "tripDate": "2025-05-08 19:46:30.56", "tripTime": null, "tripClass": "雷击", "reason1": "雷击", "reason2": null, "tripTowerID": "3522", "faultPhase": "极Ⅱ", "reclosingSituation": "2025-05-08 19:46:30 056毫秒±800kV雅湖线线路发生雷击故障，重合闸未知，故障相别为极Ⅱ，故障点位于3365号杆塔和3638号杆塔之间，(湖南省)，距离3365号杆塔大号方向81.011km，故障点位于3522号杆塔附近，所属局是国网湖南省电力有限公司输电检修分公司。", "path": null, "tripDateTime": "2025-05-08 19:46:30", "id": 2100, "tripId": "S_Y202505080552", "reclosureStatus": "重合未知", "upload_pdf": null, "upload_word": null, "upload_user_id": null, "create_time": null}, {"year": "2025", "province": "湖南", "voltage": "1000kV", "tripLineName": "荆潇Ⅰ线", "tripDate": "2025-05-08 08:30:24.453", "tripTime": null, "tripClass": "非雷击", "reason1": "非雷击", "reason2": null, "tripTowerID": "489", "faultPhase": "C相", "reclosingSituation": "2025-05-08 08:30:23 251毫秒1000kV荆潇一线线路发生雷击故障，重合闸不成功，故障相别为C相，故障点位于440号杆塔和498号杆塔之间，(湖南省)，距离440号杆塔大号方向24.654km，故障点位于489号杆塔附近，所属局是国网湖南省电力有限公司输电检修分公司。", "path": null, "tripDateTime": "2025-05-08 08:30:24", "id": 1992, "tripId": "C01120250508A0003-C011", "reclosureStatus": "重合未动作", "upload_pdf": null, "upload_word": null, "upload_user_id": null, "create_time": null}, {"year": "2025", "province": "湖南", "voltage": "1000kV", "tripLineName": "荆潇Ⅰ线", "tripDate": "2025-05-08 08:30:23.251", "tripTime": null, "tripClass": "非雷击", "reason1": "非雷击", "reason2": null, "tripTowerID": "489", "faultPhase": "C相", "reclosingSituation": "故障告警：2025-05-08 08:30:21 251毫秒，湖南公司1000kV荆潇一线线路发生跳闸，故障相为C相，重合闸成功，位置在440号杆塔和498号杆塔之间，距离440号杆塔大号方向24.557公里，故障点位于489号杆塔附近，位于湖南省岳阳市，所属单位是国网湖南省超高压输电公司。(故障点实时气象：温度21.5℃，风速1.9m/s，降水1.11mm；数据来源：气象实况插值)", "path": null, "tripDateTime": "2025-05-08 08:30:23", "id": 1993, "tripId": "C01120250508A0002", "reclosureStatus": "重合成功", "upload_pdf": null, "upload_word": null, "upload_user_id": null, "create_time": null}], "count": 3}}'''),
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

@app.post("/tgyApiservice/devicedataservice/getTripInfoData", summary="getTripInfoData")
async def getTripInfoData(
    timeOrderBy: int = Form(default=1),
    startTime: str = Form(default='2025-05-08 00:00:00'),
    endTime: str = Form(default='2025-05-08 23:59:59'),
    pressureType: int = Form(default=1),
    page: int = Form(default=0),
    pageSize: int = Form(default=999),
    access_token: str = Form(default='046794F8885BAB6CBA42C79A4C220089D152D9417F65983DFF3930851D18F922DC30727B89A32D2D03741921EE89D70D5D1F8BB43304C65DE568CEDA5DDE59B448A3E1829CA67377A2FC5443488D76CB34CE939F406EF06E635EED5554512E4E588CE3ED55045F365066C00A50A6C5E5A099D8'),
):
    body = {
        "timeOrderBy": timeOrderBy,
        "startTime": startTime,
        "endTime": endTime,
        "pressureType": pressureType,
        "page": page,
        "pageSize": pageSize,
        "access_token": access_token,
    }
    token = body.get("access_token", "")
    if not token_manager.validate_token(token):
        return {"code": 1002, "message": "未登录或token已过期"}
    if not _match_request(body, _RECORD["request"]):
        return {"code": "400003", "message": "参数错误"}
    return _RECORD["response"]