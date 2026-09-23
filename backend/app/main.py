import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .config import settings
from .data_dragon import get_game_data_ko
from .riot import PLATFORM_HOSTS, account_by_riot_id, match_by_id, match_ids

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


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home():
    return HOME_PAGE.read_text(encoding="utf-8")


@app.get("/api/health")
async def health():
    return {"status": "ok", "riot_api_key_configured": bool(settings.riot_api_key)}


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
        items = [item for item in items if q.casefold() in (item.get("name", "") + " " + item.get("description", "")).casefold()]
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
