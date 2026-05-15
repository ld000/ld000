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
    "ink": "#15131A",
    "shadow": "#0D0B12",
    "panel": "#272034",
    "panel_2": "#32283F",
    "panel_3": "#3B3149",
    "text": "#F2D6A2",
    "screen": "#8FD6C2",
    "screen_dim": "#467E72",
    "accent": "#F28F6B",
    "accent_dim": "#8E4F4C",
    "muted": "#6E5A7E",
    "cream_dim": "#BFA77E",
    "desk": "#211A25",
    "line": "#51445E",
}


LANG_COLORS = {
    "Rust": "#F28F6B",
    "Python": "#8FD6C2",
    "JavaScript": "#F2D6A2",
    "TypeScript": "#8FD6C2",
    "Shell": "#BFA77E",
    "SCSS": "#D87872",
    "CSS": "#9EC89A",
    "Java": "#D99B64",
    "GDScript": "#8FD6C2",
    "C#": "#9EC89A",
    "HTML": "#F28F6B",
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


def pixel_frame(
    x: int,
    y: int,
    w: int,
    h: int,
    fill: str,
    border: str,
    shade: str,
    cap: str | None = None,
) -> list[str]:
    parts = [
        rect(x + 8, y + 8, w, h, shade),
        rect(x, y, w, h, border),
        rect(x + 6, y + 6, w - 12, h - 12, fill),
    ]
    if cap is not None:
        parts.append(rect(x + 6, y + 6, w - 12, 8, cap))
    return parts


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
    latest_label = truncate(latest_name, 20).upper()

    parts = [
        rect(0, 0, 960, 320, PALETTE["ink"]),
        rect(32, 32, 896, 256, PALETTE["panel"]),
        rect(40, 40, 880, 240, PALETTE["ink"]),
        rect(0, 244, 960, 76, PALETTE["desk"]),
        rect(32, 244, 896, 8, PALETTE["line"]),
        rect(112, 256, 736, 16, PALETTE["shadow"]),
        rect(352, 224, 256, 20, PALETTE["shadow"]),
    ]

    parts += pixel_frame(296, 52, 368, 188, PALETTE["panel_2"], PALETTE["line"], PALETTE["shadow"])
    parts += [
        rect(320, 76, 320, 124, PALETTE["shadow"]),
        rect(328, 84, 304, 108, PALETTE["panel"]),
        rect(336, 92, 288, 92, PALETTE["screen_dim"]),
        rect(344, 100, 272, 76, PALETTE["ink"]),
        text("LD000", 480, 130, 52, PALETTE["text"], "middle"),
        text("RUST / GAMES / TOOLS / NOTES", 480, 160, 16, PALETTE["screen"], "middle", "small"),
        rect(360, 176, 72, 4, PALETTE["accent"]),
        rect(444, 176, 88, 4, PALETTE["screen"]),
        rect(544, 176, 56, 4, PALETTE["cream_dim"]),
        rect(424, 204, 112, 16, PALETTE["shadow"]),
        rect(384, 228, 192, 12, PALETTE["panel_3"]),
        rect(392, 232, 176, 4, PALETTE["muted"]),
    ]

    parts += [
        rect(96, 192, 120, 12, PALETTE["line"]),
        rect(112, 176, 88, 16, PALETTE["accent"]),
        rect(124, 160, 64, 16, PALETTE["text"]),
        rect(136, 144, 40, 16, PALETTE["muted"]),
        rect(160, 92, 12, 52, PALETTE["line"]),
        rect(124, 76, 72, 20, PALETTE["accent"]),
        rect(132, 84, 56, 8, PALETTE["text"]),
        rect(192, 252, 120, 24, PALETTE["shadow"]),
        rect(204, 236, 96, 16, PALETTE["panel_3"]),
        rect(212, 240, 32, 4, PALETTE["screen"]),
        rect(252, 240, 32, 4, PALETTE["cream_dim"]),
        rect(724, 224, 92, 40, PALETTE["shadow"]),
        rect(736, 204, 68, 20, PALETTE["panel_3"]),
        rect(748, 212, 44, 4, PALETTE["screen"]),
        rect(824, 252, 44, 24, PALETTE["accent_dim"]),
        rect(832, 240, 28, 12, PALETTE["text"]),
    ]

    parts += pixel_frame(696, 64, 176, 128, PALETTE["panel_2"], PALETTE["line"], PALETTE["shadow"])
    parts += [
        text("STATUS", 724, 96, 18, PALETTE["text"], klass="small"),
        text(f"REPOS {summary['public_repos']}", 724, 124, 15, PALETTE["screen"], klass="small"),
        text(f"STARS {summary['total_stars']}", 724, 148, 15, PALETTE["screen"], klass="small"),
        text(f"FOLLOWERS {summary['followers']}", 724, 172, 15, PALETTE["screen"], klass="small"),
    ]

    parts += pixel_frame(320, 260, 320, 36, PALETTE["panel_2"], PALETTE["line"], PALETTE["shadow"])
    parts += [
        text(f"QUEST: {latest_label}", 480, 284, 15, PALETTE["text"], "middle", "small"),
        text(f"SYNC {summary['updated']}", 816, 292, 13, PALETTE["cream_dim"], "middle", "small"),
    ]
    return svg_shell(
        960,
        320,
        "\n".join(f"  {part}" for part in parts),
        "ld000 pixel profile title screen",
        "A warm pixel terminal desk banner with GitHub counters.",
    )


def generate_status(summary: dict) -> str:
    parts = [
        rect(0, 0, 960, 360, PALETTE["ink"]),
        rect(40, 32, 880, 296, PALETTE["panel"]),
        rect(48, 40, 864, 280, PALETTE["ink"]),
        rect(64, 56, 832, 248, PALETTE["panel"]),
    ]

    parts += pixel_frame(88, 72, 216, 204, PALETTE["panel_2"], PALETTE["line"], PALETTE["shadow"])
    parts += [
        text("PROFILE", 112, 108, 22, PALETTE["text"]),
        text("PUBLIC COUNTERS", 112, 132, 13, PALETTE["screen"], klass="small"),
        rect(112, 148, 152, 4, PALETTE["muted"]),
    ]

    stat_items = [
        ("REPOS", summary["public_repos"], 112, 180),
        ("STARS", summary["total_stars"], 112, 218),
        ("FOLLOWERS", summary["followers"], 112, 256),
    ]
    for label, value, x, y in stat_items:
        parts += [
            rect(x, y - 18, 152, 32, PALETTE["shadow"]),
            rect(x + 8, y - 10, 40, 4, PALETTE["accent"]),
            text(label, x + 64, y - 1, 12, PALETTE["screen"], klass="small"),
            text(value, x + 148, y + 15, 15, PALETTE["text"], "end"),
        ]

    parts += pixel_frame(328, 72, 256, 204, PALETTE["panel_2"], PALETTE["line"], PALETTE["shadow"])
    parts += [
        text("LATEST QUESTS", 352, 108, 22, PALETTE["text"]),
        text("RECENT PUSH TRAIL", 352, 132, 13, PALETTE["accent"], klass="small"),
        rect(352, 148, 176, 4, PALETTE["muted"]),
    ]
    for index, repo in enumerate(summary["latest"][:5]):
        y = 172 + index * 20
        name = truncate(repo.get("name") or "unknown", 15)
        lang = truncate(repo.get("language") or "Unknown", 7)
        stars = repo.get("stargazers_count") or 0
        marker = "accent" if index == 0 else "muted"
        parts += [
            rect(352, y - 13, 8, 8, PALETTE[marker]),
            text(name, 372, y, 13, PALETTE["text"], klass="small"),
            text(f"{lang} *{stars}", 560, y, 11, PALETTE["screen"], "end", "small"),
        ]

    parts += pixel_frame(608, 72, 264, 204, PALETTE["panel_2"], PALETTE["line"], PALETTE["shadow"])
    parts += [
        text("LANGUAGE MAP", 632, 108, 22, PALETTE["text"]),
        text("ACTIVE REPO CLUSTERS", 632, 132, 13, PALETTE["screen"], klass="small"),
        rect(632, 148, 184, 4, PALETTE["muted"]),
    ]
    max_count = max([count for _, count in summary["top_languages"]] or [1])
    for index, (language, count) in enumerate(summary["top_languages"][:6]):
        y = 172 + index * 16
        bar_width = max(16, int(104 * count / max_count))
        color = LANG_COLORS.get(language, PALETTE["screen"])
        parts += [
            text(truncate(language, 8), 632, y, 11, PALETTE["text"], klass="small"),
            rect(724, y - 9, 112, 8, PALETTE["shadow"]),
            rect(728, y - 7, bar_width, 4, color),
            text(count, 852, y, 11, PALETTE["cream_dim"], "end", "small"),
        ]

    parts += [
        rect(88, 280, 784, 24, PALETTE["shadow"]),
        rect(104, 288, 408, 4, PALETTE["screen"]),
        rect(512, 288, 88, 4, PALETTE["accent"]),
        rect(600, 288, 64, 4, PALETTE["muted"]),
        rect(696, 282, 160, 16, PALETTE["panel_3"]),
        text(f"SYNC {summary['updated']}", 844, 294, 12, PALETTE["cream_dim"], "end", "small"),
    ]

    return svg_shell(
        960,
        360,
        "\n".join(f"  {part}" for part in parts),
        "ld000 pixel status board",
        "A warm pixel developer status board generated from public GitHub profile data.",
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
