"""EA App / Origin scanner.

Looks in `EA Games`, `Origin Games` folders and parses each game's
`__Installer\\installerdata.xml` for the display name and launcher URI.
"""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple

from ..models import Game, make_id
from ..util import find_main_exe

_GAME_TAG = re.compile(r"<game>(.*?)</game>", re.DOTALL)


def _roots() -> List[Path]:
    out = []
    for env in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env)
        if base:
            out.append(Path(base) / "EA Games")
            out.append(Path(base) / "Origin Games")
    return out


def _parse_installerdata(install: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Returns (display name, game code, registry key) from installerdata.xml."""
    xml_path = install / "__Installer" / "installerdata.xml"
    if not xml_path.exists():
        return None, None, None
    try:
        text = xml_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None, None

    def tag(name: str) -> Optional[str]:
        m = re.search(rf"<{name}[^>]*>(.*?)</{name}>", text, re.DOTALL)
        return m.group(1).strip() if m else None

    name = tag("gameTitle") or tag("displayName")
    code = tag("gameSlug") or tag("gameCode")
    return name, code, None


def scan() -> List[Game]:
    games: List[Game] = []
    for root in _roots():
        if not root.is_dir():
            continue
        for folder in sorted(root.iterdir()):
            if not folder.is_dir():
                continue
            name, code, _ = _parse_installerdata(folder)
            if not name:
                name = folder.name.replace("_", " ").title()
            exe = find_main_exe(folder, prefer_name=folder.name.replace(" ", ""))
            if not exe:
                continue
            launch_uri = f"origin2://game/launch?offerIds={code}" if code else None
            games.append(
                Game(
                    id=make_id("ea", code or folder.name),
                    name=name,
                    platform="ea",
                    install_path=str(folder),
                    executable=str(exe),
                    working_dir=str(exe.parent),
                    launch_uri=launch_uri,
                    source="ea",
                )
            )
    return games
