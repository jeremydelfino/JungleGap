"""
services/riot_league.py
Client LEAGUE-V4 pour pull des leaderboards Challenger/GM/Master.

Riot a déprécié summonerId en faveur de puuid en 2024. Les endpoints leaderboard
modernes retournent directement le puuid dans chaque entry — plus besoin de
faire un round-trip SUMMONER-V4.
"""
import asyncio
import logging
import httpx
from services.riot import REGIONS, get_headers

logger = logging.getLogger(__name__)


async def get_master_plus_puuids(region: str, max_per_tier: int = 100) -> list[str]:
    """
    Récupère jusqu'à 3*max_per_tier puuids (Challenger + GM + Master) via LEAGUE-V4.
    Les entries retournées contiennent désormais directement le puuid.
    """
    platform = REGIONS.get(region.upper(), "euw1")
    base     = f"https://{platform}.api.riotgames.com/lol/league/v4"
    queue    = "RANKED_SOLO_5x5"

    endpoints = [
        ("CHALLENGER",  f"{base}/challengerleagues/by-queue/{queue}"),
        ("GRANDMASTER", f"{base}/grandmasterleagues/by-queue/{queue}"),
        ("MASTER",      f"{base}/masterleagues/by-queue/{queue}"),
    ]

    all_puuids: list[str] = []

    async with httpx.AsyncClient(timeout=15) as client:
        for tier_name, url in endpoints:
            try:
                r = await client.get(url, headers=get_headers())
                if r.status_code != 200:
                    logger.warning(f"LEAGUE-V4 {region} {tier_name}: status {r.status_code} — body: {r.text[:200]}")
                    continue

                data    = r.json()
                entries = data.get("entries", [])
                entries.sort(key=lambda e: e.get("leaguePoints", 0), reverse=True)
                top = entries[:max_per_tier]

                # Les entries modernes contiennent directement le puuid
                tier_puuids = [e["puuid"] for e in top if e.get("puuid")]
                all_puuids.extend(tier_puuids)

                logger.info(
                    f"LEAGUE-V4 {region} {tier_name}: {len(tier_puuids)} puuids récupérés "
                    f"(sur {len(top)} entries)"
                )
            except Exception as e:
                logger.error(f"LEAGUE-V4 {region} {tier_name} erreur : {e}", exc_info=True)

    # Déduplication (un même joueur peut traîner sur plusieurs tiers en théorie)
    unique = list(dict.fromkeys(all_puuids))
    logger.info(f"LEAGUE-V4 {region}: {len(unique)} puuids uniques au total")
    return unique