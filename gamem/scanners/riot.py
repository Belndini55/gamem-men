"""Riot Games scanner (League of Legends, VALORANT, TFT ...)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from ..models import Game, make_id

RIOT_TITLES = {
    "League of Legends": ("LeagueClient.exe", "RiotClientServices.exe"),
    "VALORANT": ("VALORANT-Win64-Shipping.exe", "RiotClientServices.exe"),
    "Teamfight Tactics": ("LeagueClient.exe", "RiotClientServices.exe"),
    "Legends of Runeterra": ("LoR.exe", "RiotClientServices.exe"),
}


def scan() -> List[Game]:
    games: List[Game] = []
    candidates = []
    for env in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env)
        if base:
            candidates.append(Path(base) / "Riot Games")
    candidates.append(Path(r"C:\Riot Games"))

    checked = set()
    for riot_root in candidates:
        key = str(riot_root).lower()
        if key in checked or not riot_root.is_dir():
            continue
        checked.add(key)
        for folder in sorted(riot_root.iterdir()):
            if not folder.is_dir():
                continue
            title = RIOT_TITLES.get(folder.name)
            if not title:
                continue
            primary = folder / title[0]
            if not primary.exists():
                continue
            client = folder / title[1]
            # Riot games are best started through the Riot client so the
            # right account/region is picked up.
            launch = None
            if client.exists():
                game_code = {
                    "League of Legends": "league_of_legends",
                    "VALORANT": "valorant",
                    "Teamfight Tactics": "teamfight_tactics",
                    "Legends of Runeterra": "lor",
                }.get(folder.name)
                if game_code:
                    launch = f"riotclient://rso-auth?client_id=riot-client&product_id={game_code}&locale=pl"
            games.append(
                Game(
                    id=make_id("riot", folder.name),
                    name=folder.name,
                    platform="riot",
                    install_path=str(folder),
                    executable=str(primary),
                    working_dir=str(folder),
                    launch_uri=launch,
                    source="riot",
                )
            )
    return games
