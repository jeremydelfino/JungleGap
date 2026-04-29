"""
services/riot_stats.py
Pull et cache des stats MATCH-V5 par joueur (winrate global, winrate champion, forme).
Cache en mémoire avec TTL 30 min pour éviter de flood l'API Riot.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from services.riot import ROUTING, get_headers
import httpx

logger = logging.getLogger(__name__)

# ─── Cache en mémoire ────────────────────────────────────────
# { puuid: { "data": {...}, "expires_at": datetime } }
_STATS_CACHE: dict = {}
CACHE_TTL_MINUTES = 30
N_GAMES = 20


def _cache_get(puuid: str) -> dict | None:
    entry = _STATS_CACHE.get(puuid)
    if not entry:
        return None
    if datetime.utcnow() > entry["expires_at"]:
        del _STATS_CACHE[puuid]
        return None
    return entry["data"]


def _cache_set(puuid: str, data: dict):
    _STATS_CACHE[puuid] = {
        "data":       data,
        "expires_at": datetime.utcnow() + timedelta(minutes=CACHE_TTL_MINUTES),
    }


async def _fetch_match_ids(puuid: str, region: str, count: int = N_GAMES) -> list[str]:
    routing = ROUTING.get(region.upper(), "europe")
    url = (
        f"https://{routing}.api.riotgames.com"
        f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        f"?queue=420&count={count}"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url, headers=get_headers())
            if r.status_code != 200:
                return []
            return r.json()
    except Exception as e:
        logger.error(f"_fetch_match_ids error {puuid[:16]}: {e}")
        return []


async def _fetch_match(match_id: str, routing: str) -> dict | None:
    url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            async with riot_limiter:
                r = await c.get(url, headers=get_headers())
                if r.status_code == 200:
                    return r.json()
                return None
    except Exception as e:
        logger.error(f"_fetch_match error {match_id}: {e}")
        return None


async def get_player_stats(puuid: str, region: str, current_champ: str | None = None) -> dict:
    """
    Retourne un dict avec :
    - winrate_global   : float [0, 1]
    - winrate_champ    : float [0, 1] (sur current_champ, ou 0.5 si pas de data)
    - forme_5          : float [0, 1] (ratio W sur les 5 dernières)
    - n_games          : int (nb de games analysées)
    - n_games_champ    : int
    """
    cached = _cache_get(puuid)
    if cached:
        # Si on a le cache mais pas les stats du champion actuel, on ne re-fetch pas
        # (le champ peut avoir changé entre deux appels)
        return _compute_stats(cached, current_champ)

    routing  = ROUTING.get(region.upper(), "europe")
    match_ids = await _fetch_match_ids(puuid, region, N_GAMES)

    if not match_ids:
        return _default_stats()

    # Fetch toutes les games en parallèle (max 20 → raisonnable)
    tasks   = [_fetch_match(mid, routing) for mid in match_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    games_raw = []
    for match in results:
        if not match or isinstance(match, Exception):
            continue
        part = next(
            (p for p in match["info"]["participants"] if p["puuid"] == puuid),
            None,
        )
        if part:
            games_raw.append({
                "win":          part["win"],
                "champion":     part["championName"],
                "kills":        part["kills"],
                "deaths":       part["deaths"],
                "assists":      part["assists"],
                "game_end_ts":  match["info"].get("gameEndTimestamp", 0),
            })

    _cache_set(puuid, games_raw)
    return _compute_stats(games_raw, current_champ)


def _compute_stats(games: list[dict], current_champ: str | None) -> dict:
    if not games:
        return _default_stats()

    # Winrate global
    wins_global = sum(1 for g in games if g["win"])
    wr_global   = wins_global / len(games)

    # Winrate sur le champion joué maintenant
    champ_games = [g for g in games if g["champion"] == current_champ] if current_champ else []
    wr_champ    = (sum(1 for g in champ_games if g["win"]) / len(champ_games)) if champ_games else 0.50

    # Forme sur les 5 dernières (triées par timestamp desc = déjà dans l'ordre)
    recent_5  = games[:5]
    forme_5   = sum(1 for g in recent_5 if g["win"]) / len(recent_5) if recent_5 else 0.50

    return {
        "winrate_global": round(wr_global,  3),
        "winrate_champ":  round(wr_champ,   3),
        "forme_5":        round(forme_5,    3),
        "n_games":        len(games),
        "n_games_champ":  len(champ_games),
    }


def _default_stats() -> dict:
    return {
        "winrate_global": 0.50,
        "winrate_champ":  0.50,
        "forme_5":        0.50,
        "n_games":        0,
        "n_games_champ":  0,
    }