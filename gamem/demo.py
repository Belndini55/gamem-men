"""Demo library — fictional games so the UI is alive in preview/demo mode."""

from __future__ import annotations

from typing import List

from .models import Game

_DEMO = [
    dict(
        id="demo-neon-rift",
        name="Neon Rift: Overdrive",
        platform="steam",
        install_path=r"D:\SteamLibrary\steamapps\common\Neon Rift Overdrive",
        size_bytes=68_719_476_736,
        install_date="2026-03-12",
        launch_uri="steam://rungameid/900001",
        cover_url="/covers/neon-rift.jpg",
    ),
    dict(
        id="demo-emberfall",
        name="Kingdoms of Emberfall",
        platform="steam",
        install_path=r"D:\SteamLibrary\steamapps\common\Kingdoms of Emberfall",
        size_bytes=42_949_672_960,
        install_date="2025-11-02",
        launch_uri="steam://rungameid/900002",
        cover_url="/covers/emberfall.jpg",
    ),
    dict(
        id="demo-stellar-ascent",
        name="Stellar Ascent",
        platform="epic",
        install_path=r"C:\Program Files (x86)\Epic Games\StellarAscent",
        size_bytes=51_539_607_552,
        install_date="2026-01-20",
        launch_uri="com.epicgames.launcher://apps/StellarAscent?action=launch&silent=true",
        cover_url="/covers/stellar-ascent.jpg",
    ),
    dict(
        id="demo-frostline",
        name="Frostline",
        platform="gog",
        install_path=r"C:\GOG Games\Frostline",
        size_bytes=12_884_901_888,
        install_date="2025-08-14",
        launch_uri="goggalaxy://openGameView/1421001234",
        cover_url="/covers/frostline.jpg",
    ),
    dict(
        id="demo-shadow-protocol",
        name="Shadow Protocol",
        platform="epic",
        install_path=r"C:\Program Files (x86)\Epic Games\ShadowProtocol",
        size_bytes=85_899_345_920,
        install_date="2026-05-30",
        launch_uri="com.epicgames.launcher://apps/ShadowProtocol?action=launch&silent=true",
        cover_url="/covers/shadow-protocol.jpg",
    ),
    dict(
        id="demo-wildwood",
        name="Wildwood Tales",
        platform="gog",
        install_path=r"C:\GOG Games\Wildwood Tales",
        size_bytes=6_442_450_944,
        install_date="2026-02-08",
        launch_uri="goggalaxy://openGameView/1421005678",
        cover_url="/covers/wildwood.jpg",
    ),
    dict(
        id="demo-turbo-legends",
        name="Turbo Legends",
        platform="xbox",
        install_path=r"C:\XboxGames\Turbo Legends",
        size_bytes=29_360_128_000,
        install_date="2026-06-18",
        launch_uri=None,
        cover_url="/covers/turbo-legends.jpg",
    ),
    dict(
        id="demo-runeforge",
        name="Runeforge Arena",
        platform="riot",
        install_path=r"C:\Riot Games\Runeforge Arena",
        size_bytes=18_253_611_008,
        install_date="2026-04-25",
        launch_uri=None,
        cover_url="/covers/runeforge.jpg",
    ),
]


def demo_games() -> List[Game]:
    games = []
    for raw in _DEMO:
        games.append(
            Game(
                id=raw["id"],
                name=raw["name"],
                platform=raw["platform"],
                install_path=raw.get("install_path"),
                executable=None,
                working_dir=raw.get("install_path"),
                size_bytes=raw.get("size_bytes"),
                install_date=raw.get("install_date"),
                launch_uri=raw.get("launch_uri"),
                cover_url=raw.get("cover_url"),
                source="demo",
            )
        )
    return games
