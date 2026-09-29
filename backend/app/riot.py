from urllib.parse import quote

import httpx
from fastapi import HTTPException

from .config import settings

PLATFORM_HOSTS = {
    "kr": "kr.api.riotgames.com",
    "na1": "na1.api.riotgames.com",
    "euw1": "euw1.api.riotgames.com",
    "eun1": "eun1.api.riotgames.com",
    "jp1": "jp1.api.riotgames.com",
    "br1": "br1.api.riotgames.com",
    "la1": "la1.api.riotgames.com",
    "la2": "la2.api.riotgames.com",
    "oc1": "oc1.api.riotgames.com",
    "tr1": "tr1.api.riotgames.com",
    "ru": "ru.api.riotgames.com",
    "ph2": "ph2.api.riotgames.com",
    "sg2": "sg2.api.riotgames.com",
    "th2": "th2.api.riotgames.com",
    "tw2": "tw2.api.riotgames.com",
    "vn2": "vn2.api.riotgames.com",
}
REGIONAL_HOSTS = {
    "kr": "asia.api.riotgames.com", "jp1": "asia.api.riotgames.com",
    "na1": "americas.api.riotgames.com", "br1": "americas.api.riotgames.com",
    "la1": "americas.api.riotgames.com", "la2": "americas.api.riotgames.com",
    "euw1": "europe.api.riotgames.com", "eun1": "europe.api.riotgames.com",
    "tr1": "europe.api.riotgames.com", "ru": "europe.api.riotgames.com",
    "oc1": "sea.api.riotgames.com", "ph2": "sea.api.riotgames.com",
    "sg2": "sea.api.riotgames.com", "th2": "sea.api.riotgames.com",
    "tw2": "sea.api.riotgames.com", "vn2": "sea.api.riotgames.com",
}


async def get_json(url: str):
    if not settings.riot_api_key:
        raise HTTPException(503, "Riot API 키를 설정해 주세요. 프로젝트 루트의 .env 파일을 확인하세요.")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers={"X-Riot-Token": settings.riot_api_key})
    except httpx.RequestError as exc:
        raise HTTPException(503, "Riot API 서버에 연결할 수 없습니다. 인터넷 연결 또는 방화벽 설정을 확인해 주세요.") from exc
    if response.status_code == 404:
        raise HTTPException(404, "소환사 또는 경기 기록을 찾을 수 없습니다.")
    if response.status_code in (401, 403):
        raise HTTPException(502, "Riot API 키가 만료되었거나 유효하지 않습니다. 개발자 포털에서 갱신해 주세요.")
    if response.status_code == 429:
        raise HTTPException(429, "Riot API 요청 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.")
    if response.is_error:
        raise HTTPException(502, f"Riot API 오류 ({response.status_code})")
    return response.json()


async def account_by_riot_id(region: str, game_name: str, tag_line: str):
    host = REGIONAL_HOSTS[region]
    name, tag = quote(game_name, safe=""), quote(tag_line, safe="")
    return await get_json(f"https://{host}/riot/account/v1/accounts/by-riot-id/{name}/{tag}")


async def match_ids(region: str, puuid: str, count: int):
    host = REGIONAL_HOSTS[region]
    return await get_json(f"https://{host}/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids?start=0&count={count}")


async def match_by_id(region: str, match_id: str):
    host = REGIONAL_HOSTS[region]
    return await get_json(f"https://{host}/lol/match/v5/matches/{quote(match_id, safe='')}")


async def tft_match_ids(region: str, puuid: str, count: int):
    host = REGIONAL_HOSTS[region]
    return await get_json(
        f"https://{host}/tft/match/v1/matches/by-puuid/{quote(puuid, safe='')}/ids?start=0&count={count}"
    )


async def tft_match_by_id(region: str, match_id: str):
    host = REGIONAL_HOSTS[region]
    return await get_json(f"https://{host}/tft/match/v1/matches/{quote(match_id, safe='')}")
