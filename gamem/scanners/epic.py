"""Epic Games Launcher scanner.

Parses the JSON `.item` manifests kept in
`%ProgramData%\\Epic\\EpicGamesLauncher\\Data\\Manifests`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from ..models import Game, make_id
from ..util import IS_WINDOWS


def _manifest_dirs() -> List[Path]:
    dirs = []
    if IS_WINDOWS:
        progdata = os.environ.get("ProgramData", r"C:\ProgramData")
        dirs.append(Path(progdata) / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests")
    # Legendary / Heroic (open source Epic launchers), handy on any OS
    home = Path.home()
    dirs.append(home / ".config" / "legendary")
    dirs.append(home / ".config" / "heroic" / "legendaryConfig" / "legendary" / "installed.json")
    return dirs


def scan() -> List[Game]:
    games: List[Game] = []
    seen = set()

    for d in _manifest_dirs():
        if d.is_file() and d.name.endswith(".json"):
            # Heroic/Legendary installed.json: {app_name: {...}}
            try:
                data = json.loads(d.read_text(encoding="utf-8", errors="replace"))
            except (OSError, ValueError):
                continue
            for app_name, info in data.items():
                if not isinstance(info, dict):
                    continue
                name = info.get("title") or app_name
                loc = info.get("install_path") or info.get("install_path".upper())
                exe_rel = info.get("executable") or ""
                if not loc:
                    continue
                install = Path(loc)
                exe = (install / exe_rel) if exe_rel else None
                key = str(install).lower()
                if key in seen:
                    continue
                seen.add(key)
                games.append(
                    Game(
                        id=make_id("epic", app_name),
                        name=str(name),
                        platform="epic",
                        install_path=str(install),
                        executable=str(exe) if exe and exe.exists() else None,
                        working_dir=str(install),
                        size_bytes=info.get("install_size") or None,
                        launch_uri=f"com.epicgames.launcher://apps/{app_name}?action=launch&silent=true",
                        source="epic-legendary",
                    )
                )
            continue

        if not d.is_dir():
            continue
        for item in d.glob("*.item"):
            try:
                info = json.loads(item.read_text(encoding="utf-8", errors="replace"))
            except (OSError, ValueError):
                continue
            name = (info.get("DisplayName") or "").strip()
            app_name = (info.get("AppName") or "").strip()
            loc = (info.get("InstallLocation") or "").strip()
            launch_exe = (info.get("LaunchExecutable") or "").strip()
            if not name or not loc:
                continue
            install = Path(loc.replace("\\\\", "\\"))
            if not install.exists():
                continue
            exe = install / launch_exe if launch_exe else None
            key = str(install).lower()
            if key in seen:
                continue
            seen.add(key)
            size = None
            chunk = info.get("InstallSize")
            if isinstance(chunk, (int, float)) and chunk > 0:
                size = int(chunk)
            games.append(
                Game(
                    id=make_id("epic", app_name or name),
                    name=name,
                    platform="epic",
                    install_path=str(install),
                    executable=str(exe) if exe and exe.exists() else None,
                    working_dir=str(install),
                    size_bytes=size,
                    launch_uri=(
                        f"com.epicgames.launcher://apps/{app_name}?action=launch&silent=true"
                        if app_name
                        else None
                    ),
                    source="epic",
                )
            )
    return games
