"""
services/riot_league.py
Client LEAGUE-V4 pour pull des leaderboards Challenger/GM/Master.
"""
import asyncio
import logging
import httpx
from services.riot import REGIONS, get_headers

logger = logging.getLogger(__name__)


async def get_master_plus_puuids(region: str, max_per_tier: int = 100) -> list[str]:
    """
    Récupère jusqu'à 3*max_per_tier puuids (Challenger + GM + Master).
    Utilise le endpoint /lol/league/v4/{tier}/{queue} qui retourne directement les entries.

    NB : LEAGUE-V4 retourne summonerId, pas puuid directement → on doit faire un appel
    SUMMONER-V4 pour résoudre. Mais Riot a déprécié summonerId en faveur de puuid en 2024,
    donc l'endpoint moderne est /lol/league/v4/entries/by-puuid → on fait l'inverse :
    on récupère les summonerIds puis on convertit.

    Pour simplifier et limiter les appels API, on utilise le top des leaderboards
    via /lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5 etc.
    """
    platform = REGIONS.get(region.upper(), "euw1")
    base     = f"https://{platform}.api.riotgames.com/lol/league/v4"
    queue    = "RANKED_SOLO_5x5"

    endpoints = [
        ("CHALLENGER", f"{base}/challengerleagues/by-queue/{queue}"),
        ("GRANDMASTER", f"{base}/grandmasterleagues/by-queue/{queue}"),
        ("MASTER",      f"{base}/masterleagues/by-queue/{queue}"),
    ]

    all_summoner_ids: list[str] = []
    async with httpx.AsyncClient(timeout=15) as client:
        for tier_name, url in endpoints:
            try:
                r = await client.get(url, headers=get_headers())
                if r.status_code != 200:
                    logger.warning(f"LEAGUE-V4 {region} {tier_name}: status {r.status_code}")
                    continue
                data    = r.json()
                entries = data.get("entries", [])
                # Trier par leaguePoints desc, prendre top N
                entries.sort(key=lambda e: e.get("leaguePoints", 0), reverse=True)
                top = entries[:max_per_tier]
                all_summoner_ids.extend(e["summonerId"] for e in top if "summonerId" in e)
                logger.info(f"LEAGUE-V4 {region} {tier_name}: {len(top)} entries")
            except Exception as e:
                logger.error(f"LEAGUE-V4 {region} {tier_name} erreur : {e}")

    if not all_summoner_ids:
        return []

    # ── Convertir summonerId → puuid via SUMMONER-V4 ──────────
    sem = asyncio.Semaphore(8)  # respect rate limit Riot

    async def resolve_puuid(sid: str) -> str | None:
        async with sem:
            url = f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/{sid}"
            try:
                async with httpx.AsyncClient(timeout=10) as c:
                    r = await c.get(url, headers=get_headers())
                    if r.status_code == 200:
                        return r.json().get("puuid")
            except Exception:
                pass
            return None

    puuids = await asyncio.gather(*[resolve_puuid(sid) for sid in all_summoner_ids])
    valid  = [p for p in puuids if p]
    logger.info(f"LEAGUE-V4 {region}: {len(valid)} puuids résolus / {len(all_summoner_ids)} summonerIds")
    return valid