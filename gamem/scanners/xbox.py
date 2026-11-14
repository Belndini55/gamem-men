"""Xbox / PC Game Pass scanner.

Game Pass installs live in `C:\\XboxGames` (library location is listed in
`.gamingroot`). Launching UWP games needs the AppUserModelID which we grab
from `Get-StartApps` and match by name.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from ..models import Game, make_id
from ..util import IS_WINDOWS, find_main_exe, powershell_json

AUMID_CACHE: Optional[Dict[str, str]] = None


def _library_root() -> Optional[Path]:
    default = Path(r"C:\XboxGames")
    marker = default / ".gamingroot"
    if marker.exists():
        try:
            raw = marker.read_bytes()
            text = raw.decode("utf-16-le", errors="replace").strip("\x00").strip()
            if not text or text.startswith("\x00"):
                text = raw.decode("utf-8", errors="replace").strip("\x00").strip()
            if text:
                p = Path(text)
                if p.exists():
                    return p
        except OSError:
            pass
    return default if default.exists() else None


def _start_apps() -> Dict[str, str]:
    """Map lowercased Start menu names -> AppUserModelID (best effort)."""
    global AUMID_CACHE
    if AUMID_CACHE is not None:
        return AUMID_CACHE
    AUMID_CACHE = {}
    if not IS_WINDOWS:
        return AUMID_CACHE
    out = powershell_json("Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Compress")
    if isinstance(out, list):
        for entry in out:
            if isinstance(entry, dict) and entry.get("Name") and entry.get("AppID"):
                AUMID_CACHE[str(entry["Name"]).strip().lower()] = str(entry["AppID"]).strip()
    elif isinstance(out, dict) and out.get("Name") and out.get("AppID"):
        AUMID_CACHE[str(out["Name"]).strip().lower()] = str(out["AppID"]).strip()
    return AUMID_CACHE


def _match_aumid(name: str) -> Optional[str]:
    apps = _start_apps()
    key = name.strip().lower()
    if key in apps:
        return apps[key]
    for app_name, aumid in apps.items():
        if key and (key in app_name or app_name in key):
            return aumid
    return None


def scan() -> List[Game]:
    games: List[Game] = []
    root = _library_root()
    if not root:
        return games

    for folder in sorted(root.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        content = folder / "Content"
        target = content if content.is_dir() else folder
        exe = find_main_exe(target, prefer_name=folder.name)
        if not exe:
            continue
        name = folder.name.replace("_", " ").replace("-", " ").strip()
        aumid = _match_aumid(name)
        launch_uri = None
        if aumid:
            # Launch through the shell so UWP permissions are honoured.
            launch_uri = f"shell:AppsFolder\\{aumid}"
        games.append(
            Game(
                id=make_id("xbox", folder.name),
                name=name.title() if name.islower() else name,
                platform="xbox",
                install_path=str(folder),
                executable=str(exe),
                working_dir=str(target),
                launch_uri=launch_uri,
                source="xbox",
            )
        )
    return games
