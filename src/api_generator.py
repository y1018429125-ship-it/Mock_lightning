"""Generate FastAPI endpoint modules from api_schema.json."""

import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent / "api_schema.json"
OUTPUT_DIR = Path(__file__).parent / "generated"


def generate_module(slug: str, info: dict) -> str:
    """Generate a single API module's source code using Form parameters."""
    func_name = slug
    endpoint = info["endpoint"]
    is_login = slug == "login"

    lines = []

    # Imports
    lines.append("from main_app import app")
    lines.append("from fastapi import Form")
    lines.append("import token_manager")
    lines.append("")

    # _RECORD with request/response
    request_dict = {k: v["default"] for k, v in info["params"].items()}
    request_json = json.dumps(request_dict, ensure_ascii=False)
    response_json = json.dumps(info["response"], ensure_ascii=False)

    lines.append("import json")
    lines.append("")
    lines.append("_RECORD = {")
    lines.append(f'    "request": json.loads(r\'\'\'{request_json}\'\'\'),')
    lines.append(f'    "response": json.loads(r\'\'\'{response_json}\'\'\'),')
    lines.append("}")
    lines.append("")

    # Match function: received may contain extra fields (per requirements §6.2)
    lines.append("def _match_request(received: dict, expected: dict) -> bool:")
    lines.append('    skip = {"access_token", "accsess_token"}')
    lines.append("    for key, expected_val in expected.items():")
    lines.append("        if key in skip:")
    lines.append("            continue")
    lines.append("        if key not in received:")
    lines.append("            return False")
    lines.append("        if received[key] != expected_val:")
    lines.append("            return False")
    lines.append("    return True")
    lines.append("")

    # Build Form parameter declarations
    form_params = []
    for key, param in info["params"].items():
        py_type = param["type"]
        default = param["default"]
        if py_type == "str":
            form_params.append(f'{key}: str = Form(default={repr(default)})')
        elif py_type == "int":
            form_params.append(f'{key}: int = Form(default={default})')
        elif py_type == "bool":
            form_params.append(f'{key}: bool = Form(default={default})')
        elif py_type == "float":
            form_params.append(f'{key}: float = Form(default={default})')
        else:
            if default is None:
                form_params.append(f'{key}: str = Form(default="")')
            else:
                form_params.append(f'{key}: str = Form(default={repr(str(default))})')

    # Endpoint signature
    lines.append(f'@app.post("{endpoint}", summary="{slug}")')
    if form_params:
        lines.append(f"async def {func_name}(")
        for fp in form_params:
            lines.append(f"    {fp},")
        lines.append("):")
    else:
        lines.append(f"async def {func_name}():")

    # Build body dict from Form parameters
    if form_params:
        lines.append("    body = {")
        for key in info["params"].keys():
            lines.append(f'        "{key}": {key},')
        lines.append("    }")
    else:
        lines.append("    body = {}")

    if is_login:
        lines.append('    token = token_manager.login(account, password)')
        lines.append('    if token is None:')
        lines.append('        return {"code": "400003", "message": "参数错误"}')
        lines.append('    resp = dict(_RECORD["response"])')
        lines.append('    resp["data"] = dict(resp["data"])')
        lines.append('    resp["data"]["access_token"] = token')
        lines.append('    return resp')
    else:
        lines.append('    token = body.get("access_token", "")')
        lines.append('    if not token_manager.validate_token(token):')
        lines.append('        return {"code": 1002, "message": "未登录或token已过期"}')
        lines.append('    if not _match_request(body, _RECORD["request"]):')
        lines.append('        return {"code": "400003", "message": "参数错误"}')
        lines.append('    return _RECORD["response"]')

    return "\n".join(lines)


def main():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    print(f"Generating {len(schema)} API modules to: {OUTPUT_DIR}")

    for slug, info in schema.items():
        code = generate_module(slug, info)
        filepath = OUTPUT_DIR / f"{slug}_api.py"
        filepath.write_text(code, encoding="utf-8")
        print(f"  Generated: {filepath.name} ({len(code)} bytes)")

    print("Done.")


if __name__ == "__main__":
    main()
