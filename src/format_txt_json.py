#!/usr/bin/env python3
"""Format the JSON response (part 3) of each txt file with proper indentation."""

import json
from pathlib import Path

INTERFACE_DIR = Path(__file__).parent.parent / "接口"


def format_file(filepath: Path) -> bool:
    """Format part 3 JSON of a single txt file. Returns True if changed."""
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    # Find the first line from the end that starts with '{'
    json_start = -1
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].lstrip()
        if stripped.startswith("{"):
            json_start = i
            break

    if json_start == -1:
        print(f"  SKIP: no JSON found in {filepath.name}")
        return False

    # Part 1 + 2: everything before json_start
    prefix_lines = lines[:json_start]
    # Part 3: json_start to end (may span multiple lines, but currently all on one line)
    json_lines = lines[json_start:]
    raw_json = "".join(json_lines).strip()

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"  ERROR: invalid JSON in {filepath.name}: {e}")
        return False

    formatted = json.dumps(parsed, indent=4, ensure_ascii=False)

    # Rebuild: prefix + formatted JSON + final newline
    new_content = "".join(prefix_lines) + formatted + "\n"

    filepath.write_text(new_content, encoding="utf-8")
    print(f"  DONE: {filepath.name}")
    return True


def main():
    txt_files = sorted(INTERFACE_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} txt files in {INTERFACE_DIR}")
    changed = 0
    for filepath in txt_files:
        if format_file(filepath):
            changed += 1
    print(f"\nFormatted {changed}/{len(txt_files)} files.")


if __name__ == "__main__":
    main()
