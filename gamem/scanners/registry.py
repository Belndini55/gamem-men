"""Generic scanner: Windows Uninstall registry keys.

Catches games from launchers we do not parse natively (Bethesda, Rockstar,
indie installs, DRM-free copies ...). Only entries from known game
publishers or with game-like install paths are kept.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..models import Game, make_id
from ..util import IS_WINDOWS, iso_from_yyyymmdd, norm_path

GAME_PUBLISHERS = (
    "ubisoft", "electronic arts", "ea games", "ea", "bethesda", "zenimax",
    "2k games", "2k", "square enix", "warner bros", "sega", "capcom",
    "rockstar", "activision", "blizzard", "riot games", "valve", "gog",
    "cd projekt", "paradox", "focus entertainment", "deep silver", "thq",
    "bandai namco", "konami", "sony interactive", "xbox game studios",
    "microsoft studios", "mojang", "telltale", "larian", "fromsoftware",
    "techland", "ci games", "platinumgames", "team17", "devolver digital",
    "coffee stain", "re-logic", "klei", "supergiant", "motion twin",
    "hi-rez", "funcom", "bohemia interactive", "crytek", "frictional games",
    "obsidian entertainment", "bioware", "naughty dog", "santa monica studio",
    "sucker punch", "guerrilla games", "housemarque", "insomniac",
)

BLOCK_PUBLISHERS = (
    "microsoft corporation", "adobe", "google llc", "mozilla", "oracle",
    "intel", "nvidia", "advanced micro devices", "realtek", "synaptics",
    "hp inc.", "dell", "lenovo", "asus", "nvidia corporation",
)

BLOCK_NAME_HINTS = (
    "redistributable", "runtime", "driver", "toolbar", "plugin", "extension",
    "update", "helper", "launcher sdk", "prerequisites", "vcredist",
    "visual c++", ".net", "framework", "browser", "antivirus", "codec",
)

_PUBLISHER_MAP = {
    "ubisoft": "ubisoft",
    "electronic arts": "ea",
    "ea games": "ea",
    "blizzard": "battlenet",
    "activision": "battlenet",
    "riot games": "riot",
    "mojang": "minecraft",
    "bethesda": "other",
    "zenimax": "other",
}


def _iter_uninstall_keys():
    import winreg

    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, path in roots:
        try:
            root_key = winreg.OpenKey(hive, path)
        except OSError:
            continue
        try:
            i = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(root_key, i)
                except OSError:
                    break
                i += 1
                try:
                    sub = winreg.OpenKey(root_key, sub_name)
                except OSError:
                    continue
                yield sub
                winreg.CloseKey(sub)
        finally:
            winreg.CloseKey(root_key)


def _query(key, name: str):
    import winreg

    try:
        value, _ = winreg.QueryValueEx(key, name)
        return value
    except OSError:
        return None


def scan(existing_paths: List[str]) -> List[Game]:
    if not IS_WINDOWS:
        return []
    known = {norm_path(p) for p in existing_paths if p}
    games: List[Game] = []

    for key in _iter_uninstall_keys():
        name = _query(key, "DisplayName")
        if not name or not isinstance(name, str):
            continue
        publisher = _query(key, "Publisher") or ""
        location = _query(key, "InstallLocation") or ""
        icon = _query(key, "DisplayIcon") or ""
        size_kb = _query(key, "EstimatedSize")
        date = _query(key, "InstallDate")
        uninstall = _query(key, "UninstallString")

        low_name = name.lower()
        low_pub = str(publisher).lower()
        if any(b in low_name for b in BLOCK_NAME_HINTS):
            continue
        if any(b in low_pub for b in BLOCK_PUBLISHERS):
            continue

        is_game_pub = any(p in low_pub for p in GAME_PUBLISHERS)
        loc = str(location).strip().strip('"')
        path_like_game = any(x in loc.lower() for x in ("\\games\\", "\\game\\", "steam", "epic", "gog"))
        if not is_game_pub and not path_like_game:
            continue
        if not loc or not Path(loc).exists():
            # Fall back to the exe folder from the icon entry
            icon_path = str(icon).split(",")[0].strip().strip('"')
            if icon_path.lower().endswith(".exe"):
                loc = str(Path(icon_path).parent)
        if not loc or not Path(loc).exists():
            continue
        if norm_path(loc) in known:
            continue
        known.add(norm_path(loc))

        platform = "other"
        for needle, plat in _PUBLISHER_MAP.items():
            if needle in low_pub:
                platform = plat
                break

        exe = None
        icon_path = str(icon).split(",")[0].strip().strip('"')
        if icon_path.lower().endswith(".exe") and Path(icon_path).exists():
            exe = icon_path

        size = None
        if isinstance(size_kb, (int, float)) and size_kb > 0:
            size = int(size_kb) * 1024

        games.append(
            Game(
                id=make_id("reg", name, loc),
                name=name.strip(),
                platform=platform,
                install_path=loc,
                executable=exe,
                working_dir=loc,
                size_bytes=size,
                install_date=iso_from_yyyymmdd(str(date) if date else None),
                uninstall_string=str(uninstall) if uninstall else None,
                source="registry",
            )
        )
    return games
