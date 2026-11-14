"""Minecraft scanner (Java edition .minecraft + launcher)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from ..models import Game, make_id
from ..util import IS_WINDOWS, first_existing


def _minecraft_dir() -> Optional[Path]:
    if IS_WINDOWS:
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / ".minecraft"
    return Path.home() / ".minecraft"


def _launcher_exe() -> Optional[Path]:
    if not IS_WINDOWS:
        return None
    candidates = []
    for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            candidates.append(Path(base) / "Minecraft Launcher" / "MinecraftLauncher.exe")
            candidates.append(Path(base) / "Minecraft" / "MinecraftLauncher.exe")
    candidates.append(Path(r"C:\XboxGames\Minecraft Launcher\Content\Minecraft.exe"))
    return first_existing(candidates)


def scan() -> List[Game]:
    games: List[Game] = []
    mc = _minecraft_dir()
    if not mc or not mc.is_dir():
        return games
    launcher = _launcher_exe()
    games.append(
        Game(
            id=make_id("minecraft", "java"),
            name="Minecraft",
            platform="minecraft",
            install_path=str(mc),
            executable=str(launcher) if launcher else None,
            working_dir=str(mc),
            launch_uri="minecraft://" if IS_WINDOWS else None,
            source="minecraft",
        )
    )
    return games
