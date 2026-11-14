"""Data models for GameMen."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional

# Platform id -> (display name, brand color)
PLATFORMS = {
    "steam": ("Steam", "#66c0f4"),
    "epic": ("Epic Games", "#ffffff"),
    "gog": ("GOG", "#a86dd6"),
    "xbox": ("Xbox / Game Pass", "#52c41a"),
    "battlenet": ("Battle.net", "#148eff"),
    "ea": ("EA App", "#ff5b4d"),
    "ubisoft": ("Ubisoft Connect", "#2bb3f3"),
    "riot": ("Riot Games", "#d13639"),
    "minecraft": ("Minecraft", "#6bbf3b"),
    "other": ("Inne", "#9aa4b2"),
}


@dataclass
class Game:
    id: str
    name: str
    platform: str
    install_path: Optional[str] = None
    executable: Optional[str] = None
    working_dir: Optional[str] = None
    size_bytes: Optional[int] = None
    install_date: Optional[str] = None  # ISO date string (YYYY-MM-DD)
    launch_uri: Optional[str] = None   # e.g. steam://rungameid/123
    launch_args: Optional[str] = None
    uninstall_string: Optional[str] = None
    cover_url: Optional[str] = None
    favorite: bool = False
    source: str = ""  # which scanner found it (for debugging)

    @property
    def platform_name(self) -> str:
        return PLATFORMS.get(self.platform, (self.platform, ""))[0]

    @property
    def platform_color(self) -> str:
        return PLATFORMS.get(self.platform, ("", "#9aa4b2"))[1]

    @property
    def monogram(self) -> str:
        """Two-letter monogram used for placeholder covers."""
        words = [w for w in self.name.replace(":", " ").split() if w and w[0].isalnum()]
        if not words:
            return "??"
        if len(words) == 1:
            return words[0][:2].upper()
        return (words[0][0] + words[1][0]).upper()

    @property
    def color_hint(self) -> str:
        """Deterministic color pair hint for placeholder covers."""
        digest = hashlib.md5(self.name.encode("utf-8")).hexdigest()
        hue = int(digest[:4], 16) % 360
        return f"hsl({hue}, 45%, 32%)|hsl({(hue + 40) % 360}, 55%, 55%)"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "platform": self.platform,
            "platform_name": self.platform_name,
            "platform_color": self.platform_color,
            "install_path": self.install_path,
            "executable": self.executable,
            "size_bytes": self.size_bytes,
            "install_date": self.install_date,
            "launch_uri": self.launch_uri,
            "has_executable": bool(self.executable),
            "uninstall_string": self.uninstall_string,
            "cover": self.cover_url,
            "favorite": self.favorite,
            "monogram": self.monogram,
            "color_hint": self.color_hint,
        }


def make_id(*parts: str) -> str:
    raw = "|".join(p.strip().lower() for p in parts if p)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
