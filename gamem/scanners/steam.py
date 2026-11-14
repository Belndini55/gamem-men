"""Steam library scanner.

Reads every library folder listed in `libraryfolders.vdf` and parses
`appmanifest_*.acf` files for installed games.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from ..models import Game, make_id
from ..util import (
    IS_WINDOWS,
    first_existing,
    looks_like_tool,
    parse_acf_date,
    powershell_json,
)
from ..vdf import get_ci, parse_vdf

STEAM_COVER = "https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"


def find_steam_root() -> Optional[Path]:
    if IS_WINDOWS:
        # Registry query (works even for non-default installs)
        out = powershell_json(
            "(Get-ItemProperty 'HKCU:\\Software\\Valve\\Steam' -ErrorAction SilentlyContinue).SteamPath"
        )
        if isinstance(out, str) and out.strip():
            p = Path(out.strip().strip('"'))
            if p.exists():
                return p
        candidates = [
            Path(r"C:\Program Files (x86)\Steam"),
            Path(r"C:\Program Files\Steam"),
            Path(r"D:\Steam"),
            Path(r"D:\SteamLibrary\Steam"),
        ]
    else:
        candidates = [
            Path.home() / ".steam" / "steam",
            Path.home() / ".local" / "share" / "Steam",
            Path.home() / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
        ]
    return first_existing(candidates)


def library_folders(steam_root: Path) -> List[Path]:
    libs = [steam_root]
    vdf = steam_root / "steamapps" / "libraryfolders.vdf"
    if not vdf.exists():
        vdf = steam_root / "steamapps" / "LibraryFolders.vdf"  # legacy casing
    if not vdf.exists():
        return libs
    try:
        data = parse_vdf(vdf.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return libs
    root = get_ci(data, "libraryfolders") or {}
    if not isinstance(root, dict):
        return libs
    for key, value in root.items():
        if not isinstance(value, dict):
            # Old format: "1" "D:\\SteamLibrary"
            if key.isdigit() and isinstance(value, str):
                p = Path(value.replace("\\\\", "\\"))
                if p.exists() and p not in libs:
                    libs.append(p)
            continue
        path_str = get_ci(value, "path")
        if path_str:
            p = Path(str(path_str).replace("\\\\", "\\"))
            try:
                if p.exists() and p not in libs:
                    libs.append(p)
            except OSError:
                continue
    return libs


def scan() -> List[Game]:
    games: List[Game] = []
    steam_root = find_steam_root()
    if not steam_root:
        return games

    for lib in library_folders(steam_root):
        steamapps = lib / "steamapps"
        if not steamapps.exists():
            steamapps = lib  # sometimes the path is already .../steamapps
        for acf in steamapps.glob("appmanifest_*.acf"):
            try:
                data = parse_vdf(acf.read_text(encoding="utf-8", errors="replace"))
            except (OSError, ValueError):
                continue
            app = get_ci(data, "appstate") or {}
            if not isinstance(app, dict):
                continue
            appid = str(get_ci(app, "appid") or "").strip()
            name = str(get_ci(app, "name") or "").strip()
            installdir = str(get_ci(app, "installdir") or "").strip()
            if not appid or not name or looks_like_tool(name):
                continue
            size_raw = get_ci(app, "sizeondisk")
            try:
                size = int(size_raw) if size_raw else None
            except (TypeError, ValueError):
                size = None
            install_path = (steamapps / "common" / installdir) if installdir else None
            exe = None
            if install_path and install_path.exists():
                from ..util import find_main_exe

                exe = find_main_exe(install_path, prefer_name=installdir)
            games.append(
                Game(
                    id=make_id("steam", appid),
                    name=name,
                    platform="steam",
                    install_path=str(install_path) if install_path else None,
                    executable=str(exe) if exe else None,
                    working_dir=str(install_path) if install_path else None,
                    size_bytes=size,
                    install_date=parse_acf_date(get_ci(app, "lastupdated")),
                    launch_uri=f"steam://rungameid/{appid}",
                    cover_url=STEAM_COVER.format(appid=appid),
                    source="steam",
                )
            )
    return games
