#!/usr/bin/env python3
"""Generate local supporting pixel-art PNG assets for the ld000 profile README.

The generator intentionally avoids third-party drawing dependencies so GitHub
Actions can refresh the dynamic status board with only Python's standard
library. The static hero image is generated separately and is not overwritten.
"""

from __future__ import annotations

import json
import os
import struct
import sys
import urllib.error
import urllib.request
import zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.8 fallback
    ZoneInfo = None


USERNAME = os.environ.get("GITHUB_USERNAME", "ld000")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USER_AGENT = "ld000-pixel-profile-generator"


COLORS = {
    "void": "#070B12",
    "ink": "#101622",
    "night": "#0B1020",
    "wall": "#18243B",
    "wall_2": "#22314C",
    "wall_3": "#2D4264",
    "line": "#3D4E68",
    "screen": "#64D2FF",
    "screen_dim": "#287A95",
    "cream": "#E9DCC9",
    "paper": "#FFE6A7",
    "gold": "#FFD166",
    "amber": "#B17647",
    "wood": "#8A5A3C",
    "wood_dark": "#5F3B28",
    "rust": "#FF9B71",
    "red": "#FF6B6B",
    "green": "#6BCB77",
    "muted": "#6F7B91",
    "purple": "#9D8CFF",
}

LANG_COLORS = {
    "Rust": COLORS["rust"],
    "Python": COLORS["screen"],
    "JavaScript": COLORS["gold"],
    "TypeScript": COLORS["screen"],
    "Shell": COLORS["cream"],
    "SCSS": "#F28FB3",
    "CSS": COLORS["green"],
    "Java": COLORS["amber"],
    "GDScript": COLORS["screen"],
    "C#": COLORS["green"],
    "HTML": COLORS["rust"],
}

PROJECTS = [
    ("bevy-tetris", "BLOCK STACK", "RUST + BEVY"),
    ("redis-rust", "DATA DUNGEON", "STORAGE NOTES"),
    ("spider", "CRAWLER ROAD", "WEB AUTOMATION"),
    ("blog-hugo", "CAMPFIRE NOTES", "HUGO BLOG"),
]


FONT = {
    " ": ["000", "000", "000", "000", "000", "000", "000"],
    ".": ["0", "0", "0", "0", "0", "0", "1"],
    "-": ["000", "000", "000", "111", "000", "000", "000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    ":": ["0", "1", "0", "0", "0", "1", "0"],
    "*": ["00000", "10101", "01110", "11111", "01110", "10101", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    ">": ["10000", "01000", "00100", "00010", "00100", "01000", "10000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "11100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


class Canvas:
    def __init__(self, width: int, height: int, background: str) -> None:
        self.width = width
        self.height = height
        bg = hex_to_rgb(background)
        self.pixels = [bg] * (width * height)

    def set(self, x: int, y: int, color: str) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y * self.width + x] = hex_to_rgb(color)

    def rect(self, x: int, y: int, w: int, h: int, color: str) -> None:
        for yy in range(max(0, y), min(self.height, y + h)):
            start = yy * self.width + max(0, x)
            end = yy * self.width + min(self.width, x + w)
            self.pixels[start:end] = [hex_to_rgb(color)] * max(0, end - start)

    def frame(self, x: int, y: int, w: int, h: int, fill: str, border: str, shadow: str) -> None:
        self.rect(x + 4, y + 4, w, h, shadow)
        self.rect(x, y, w, h, border)
        self.rect(x + 3, y + 3, w - 6, h - 6, fill)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: str) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def text(self, value: object, x: int, y: int, color: str, scale: int = 1) -> None:
        cursor = x
        for char in str(value).upper():
            glyph = FONT.get(char, FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cursor + gx * scale, y + gy * scale, scale, scale, color)
            cursor += (len(glyph[0]) + 1) * scale

    def text_width(self, value: object, scale: int = 1) -> int:
        width = 0
        for char in str(value).upper():
            glyph = FONT.get(char, FONT[" "])
            width += (len(glyph[0]) + 1) * scale
        return max(0, width - scale)

    def centered_text(self, value: object, cx: int, y: int, color: str, scale: int = 1) -> None:
        self.text(value, cx - self.text_width(value, scale) // 2, y, color, scale)

    def save_png(self, path: Path, scale: int = 1) -> None:
        width = self.width * scale
        height = self.height * scale
        raw = bytearray()
        for y in range(height):
            raw.append(0)
            source_y = y // scale
            for x in range(width):
                raw.extend(self.pixels[source_y * self.width + (x // scale)])
        compressed = zlib.compress(bytes(raw), 9)

        def chunk(kind: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + kind
                + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            )

        payload = b"\x89PNG\r\n\x1a\n"
        payload += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        payload += chunk(b"IDAT", compressed)
        payload += chunk(b"IEND", b"")
        path.write_bytes(payload)


def fetch_json(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&sort=updated&type=owner"
        )
        batch = fetch_json(url)
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected GitHub repos response")
        if not batch:
            return repos
        repos.extend(repo for repo in batch if isinstance(repo, dict))
        page += 1


def parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def display_time() -> str:
    now = datetime.now(timezone.utc)
    if ZoneInfo is not None:
        now = now.astimezone(ZoneInfo("Asia/Shanghai"))
        return now.strftime("%m-%d %H:%M CST")
    return now.strftime("%m-%d %H:%M UTC")


def summarize(user: dict, repos: list[dict]) -> dict:
    owned = [repo for repo in repos if not repo.get("fork")]
    active = [repo for repo in owned if not repo.get("archived")]
    quest_repos = [repo for repo in active if repo.get("name") != USERNAME]
    latest = sorted(quest_repos, key=lambda repo: parse_time(repo.get("pushed_at")), reverse=True)
    languages = Counter(repo.get("language") for repo in active if repo.get("language"))
    return {
        "public_repos": user.get("public_repos") or len(owned),
        "total_stars": sum(int(repo.get("stargazers_count") or 0) for repo in owned),
        "followers": user.get("followers") or 0,
        "latest": latest[:5],
        "top_languages": languages.most_common(6),
        "updated": display_time(),
    }


def fallback_summary() -> dict:
    return {
        "public_repos": 0,
        "total_stars": 0,
        "followers": 0,
        "latest": [{"name": name, "language": label.split()[0], "stargazers_count": 0} for name, _, label in PROJECTS],
        "top_languages": [("Rust", 3), ("JavaScript", 2), ("Python", 2), ("Shell", 1)],
        "updated": display_time(),
    }


def truncate(value: object, limit: int) -> str:
    text = str(value)
    return text if len(text) <= limit else text[: max(0, limit - 1)] + "."


def draw_stars(c: Canvas) -> None:
    for x, y, color in [
        (54, 35, "screen"), (83, 52, "cream"), (118, 29, "screen"), (144, 69, "muted"),
        (509, 36, "screen"), (548, 58, "cream"), (602, 27, "gold"), (620, 82, "screen"),
    ]:
        c.rect(x, y, 2, 2, COLORS[color])


def draw_room_shell(c: Canvas, width: int, height: int) -> None:
    c.rect(0, 0, width, height, COLORS["ink"])
    c.rect(10, 10, width - 20, height - 42, COLORS["wall"])
    c.rect(16, 16, width - 32, height - 54, COLORS["night"])
    draw_stars(c)
    c.rect(0, height - 52, width, 52, COLORS["wood"])
    c.rect(0, height - 34, width, 34, COLORS["wood_dark"])
    c.rect(16, height - 52, width - 32, 4, COLORS["amber"])


def draw_window(c: Canvas, x: int, y: int) -> None:
    c.frame(x, y, 142, 86, COLORS["wall_2"], COLORS["line"], COLORS["void"])
    c.rect(x + 10, y + 10, 122, 66, "#0C1830")
    c.rect(x + 70, y + 10, 2, 66, COLORS["line"])
    c.rect(x + 10, y + 43, 122, 2, COLORS["line"])
    c.rect(x + 102, y + 18, 12, 12, COLORS["cream"])
    c.rect(x + 99, y + 18, 6, 6, "#0C1830")
    for sx, sy in [(20, 18), (34, 54), (61, 25), (117, 51)]:
        c.rect(x + sx, y + sy, 2, 2, COLORS["screen"])
    c.rect(x + 24, y + 58, 18, 12, COLORS["wall_3"])
    c.rect(x + 46, y + 52, 22, 18, COLORS["wall_2"])
    c.rect(x + 74, y + 56, 30, 14, COLORS["wall_3"])
    c.rect(x + 87, y + 39, 22, 6, COLORS["screen_dim"])
    c.rect(x + 94, y + 36, 16, 3, COLORS["screen"])
    c.rect(x + 78, y + 42, 8, 2, COLORS["gold"])
    c.rect(x + 110, y + 42, 10, 2, COLORS["gold"])


def draw_lamp_and_props(c: Canvas, y: int) -> None:
    c.rect(50, y + 18, 60, 8, COLORS["wood_dark"])
    c.rect(62, y + 6, 38, 12, COLORS["rust"])
    c.rect(70, y, 22, 6, COLORS["paper"])
    c.rect(77, y - 28, 4, 28, COLORS["line"])
    c.rect(60, y - 40, 46, 10, COLORS["gold"])
    c.rect(68, y - 36, 30, 4, COLORS["paper"])
    c.rect(118, y + 15, 44, 14, COLORS["wall_3"])
    c.rect(126, y + 19, 17, 3, COLORS["screen"])
    c.rect(238, y + 12, 46, 10, COLORS["void"])
    c.rect(250, y, 24, 14, COLORS["wall_3"])
    c.rect(258, y - 12, 4, 12, COLORS["green"])
    c.rect(251, y - 18, 10, 8, COLORS["green"])
    c.rect(263, y - 18, 10, 8, COLORS["green"])
    c.rect(422, y + 17, 52, 4, COLORS["line"])
    c.rect(480, y + 15, 7, 7, COLORS["line"])
    c.rect(487, y + 21, 36, 4, COLORS["line"])
    c.rect(534, y + 8, 42, 18, COLORS["wall_3"])
    c.rect(542, y + 15, 26, 3, COLORS["screen"])
    c.rect(585, y + 10, 28, 18, COLORS["wood_dark"])
    c.rect(590, y + 3, 18, 7, COLORS["paper"])


def draw_main_terminal(c: Canvas, x: int, y: int) -> None:
    c.frame(x, y, 188, 108, COLORS["wall_2"], COLORS["line"], COLORS["void"])
    c.rect(x + 13, y + 13, 162, 70, COLORS["void"])
    c.rect(x + 19, y + 18, 150, 58, COLORS["screen_dim"])
    c.rect(x + 24, y + 23, 140, 48, COLORS["ink"])
    c.centered_text("LD000", x + 94, y + 35, COLORS["cream"], 4)
    c.centered_text("RUST / GAMES / TOOLS / NOTES", x + 94, y + 65, COLORS["screen"], 1)
    c.rect(x + 43, y + 82, 68, 11, COLORS["void"])
    c.rect(x + 22, y + 94, 124, 8, COLORS["wall_3"])
    c.rect(x + 28, y + 97, 112, 2, COLORS["muted"])


def draw_wall_board(c: Canvas, x: int, y: int, summary: dict) -> None:
    c.frame(x, y, 140, 88, COLORS["wall_2"], COLORS["line"], COLORS["void"])
    for nx, ny, color in [(12, 11, "paper"), (51, 11, "gold"), (92, 11, "paper")]:
        c.rect(x + nx, y + ny, 30, 22, COLORS[color])
        c.rect(x + nx + 6, y + ny + 8, 18, 2, COLORS["line"])
    c.text("STATUS", x + 22, y + 43, COLORS["cream"], 1)
    c.text(f"REPOS {summary['public_repos']}", x + 22, y + 57, COLORS["screen"], 1)
    c.text(f"STARS {summary['total_stars']}", x + 22, y + 69, COLORS["screen"], 1)
    c.text(f"FOL {summary['followers']}", x + 90, y + 69, COLORS["screen"], 1)
    c.rect(x + 116, y + 46, 8, 26, COLORS["line"])
    c.rect(x + 111, y + 72, 18, 7, COLORS["gold"])


def generate_hero(summary: dict) -> None:
    c = Canvas(640, 260, COLORS["ink"])
    draw_room_shell(c, 640, 260)
    draw_window(c, 40, 30)
    draw_main_terminal(c, 224, 35)
    draw_wall_board(c, 452, 35, summary)
    draw_lamp_and_props(c, 177)
    latest = truncate((summary["latest"][0].get("name") if summary["latest"] else "ready"), 18)
    c.frame(210, 207, 220, 28, COLORS["wall_2"], COLORS["line"], COLORS["void"])
    c.rect(224, 217, 7, 7, COLORS["gold"])
    c.centered_text(f"QUEST: {latest}", 320, 216, COLORS["cream"], 1)
    c.text(f"SYNC {summary['updated']}", 496, 237, COLORS["paper"], 1)
    c.save_png(ASSETS / "hero-room.png", scale=2)


def generate_status(summary: dict) -> None:
    c = Canvas(960, 360, COLORS["ink"])
    draw_room_shell(c, 960, 360)
    c.rect(52, 52, 856, 210, "#142039")
    c.text("LD000 STATUS TERMINAL", 86, 76, COLORS["cream"], 2)
    for label, value, x in [
        ("REPOS", summary["public_repos"], 86),
        ("STARS", summary["total_stars"], 228),
        ("FOLLOWERS", summary["followers"], 370),
    ]:
        c.frame(x, 104, 112, 58, COLORS["wall_2"], COLORS["line"], COLORS["void"])
        c.text(label, x + 14, 120, COLORS["screen"], 1)
        c.text(value, x + 14, 138, COLORS["cream"], 2)

    c.frame(86, 180, 394, 106, COLORS["wall_2"], COLORS["line"], COLORS["void"])
    c.text("LATEST", 108, 202, COLORS["cream"], 2)
    for index, repo in enumerate(summary["latest"][:4]):
        y = 229 + index * 13
        name = truncate(repo.get("name") or "unknown", 18)
        lang = truncate(repo.get("language") or "Unknown", 8)
        stars = repo.get("stargazers_count") or 0
        c.text(">", 110, y, COLORS["gold"] if index == 0 else COLORS["screen"], 1)
        c.text(name, 126, y, COLORS["cream"], 1)
        c.text(f"{lang} *{stars}", 322, y, COLORS["screen"], 1)

    c.frame(548, 96, 300, 184, COLORS["wall_2"], COLORS["line"], COLORS["void"])
    c.text("TOP LANGUAGE", 576, 120, COLORS["cream"], 2)
    max_count = max([count for _, count in summary["top_languages"]] or [1])
    for index, (language, count) in enumerate(summary["top_languages"][:6]):
        y = 155 + index * 18
        width = max(18, int(138 * count / max_count))
        c.text(truncate(language, 10), 580, y, COLORS["cream"], 1)
        c.rect(680, y - 4, 148, 8, COLORS["void"])
        c.rect(684, y - 2, width, 4, LANG_COLORS.get(language, COLORS["screen"]))
        c.text(count, 838, y, COLORS["paper"], 1)
    c.rect(612, 292, 82, 22, COLORS["void"])
    c.rect(628, 272, 34, 22, COLORS["screen_dim"])
    c.rect(642, 258, 6, 14, COLORS["green"])
    c.rect(628, 251, 18, 11, COLORS["green"])
    c.rect(650, 251, 18, 11, COLORS["green"])
    c.text(f"SYNC {summary['updated']}", 686, 300, COLORS["paper"], 1)
    c.save_png(ASSETS / "status-board.png")


def draw_icon(c: Canvas, name: str, x: int, y: int) -> None:
    if name == "Rust":
        c.rect(x + 10, y + 10, 28, 28, COLORS["rust"])
        c.rect(x + 16, y + 16, 16, 16, COLORS["ink"])
        c.rect(x + 21, y + 21, 6, 6, COLORS["rust"])
    elif name == "Game":
        c.rect(x + 8, y + 18, 32, 18, COLORS["screen_dim"])
        c.rect(x + 13, y + 23, 8, 4, COLORS["cream"])
        c.rect(x + 15, y + 21, 4, 8, COLORS["cream"])
        c.rect(x + 31, y + 22, 4, 4, COLORS["gold"])
        c.rect(x + 35, y + 28, 4, 4, COLORS["red"])
    elif name == "Web":
        c.rect(x + 9, y + 10, 31, 28, COLORS["screen"])
        c.rect(x + 13, y + 17, 23, 17, COLORS["ink"])
        c.rect(x + 16, y + 20, 8, 2, COLORS["gold"])
        c.rect(x + 16, y + 26, 16, 2, COLORS["cream"])
    elif name == "Auto":
        c.rect(x + 12, y + 12, 24, 24, COLORS["purple"])
        c.rect(x + 18, y + 18, 12, 12, COLORS["ink"])
        c.rect(x + 22, y + 7, 4, 8, COLORS["gold"])
        c.rect(x + 7, y + 22, 8, 4, COLORS["gold"])
        c.rect(x + 33, y + 22, 8, 4, COLORS["gold"])
    else:
        c.rect(x + 12, y + 8, 24, 32, COLORS["paper"])
        c.rect(x + 17, y + 17, 14, 2, COLORS["line"])
        c.rect(x + 17, y + 24, 14, 2, COLORS["line"])
        c.rect(x + 17, y + 31, 10, 2, COLORS["line"])


def generate_inventory() -> None:
    c = Canvas(960, 220, COLORS["ink"])
    c.rect(0, 0, 960, 220, COLORS["night"])
    c.text("INVENTORY", 44, 36, COLORS["cream"], 2)
    items = [("Rust", "SYSTEMS"), ("Game", "GAME DEV"), ("Web", "WEB"), ("Auto", "AUTOMATION"), ("Notes", "NOTES")]
    for index, (name, label) in enumerate(items):
        x = 52 + index * 174
        c.frame(x, 76, 132, 92, COLORS["wall_2"], COLORS["line"], COLORS["void"])
        draw_icon(c, name, x + 42, 92)
        c.centered_text(name, x + 66, 134, COLORS["cream"], 1)
        c.centered_text(label, x + 66, 150, COLORS["screen"], 1)
    c.rect(44, 186, 872, 4, COLORS["line"])
    c.rect(44, 186, 270, 4, COLORS["gold"])
    c.save_png(ASSETS / "inventory.png")


def generate_project_cards() -> None:
    for index, (repo, title, subtitle) in enumerate(PROJECTS):
        c = Canvas(640, 180, COLORS["ink"])
        c.rect(0, 0, 640, 180, COLORS["night"])
        c.frame(26, 22, 588, 126, COLORS["wall_2"], COLORS["line"], COLORS["void"])
        if index % 2 == 0:
            c.rect(58, 54, 100, 64, COLORS["wood_dark"])
            c.rect(72, 40, 72, 24, COLORS["gold"])
            c.rect(80, 72, 54, 32, COLORS["ink"])
            c.rect(92, 84, 30, 6, COLORS["screen"])
        else:
            c.rect(64, 42, 96, 86, COLORS["wall_3"])
            c.rect(76, 54, 72, 28, COLORS["ink"])
            c.rect(92, 92, 40, 24, COLORS["void"])
            c.rect(88, 60, 44, 6, COLORS["screen"])
        c.text(f"0{index + 1}", 200, 52, COLORS["gold"], 2)
        c.text(title, 250, 50, COLORS["cream"], 2)
        c.text(subtitle, 252, 90, COLORS["screen"], 1)
        c.text(repo, 252, 112, COLORS["paper"], 1)
        c.rect(74, 140, 496, 4, COLORS["line"])
        c.rect(74, 140, 110 + index * 74, 4, COLORS["gold"])
        c.save_png(ASSETS / f"project-{repo}.png")


def main() -> int:
    try:
        user = fetch_json(f"https://api.github.com/users/{USERNAME}")
        if not isinstance(user, dict):
            raise RuntimeError("Unexpected GitHub user response")
        summary = summarize(user, fetch_repos())
    except (RuntimeError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"warning: using fallback profile data: {exc}", file=sys.stderr)
        summary = fallback_summary()

    ASSETS.mkdir(parents=True, exist_ok=True)
    generate_status(summary)
    generate_inventory()
    generate_project_cards()
    print(f"Generated supporting PNG profile assets for {USERNAME} at {summary['updated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
