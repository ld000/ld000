#!/usr/bin/env python3
"""Generate local Daily Stamp / Signal Passport PNG assets for ld000."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import struct
import sys
import urllib.error
import urllib.request
import zlib
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


USERNAME = os.environ.get("GITHUB_USERNAME", "ld000")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USER_AGENT = "ld000-signal-passport-generator"

COLORS = {
    "paper": "#f4ead7",
    "ink": "#221b16",
    "muted": "#7b6a58",
    "stamp": "#b8322b",
    "faded": "#d87962",
    "teal": "#2f8f83",
    "pale_teal": "#b8d8ce",
    "white": "#fffaf0",
}

FONT = {
    " ": ["000", "000", "000", "000", "000", "000", "000"],
    ".": ["0", "0", "0", "0", "0", "0", "1"],
    "-": ["000", "000", "000", "111", "000", "000", "000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    ":": ["0", "1", "0", "0", "0", "1", "0"],
    "|": ["1", "1", "1", "1", "1", "1", "1"],
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


@dataclass(frozen=True)
class ProfileSignal:
    username: str
    public_repos: int | str
    stars: int | str
    languages: list[str]
    pulse: str
    pulse_days: list[bool]
    last_sync: str
    fallback: bool = False


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


class Canvas:
    def __init__(self, width: int, height: int, background: str) -> None:
        self.width = width
        self.height = height
        self.pixels = [hex_to_rgb(background)] * (width * height)

    def set(self, x: int, y: int, color: str) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y * self.width + x] = hex_to_rgb(color)

    def rect(self, x: int, y: int, w: int, h: int, color: str) -> None:
        rgb = hex_to_rgb(color)
        for yy in range(max(0, y), min(self.height, y + h)):
            start = yy * self.width + max(0, x)
            end = yy * self.width + min(self.width, x + w)
            self.pixels[start:end] = [rgb] * max(0, end - start)

    def outline_rect(self, x: int, y: int, w: int, h: int, fill: str, border: str, stroke: int = 4) -> None:
        self.rect(x, y, w, h, border)
        self.rect(x + stroke, y + stroke, w - stroke * 2, h - stroke * 2, fill)

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

    def circle(self, cx: int, cy: int, radius: int, fill: str, border: str | None = None, stroke: int = 3) -> None:
        r2 = radius * radius
        inner = max(1, radius - stroke)
        inner2 = inner * inner
        for yy in range(-radius, radius + 1):
            for xx in range(-radius, radius + 1):
                d = xx * xx + yy * yy
                if d <= r2:
                    self.set(cx + xx, cy + yy, fill if border is None or d <= inner2 else border)

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


def fetch_repos(username: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{username}/repos?per_page=100&page={page}&sort=pushed&type=owner"
        batch = fetch_json(url)
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected GitHub repos response")
        if not batch:
            return repos
        repos.extend(repo for repo in batch if isinstance(repo, dict))
        page += 1


def parse_github_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def build_signal(username: str) -> ProfileSignal:
    user = fetch_json(f"https://api.github.com/users/{username}")
    if not isinstance(user, dict):
        raise RuntimeError("Unexpected GitHub user response")

    repos = [repo for repo in fetch_repos(username) if not repo.get("fork")]
    stars = sum(int(repo.get("stargazers_count") or 0) for repo in repos)
    languages = [
        language
        for language, _ in Counter(repo.get("language") for repo in repos if repo.get("language")).most_common(3)
    ]

    now = datetime.now(timezone.utc)
    pushed_dates = {
        pushed.date()
        for pushed in (parse_github_time(repo.get("pushed_at")) for repo in repos)
        if pushed is not None
    }
    pulse_days = [(now.date() - timedelta(days=days)) in pushed_dates for days in range(6, -1, -1)]
    active_days = sum(pulse_days)
    recent_repos = sum(
        1
        for repo in repos
        if (pushed := parse_github_time(repo.get("pushed_at"))) is not None and now - pushed <= timedelta(days=30)
    )
    if active_days >= 3:
        pulse = "ACTIVE"
    elif active_days >= 1 or recent_repos >= 3:
        pulse = "WARM"
    else:
        pulse = "QUIET"

    return ProfileSignal(
        username=username,
        public_repos=user.get("public_repos") or len(repos),
        stars=stars,
        languages=languages or ["--"],
        pulse=pulse,
        pulse_days=pulse_days,
        last_sync=now.strftime("%Y-%m-%d"),
    )


def fallback_signal(username: str) -> ProfileSignal:
    return ProfileSignal(
        username=username,
        public_repos="--",
        stars="--",
        languages=["local"],
        pulse="LOCAL",
        pulse_days=[False] * 7,
        last_sync="LOCAL",
        fallback=True,
    )


def draw_security_lines(c: Canvas, step: int = 38) -> None:
    for x in range(-c.height, c.width, step):
        c.line(x, c.height, x + c.height, 0, COLORS["pale_teal"], 1)
    for x in range(0, c.width, step * 2):
        c.line(x, 0, x + c.height // 2, c.height, COLORS["pale_teal"], 1)


def draw_stamp(c: Canvas, cx: int, cy: int) -> None:
    c.circle(cx, cy, 116, COLORS["paper"], COLORS["stamp"], 8)
    c.circle(cx, cy, 92, COLORS["paper"], COLORS["faded"], 4)
    c.centered_text("CLEARED", cx, cy - 42, COLORS["stamp"], 4)
    c.centered_text("TO BUILD", cx, cy + 2, COLORS["stamp"], 3)
    c.rect(cx - 116, cy + 48, 232, 22, COLORS["stamp"])
    c.centered_text("DAILY STAMP", cx, cy + 54, COLORS["paper"], 2)
    c.line(cx - 86, cy - 70, cx + 86, cy + 70, COLORS["faded"], 3)
    c.line(cx + 86, cy - 70, cx - 86, cy + 70, COLORS["faded"], 3)


def draw_pulse_dots(c: Canvas, x: int, y: int, days: list[bool], size: int = 14) -> None:
    for index, active in enumerate(days):
        fill = COLORS["teal"] if active else COLORS["paper"]
        c.outline_rect(x + index * (size + 10), y, size, size, fill, COLORS["teal"], 3)


def draw_hero(signal: ProfileSignal) -> None:
    c = Canvas(1280, 560, COLORS["paper"])
    draw_security_lines(c)
    c.outline_rect(34, 34, 1212, 492, COLORS["paper"], COLORS["ink"], 5)
    c.outline_rect(62, 62, 1156, 436, COLORS["white"], COLORS["pale_teal"], 3)

    c.text("LD000", 102, 112, COLORS["ink"], 8)
    c.text("SYSTEMS / GAMES", 108, 198, COLORS["muted"], 3)
    c.text("TOOLS / NOTES", 108, 236, COLORS["muted"], 3)
    c.rect(104, 304, 314, 44, COLORS["ink"])
    c.text("SIGNAL PASSPORT", 122, 316, COLORS["paper"], 3)
    c.text("PUBLIC BUILD CLEARANCE", 108, 384, COLORS["muted"], 2)
    c.text(f"ID {signal.username}", 108, 424, COLORS["ink"], 2)

    draw_stamp(c, 640, 278)

    sync_value = signal.last_sync if not signal.fallback else "LOCAL"
    c.text("SYNC", 936, 116, COLORS["muted"], 2)
    c.text(sync_value, 936, 150, COLORS["ink"], 3)
    c.text("PUBLIC SIGNAL", 936, 220, COLORS["muted"], 2)
    c.text(signal.pulse, 936, 254, COLORS["stamp"] if signal.fallback else COLORS["teal"], 5)
    c.text("PULSE", 936, 354, COLORS["muted"], 2)
    draw_pulse_dots(c, 936, 390, signal.pulse_days, 17)
    c.rect(86, 474, 1108, 7, COLORS["ink"])
    c.rect(86, 474, 326, 7, COLORS["stamp"])
    c.rect(412, 474, 456, 7, COLORS["teal"])
    c.save_png(ASSETS / "hero-signal-passport.png")


def draw_receipt_field(c: Canvas, x: int, y: int, label: str, value: object, width: int) -> None:
    c.text(label, x, y, COLORS["muted"], 2)
    c.rect(x, y + 34, width, 58, COLORS["paper"])
    c.outline_rect(x, y + 34, width, 58, COLORS["paper"], COLORS["ink"], 3)
    c.text(value, x + 18, y + 52, COLORS["ink"], 3)


def draw_signal_panel(signal: ProfileSignal) -> None:
    c = Canvas(960, 300, COLORS["paper"])
    draw_security_lines(c, 34)
    c.outline_rect(28, 26, 904, 260, COLORS["white"], COLORS["ink"], 4)
    c.text("PASSPORT SCAN RECEIPT", 58, 52, COLORS["ink"], 3)
    c.text(f"SYNC {signal.last_sync}", 670, 58, COLORS["muted"], 2)
    c.rect(58, 96, 844, 4, COLORS["pale_teal"])

    draw_receipt_field(c, 58, 118, "REPOS", signal.public_repos, 138)
    draw_receipt_field(c, 232, 118, "STARS", signal.stars, 138)
    draw_receipt_field(c, 406, 118, "PULSE", signal.pulse, 178)

    languages = " / ".join(signal.languages[:3])
    c.text("LANG", 58, 218, COLORS["muted"], 2)
    c.outline_rect(58, 242, 520, 32, COLORS["paper"], COLORS["ink"], 3)
    c.text(languages, 76, 252, COLORS["ink"], 2)

    c.text("7D PUSH PULSE", 650, 218, COLORS["muted"], 1)
    draw_pulse_dots(c, 650, 242, signal.pulse_days, 13)
    c.text("OLDEST TO NEWEST", 650, 266, COLORS["muted"], 1)
    c.save_png(ASSETS / "signal-panel.png")


def main() -> int:
    try:
        signal = build_signal(USERNAME)
    except (RuntimeError, urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        print(f"warning: using fallback profile data: {exc}", file=sys.stderr)
        signal = fallback_signal(USERNAME)

    ASSETS.mkdir(parents=True, exist_ok=True)
    draw_hero(signal)
    draw_signal_panel(signal)
    print(f"Generated signal passport PNG assets for {USERNAME}: {signal.pulse} {signal.last_sync}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
