import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

_champions_ko: dict[str, dict[str, str]] | None = None
_items_ko: dict[str, dict[str, str]] | None = None
_version: str | None = None
_lock = asyncio.Lock()


async def get_game_data_ko() -> tuple[str, dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Load Riot's Korean champion and item data, keyed by numeric game ID."""
    global _champions_ko, _items_ko, _version
    if _champions_ko is not None and _items_ko is not None:
        return _version or "", _champions_ko, _items_ko

    async with _lock:
        if _champions_ko is not None and _items_ko is not None:
            return _version or "", _champions_ko, _items_ko
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                versions_response = await client.get("https://ddragon.leagueoflegends.com/api/versions.json")
                versions_response.raise_for_status()
                _version = versions_response.json()[0]
                base_url = f"https://ddragon.leagueoflegends.com/cdn/{_version}/data/ko_KR"
                champion_response, item_response = await asyncio.gather(
                    client.get(f"{base_url}/champion.json"),
                    client.get(f"{base_url}/item.json"),
                )
                champion_response.raise_for_status()
                item_response.raise_for_status()
                champions = champion_response.json().get("data", {}).values()
                items = item_response.json().get("data", {})
                _champions_ko = {
                    str(champion["key"]): {
                        "name": champion["name"],
                        "image": champion.get("image", {}).get("full", ""),
                    }
                    for champion in champions
                    if champion.get("key") and champion.get("name")
                }
                _items_ko = {
                    str(item_id): {
                        "name": item.get("name", f"아이템 {item_id}"),
                        "description": item.get("plaintext", ""),
                        "image": item.get("image", {}).get("full", ""),
                    }
                    for item_id, item in items.items()
                }
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            logger.warning("Could not load Korean game data from Data Dragon: %s", error)
            return "", {}, {}
        return _version or "", _champions_ko, _items_ko
