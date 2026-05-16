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
    "ink": "#101622",
    "shadow": "#070B12",
    "panel": "#18243B",
    "panel_2": "#24344F",
    "panel_3": "#2E405E",
    "text": "#E9DCC9",
    "screen": "#64D2FF",
    "screen_dim": "#287A95",
    "accent": "#FFD166",
    "accent_dim": "#8A5A3C",
    "muted": "#6F7B91",
    "cream_dim": "#BFAE92",
    "desk": "#8A5A3C",
    "line": "#3D4E68",
    "leaf": "#6BCB77",
    "paper": "#E9DCC9",
    "night": "#0B1020",
    "lamp": "#FFD166",
}


LANG_COLORS = {
    "Rust": "#FF9B71",
    "Python": "#64D2FF",
    "JavaScript": "#FFD166",
    "TypeScript": "#64D2FF",
    "Shell": "#E9DCC9",
    "SCSS": "#F28FB3",
    "CSS": "#6BCB77",
    "Java": "#D99B64",
    "GDScript": "#64D2FF",
    "C#": "#6BCB77",
    "HTML": "#FF9B71",
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


def polygon(points: str, fill: str) -> str:
    return f'<polygon points="{points}" fill="{fill}"/>'


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
        rect(24, 24, 912, 248, PALETTE["panel"]),
        rect(32, 32, 896, 232, PALETTE["night"]),
        rect(0, 228, 960, 92, PALETTE["desk"]),
        rect(0, 252, 960, 68, "#6F432D"),
        rect(32, 228, 896, 8, "#B17647"),
        rect(72, 264, 816, 18, PALETTE["shadow"]),
    ]

    # Left window: moonlit skyline and a tiny passing ship.
    parts += pixel_frame(64, 48, 248, 148, PALETTE["panel_2"], PALETTE["line"], PALETTE["shadow"])
    parts += [
        rect(84, 68, 208, 104, PALETTE["shadow"]),
        rect(92, 76, 192, 88, "#0C1830"),
        rect(184, 76, 4, 88, PALETTE["line"]),
        rect(92, 116, 192, 4, PALETTE["line"]),
        rect(240, 84, 20, 20, PALETTE["paper"]),
        rect(236, 84, 8, 8, "#0C1830"),
        rect(116, 92, 6, 6, PALETTE["screen"]),
        rect(144, 104, 4, 4, PALETTE["paper"]),
        rect(268, 132, 4, 4, PALETTE["screen"]),
        polygon("130,120 158,108 198,108 222,120 194,132 154,132", PALETTE["screen_dim"]),
        rect(160, 112, 32, 8, PALETTE["screen"]),
        rect(130, 124, 16, 4, PALETTE["accent"]),
        rect(224, 124, 20, 4, PALETTE["accent"]),
        rect(108, 144, 28, 20, PALETTE["panel"]),
        rect(140, 136, 28, 28, PALETTE["panel_3"]),
        rect(172, 148, 36, 16, PALETTE["panel"]),
        rect(216, 132, 32, 32, PALETTE["panel_3"]),
        rect(116, 148, 4, 4, PALETTE["screen"]),
        rect(148, 144, 4, 8, PALETTE["screen_dim"]),
        rect(224, 140, 4, 4, PALETTE["screen"]),
    ]

    # Desk lamp, books, plant, coffee, cables, and tiny device props.
    parts += [
        rect(96, 216, 116, 12, "#5F3B28"),
        rect(116, 200, 72, 16, "#FF9B71"),
        rect(128, 188, 48, 12, PALETTE["paper"]),
        rect(144, 172, 20, 16, PALETTE["muted"]),
        rect(156, 132, 8, 40, PALETTE["line"]),
        polygon("120,112 204,112 188,132 136,132", PALETTE["lamp"]),
        rect(136, 120, 52, 8, PALETTE["paper"]),
        rect(86, 244, 100, 16, PALETTE["shadow"]),
        rect(96, 224, 72, 20, PALETTE["panel_3"]),
        rect(104, 232, 24, 4, PALETTE["screen"]),
        rect(136, 232, 20, 4, PALETTE["paper"]),
        rect(216, 244, 40, 24, PALETTE["shadow"]),
        rect(224, 224, 24, 20, PALETTE["accent_dim"]),
        rect(228, 216, 16, 8, PALETTE["paper"]),
        rect(254, 244, 80, 12, PALETTE["shadow"]),
        rect(274, 222, 40, 24, PALETTE["panel_3"]),
        rect(290, 202, 8, 20, PALETTE["leaf"]),
        rect(278, 194, 16, 12, PALETTE["leaf"]),
        rect(298, 194, 16, 12, PALETTE["leaf"]),
        rect(314, 234, 8, 12, PALETTE["line"]),
        rect(726, 244, 104, 16, PALETTE["shadow"]),
        rect(740, 222, 68, 24, PALETTE["panel_3"]),
        rect(752, 230, 44, 4, PALETTE["screen"]),
        rect(836, 244, 48, 24, PALETTE["accent_dim"]),
        rect(844, 232, 28, 12, PALETTE["paper"]),
        rect(614, 246, 56, 4, PALETTE["line"]),
        rect(666, 246, 8, 8, PALETTE["line"]),
        rect(674, 254, 64, 4, PALETTE["line"]),
    ]

    # Main terminal keeps the profile identity readable.
    parts += pixel_frame(336, 52, 304, 176, PALETTE["panel_2"], PALETTE["line"], PALETTE["shadow"])
    parts += [
        rect(360, 76, 256, 104, PALETTE["shadow"]),
        rect(368, 84, 240, 88, PALETTE["screen_dim"]),
        rect(376, 92, 224, 72, PALETTE["ink"]),
        text("LD000", 488, 124, 50, PALETTE["text"], "middle"),
        text("RUST / GAMES / TOOLS / NOTES", 488, 154, 15, PALETTE["screen"], "middle", "small"),
        rect(392, 170, 56, 4, "#FF9B71"),
        rect(460, 170, 84, 4, PALETTE["screen"]),
        rect(556, 170, 36, 4, PALETTE["paper"]),
        rect(438, 190, 100, 20, PALETTE["shadow"]),
        rect(394, 214, 188, 14, PALETTE["panel_3"]),
        rect(402, 220, 172, 4, PALETTE["muted"]),
    ]

    parts += [
        rect(660, 56, 224, 136, PALETTE["shadow"]),
        rect(660, 56, 216, 128, PALETTE["panel_2"]),
        rect(660, 56, 216, 8, PALETTE["line"]),
        rect(660, 176, 216, 8, PALETTE["line"]),
        rect(668, 72, 52, 36, PALETTE["paper"]),
        rect(728, 72, 60, 36, "#FFE6A7"),
        rect(796, 72, 52, 36, PALETTE["paper"]),
        rect(676, 84, 32, 4, PALETTE["line"]),
        rect(736, 84, 36, 4, PALETTE["line"]),
        rect(804, 84, 28, 4, PALETTE["line"]),
    ]
    parts += [
        text("STATUS", 688, 128, 17, PALETTE["text"], klass="small"),
        text(f"REPOS {summary['public_repos']}", 688, 150, 14, PALETTE["screen"], klass="small"),
        text(f"STARS {summary['total_stars']}", 776, 150, 14, PALETTE["screen"], klass="small"),
        text(f"FOLLOWERS {summary['followers']}", 688, 170, 14, PALETTE["screen"], klass="small"),
        rect(844, 104, 12, 52, PALETTE["line"]),
        rect(836, 156, 28, 12, PALETTE["lamp"]),
        rect(840, 168, 20, 12, PALETTE["paper"]),
    ]

    parts += pixel_frame(320, 252, 320, 40, PALETTE["panel_2"], PALETTE["line"], PALETTE["shadow"])
    parts += [
        rect(340, 264, 12, 12, PALETTE["lamp"]),
        text(f"QUEST: {latest_label}", 488, 278, 15, PALETTE["text"], "middle", "small"),
        text(f"SYNC {summary['updated']}", 812, 292, 13, PALETTE["paper"], "middle", "small"),
    ]
    return svg_shell(
        960,
        320,
        "\n".join(f"  {part}" for part in parts),
        "ld000 pixel profile title screen",
        "A cozy pixel developer room with a night desk, terminal, and GitHub counters.",
    )


def generate_status(summary: dict) -> str:
    parts = [
        rect(0, 0, 960, 360, PALETTE["ink"]),
        rect(40, 32, 880, 288, PALETTE["panel"]),
        rect(48, 40, 864, 272, PALETTE["night"]),
        rect(56, 264, 848, 48, PALETTE["desk"]),
        rect(56, 288, 848, 24, "#6F432D"),
        rect(64, 72, 832, 192, "#142039"),
    ]

    # A single wall scene: shelf, status notes, terminal prompt, and desktop props.
    parts += [
        rect(88, 104, 212, 12, PALETTE["line"]),
        rect(104, 76, 20, 28, "#FF9B71"),
        rect(132, 84, 14, 20, PALETTE["paper"]),
        rect(154, 72, 18, 32, PALETTE["screen"]),
        rect(182, 92, 56, 12, PALETTE["muted"]),
        rect(248, 80, 16, 24, PALETTE["lamp"]),
        rect(268, 88, 12, 16, PALETTE["paper"]),
        rect(104, 136, 76, 56, PALETTE["paper"]),
        rect(112, 148, 44, 4, PALETTE["line"]),
        rect(112, 162, 52, 4, PALETTE["line"]),
        rect(112, 176, 36, 4, PALETTE["line"]),
        rect(196, 132, 88, 64, "#FFE6A7"),
        rect(208, 148, 48, 4, PALETTE["line"]),
        rect(208, 162, 56, 4, PALETTE["line"]),
        text("COUNTERS", 112, 224, 18, PALETTE["text"], klass="small"),
    ]

    stat_items = [
        ("REPOS", summary["public_repos"], 112, 244, 84),
        ("STARS", summary["total_stars"], 208, 244, 84),
        ("FOLLOWERS", summary["followers"], 112, 264, 128),
    ]
    for label, value, x, y, width in stat_items:
        parts += [
            rect(x, y - 12, width, 16, PALETTE["shadow"]),
            rect(x + 6, y - 6, 16, 4, PALETTE["lamp"]),
            text(label, x + 28, y + 1, 10, PALETTE["screen"], klass="small"),
            text(value, x + width - 4, y + 1, 12, PALETTE["text"], "end", "small"),
        ]

    # Center terminal output sits on the same desk, not in a separate card.
    parts += [
        rect(328, 88, 280, 168, PALETTE["shadow"]),
        rect(320, 80, 280, 168, PALETTE["panel_2"]),
        rect(336, 104, 248, 112, PALETTE["ink"]),
        rect(344, 112, 232, 96, "#09131E"),
        rect(400, 224, 112, 20, PALETTE["shadow"]),
        rect(360, 248, 192, 12, PALETTE["panel_3"]),
        text("LATEST QUESTS", 344, 100, 20, PALETTE["text"]),
        rect(548, 88, 24, 24, PALETTE["lamp"]),
        rect(552, 92, 16, 16, PALETTE["paper"]),
    ]
    for index, repo in enumerate(summary["latest"][:5]):
        y = 132 + index * 14
        name = truncate(repo.get("name") or "unknown", 15)
        lang = truncate(repo.get("language") or "Unknown", 7)
        stars = repo.get("stargazers_count") or 0
        marker = "lamp" if index == 0 else "screen"
        parts += [
            text(">", 352, y, 11, PALETTE[marker], klass="small"),
            text(name, 368, y, 11, PALETTE["text"], klass="small"),
            text(f"{lang} *{stars}", 568, y, 10, PALETTE["screen"], "end", "small"),
        ]
    parts += [
        rect(336, 268, 48, 12, "#FF9B71"),
        rect(392, 268, 72, 12, PALETTE["paper"]),
        rect(472, 268, 56, 12, PALETTE["screen_dim"]),
    ]

    # Right side: language bookshelf, gauge, plant, and a ship badge.
    parts += [
        rect(640, 100, 224, 12, PALETTE["line"]),
        rect(652, 68, 16, 32, "#FF9B71"),
        rect(672, 80, 16, 20, PALETTE["screen"]),
        rect(692, 72, 16, 28, PALETTE["paper"]),
        rect(712, 88, 44, 12, PALETTE["muted"]),
        polygon("778,70 810,58 842,70 812,82", PALETTE["screen_dim"]),
        rect(802, 64, 24, 6, PALETTE["screen"]),
        rect(768, 74, 16, 4, PALETTE["lamp"]),
        rect(842, 74, 16, 4, PALETTE["lamp"]),
        text("LANGUAGE MAP", 648, 134, 20, PALETTE["text"]),
        text("ACTIVE CLUSTERS", 648, 154, 12, PALETTE["screen"], klass="small"),
        rect(648, 164, 184, 4, PALETTE["muted"]),
        rect(696, 268, 48, 24, PALETTE["shadow"]),
        rect(708, 244, 24, 24, PALETTE["screen_dim"]),
        rect(716, 232, 8, 12, PALETTE["leaf"]),
        rect(704, 228, 16, 12, PALETTE["leaf"]),
        rect(724, 228, 16, 12, PALETTE["leaf"]),
    ]
    max_count = max([count for _, count in summary["top_languages"]] or [1])
    for index, (language, count) in enumerate(summary["top_languages"][:6]):
        y = 184 + index * 13
        bar_width = max(16, int(104 * count / max_count))
        color = LANG_COLORS.get(language, PALETTE["screen"])
        parts += [
            text(truncate(language, 8), 648, y, 10, PALETTE["text"], klass="small"),
            rect(724, y - 8, 112, 8, PALETTE["shadow"]),
            rect(728, y - 6, bar_width, 4, color),
            text(count, 852, y, 10, PALETTE["paper"], "end", "small"),
        ]

    parts += [
        rect(760, 270, 108, 18, PALETTE["shadow"]),
        rect(772, 274, 80, 4, PALETTE["screen"]),
        rect(104, 292, 520, 4, PALETTE["screen"]),
        rect(624, 292, 88, 4, PALETTE["lamp"]),
        rect(712, 292, 64, 4, PALETTE["muted"]),
        text(f"SYNC {summary['updated']}", 856, 296, 12, PALETTE["paper"], "end", "small"),
    ]

    return svg_shell(
        960,
        360,
        "\n".join(f"  {part}" for part in parts),
        "ld000 pixel status board",
        "A pixel developer room status board with counters, recent quests, and language shelves.",
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
