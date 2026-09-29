"""Refresh the locally maintained ARAM: Mayhem augment catalog.

The live names, rarities, and top champion picks come from ARAM Mayhem's Patch 26.19 catalog.
Korean effect text is reused from the previous public catalog snapshot where
available; rows without a verified description are left explicitly unknown.
"""

from __future__ import annotations

import json
import re
import argparse
from html.parser import HTMLParser
from pathlib import Path
import ssl
from urllib.request import Request, urlopen


LIVE_KO_URL = "https://arammayhem.com/ko-kr/augments/"
LIVE_EN_URL = "https://arammayhem.com/augments/"
PREVIOUS_KO_URL = "https://www.arammayhem.net/ko/augments/"
OUTPUT = Path(__file__).resolve().parents[1] / "app" / "data" / "augments.json"
USER_AGENT = "LOL-Archive-Mayhem-Catalog/1.0"


def fetch(url: str, cache_dir: Path | None = None) -> str:
    if cache_dir:
        cache_name = {
            LIVE_KO_URL: "live-ko.html",
            LIVE_EN_URL: "live-en.html",
            PREVIOUS_KO_URL: "previous-ko.html",
        }[url]
        cached = cache_dir / cache_name
        if cached.exists():
            return cached.read_text(encoding="utf-8")
    request = Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    try:
        response = urlopen(request, timeout=30, context=context)
    except Exception:
        raise
    with response:
        return response.read().decode("utf-8")


class LiveListParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, object]] = []
        self.current: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs)
        href = attrs.get("href", "") or ""
        if tag == "a" and href.startswith("/") and "/augments/" in href:
            slug_match = re.search(r"/augments/([^/]+)/", href)
            if slug_match and attrs.get("data-availability") == "live":
                self.current = {
                    "slug": slug_match.group(1),
                    "tier_source": attrs.get("data-rarity", ""),
                    "name_source": attrs.get("data-name", ""),
                    "name": "",
                    "recommended_champions": [],
                }
        elif tag == "img" and self.current:
            src = attrs.get("src", "") or ""
            champion = re.search(r"/champions/icons/([^/]+)/64\.png", src)
            if champion:
                recommendations = self.current["recommended_champions"]
                if isinstance(recommendations, list):
                    recommendations.append({
                        "id": champion.group(1),
                        "name": attrs.get("alt", "") or "",
                        "icon": src,
                    })
            elif not self.current["name"]:
                self.current["name"] = attrs.get("alt", "") or ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.current:
            self.rows.append(self.current)
            self.current = None


class PreviousListParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: dict[str, dict[str, str]] = {}
        self.in_article = False
        self.in_description = False
        self.slug = ""
        self.source = ""
        self.description: list[str] = []
        self.description_found = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs)
        if tag == "article" and "data-augment-card" in attrs:
            self.in_article = True
            self.slug = ""
            self.source = ""
            self.description = []
            self.description_found = False
        elif self.in_article and tag == "a" and not self.slug:
            match = re.search(r"/augments/(\d+-[^/]+)/", attrs.get("href", "") or "")
            if match:
                self.source = f"https://www.arammayhem.net/ko/augments/{match.group(1)}/"
                self.slug = re.sub(r"^\d+-", "", match.group(1))
        elif self.in_article and tag == "p" and not self.description_found:
            self.in_description = True
            self.description_found = True

    def handle_data(self, data: str) -> None:
        if self.in_article and self.in_description:
            self.description.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "p" and self.in_description:
            self.in_description = False
        elif tag == "article" and self.in_article:
            if self.slug and self.description_found:
                text = re.sub(r"\s+", " ", " ".join(self.description)).strip()
                self.rows[self.slug] = {"description": text, "source": self.source}
            self.in_article = False


ALIASES = {
    "quest-steel-your-heart": "steel-your-heart",
    "stackosaurusrex": "stackosaurus-rex",
    "quest-wooglets-witchcap": "wooglet-s-witchcap",
    "outlaws-grit": "outlaw-s-grit",
    "windspeakers-blessing": "windspeaker-s-blessing",
    "dont-change-the-channel": "don-t-change-the-channel",
    "upgrade-zhonyas": "upgrade-zhonya-s",
    "dont-blink": "don-t-blink",
    "terraind": "terrain-d",
    "its-critical": "it-s-critical",
    "dawnbringers-resolve": "dawnbringer-s-resolve",
    "its-killing-time": "it-s-killing-time",
    "pandorasbox": "pandora-s-box",
    "mercys-strike": "mercy-s-strike",
    "cant-touch-this": "can-t-touch-this",
    "mountainsoul": "mountain-soul",
    "titans-resolve": "titan-s-resolve",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, help="Read downloaded source HTML from this directory")
    args = parser.parse_args()

    live_ko = LiveListParser()
    live_ko.feed(fetch(LIVE_KO_URL, args.cache_dir))
    live_en = LiveListParser()
    live_en.feed(fetch(LIVE_EN_URL, args.cache_dir))
    previous = PreviousListParser()
    previous.feed(fetch(PREVIOUS_KO_URL, args.cache_dir))

    english_names = {row["slug"]: row["name"] for row in live_en.rows}
    english_champions = {
        row["slug"]: {
            champion["id"]: champion["name"]
            for champion in row["recommended_champions"]
        }
        for row in live_en.rows
    }
    rarity = {"silver": "실버", "gold": "골드", "prismatic": "프리즘"}
    items = []
    missing = []
    for row in live_ko.rows:
        slug = row["slug"]
        description_data = previous.rows.get(slug)
        if not description_data:
            alias = ALIASES.get(slug)
            if alias:
                description_data = previous.rows.get(alias)
        description = description_data["description"] if description_data else ""
        description_source = description_data["source"] if description_data else ""
        description_patch = "26.17" if description else None
        if not description:
            description = "효과 설명은 현재 확인 가능한 자료에 없어, 정확한 효과를 확인하지 못했습니다."
            missing.append(slug)

        # Patch 26.18 explicitly raised Spin To Win's R damage bonus.
        if slug == "spin-to-win" and description:
            description = description.replace("30%", "50%")
            description_patch = "26.18"

        champion_names = english_champions.get(slug, {})
        recommended_champions = [
            {
                **champion,
                "english_name": champion_names.get(champion["id"], champion["id"].title()),
            }
            for champion in row["recommended_champions"]
        ]

        items.append({
            "id": slug,
            "name": row["name"],
            "english_name": english_names.get(slug, slug.replace("-", " ").title()),
            "description": description,
            "tier": rarity.get(row["tier_source"], row["tier_source"]),
            "patch": "26.19",
            "recommended_champions": recommended_champions,
            "recommendations_patch": "26.19",
            "recommendations_source": f"https://arammayhem.com/ko-kr/augments/{slug}/",
            "description_patch": description_patch,
            "description_source": description_source,
            "source": f"https://arammayhem.com/ko-kr/augments/{slug}/",
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {label: sum(item["tier"] == label for item in items) for label in ("실버", "골드", "프리즘")}
    print(f"Wrote {len(items)} current augment entries: {counts}")
    print(f"Descriptions unavailable for {len(missing)} entries: {', '.join(missing)}")


if __name__ == "__main__":
    main()
