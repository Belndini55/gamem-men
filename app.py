#!/usr/bin/env python3
"""GameMen — menedżer gier dla Windows (jak Lutris na Linuxie).

Uruchomienie:
    python app.py                # skanuje gry i otwiera interfejs w przeglądarce
    python app.py --demo         # tryb demo z przykładową biblioteką
    python app.py --port 8765    # inny port
    python app.py --rescan       # wymuś świeże skanowanie przy starcie

Interfejs: http://127.0.0.1:8765
"""

from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gamem import __version__  # noqa: E402
from gamem.config import Config  # noqa: E402
from gamem.demo import demo_games  # noqa: E402
from gamem.launch import launch, open_folder, uninstall  # noqa: E402
from gamem.models import PLATFORMS  # noqa: E402
from gamem.scanner import scan_all  # noqa: E402

log = logging.getLogger("gamem")

WEB_ROOT = Path(__file__).resolve().parent / "web"


class Library:
    """Thread-safe holder for the current game list."""

    def __init__(self, demo: bool) -> None:
        self.forced_demo = demo
        self.demo = demo
        self.lock = threading.Lock()
        self.games: List[Dict[str, Any]] = []
        self.last_scan: Optional[float] = None
        self.scan_ms: Optional[float] = None
        self.scanning = False

    def rescan(self, config: Config) -> Dict[str, Any]:
        with self.lock:
            self.scanning = True
        started = time.perf_counter()
        if self.forced_demo:
            games = demo_games()
            self.demo = True
        else:
            games = scan_all(config)
            if games:
                self.demo = False
            else:
                # Nothing found (e.g. running off-Windows) -> show demo library
                # so the UI is not a desert, but keep mode honest via flag.
                games = demo_games()
                self.demo = True
        elapsed = (time.perf_counter() - started) * 1000
        with self.lock:
            self.games = [g.to_dict() for g in games]
            self.last_scan = time.time()
            self.scan_ms = elapsed
            self.scanning = False
            return self.state_locked()

    def state_locked(self) -> Dict[str, Any]:
        return {
            "games": self.games,
            "mode": "demo" if self.demo else "live",
            "last_scan": self.last_scan,
            "scan_ms": round(self.scan_ms or 0, 1),
            "scanning": self.scanning,
        }

    def state(self) -> Dict[str, Any]:
        with self.lock:
            return self.state_locked()

    def find(self, game_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            for g in self.games:
                if g["id"] == game_id:
                    return g
        return None


CONFIG = Config()
LIBRARY = Library(demo="--demo" in sys.argv)


class Handler(BaseHTTPRequestHandler):
    server_version = f"GameMen/{__version__}"
    quiet = True

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        if not self.quiet:
            log.info("%s - %s", self.address_string(), fmt % args)

    # ---- helpers ------------------------------------------------------
    def _json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except ValueError:
            return {}

    def _serve_static(self, rel: str) -> None:
        target = (WEB_ROOT / rel).resolve()
        if not str(target).startswith(str(WEB_ROOT.resolve())) or not target.is_file():
            self.send_error(404, "Not found")
            return
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if target.suffix in (".jpg", ".jpeg", ".png", ".svg", ".webp", ".woff2"):
            self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(data)

    # ---- routing ------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/games":
            self._json(LIBRARY.state())
        elif path == "/api/health":
            self._json({"ok": True, "version": __version__, "platform": sys.platform})
        elif path == "/api/config":
            self._json(
                {
                    "favorites": sorted(CONFIG.favorites()),
                    "extra_folders": CONFIG.extra_folders(),
                    "platforms": {k: {"name": v[0], "color": v[1]} for k, v in PLATFORMS.items()},
                }
            )
        elif path == "/" or path == "/index.html":
            self._serve_static("index.html")
        else:
            self._serve_static(path.lstrip("/"))

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        body = self._read_body()
        if path == "/api/scan":
            state = LIBRARY.rescan(CONFIG)
            self._json(state)
        elif path == "/api/launch":
            self._game_action(body, launch, "launch")
        elif path == "/api/folder":
            self._game_action(body, open_folder, "folder")
        elif path == "/api/uninstall":
            self._game_action(body, uninstall, "uninstall")
        elif path == "/api/favorite":
            game_id = str(body.get("id") or "")
            if not game_id:
                self._json({"ok": False, "message": "Brak identyfikatora gry."}, 400)
                return
            state = CONFIG.toggle_favorite(game_id)
            game = LIBRARY.find(game_id)
            if game:
                game["favorite"] = state
            self._json({"ok": True, "favorite": state})
        elif path == "/api/settings":
            folders = body.get("extra_folders")
            if isinstance(folders, list):
                CONFIG.set_extra_folders([str(f) for f in folders])
            self._json({"ok": True, "extra_folders": CONFIG.extra_folders()})
        else:
            self._json({"ok": False, "message": "Nieznane API."}, 404)

    def _game_action(self, body: Dict[str, Any], fn, kind: str) -> None:
        if LIBRARY.demo:
            self._json(
                {
                    "ok": False,
                    "demo": True,
                    "message": "Tryb demo — uruchom GameMen na Windows, aby grać w swoje gry.",
                }
            )
            return
        game_id = str(body.get("id") or "")
        game = LIBRARY.find(game_id)
        if not game:
            self._json({"ok": False, "message": "Nie znaleziono gry."}, 404)
            return
        from gamem.models import Game  # local import to rebuild the object

        obj = Game(
            id=game["id"],
            name=game["name"],
            platform=game["platform"],
            install_path=game.get("install_path"),
            executable=game.get("executable"),
            launch_uri=game.get("launch_uri"),
            uninstall_string=game.get("uninstall_string"),
        )
        ok, message = fn(obj)
        self._json({"ok": ok, "message": message, "action": kind})


def main() -> None:
    parser = argparse.ArgumentParser(description="GameMen — menedżer gier dla Windows")
    parser.add_argument("--host", default="127.0.0.1", help="Adres serwera (domyślnie 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port serwera (domyślnie 8765)")
    parser.add_argument("--demo", action="store_true", help="Włącz tryb demo z przykładowymi grami")
    parser.add_argument("--no-browser", action="store_true", help="Nie otwieraj przeglądarki")
    parser.add_argument("--rescan", action="store_true", help="Wymuś skanowanie przy starcie")
    parser.add_argument("--verbose", action="store_true", help="Więcej logów")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    if args.demo:
        LIBRARY.forced_demo = True
        LIBRARY.demo = True

    print(f"GameMen v{__version__} — skanowanie biblioteki…")
    state = LIBRARY.rescan(CONFIG)
    count = len(state["games"])
    mode = "demo" if state["mode"] == "demo" else "na żywo"
    print(f"Znaleziono gier: {count} (tryb: {mode}, {state['scan_ms']:.0f} ms)")

    # Serve on all interfaces when the user explicitly asked for it.
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host if args.host != '0.0.0.0' else '127.0.0.1'}:{args.port}"
    print(f"Interfejs: {url}")
    print("Naciśnij Ctrl+C aby zakończyć.")

    if not args.no_browser and args.host in ("127.0.0.1", "localhost"):
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nNa razie!")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
