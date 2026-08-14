#!/usr/bin/env python3
"""One-click setup: parse txt -> generate code -> start uvicorn."""

import subprocess
import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent


def run(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def main():
    print("=" * 60)
    print("特高压线路故障诊断 API Mock 测试平台 - 一键启动")
    print("=" * 60)

    # Step 1: Parse txt files
    print("\n[1/3] Parsing txt files...")
    run([sys.executable, "txt_parser.py"], cwd=SRC_DIR)

    # Step 2: Generate API modules
    print("\n[2/3] Generating API modules...")
    run([sys.executable, "api_generator.py"], cwd=SRC_DIR)

    # Step 3: Start uvicorn
    print("\n[3/3] Starting uvicorn server...")
    print("Access Swagger UI at: http://127.0.0.1:8000/docs")
    print("Press Ctrl+C to stop\n")
    run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=SRC_DIR,
    )


if __name__ == "__main__":
    main()
