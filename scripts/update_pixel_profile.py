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
    "bg": "#191724",
    "panel": "#1f1d2e",
    "panel_2": "#26233a",
    "muted": "#6e6a86",
    "text": "#e0def4",
    "gold": "#f6c177",
    "pink": "#eb6f92",
    "rose": "#ebbcba",
    "cyan": "#9ccfd8",
    "blue": "#31748f",
}


LANG_COLORS = {
    "Rust": "#dea584",
    "Python": "#ffd343",
    "JavaScript": "#f7df1e",
    "TypeScript": "#3178c6",
    "Shell": "#89e051",
    "SCSS": "#c6538c",
    "CSS": "#563d7c",
    "Java": "#b07219",
    "GDScript": "#355570",
    "C#": "#178600",
    "HTML": "#e34c26",
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
        rect(0, 242, 960, 78, PALETTE["panel_2"]),
        rect(0, 258, 960, 14, PALETTE["blue"]),
        rect(0, 286, 960, 34, PALETTE["panel"]),
        rect(0, 0, 960, 14, PALETTE["pink"]),
        rect(0, 14, 960, 8, PALETTE["gold"]),
        rect(0, 298, 960, 8, PALETTE["gold"]),
        rect(0, 306, 960, 14, PALETTE["pink"]),
    ]

    for x, y, size, color in [
        (70, 48, 12, "gold"),
        (106, 84, 8, "text"),
        (154, 42, 8, "text"),
        (818, 54, 10, "gold"),
        (876, 92, 8, "text"),
        (736, 34, 6, "text"),
    ]:
        parts.append(rect(x, y, size, size, PALETTE[color]))

    parts += [
        rect(790, 40, 48, 48, PALETTE["gold"]),
        rect(778, 52, 12, 24, PALETTE["gold"]),
        rect(838, 52, 12, 24, PALETTE["gold"]),
        rect(802, 52, 12, 12, PALETTE["bg"]),
        rect(826, 52, 12, 12, PALETTE["bg"]),
        rect(814, 76, 12, 12, PALETTE["bg"]),
        rect(54, 206, 52, 36, "#403d52"),
        rect(118, 174, 64, 68, "#403d52"),
        rect(194, 196, 50, 46, "#403d52"),
        rect(714, 190, 62, 52, "#403d52"),
        rect(790, 160, 58, 82, "#403d52"),
        rect(864, 204, 44, 38, "#403d52"),
        rect(130, 188, 10, 10, PALETTE["cyan"]),
        rect(154, 188, 10, 10, PALETTE["cyan"]),
        rect(802, 174, 10, 10, PALETTE["cyan"]),
        rect(826, 174, 10, 10, PALETTE["cyan"]),
        rect(802, 202, 10, 10, PALETTE["cyan"]),
        rect(826, 202, 10, 10, PALETTE["cyan"]),
        rect(86, 252, 24, 24, PALETTE["pink"]),
        rect(110, 252, 24, 24, PALETTE["gold"]),
        rect(134, 252, 24, 24, PALETTE["pink"]),
        rect(110, 228, 24, 24, PALETTE["gold"]),
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
        rect(246, 50, 468, 152, PALETTE["panel"]),
        rect(258, 62, 444, 128, PALETTE["panel_2"]),
        rect(246, 50, 468, 8, PALETTE["gold"]),
        rect(246, 194, 468, 8, PALETTE["pink"]),
        rect(246, 50, 8, 152, PALETTE["pink"]),
        rect(706, 50, 8, 152, PALETTE["pink"]),
        text("LD000", 480, 108, 60, PALETTE["text"], "middle"),
        text("RUST  GAMES  TOOLS  NOTES", 480, 142, 18, PALETTE["cyan"], "middle", "small"),
        text(f"REPOS {summary['public_repos']}", 332, 174, 16, PALETTE["gold"], "start", "small"),
        text(f"STARS {summary['total_stars']}", 488, 174, 16, PALETTE["gold"], "middle", "small"),
        text(f"FOLLOWERS {summary['followers']}", 682, 174, 16, PALETTE["gold"], "end", "small"),
        rect(312, 214, 336, 38, PALETTE["bg"]),
        rect(324, 224, 312, 18, PALETTE["rose"]),
        text(f"LATEST QUEST: {latest_label}", 480, 240, 17, PALETTE["bg"], "middle", "small"),
        text(f"SYNC {summary['updated']}", 480, 276, 14, PALETTE["text"], "middle", "small"),
        rect(0, 0, 8, 320, PALETTE["pink"]),
        rect(952, 0, 8, 320, PALETTE["pink"]),
    ]
    return svg_shell(
        960,
        320,
        "\n".join(f"  {part}" for part in parts),
        "ld000 pixel game banner",
        "A dynamic retro pixel art profile banner with GitHub counters.",
    )


def generate_status(summary: dict) -> str:
    parts = [
        rect(0, 0, 960, 360, PALETTE["bg"]),
        rect(14, 14, 932, 332, PALETTE["panel"]),
        rect(28, 28, 904, 304, PALETTE["panel_2"]),
        rect(14, 14, 932, 10, PALETTE["pink"]),
        rect(14, 336, 932, 10, PALETTE["gold"]),
        rect(14, 14, 10, 332, PALETTE["gold"]),
        rect(936, 14, 10, 332, PALETTE["pink"]),
        text("[ SCORE BOARD ]", 54, 70, 28, PALETTE["gold"]),
        text("AUTO-GENERATED PIXEL STATUS", 54, 100, 18, PALETTE["cyan"], klass="small"),
    ]

    stat_items = [
        ("REPOS", summary["public_repos"], 54),
        ("STARS", summary["total_stars"], 190),
        ("FOLLOWERS", summary["followers"], 326),
    ]
    for label, value, x in stat_items:
        parts += [
            rect(x, 124, 112, 70, PALETTE["bg"]),
            rect(x + 8, 132, 96, 54, PALETTE["panel"]),
            text(label, x + 56, 154, 16, PALETTE["cyan"], "middle", "small"),
            text(value, x + 56, 178, 24, PALETTE["gold"], "middle"),
        ]

    parts += [
        text("LATEST QUESTS", 54, 228, 20, PALETTE["rose"]),
    ]
    for index, repo in enumerate(summary["latest"][:4]):
        y = 258 + index * 24
        name = truncate(repo.get("name") or "unknown", 24)
        lang = repo.get("language") or "Unknown"
        stars = repo.get("stargazers_count") or 0
        parts += [
            rect(60, y - 14, 12, 12, PALETTE["gold"] if index == 0 else PALETTE["muted"]),
            text(name, 84, y, 17, PALETTE["text"], klass="small"),
            text(f"{lang}  *{stars}", 318, y, 16, PALETTE["cyan"], klass="small"),
        ]

    parts += [text("LANGUAGE MAP", 540, 70, 24, PALETTE["rose"])]
    max_count = max([count for _, count in summary["top_languages"]] or [1])
    for index, (language, count) in enumerate(summary["top_languages"][:6]):
        y = 106 + index * 34
        bar_width = max(18, int(260 * count / max_count))
        color = LANG_COLORS.get(language, PALETTE["cyan"])
        parts += [
            text(truncate(language, 12), 540, y, 16, PALETTE["text"], klass="small"),
            rect(670, y - 15, 270, 18, PALETTE["bg"]),
            rect(674, y - 11, bar_width, 10, color),
            text(count, 920, y, 15, PALETTE["gold"], "end", "small"),
        ]

    parts += [
        rect(540, 290, 360, 32, PALETTE["bg"]),
        text(f"SYNC: {summary['updated']}", 558, 312, 14, PALETTE["gold"], "start", "small"),
    ]

    return svg_shell(
        960,
        360,
        "\n".join(f"  {part}" for part in parts),
        "ld000 pixel status board",
        "A dynamic pixel style status board generated from public GitHub profile data.",
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
