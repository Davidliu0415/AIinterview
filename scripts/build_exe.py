from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def data_arg(source: str, target: str) -> str:
    separator = ";" if os.name == "nt" else ":"
    return f"{source}{separator}{target}"


def main() -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "AIInterviewAgent",
        "--add-data",
        data_arg(str(ROOT / "app" / "templates"), "app/templates"),
        "--add-data",
        data_arg(str(ROOT / "app" / "static"), "app/static"),
        "--collect-submodules",
        "langchain",
        "--collect-submodules",
        "langchain_openai",
        str(ROOT / "run_app.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    print("Built dist/AIInterviewAgent.exe")


if __name__ == "__main__":
    main()
