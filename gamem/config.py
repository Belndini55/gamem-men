"""Persistent app configuration (favorites, extra scan folders ...)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


def config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        p = Path(base) / "GameMen"
    else:
        p = Path.home() / ".config" / "gamem"
    p.mkdir(parents=True, exist_ok=True)
    return p


class Config:
    def __init__(self) -> None:
        self.path = config_dir() / "config.json"
        self.data: Dict[str, Any] = {
            "favorites": [],
            "extra_folders": [],
        }
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.data.update(loaded)
        except (OSError, ValueError):
            pass

    def save(self) -> None:
        try:
            self.path.write_text(
                json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass

    # -- favorites ------------------------------------------------------
    def favorites(self) -> Set[str]:
        return set(self.data.get("favorites", []))

    def toggle_favorite(self, game_id: str) -> bool:
        favs = self.favorites()
        if game_id in favs:
            favs.discard(game_id)
            state = False
        else:
            favs.add(game_id)
            state = True
        self.data["favorites"] = sorted(favs)
        self.save()
        return state

    # -- extra folders --------------------------------------------------
    def extra_folders(self) -> List[str]:
        return list(self.data.get("extra_folders", []))

    def set_extra_folders(self, folders: List[str]) -> None:
        cleaned = [str(f).strip() for f in folders if str(f).strip()]
        self.data["extra_folders"] = cleaned
        self.save()
