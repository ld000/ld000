#!/usr/bin/env python3
"""Generate local toy-packaging PNG assets for the ld000 profile README.

The generator intentionally avoids third-party drawing dependencies so GitHub
Actions can refresh the dynamic profile panels with only Python's standard
library.
"""

from __future__ import annotations

import json
import os
import struct
import sys
import urllib.error
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.8 fallback
    ZoneInfo = None


USERNAME = os.environ.get("GITHUB_USERNAME", "ld000")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USER_AGENT = "ld000-playable-systems-generator"

COLORS = {
    "paper": "#F7F1DF",
    "ink": "#171717",
    "cream": "#FFF8E7",
    "shadow": "#D8CDB5",
    "red": "#FF4D3D",
    "acid": "#D8FF4F",
    "cyan": "#00CFC8",
    "purple": "#A78BFA",
    "rust": "#D96C2C",
    "yellow": "#FFD166",
    "muted": "#5F5A50",
    "white": "#FFFFFF",
}

PROJECTS = {
    "bevy-tetris": {
        "number": "01",
        "language": "Rust",
        "line": "A RUST BEVY GAME PROJECT",
        "accent": "red",
    },
    "redis-rust": {
        "number": "02",
        "language": "Rust",
        "line": "A RUST STORAGE SYSTEMS PROJECT",
        "accent": "rust",
    },
    "spider": {
        "number": "03",
        "language": "Python",
        "line": "A WEB AUTOMATION PROJECT",
        "accent": "cyan",
    },
    "blog-hugo": {
        "number": "04",
        "language": "HTML",
        "line": "A PUBLIC NOTES AND HUGO BLOG PROJECT",
        "accent": "purple",
    },
}

GENERATED_ASSETS = [
    "hero-playable-systems.png",
    "build-modes.png",
    *[f"project-{repo}.png" for repo in PROJECTS],
]

FONT = {
    " ": ["000", "000", "000", "000", "000", "000", "000"],
    ".": ["0", "0", "0", "0", "0", "0", "1"],
    "-": ["000", "000", "000", "111", "000", "000", "000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    ":": ["0", "1", "0", "0", "0", "1", "0"],
    "*": ["00000", "10101", "01110", "11111", "01110", "10101", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "|": ["1", "1", "1", "1", "1", "1", "1"],
    "#": ["01010", "11111", "01010", "01010", "11111", "01010", "00000"],
    "@": ["01110", "10001", "10111", "10101", "10111", "10000", "01111"],
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

    def outline_rect(self, x: int, y: int, w: int, h: int, fill: str, border: str, stroke: int = 5) -> None:
        self.rect(x, y, w, h, border)
        self.rect(x + stroke, y + stroke, w - stroke * 2, h - stroke * 2, fill)

    def shadow_rect(self, x: int, y: int, w: int, h: int, fill: str, stroke: int = 5) -> None:
        self.rect(x + 8, y + 8, w, h, COLORS["shadow"])
        self.outline_rect(x, y, w, h, fill, COLORS["ink"], stroke)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: str, thickness: int = 1) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - thickness // 2, y0 - thickness // 2, thickness, thickness, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx: int, cy: int, radius: int, fill: str, border: str, stroke: int = 4) -> None:
        r2 = radius * radius
        inner = max(1, radius - stroke)
        inner2 = inner * inner
        for yy in range(-radius, radius + 1):
            for xx in range(-radius, radius + 1):
                d = xx * xx + yy * yy
                if d <= r2:
                    self.set(cx + xx, cy + yy, fill if d <= inner2 else border)

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

    def save_png(self, path: Path) -> None:
        raw = bytearray()
        for y in range(self.height):
            raw.append(0)
            for x in range(self.width):
                raw.extend(self.pixels[y * self.width + x])
        compressed = zlib.compress(bytes(raw), 9)

        def chunk(kind: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + kind
                + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            )

        payload = b"\x89PNG\r\n\x1a\n"
        payload += chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0))
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


def updated_stamp(value: str | None) -> str:
    parsed = parse_time(value)
    if parsed == datetime.min.replace(tzinfo=timezone.utc):
        return "local"
    return parsed.strftime("%m-%d")


def display_time() -> str:
    now = datetime.now(timezone.utc)
    if ZoneInfo is not None:
        now = now.astimezone(ZoneInfo("Asia/Shanghai"))
    return now.strftime("%m-%d")


def summarize(user: dict, repos: list[dict]) -> dict:
    owned = [repo for repo in repos if not repo.get("fork")]
    active = [repo for repo in owned if not repo.get("archived")]
    latest = sorted(
        [repo for repo in active if repo.get("name") != USERNAME],
        key=lambda repo: parse_time(repo.get("pushed_at")),
        reverse=True,
    )
    by_name = {repo.get("name"): repo for repo in owned}
    projects: dict[str, dict[str, object]] = {}
    for name, meta in PROJECTS.items():
        repo = by_name.get(name, {})
        projects[name] = {
            "language": repo.get("language") or meta["language"],
            "stars": repo.get("stargazers_count") if repo else "--",
            "updated_short": updated_stamp(repo.get("pushed_at")) if repo else "local",
        }
    return {
        "public_repos": user.get("public_repos") or len(owned) or "--",
        "total_stars": sum(int(repo.get("stargazers_count") or 0) for repo in owned),
        "latest": latest[:5] or [{"name": "workbench"}],
        "updated": display_time(),
        "projects": projects,
    }


def fallback_summary() -> dict:
    return {
        "public_repos": "--",
        "total_stars": "--",
        "latest": [{"name": "workbench"}],
        "updated": "local build",
        "projects": {
            name: {
                "language": meta["language"],
                "stars": "--",
                "updated_short": "local",
            }
            for name, meta in PROJECTS.items()
        },
    }


def truncate(value: object, limit: int) -> str:
    text = str(value)
    return text if len(text) <= limit else text[: max(0, limit - 1)] + "."


def decorate_background(c: Canvas) -> None:
    c.rect(0, 0, c.width, c.height, COLORS["paper"])
    for y in range(10, c.height, 18):
        for x in range((y // 18) % 2 * 9, c.width, 18):
            c.rect(x, y, 2, 2, COLORS["shadow"])
    for x in range(0, c.width, 80):
        c.line(x, 0, x + 120, c.height, COLORS["cream"], 2)


def punch_holes(c: Canvas, x: int, y: int, w: int) -> None:
    c.circle(x + 28, y + 24, 11, COLORS["paper"], COLORS["ink"], 4)
    c.circle(x + w - 28, y + 24, 11, COLORS["paper"], COLORS["ink"], 4)


def sticker(c: Canvas, x: int, y: int, w: int, h: int, label: str, value: object, fill: str) -> None:
    c.rect(x + 5, y + 5, w, h, COLORS["shadow"])
    c.outline_rect(x, y, w, h, fill, COLORS["ink"], 5)
    c.text(label, x + 16, y + 16, COLORS["ink"], 2)
    c.text(truncate(value, 15), x + 18, y + 48, COLORS["ink"], 3)
    c.rect(x + 16, y + h - 18, w - 32, 5, COLORS["ink"])


def draw_code_block(c: Canvas, x: int, y: int) -> None:
    c.shadow_rect(x, y, 156, 110, COLORS["cream"])
    c.text("CODE", x + 20, y + 18, COLORS["ink"], 2)
    for index, width in enumerate([86, 112, 68, 124]):
        yy = y + 52 + index * 13
        c.rect(x + 22, yy, width, 5, [COLORS["red"], COLORS["cyan"], COLORS["purple"], COLORS["rust"]][index])


def draw_gear_loop(c: Canvas, x: int, y: int) -> None:
    c.circle(x + 62, y + 58, 50, COLORS["yellow"], COLORS["ink"], 7)
    for dx, dy in [(55, 0), (-55, 0), (0, 55), (0, -55), (39, 39), (-39, -39)]:
        c.rect(x + 58 + dx, y + 54 + dy, 10, 10, COLORS["ink"])
    c.circle(x + 62, y + 58, 25, COLORS["paper"], COLORS["ink"], 6)
    c.text("LOOP", x + 33, y + 52, COLORS["ink"], 2)


def draw_tool_note(c: Canvas, x: int, y: int) -> None:
    c.shadow_rect(x, y, 154, 112, COLORS["cream"])
    c.rect(x + 24, y + 28, 58, 18, COLORS["cyan"])
    c.rect(x + 42, y + 46, 20, 45, COLORS["ink"])
    c.rect(x + 90, y + 25, 40, 58, COLORS["yellow"])
    c.rect(x + 98, y + 38, 22, 4, COLORS["ink"])
    c.rect(x + 98, y + 51, 22, 4, COLORS["ink"])
    c.text("NOTE", x + 92, y + 92, COLORS["ink"], 1)


def draw_button(c: Canvas, x: int, y: int, label: str, fill: str) -> None:
    c.rect(x + 7, y + 7, 142, 58, COLORS["shadow"])
    c.outline_rect(x, y, 142, 58, fill, COLORS["ink"], 6)
    c.centered_text(label, x + 71, y + 20, COLORS["ink"], 3)


def generate_hero(summary: dict) -> None:
    c = Canvas(1280, 560, COLORS["paper"])
    decorate_background(c)
    c.shadow_rect(34, 28, 1212, 486, COLORS["cream"], 7)
    punch_holes(c, 34, 28, 1212)

    sticker(c, 82, 102, 250, 92, "REPOS", summary["public_repos"], COLORS["acid"])
    sticker(c, 96, 218, 250, 92, "STARS", summary["total_stars"], COLORS["yellow"])
    latest = truncate(summary["latest"][0].get("name", "workbench"), 15)
    sticker(c, 78, 334, 286, 96, "LATEST", latest, COLORS["cyan"])

    c.text("LD000", 490, 70, COLORS["ink"], 4)
    c.text("OPEN COVER MACHINE", 492, 118, COLORS["muted"], 2)
    draw_code_block(c, 426, 188)
    draw_gear_loop(c, 626, 184)
    draw_tool_note(c, 824, 187)
    c.line(583, 244, 620, 244, COLORS["ink"], 5)
    c.line(757, 244, 814, 244, COLORS["ink"], 5)
    c.rect(607, 232, 16, 24, COLORS["ink"])
    c.rect(802, 232, 16, 24, COLORS["ink"])

    draw_button(c, 1054, 130, "RUN", COLORS["red"])
    draw_button(c, 1040, 232, "FEEL", COLORS["purple"])
    draw_button(c, 1024, 334, "USEFUL", COLORS["acid"])
    c.text(f"SYNC {summary['updated']}", 1020, 468, COLORS["ink"], 2)
    c.rect(64, 492, 1136, 8, COLORS["ink"])
    c.rect(64, 492, 420, 8, COLORS["red"])
    c.rect(484, 492, 320, 8, COLORS["cyan"])
    c.rect(804, 492, 396, 8, COLORS["yellow"])
    c.save_png(ASSETS / "hero-playable-systems.png")


def draw_mode_icon(c: Canvas, x: int, y: int, mode: str) -> None:
    if mode == "run":
        for row in range(3):
            c.rect(x + row * 18, y + row * 14, 72 - row * 18, 12, COLORS["cyan"])
            c.outline_rect(x + row * 18, y + row * 14, 72 - row * 18, 12, COLORS["cyan"], COLORS["ink"], 3)
    elif mode == "feel":
        c.circle(x + 38, y + 32, 33, COLORS["purple"], COLORS["ink"], 5)
        c.circle(x + 38, y + 32, 12, COLORS["paper"], COLORS["ink"], 4)
        c.rect(x + 25, y + 4, 26, 12, COLORS["red"])
        c.rect(x + 25, y + 49, 26, 12, COLORS["acid"])
    else:
        c.rect(x + 15, y + 8, 70, 30, COLORS["yellow"])
        c.rect(x + 8, y + 30, 28, 46, COLORS["ink"])
        c.rect(x + 38, y + 39, 38, 12, COLORS["cyan"])


def generate_build_modes() -> None:
    c = Canvas(960, 320, COLORS["paper"])
    decorate_background(c)
    panels = [
        (38, "MAKE IT RUN", "SYSTEMS THAT HOLD TOGETHER", "run", "acid"),
        (337, "MAKE IT FEEL", "LOOPS THAT FEEL ALIVE", "feel", "purple"),
        (636, "MAKE IT USEFUL", "TOOLS WITH A HANDLE", "useful", "yellow"),
    ]
    for x, title, subtitle, mode, color in panels:
        c.shadow_rect(x, 46, 286, 220, COLORS["cream"], 6)
        c.rect(x + 16, 68, 254, 36, COLORS[color])
        c.text(title, x + 30, 78, COLORS["ink"], 2)
        draw_mode_icon(c, x + 100, 126, mode)
        c.centered_text(subtitle, x + 143, 224, COLORS["ink"], 1)
        c.rect(x + 24, 246, 238, 6, COLORS["ink"])
    c.save_png(ASSETS / "build-modes.png")


def project_art(c: Canvas, repo: str, x: int, y: int, accent: str) -> None:
    if repo == "bevy-tetris":
        blocks = [(0, 0, "red"), (22, 0, "yellow"), (44, 0, "cyan"), (22, 22, "purple"), (44, 22, "acid")]
        for dx, dy, color in blocks:
            c.outline_rect(x + dx, y + dy, 22, 22, COLORS[color], COLORS["ink"], 3)
        c.rect(x + 88, y + 6, 72, 66, COLORS["ink"])
        c.rect(x + 96, y + 14, 56, 50, COLORS["cream"])
        c.rect(x + 106, y + 28, 36, 8, COLORS["red"])
    elif repo == "redis-rust":
        for index in range(3):
            c.outline_rect(x + index * 34, y + index * 18, 112, 24, COLORS["rust"], COLORS["ink"], 4)
        c.circle(x + 166, y + 48, 28, COLORS["yellow"], COLORS["ink"], 5)
        c.rect(x + 152, y + 35, 28, 8, COLORS["ink"])
        c.rect(x + 152, y + 51, 28, 8, COLORS["ink"])
    elif repo == "spider":
        c.circle(x + 78, y + 42, 32, COLORS["cyan"], COLORS["ink"], 5)
        for dx, dy in [(-60, -28), (-62, 12), (62, -28), (64, 12)]:
            c.line(x + 78, y + 42, x + 78 + dx, y + 42 + dy, COLORS["ink"], 5)
        c.rect(x + 130, y + 14, 70, 60, COLORS["cream"])
        c.rect(x + 142, y + 28, 44, 6, COLORS["red"])
        c.rect(x + 142, y + 44, 30, 6, COLORS["purple"])
    else:
        c.outline_rect(x + 12, y + 4, 96, 76, COLORS["yellow"], COLORS["ink"], 5)
        c.rect(x + 28, y + 24, 62, 5, COLORS["ink"])
        c.rect(x + 28, y + 40, 48, 5, COLORS["ink"])
        c.rect(x + 130, y + 12, 64, 58, COLORS[accent])
        c.rect(x + 145, y + 26, 34, 6, COLORS["ink"])
        c.rect(x + 145, y + 42, 34, 6, COLORS["ink"])


def generate_project_cards(summary: dict) -> None:
    for repo, meta in PROJECTS.items():
        c = Canvas(640, 220, COLORS["paper"])
        decorate_background(c)
        c.shadow_rect(24, 22, 592, 166, COLORS["cream"], 6)
        punch_holes(c, 24, 22, 592)
        c.circle(84, 78, 32, COLORS[meta["accent"]], COLORS["ink"], 5)
        c.centered_text(meta["number"], 84, 66, COLORS["ink"], 2)
        c.rect(136, 50, 246, 42, COLORS[meta["accent"]])
        c.text(repo, 154, 62, COLORS["ink"], 2)
        c.text(meta["line"], 154, 106, COLORS["muted"], 1)
        project_art(c, repo, 398, 68, meta["accent"])

        telemetry = summary["projects"][repo]
        c.rect(56, 162, 528, 34, COLORS["ink"])
        c.text(f"LANG {telemetry['language']}", 72, 174, COLORS["cream"], 1)
        c.text(f"STARS {telemetry['stars']}", 254, 174, COLORS["cream"], 1)
        c.text(f"UPDATED {telemetry['updated_short']}", 410, 174, COLORS["cream"], 1)
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
    generate_hero(summary)
    generate_build_modes()
    generate_project_cards(summary)
    print(f"Generated playable systems PNG profile assets for {USERNAME} at {summary['updated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
