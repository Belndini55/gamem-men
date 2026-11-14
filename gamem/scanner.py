"""Scan orchestration: runs every scanner and de-duplicates results."""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from .config import Config
from .models import Game
from .util import norm_path
from .scanners import (
    battlenet,
    ea,
    epic,
    folders,
    gog,
    minecraft,
    registry,
    riot,
    steam,
    ubisoft,
    xbox,
)

log = logging.getLogger("gamem")

# Order matters: first scanner that claims an install path wins.
NATIVE_SCANNERS = (
    ("steam", steam.scan),
    ("epic", epic.scan),
    ("gog", gog.scan),
    ("xbox", xbox.scan),
    ("battlenet", battlenet.scan),
    ("ea", ea.scan),
    ("ubisoft", ubisoft.scan),
    ("riot", riot.scan),
    ("minecraft", minecraft.scan),
)


def scan_all(config: Optional[Config] = None, progress: Optional[callable] = None) -> List[Game]:
    config = config or Config()
    games: List[Game] = []
    seen_paths = set()
    seen_ids = set()

    def claim(new_games: List[Game]) -> None:
        for g in new_games:
            if g.id in seen_ids:
                continue
            key = norm_path(g.install_path)
            if key and key in seen_paths:
                continue
            seen_ids.add(g.id)
            if key:
                seen_paths.add(key)
            games.append(g)

    steps = [f for f in NATIVE_SCANNERS] + [
        ("registry", lambda: registry.scan([g.install_path or "" for g in games])),
        ("folders", lambda: folders.scan(config.extra_folders(), [g.install_path or "" for g in games])),
    ]

    total = len(steps)
    for i, (name, fn) in enumerate(steps):
        if progress:
            progress(name, i, total)
        started = time.perf_counter()
        try:
            found = fn()
        except Exception:  # noqa: BLE001 - a broken scanner must not kill the app
            log.exception("scanner %s failed", name)
            found = []
        claim(found)
        log.info("scanner %-10s -> %2d games (%.2fs)", name, len(found), time.perf_counter() - started)

    favs = config.favorites()
    for g in games:
        g.favorite = g.id in favs

    games.sort(key=lambda g: (g.platform_name, g.name.lower()))
    return games
