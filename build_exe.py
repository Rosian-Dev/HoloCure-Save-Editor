"""Build a standalone Windows .exe for the HoloCure Save Editor.

Usage:
    pip install -r requirements-dev.txt
    python build_exe.py

Produces:  dist/HoloCure Save Editor.exe   (single file, no console window)

customtkinter ships theme/asset data files that must be bundled, hence
--collect-data customtkinter.
"""

from __future__ import annotations

import subprocess
import sys

APP_NAME = "HoloCure Save Editor"
ENTRY = "holocure_editor.py"


def main() -> int:
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",            # GUI app: no console window
        "--name", APP_NAME,
        "--collect-data", "customtkinter",
        ENTRY,
    ]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
