"""GOG scanner.

Finds games via `goggame-*.info` sidecar files (GOG Galaxy and offline
installers both create them) in the usual GOG library folders.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

from ..models import Game, make_id
from ..util import IS_WINDOWS, find_main_exe


def _candidate_roots() -> List[Path]:
    roots: List[Path] = []
    if IS_WINDOWS:
        for env in ("ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(env)
            if base:
                roots.append(Path(base) / "GOG Galaxy" / "Games")
        roots.append(Path(r"C:\GOG Games"))
        progdata = os.environ.get("ProgramData", r"C:\ProgramData")
        roots.append(Path(progdata) / "GOG.com" / "Galaxy" / "storage" / "webpublish")
    else:
        home = Path.home()
        roots.append(home / "GOG Games")
        roots.append(home / ".config" / "heroic" / "gog_store")
    return roots


def _extract_exe(install: Path, info: dict) -> Optional[Path]:
    tasks = info.get("playTasks") or []
    if isinstance(tasks, list):
        for task in tasks:
            if not isinstance(task, dict):
                continue
            if not task.get("isPrimary", True):
                continue
            path = (task.get("path") or "").replace("/", os.sep)
            if path:
                p = install / path
                if p.exists():
                    return p
    return find_main_exe(install, prefer_name=install.name)


def scan() -> List[Game]:
    games: List[Game] = []
    seen = set()

    # Fast path: known library folders
    info_files = []
    for root in _candidate_roots():
        if root.is_dir():
            info_files.extend(root.glob("*/goggame-*.info"))
            info_files.extend(root.glob("goggame-*.info"))

    # Deep path: also check the GOG Galaxy storage DB location for installs
    if IS_WINDOWS:
        progdata = os.environ.get("ProgramData", r"C:\ProgramData")
        gal = Path(progdata) / "GOG.com" / "Galaxy" / "storage"
        if gal.is_dir():
            for sub in gal.iterdir():
                if sub.is_dir():
                    info_files.extend(sub.glob("goggame-*.info"))

    for info_path in info_files:
        try:
            data = json.loads(info_path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, ValueError):
            continue
        name = (data.get("name") or "").strip()
        game_id = str(data.get("gameId") or data.get("rootGameId") or "").strip()
        install = info_path.parent
        key = str(install).lower()
        if not name or key in seen:
            continue
        seen.add(key)
        exe = _extract_exe(install, data)
        games.append(
            Game(
                id=make_id("gog", game_id or name),
                name=name,
                platform="gog",
                install_path=str(install),
                executable=str(exe) if exe else None,
                working_dir=str(install),
                launch_uri=f"goggalaxy://openGameView/{game_id}" if game_id else None,
                source="gog",
            )
        )
    return games
