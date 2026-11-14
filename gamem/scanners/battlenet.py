"""Battle.net scanner.

Battle.net games live under `Battle.net\\Games\\<Game>`. Blizzard publishes
a URI scheme per title which we map from folder names.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from ..models import Game, make_id
from ..util import find_main_exe

# folder name (lower) -> battle.net protocol code
BNET_CODES: Dict[str, str] = {
    "world of warcraft": "WoW",
    "diablo ii resurrected": "D2",
    "diablo iii": "D3",
    "diablo iv": "D4",
    "diablo": "D3",
    "starcraft ii": "S2",
    "starcraft": "S1",
    "starcraft remastered": "S1",
    "hearthstone": "WTCG",
    "heroes of the storm": "Hero",
    "overwatch": "Pro",
    "overwatch 2": "Pro",
    "call of duty": "VIP",
    "call of duty hq": "VIP",
    "modern warfare": "ODI",
    "black ops": "ODI",
    "warcraft iii reforged": "W3",
    "warcraft iii": "W3",
    "wow classic": "WoW",
    "world of warcraft classic": "WoW",
    "lost ark": "LOSTARK",
    "crash bandicoot 4": "VIP",
    "diablo immortal": "OSI",
}

BNET_EXE_HINTS = {
    "world of warcraft": "wow",
    "wow classic": "wow",
    "diablo ii resurrected": "d2r",
    "diablo iii": "diablo iii",
    "diablo iv": "diablo iv",
    "hearthstone": "hearthstone",
    "starcraft ii": "starcraft ii",
    "overwatch": "overwatch",
    "overwatch 2": "overwatch",
}


def _game_dirs() -> List[Path]:
    out = []
    for env in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(env)
        if base:
            d = Path(base) / "Battle.net" / "Games"
            if d.is_dir():
                out.append(d)
    return out


def scan() -> List[Game]:
    games: List[Game] = []
    for root in _game_dirs():
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():
                continue
            key = folder.name.lower().strip()
            pretty = folder.name.replace("_", " ")
            hint = BNET_EXE_HINTS.get(key, folder.name)
            exe = find_main_exe(folder, prefer_name=hint)
            if not exe:
                continue
            code = BNET_CODES.get(key)
            # Some installs nest the real game one level deeper (_retail_ etc.)
            launch_uri = f"battlenet://{code}" if code else None
            games.append(
                Game(
                    id=make_id("battlenet", folder.name),
                    name=pretty.title() if pretty.islower() else pretty,
                    platform="battlenet",
                    install_path=str(folder),
                    executable=str(exe),
                    working_dir=str(exe.parent),
                    launch_uri=launch_uri,
                    source="battlenet",
                )
            )
    return games
