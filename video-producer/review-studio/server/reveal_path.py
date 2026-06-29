#!/usr/bin/env python3
"""Open a file or folder in the system file manager (Review Studio)."""
from __future__ import annotations

import platform
import subprocess
from pathlib import Path


def reveal_in_filesystem(path: Path) -> None:
    """Reveal *path* in the OS file manager (select file or open folder)."""
    target = path.resolve()
    if not target.exists():
        if target.suffix:
            folder = target.parent
            if not folder.is_dir():
                raise FileNotFoundError(str(target))
            target = folder
        else:
            raise FileNotFoundError(str(target))

    system = platform.system()
    if system == "Windows":
        if target.is_file():
            subprocess.run(["explorer", "/select,", str(target)], check=False)  # noqa: S603
        else:
            subprocess.run(["explorer", str(target)], check=False)  # noqa: S603
        return

    if system == "Darwin":
        if target.is_file():
            subprocess.run(["open", "-R", str(target)], check=False)  # noqa: S603
        else:
            subprocess.run(["open", str(target)], check=False)  # noqa: S603
        return

    folder = target if target.is_dir() else target.parent
    subprocess.run(["xdg-open", str(folder)], check=False)  # noqa: S603
