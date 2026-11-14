"""Ubisoft Connect scanner.

Games are installed under `Ubisoft Game Launcher\\games\\<Title>`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from ..models import Game, make_id
from ..util import find_main_exe


def _roots() -> List[Path]:
    out = []
    for env in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(env)
        if base:
            out.append(Path(base) / "Ubisoft" / "Ubisoft Game Launcher" / "games")
    return out


def scan() -> List[Game]:
    games: List[Game] = []
    for root in _roots():
        if not root.is_dir():
            continue
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():
                continue
            exe = find_main_exe(folder, prefer_name=folder.name)
            if not exe:
                continue
            name = folder.name.replace("_", " ").replace("-", " ")
            games.append(
                Game(
                    id=make_id("ubisoft", folder.name),
                    name=name.title() if name.islower() else name,
                    platform="ubisoft",
                    install_path=str(folder),
                    executable=str(exe),
                    working_dir=str(exe.parent),
                    source="ubisoft",
                )
            )
    return games
