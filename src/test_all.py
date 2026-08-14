#!/usr/bin/env python3
"""Automated test: verify all 13 interfaces match txt source exactly."""

import json
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000"


def post(url, body, timeout=30):
    data = urllib.parse.urlencode(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))
    except Exception as e:
        return {"__error__": str(e)}


def main():
    with open("api_schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    # 先登录获取 token
    login_info = schema["login"]
    login_body = {k: v["default"] for k, v in login_info["params"].items()}
    login_data = post(f"{BASE}{login_info['endpoint']}", login_body)
    assert login_data["code"] == 1001, f"登录失败: {login_data}"
    token = login_data["data"]["access_token"]
    print(f"登录成功，token: {token[:30]}...")
    print()

    # 1. 响应一致性验证（所有13个接口）
    print("=== 1. 响应一致性验证（所有13个接口）===")
    passed = 0
    failed = 0
    for slug in sorted(schema.keys()):
        if slug == "login":
            continue
        info = schema[slug]
        body = {k: v["default"] for k, v in info["params"].items()}
        if "access_token" in body:
            body["access_token"] = token
        actual = post(f"{BASE}{info['endpoint']}", body)
        expected = info["response"]
        if actual == expected:
            print(f"  [PASS] {slug}")
            passed += 1
        else:
            print(f"  [FAIL] {slug}: code={actual.get('code')}")
            failed += 1

    # login 单独验证（access_token 是新生成的，不能精确比较）
    # login 响应结构验证（不调用login，避免覆盖token，用login_info中的预期响应结构验证）
    ok = (
        login_data.get("code") == 1001
        and "access_token" in login_data.get("data", {})
        and len(login_data["data"]["access_token"]) == 256
    )
    if ok:
        print(f"  [PASS] login")
        passed += 1
    else:
        print(f"  [FAIL] login")
        failed += 1

    print(f"\n结果: {passed}/13 通过, {failed} 失败")
    print()

    # 2. 入参不匹配测试（所有业务接口）—— 使用同一个token，不重新登录
    print("=== 2. 入参不匹配测试（所有业务接口）===")
    mismatch_pass = 0
    mismatch_fail = 0
    for slug in sorted(schema.keys()):
        if slug == "login":
            continue
        info = schema[slug]
        body = {k: v["default"] for k, v in info["params"].items()}
        if "access_token" in body:
            body["access_token"] = token

        changed = False
        for k, v in info["params"].items():
            if k == "access_token":
                continue
            py_type = v["type"]
            if py_type == "int":
                body[k] = 999999
            elif py_type == "str":
                body[k] = "MISMATCH_VALUE"
            elif py_type == "bool":
                body[k] = not v["default"]
            else:
                body[k] = "MISMATCH_VALUE"
            changed = True
            break

        if changed:
            resp = post(f"{BASE}{info['endpoint']}", body)
            if resp.get("code") == "400003":
                print(f"  [PASS] {slug}")
                mismatch_pass += 1
            else:
                print(f"  [FAIL] {slug}: 返回 code={resp.get('code')}")
                mismatch_fail += 1

    # 统计有非token字段的接口数
    testable = sum(
        1
        for slug in schema
        if slug != "login"
        and any(k not in ("access_token", "accsess_token") for k in schema[slug]["params"])
    )
    skipped = 12 - testable
    print(f"\n结果: {mismatch_pass}/{testable} 通过, {mismatch_fail} 失败, {skipped} 个接口无可修改字段跳过")
    print()
    print("=== 3. login 错误入参测试 ===")
    bad_login = dict(login_body)
    bad_login["password"] = 999999
    resp = post(f"{BASE}{login_info['endpoint']}", bad_login)
    if resp.get("code") == "400003":
        print(f"  [PASS] login 错误密码: 返回 400003")
    else:
        print(f"  [FAIL] login 错误密码: 返回 {resp.get('code')}")

    print()

    # 4. 重新登录后旧 token 失效测试
    print("=== 4. 重新登录后旧 token 失效测试 ===")
    login_again = post(f"{BASE}{login_info['endpoint']}", login_body)
    new_token = login_again["data"]["access_token"]
    old_resp = post(
        f"{BASE}{schema['getTripFIlter']['endpoint']}", {"access_token": token}
    )
    new_resp = post(
        f"{BASE}{schema['getTripFIlter']['endpoint']}", {"access_token": new_token}
    )
    if old_resp.get("code") == 1002:
        print(f"  [PASS] 旧 token 已失效 (code=1002)")
    else:
        print(f"  [FAIL] 旧 token 应失效, 返回 {old_resp.get('code')}")
    if new_resp.get("code") == 1001:
        print(f"  [PASS] 新 token 可用 (code=1001)")
    else:
        print(f"  [FAIL] 新 token 应可用, 返回 {new_resp.get('code')}")

    # 5. 未登录访问测试
    print()
    print("=== 5. 未登录访问测试 ===")
    no_auth = post(
        f"{BASE}{schema['getTripFIlter']['endpoint']}", {"access_token": ""}
    )
    if no_auth.get("code") == 1002:
        print(f"  [PASS] 未登录返回 1002")
    else:
        print(f"  [FAIL] 未登录应返回 1002, 实际返回 {no_auth.get('code')}")

    print()
    print("=" * 50)
    print(f"最终汇总: 响应一致性 {passed}/13, 入参不匹配 {mismatch_pass}/12")
    if failed == 0 and mismatch_fail == 0:
        print("所有测试通过")
    else:
        print(f"存在失败项: 响应失败 {failed}, 入参不匹配失败 {mismatch_fail}")


if __name__ == "__main__":
    main()
