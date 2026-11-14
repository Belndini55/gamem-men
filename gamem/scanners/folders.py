"""Custom / generic folder scanner.

Scans user-configured folders and a few classic game directories
(e.g. `D:\\Games`) for game-looking subfolders that nothing else claimed.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Set

from ..models import Game, make_id
from ..util import IS_WINDOWS, find_main_exe, norm_path, drives

GAME_DIR_NAMES = ("games", "gry", "game", "gry pc", "steamlibrary")

_SKIP_NAMES = {
    "common redistributables", "steamworks", "_commonredist", "redist",
    "directx", "vcredist", "__installer", "installer", "prerequisites",
}


def scan(extra_folders: List[str], existing_paths: List[str]) -> List[Game]:
    known: Set[str] = {norm_path(p) for p in existing_paths if p}
    games: List[Game] = []

    roots: List[Path] = []
    for folder in extra_folders:
        p = Path(folder)
        if p.is_dir():
            roots.append(p)

    if IS_WINDOWS:
        for drive in drives():
            for name in GAME_DIR_NAMES:
                candidate = drive / name
                if candidate.is_dir() and candidate not in roots:
                    roots.append(candidate)

    for root in roots:
        try:
            children = sorted(root.iterdir())
        except OSError:
            continue
        for folder in children:
            if not folder.is_dir():
                continue
            if folder.name.lower().strip() in _SKIP_NAMES:
                continue
            if norm_path(str(folder)) in known:
                continue
            # Must contain at least one exe to count as a game
            exe = find_main_exe(folder, prefer_name=folder.name)
            if not exe:
                continue
            known.add(norm_path(str(folder)))
            name = folder.name.replace("_", " ").replace("-", " ")
            games.append(
                Game(
                    id=make_id("folder", str(folder)),
                    name=name.title() if name.islower() else name,
                    platform="other",
                    install_path=str(folder),
                    executable=str(exe),
                    working_dir=str(exe.parent),
                    source="folder",
                )
            )
    return games
