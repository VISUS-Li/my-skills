#!/usr/bin/env python3
"""Native folder picker for Review Studio (Windows/macOS/Linux)."""
from __future__ import annotations

import sys


def pick_directory(title: str = "选择文件夹") -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return None
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:  # noqa: BLE001
        pass
    path = filedialog.askdirectory(title=title, mustexist=True)
    root.destroy()
    return path or None


if __name__ == "__main__":
    selected = pick_directory(sys.argv[1] if len(sys.argv) > 1 else "选择文件夹")
    if selected:
        print(selected)
