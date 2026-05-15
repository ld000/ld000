#!/usr/bin/env python3
"""Generate pixel-style SVG assets for the ld000 profile README."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.8 fallback
    ZoneInfo = None


USERNAME = os.environ.get("GITHUB_USERNAME", "ld000")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USER_AGENT = "ld000-pixel-profile-generator"


PALETTE = {
    "bg": "#071a1a",
    "shadow": "#041010",
    "panel": "#0d2b2e",
    "panel_2": "#12383d",
    "line": "#1f5f5b",
    "muted": "#6b8f89",
    "text": "#f8f5dc",
    "mint": "#6fffd2",
    "cyan": "#46d9ff",
    "gold": "#ffd166",
    "coral": "#ff6b6b",
    "leaf": "#2dd4a7",
}


LANG_COLORS = {
    "Rust": "#ffd166",
    "Python": "#46d9ff",
    "JavaScript": "#f8f5dc",
    "TypeScript": "#46d9ff",
    "Shell": "#6fffd2",
    "SCSS": "#ff6b6b",
    "CSS": "#2dd4a7",
    "Java": "#ffb86b",
    "GDScript": "#6fffd2",
    "C#": "#2dd4a7",
    "HTML": "#ff6b6b",
}


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
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API error {exc.code} for {url}: {detail}") from exc


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
    latest = sorted(
        quest_repos,
        key=lambda repo: parse_time(repo.get("pushed_at")),
        reverse=True,
    )
    language_counts = Counter(
        repo.get("language") for repo in active if repo.get("language")
    )

    return {
        "name": user.get("name") or USERNAME,
        "bio": user.get("bio") or "May the code be with you.",
        "blog": user.get("blog") or "https://ld000.space/",
        "location": user.get("location") or "Beijing, China",
        "public_repos": user.get("public_repos") or len(owned),
        "total_stars": sum(int(repo.get("stargazers_count") or 0) for repo in owned),
        "followers": user.get("followers") or 0,
        "latest": latest[:5],
        "top_languages": language_counts.most_common(6),
        "updated": display_time(),
    }


def rect(x: int, y: int, w: int, h: int, fill: str) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'


def text(
    value: object,
    x: int,
    y: int,
    size: int,
    fill: str,
    anchor: str = "start",
    klass: str = "label",
) -> str:
    return (
        f'<text class="{klass}" x="{x}" y="{y}" text-anchor="{anchor}" '
        f'font-size="{size}" fill="{fill}">{escape(str(value))}</text>'
    )


def truncate(value: object, limit: int) -> str:
    raw = str(value)
    if len(raw) <= limit:
        return raw
    return raw[: max(0, limit - 1)] + "."


def svg_shell(width: int, height: int, body: str, title: str, desc: str) -> str:
    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">{escape(title)}</title>
  <desc id="desc">{escape(desc)}</desc>
  <style>
    .label {{ font-family: "Courier New", monospace; font-weight: 700; }}
    .small {{ font-family: "Courier New", monospace; font-weight: 700; }}
  </style>
{body}
</svg>
'''


def generate_hero(summary: dict) -> str:
    latest_name = summary["latest"][0]["name"] if summary["latest"] else "ready"
    latest_label = truncate(latest_name, 24).upper()

    parts = [
        rect(0, 0, 960, 320, PALETTE["bg"]),
        rect(0, 252, 960, 68, PALETTE["shadow"]),
        rect(0, 268, 960, 12, PALETTE["line"]),
        rect(0, 296, 960, 24, PALETTE["panel"]),
        rect(0, 0, 960, 10, PALETTE["mint"]),
        rect(0, 10, 960, 8, PALETTE["gold"]),
        rect(0, 302, 960, 8, PALETTE["gold"]),
        rect(0, 310, 960, 10, PALETTE["coral"]),
    ]

    for x, y, size, color in [
        (70, 48, 12, "gold"),
        (106, 84, 8, "text"),
        (154, 42, 8, "text"),
        (818, 54, 10, "mint"),
        (876, 92, 8, "text"),
        (736, 34, 6, "text"),
        (902, 42, 6, "cyan"),
        (48, 120, 6, "cyan"),
    ]:
        parts.append(rect(x, y, size, size, PALETTE[color]))

    parts += [
        rect(780, 38, 58, 50, PALETTE["gold"]),
        rect(768, 50, 12, 26, PALETTE["gold"]),
        rect(838, 50, 12, 26, PALETTE["gold"]),
        rect(802, 52, 12, 12, PALETTE["bg"]),
        rect(826, 52, 12, 12, PALETTE["bg"]),
        rect(814, 74, 12, 8, PALETTE["bg"]),
        rect(54, 212, 54, 40, PALETTE["panel_2"]),
        rect(120, 178, 64, 74, PALETTE["panel_2"]),
        rect(196, 202, 52, 50, PALETTE["panel_2"]),
        rect(712, 194, 64, 58, PALETTE["panel_2"]),
        rect(790, 166, 58, 86, PALETTE["panel_2"]),
        rect(864, 210, 44, 42, PALETTE["panel_2"]),
        rect(132, 192, 10, 10, PALETTE["mint"]),
        rect(156, 192, 10, 10, PALETTE["cyan"]),
        rect(802, 180, 10, 10, PALETTE["mint"]),
        rect(826, 180, 10, 10, PALETTE["cyan"]),
        rect(802, 208, 10, 10, PALETTE["cyan"]),
        rect(826, 208, 10, 10, PALETTE["mint"]),
        rect(86, 252, 24, 24, PALETTE["coral"]),
        rect(110, 252, 24, 24, PALETTE["gold"]),
        rect(134, 252, 24, 24, PALETTE["coral"]),
        rect(110, 228, 24, 24, PALETTE["mint"]),
        rect(110, 276, 24, 24, PALETTE["muted"]),
        rect(86, 276, 24, 14, PALETTE["cyan"]),
        rect(134, 276, 24, 14, PALETTE["cyan"]),
        rect(92, 240, 12, 12, PALETTE["bg"]),
        rect(140, 240, 12, 12, PALETTE["bg"]),
    ]

    for x, y in [(648, 236), (690, 212), (732, 236)]:
        parts += [
            rect(x, y, 26, 26, PALETTE["gold"]),
            rect(x + 6, y + 6, 14, 14, PALETTE["bg"]),
        ]

    parts += [
        rect(238, 46, 484, 166, PALETTE["shadow"]),
        rect(246, 38, 468, 166, PALETTE["panel"]),
        rect(258, 50, 444, 142, PALETTE["panel_2"]),
        rect(246, 38, 468, 8, PALETTE["mint"]),
        rect(246, 196, 468, 8, PALETTE["coral"]),
        rect(246, 38, 8, 166, PALETTE["gold"]),
        rect(706, 38, 8, 166, PALETTE["gold"]),
        rect(282, 70, 22, 8, PALETTE["mint"]),
        rect(656, 70, 22, 8, PALETTE["coral"]),
        text("LD000", 480, 108, 60, PALETTE["text"], "middle"),
        text("RUST  GAMES  TOOLS  NOTES", 480, 142, 18, PALETTE["mint"], "middle", "small"),
        text(f"REPOS {summary['public_repos']}", 332, 174, 16, PALETTE["gold"], "start", "small"),
        text(f"STARS {summary['total_stars']}", 488, 174, 16, PALETTE["gold"], "middle", "small"),
        text(f"FOLLOWERS {summary['followers']}", 682, 174, 16, PALETTE["gold"], "end", "small"),
        rect(304, 218, 352, 40, PALETTE["shadow"]),
        rect(316, 228, 328, 18, PALETTE["mint"]),
        text(f"LATEST QUEST: {latest_label}", 480, 240, 17, PALETTE["bg"], "middle", "small"),
        text(f"SYNC {summary['updated']}", 480, 282, 14, PALETTE["text"], "middle", "small"),
        rect(0, 0, 8, 320, PALETTE["mint"]),
        rect(952, 0, 8, 320, PALETTE["coral"]),
    ]
    return svg_shell(
        960,
        320,
        "\n".join(f"  {part}" for part in parts),
        "ld000 pixel profile title screen",
        "A clean pixel arcade profile banner with GitHub counters.",
    )


def generate_status(summary: dict) -> str:
    parts = [
        rect(0, 0, 960, 360, PALETTE["bg"]),
        rect(12, 12, 936, 336, PALETTE["shadow"]),
        rect(22, 22, 916, 316, PALETTE["panel"]),
        rect(36, 36, 888, 288, PALETTE["panel_2"]),
        rect(22, 22, 916, 8, PALETTE["mint"]),
        rect(22, 330, 916, 8, PALETTE["coral"]),
        rect(22, 22, 8, 316, PALETTE["gold"]),
        rect(930, 22, 8, 316, PALETTE["gold"]),
        rect(62, 52, 18, 18, PALETTE["mint"]),
        rect(86, 52, 18, 18, PALETTE["gold"]),
        rect(110, 52, 18, 18, PALETTE["coral"]),
        text("[ SAVE SLOT STATUS ]", 54, 104, 27, PALETTE["gold"]),
        text("AUTO-GENERATED FROM PUBLIC GITHUB DATA", 54, 132, 16, PALETTE["mint"], klass="small"),
    ]

    stat_items = [
        ("REPOS", summary["public_repos"], 54),
        ("STARS", summary["total_stars"], 190),
        ("FOLLOWERS", summary["followers"], 326),
    ]
    for label, value, x in stat_items:
        parts += [
            rect(x, 158, 112, 70, PALETTE["shadow"]),
            rect(x + 8, 166, 96, 54, PALETTE["panel"]),
            rect(x + 8, 166, 96, 6, PALETTE["line"]),
            text(label, x + 56, 188, 15, PALETTE["mint"], "middle", "small"),
            text(value, x + 56, 212, 24, PALETTE["gold"], "middle"),
        ]

    parts += [
        text("LATEST QUESTS", 54, 256, 20, PALETTE["coral"]),
    ]
    for index, repo in enumerate(summary["latest"][:3]):
        y = 282 + index * 20
        name = truncate(repo.get("name") or "unknown", 24)
        lang = repo.get("language") or "Unknown"
        stars = repo.get("stargazers_count") or 0
        parts += [
            rect(60, y - 14, 12, 12, PALETTE["gold"] if index == 0 else PALETTE["muted"]),
            text(name, 84, y, 17, PALETTE["text"], klass="small"),
            text(f"{lang}  *{stars}", 318, y, 16, PALETTE["mint"], klass="small"),
        ]

    parts += [
        rect(512, 54, 396, 236, PALETTE["shadow"]),
        rect(524, 66, 372, 212, PALETTE["panel"]),
        text("LANGUAGE MAP", 548, 104, 24, PALETTE["coral"]),
    ]
    max_count = max([count for _, count in summary["top_languages"]] or [1])
    for index, (language, count) in enumerate(summary["top_languages"][:6]):
        y = 136 + index * 30
        bar_width = max(18, int(200 * count / max_count))
        color = LANG_COLORS.get(language, PALETTE["cyan"])
        parts += [
            text(truncate(language, 12), 548, y, 15, PALETTE["text"], klass="small"),
            rect(674, y - 14, 236, 16, PALETTE["bg"]),
            rect(678, y - 10, bar_width, 8, color),
            text(count, 888, y, 14, PALETTE["gold"], "end", "small"),
        ]

    parts += [
        rect(524, 300, 372, 28, PALETTE["shadow"]),
        rect(536, 308, 348, 12, PALETTE["mint"]),
        text(f"SYNC: {summary['updated']}", 548, 324, 14, PALETTE["gold"], "start", "small"),
    ]

    return svg_shell(
        960,
        360,
        "\n".join(f"  {part}" for part in parts),
        "ld000 pixel status board",
        "A clean pixel style status board generated from public GitHub profile data.",
    )


def main() -> int:
    user = fetch_json(f"https://api.github.com/users/{USERNAME}")
    if not isinstance(user, dict):
        raise RuntimeError("Unexpected GitHub user response")

    repos = fetch_repos()
    summary = summarize(user, repos)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "pixel-hero.svg").write_text(generate_hero(summary), encoding="utf-8")
    (ASSETS / "pixel-status.svg").write_text(generate_status(summary), encoding="utf-8")
    print(f"Generated pixel profile assets for {USERNAME} at {summary['updated']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
