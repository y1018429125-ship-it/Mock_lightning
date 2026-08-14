"""Parse txt files in 接口/ directory and generate api_schema.json."""

import json
import os
import re
from pathlib import Path

TXT_DIR = Path("/Users/yfzx/Desktop/特高压/接口")
OUTPUT_PATH = Path(__file__).parent / "api_schema.json"


def extract_first_curl(content: str) -> str | None:
    """Extract the first (full) curl command."""
    curls = list(re.finditer(r"^curl\s", content, re.MULTILINE))
    if len(curls) < 1:
        return None
    start = curls[0].start()
    end = curls[1].start() if len(curls) > 1 else len(content)
    return content[start:end].strip()


def extract_simple_curl(content: str) -> str | None:
    """Extract the simplified curl command.

    Files normally contain two curls (full + simplified); use the second.
    Some files (e.g. getTripInfoData.txt) contain only one curl which is
    already simplified; use it directly.
    """
    curls = list(re.finditer(r"^curl\s", content, re.MULTILINE))
    if len(curls) < 1:
        return None
    start = curls[1].start() if len(curls) > 1 else curls[0].start()
    end_match = re.search(r"\n\s*\n", content[start:])
    end = start + end_match.start() if end_match else len(content)
    return content[start:end].strip()


def extract_url(curl: str) -> str | None:
    """Extract URL from simplified curl."""
    m = re.search(r"curl\s+-X\s+POST\s+'([^']+)'", curl)
    return m.group(1) if m else None


def extract_url_from_full_curl(curl: str) -> str | None:
    """Extract URL from full curl (first line format: curl 'URL')."""
    m = re.search(r"curl\s+'([^']+)'", curl)
    return m.group(1) if m else None


def extract_params(curl: str) -> dict[str, str]:
    """Extract -d 'key=value' parameters from simplified curl."""
    params = {}
    for m in re.finditer(r"-d\s+'([^']+)'", curl):
        pair = m.group(1)
        if "=" in pair:
            k, v = pair.split("=", 1)
            params[k] = v
    return params


def extract_json_response(content: str) -> dict | None:
    """Extract the last JSON response (line starting with '{')."""
    lines = content.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].lstrip().startswith("{"):
            try:
                return json.loads("\n".join(lines[i:]))
            except json.JSONDecodeError:
                continue
    return None


def infer_type(value_str: str):
    """Infer Python type from a string value."""
    if value_str == "":
        return "str", ""
    # Try JSON parsing first (bool, null, nested objects)
    try:
        parsed = json.loads(value_str)
        if parsed is None:
            return "Any | None", None
        if isinstance(parsed, bool):
            return "bool", parsed
        if isinstance(parsed, dict):
            return "dict", parsed
        if isinstance(parsed, list):
            return "list", parsed
    except (json.JSONDecodeError, ValueError):
        pass
    # Try int
    try:
        return "int", int(value_str)
    except ValueError:
        pass
    # Try float
    try:
        return "float", float(value_str)
    except ValueError:
        pass
    # Default to str
    return "str", value_str


def parse_all_txts() -> dict:
    """Parse all txt files and return the schema."""
    schema = {}
    files = sorted(TXT_DIR.glob("*.txt"))

    for filepath in files:
        content = filepath.read_text(encoding="utf-8")

        full_curl = extract_first_curl(content)
        curl = extract_simple_curl(content)
        if not curl:
            print(f"  Warning: no simplified curl found in {filepath.name}")
            continue

        # Extract URL from both curls; use full curl's URL as authoritative
        # when they differ (some txt files have incorrect simplified curl URLs)
        url_simple = extract_url(curl)
        url_full = extract_url_from_full_curl(full_curl) if full_curl else None
        url = url_full if url_full else url_simple

        params = extract_params(curl)
        response = extract_json_response(content)

        if not url:
            print(f"  Warning: no URL found in {filepath.name}")
            continue

        if response is None:
            print(f"  Warning: no JSON response found in {filepath.name}")
            continue

        # Derive slug and endpoint from filename and URL
        slug = filepath.stem
        # Extract endpoint path from URL
        endpoint = url.replace("http://10.238.0.5:31269", "")

        # Infer types for params
        typed_params = {}
        for key, val in params.items():
            py_type, default = infer_type(val)
            typed_params[key] = {
                "type": py_type,
                "default": default,
                "raw": val,
            }

        schema[slug] = {
            "url": url,
            "endpoint": endpoint,
            "params": typed_params,
            "response": response,
        }

    return schema


def main():
    print(f"Parsing txt files from: {TXT_DIR}")
    schema = parse_all_txts()
    print(f"Parsed {len(schema)} interfaces")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"Schema written to: {OUTPUT_PATH}")

    # Print summary
    for slug, info in schema.items():
        print(f"  {slug}: {info['endpoint']} ({len(info['params'])} params)")


if __name__ == "__main__":
    main()
