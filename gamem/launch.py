"""Launch helpers — start games via URI scheme or executable."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Optional, Tuple

from .models import Game

log = logging.getLogger("gamem")


def _start(target: str, cwd: Optional[str] = None) -> None:
    if sys.platform == "win32":
        os.startfile(target)  # noqa: S606 - launching games is the point
        return
    # Dev/demo convenience on other platforms
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen([opener, target], cwd=cwd or None)  # noqa: S603


def launch(game: Game) -> Tuple[bool, str]:
    """Start a game. Returns (ok, message)."""
    if game.launch_uri:
        try:
            _start(game.launch_uri, game.working_dir)
            return True, f"Uruchamianie przez {game.platform_name}…"
        except OSError as exc:
            log.warning("launch via uri failed: %s", exc)
    if game.executable and os.path.exists(game.executable):
        try:
            subprocess.Popen(  # noqa: S603
                [game.executable] + ([game.launch_args] if game.launch_args else []),
                cwd=game.working_dir or os.path.dirname(game.executable),
            )
            return True, f"Uruchamianie {game.name}…"
        except OSError as exc:
            return False, f"Nie udało się uruchomić: {exc}"
    return False, "Nie znaleziono pliku wykonywalnego gry."


def open_folder(game: Game) -> Tuple[bool, str]:
    path = game.install_path
    if not path or not os.path.exists(path):
        return False, "Ścieżka instalacji nie istnieje."
    try:
        _start(path)
        return True, "Otwieram folder…"
    except OSError as exc:
        return False, f"Nie udało się otworzyć folderu: {exc}"


def uninstall(game: Game) -> Tuple[bool, str]:
    if not game.uninstall_string:
        return False, "Brak informacji o deinstalatorze."
    try:
        if sys.platform == "win32":
            import winreg  # noqa: F401 - just to make sure it's Windows

            cmd = game.uninstall_string
            if cmd.lower().startswith("msiexec"):
                subprocess.Popen(cmd, shell=True)  # noqa: S602
            else:
                os.startfile(cmd)  # noqa: S606
        else:
            return False, "Deinstalacja działa tylko na Windows."
        return True, "Uruchamiam deinstalator…"
    except OSError as exc:
        return False, f"Nie udało się uruchomić deinstalatora: {exc}"
