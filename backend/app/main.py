import asyncio
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import settings
from .data_dragon import get_game_data_ko, get_tft_game_data_ko
from .riot import PLATFORM_HOSTS, account_by_riot_id, match_by_id, match_ids, tft_match_by_id, tft_match_ids

app = FastAPI(title="LOL Archive API", description="Riot 전적 검색과 아수라장 증강 도감")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

AUGMENT_FILE = Path(__file__).parent / "data" / "augments.json"
HOME_PAGE = Path(__file__).parent / "static" / "index.html"
_riot_health_cache = {"checked_at": 0.0, "connected": False, "message": "확인 중"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home():
    return HOME_PAGE.read_text(encoding="utf-8")


@app.get("/api/health")
async def health():
    now = time.monotonic()
    if now - _riot_health_cache["checked_at"] >= 30:
        connected = False
        if settings.riot_api_key:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(
                        "https://kr.api.riotgames.com/tft/status/v1/platform-data",
                        headers={"X-Riot-Token": settings.riot_api_key},
                    )
                connected = response.status_code == 200
                if connected:
                    message = "정상"
                elif response.status_code in (401, 403):
                    message = "API 키 확인 필요"
                elif response.status_code == 429:
                    message = "요청 한도 초과"
                else:
                    message = f"Riot 응답 오류 ({response.status_code})"
            except httpx.RequestError:
                message = "Riot 서버 연결 실패"
        else:
            message = "API 키 미설정"
        _riot_health_cache.update(checked_at=now, connected=connected, message=message)

    return {
        "status": "ok",
        "fastapi_connected": True,
        "riot_api_connected": _riot_health_cache["connected"],
        "riot_api_message": _riot_health_cache["message"],
        "riot_api_key_configured": bool(settings.riot_api_key),
    }


@app.get("/api/regions")
async def regions():
    return [{"id": key, "host": value} for key, value in PLATFORM_HOSTS.items()]


@app.get("/api/augments")
async def augments(q: str = "", tier: str = ""):
    if not AUGMENT_FILE.exists():
        return {"items": [], "total": 0}
    import json

    items = json.loads(AUGMENT_FILE.read_text(encoding="utf-8"))
    if q:
        items = [
            item for item in items
            if q.casefold() in " ".join((
                item.get("name", ""),
                item.get("english_name", ""),
                item.get("description", ""),
                " ".join(
                    name
                    for champion in item.get("recommended_champions", [])
                    for name in (champion.get("name", ""), champion.get("english_name", ""))
                ),
            )).casefold()
        ]
    if tier:
        items = [item for item in items if item.get("tier", "").casefold() == tier.casefold()]
    return {"items": items, "total": len(items)}


@app.get("/api/summoners/{region}/{riot_id}/matches")
async def search_matches(
    region: str,
    riot_id: str,
    count: int = Query(10, ge=1, le=20),
):
    region = region.lower()
    if region not in PLATFORM_HOSTS:
        raise HTTPException(422, "지원하지 않는 지역 코드입니다.")
    if "#" not in riot_id:
        raise HTTPException(422, "Riot ID를 이름#태그 형식으로 입력해 주세요.")
    game_name, tag_line = riot_id.rsplit("#", 1)
    if not game_name.strip() or not tag_line.strip():
        raise HTTPException(422, "Riot ID를 이름#태그 형식으로 입력해 주세요.")

    account = await account_by_riot_id(region, game_name.strip(), tag_line.strip())
    ids = await match_ids(region, account["puuid"], count)
    matches = await asyncio.gather(*(match_by_id(region, match_id) for match_id in ids))
    data_dragon_version, champions_ko, items_ko = await get_game_data_ko()

    results = []
    for match in matches:
        info = match.get("info", {})
        participant = next((p for p in info.get("participants", []) if p.get("puuid") == account["puuid"]), {})
        champion_name = participant.get("championName", "Unknown")
        champion_data = champions_ko.get(str(participant.get("championId")), {})
        item_ids = [participant.get(f"item{i}", 0) for i in range(7)]
        results.append({
            "match_id": match.get("metadata", {}).get("matchId"),
            "game_mode": info.get("gameMode", "UNKNOWN"),
            "game_type": info.get("gameType", "UNKNOWN"),
            "queue_id": info.get("queueId"),
            "game_start": info.get("gameStartTimestamp"),
            "duration": info.get("gameDuration", 0),
            "champion": champion_name,
            "champion_ko": champion_data.get("name", champion_name),
            "champion_icon": f"https://ddragon.leagueoflegends.com/cdn/{data_dragon_version}/img/champion/{champion_data['image']}" if data_dragon_version and champion_data.get("image") else "",
            "champion_id": participant.get("championId"),
            "win": participant.get("win"),
            "kills": participant.get("kills", 0),
            "deaths": participant.get("deaths", 0),
            "assists": participant.get("assists", 0),
            "items": item_ids,
            "item_details": [
                {
                    "id": str(item_id),
                    "name": items_ko.get(str(item_id), {}).get("name", f"아이템 {item_id}"),
                    "description": items_ko.get(str(item_id), {}).get("description", ""),
                    "icon": f"https://ddragon.leagueoflegends.com/cdn/{data_dragon_version}/img/item/{items_ko[str(item_id)]['image']}" if data_dragon_version and items_ko.get(str(item_id), {}).get("image") else "",
                }
                for item_id in item_ids
                if item_id
            ],
            "summoner_spell1": participant.get("summoner1Id"),
            "summoner_spell2": participant.get("summoner2Id"),
            "participants": [
                {"name": p.get("riotIdGameName", "Player"), "tag": p.get("riotIdTagline", ""), "champion": p.get("championName", "Unknown"), "champion_ko": champions_ko.get(str(p.get("championId")), {}).get("name", p.get("championName", "Unknown")), "champion_icon": f"https://ddragon.leagueoflegends.com/cdn/{data_dragon_version}/img/champion/{champions_ko[str(p.get('championId'))]['image']}" if data_dragon_version and champions_ko.get(str(p.get("championId")), {}).get("image") else "", "win": p.get("win")}
                for p in info.get("participants", [])
            ],
        })
    return {"account": {"game_name": account["gameName"], "tag_line": account["tagLine"], "puuid": account["puuid"]}, "matches": results}


@app.get("/api/tft/{region}/{riot_id}/matches")
async def search_tft_matches(
    region: str,
    riot_id: str,
    count: int = Query(10, ge=1, le=20),
):
    region = region.lower()
    if region not in PLATFORM_HOSTS:
        raise HTTPException(422, "지원하지 않는 지역 코드입니다.")
    if "#" not in riot_id:
        raise HTTPException(422, "Riot ID를 이름#태그 형식으로 입력해 주세요.")
    game_name, tag_line = riot_id.rsplit("#", 1)
    if not game_name.strip() or not tag_line.strip():
        raise HTTPException(422, "Riot ID를 이름#태그 형식으로 입력해 주세요.")

    account = await account_by_riot_id(region, game_name.strip(), tag_line.strip())
    match_ids = await tft_match_ids(region, account["puuid"], count)
    matches = await asyncio.gather(*(tft_match_by_id(region, match_id) for match_id in match_ids))
    version, champions, items, traits, augments, queues = await get_tft_game_data_ko()
    cdn = f"https://ddragon.leagueoflegends.com/cdn/{version}" if version else ""

    results = []
    for match in matches:
        info = match.get("info", {})
        participant = next(
            (player for player in info.get("participants", []) if player.get("puuid") == account["puuid"]),
            {},
        )
        units = []
        for unit in participant.get("units", []):
            unit_id = str(unit.get("character_id", unit.get("characterId", "")))
            champion = champions.get(unit_id, {})
            unit_items = unit.get("itemNames") or unit.get("items") or []
            normalized_items = []
            for item in unit_items:
                item_id = str(item.get("id", "")) if isinstance(item, dict) else str(item)
                item_data = items.get(item_id, {})
                normalized_items.append({
                    "id": item_id,
                    "name": item_data.get("name", item_id),
                    "icon": f"{cdn}/{item_data['image']}" if cdn and item_data.get("image") else "",
                })
            unit_image = champion.get("image", "")
            units.append({
                "id": unit_id,
                "name": champion.get("name", unit.get("name") or unit_id),
                "icon": f"{cdn}/{unit_image}" if cdn and unit_image else "",
                "star": unit.get("tier", 1),
                "items": normalized_items,
            })

        active_traits = []
        for trait in participant.get("traits", []):
            trait_id = str(trait.get("name", ""))
            trait_data = traits.get(trait_id, {})
            active_traits.append({
                "id": trait_id,
                "name": trait_data.get("name", trait_id),
                "units": trait.get("num_units", 0),
                "style": trait.get("style", 0),
                "icon": f"{cdn}/{trait_data['image']}" if cdn and trait_data.get("image") else "",
            })

        match_augments = []
        for augment_id in participant.get("augments", []):
            augment_data = augments.get(str(augment_id), {})
            match_augments.append({
                "id": str(augment_id),
                "name": augment_data.get("name", str(augment_id)),
                "icon": f"{cdn}/{augment_data['image']}" if cdn and augment_data.get("image") else "",
            })

        queue_id = str(info.get("queue_id", ""))
        queue_name = queues.get(queue_id, {}).get("name", f"TFT {queue_id}".strip())
        results.append({
            "match_id": match.get("metadata", {}).get("match_id"),
            "queue_id": info.get("queue_id"),
            "queue_name": queue_name,
            "game_start": info.get("game_datetime"),
            "duration": round(info.get("game_length", 0)),
            "placement": participant.get("placement"),
            "level": participant.get("level"),
            "last_round": participant.get("last_round"),
            "players_eliminated": participant.get("players_eliminated"),
            "gold_left": participant.get("gold_left"),
            "units": units,
            "traits": active_traits,
            "augments": match_augments,
        })

    return {
        "account": {"game_name": account["gameName"], "tag_line": account["tagLine"]},
        "matches": results,
    }
