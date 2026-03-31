import httpx
import os
from dotenv import load_dotenv
import asyncio
import logging
logger = logging.getLogger(__name__)

load_dotenv()

REGIONS = {
    "EUW": "euw1",
    "NA":  "na1",
    "KR":  "kr",
    "BR":  "br1",
    "EUN": "eun1",
    "JP":  "jp1",
    "LAN": "la1",
    "LAS": "la2",
    "OCE": "oc1",
    "TR":  "tr1",
    "RU":  "ru",
}

ROUTING = {
    "EUW": "europe",
    "EUN": "europe",
    "TR":  "europe",
    "RU":  "europe",
    "NA":  "americas",
    "BR":  "americas",
    "LAN": "americas",
    "LAS": "americas",
    "KR":  "asia",
    "JP":  "asia",
    "OCE": "sea",
}


def get_headers() -> dict:
    return {"X-Riot-Token": os.getenv("RIOT_API_KEY")}


async def get_account_by_riot_id(game_name: str, tag_line: str, region: str) -> dict:
    routing = ROUTING.get(region.upper(), "europe")
    url = f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=get_headers())
        res.raise_for_status()
        return res.json()


async def get_summoner_by_puuid(puuid: str, region: str) -> dict:
    platform = REGIONS.get(region.upper(), "euw1")
    url = f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=get_headers())
        res.raise_for_status()
        return res.json()


async def get_rank_by_puuid(puuid: str, region: str) -> list:
    platform = REGIONS.get(region.upper(), "euw1")
    url = f"https://{platform}.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=get_headers())
        res.raise_for_status()
        return res.json()


async def get_live_game_by_puuid(puuid: str, region: str) -> dict | None:
    try:
        platform = REGIONS.get(region.upper(), "euw1")
        url = f"https://{platform}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{puuid}"
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=get_headers())
            if res.status_code == 404:
                return None
            if res.status_code in (401, 403):
                import logging
                logging.getLogger(__name__).error(
                    f"get_live_game_by_puuid {res.status_code} — vérifie la clé API dans .env"
                )
                return None
            res.raise_for_status()
            if res.status_code == 429:
                retry_after = int(res.headers.get("Retry-After", 5))
                await asyncio.sleep(retry_after)
                return None
            return res.json()
            

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"get_live_game_by_puuid error: {e}")
        return None


async def get_match_history(puuid: str, region: str, count: int = 10) -> list:
    routing = ROUTING.get(region.upper(), "europe")
    url = (
        f"https://{routing}.api.riotgames.com"
        f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        f"?count={count}&queue=420"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=get_headers())
            if res.status_code != 200:
                return []
            match_ids = res.json()
    except Exception:
        return []

    async def fetch_one(match_id: str) -> dict | None:
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                res = await client.get(url, headers=get_headers())
                return res.json() if res.status_code == 200 else None
        except Exception:
            return None

    try:
        results = await asyncio.wait_for(
            asyncio.gather(*[fetch_one(mid) for mid in match_ids]),
            timeout=20.0,   # 20s max pour tout l'historique
        )
    except asyncio.TimeoutError:
        results = []

    return [r for r in results if r is not None]


async def get_match_result(puuid: str, riot_game_id: str, region: str) -> dict | None:
    try:
        routing = ROUTING.get(region.upper(), "europe")

        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?count=5"
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=get_headers())
            if res.status_code != 200:
                return None
            match_ids = res.json()

        target_match_id = None
        for mid in match_ids:
            if mid.split("_")[-1] == str(riot_game_id):
                target_match_id = mid
                break

        if not target_match_id:
            return None

        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{target_match_id}"
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(url, headers=get_headers())
            if res.status_code != 200:
                return None
            match_data = res.json()

        info         = match_data["info"]
        participants = info["participants"]
        teams        = info["teams"]
        duration_s   = info.get("gameDuration", 0)

        # ── Équipe gagnante ───────────────────────────────────
        winner_team = None
        for team in teams:
            if team.get("win"):
                winner_team = "blue" if team["teamId"] == 100 else "red"
                break

        # ── First Blood ───────────────────────────────────────
        first_blood_champ = None
        for p in participants:
            if p.get("firstBloodKill"):
                first_blood_champ = p.get("championName")
                break

        # ── Objectifs par équipe ──────────────────────────────
        objectives = {}
        for team in teams:
            side = "blue" if team["teamId"] == 100 else "red"
            obj  = team.get("objectives", {})
            objectives[side] = {
                "first_tower":  obj.get("tower",  {}).get("first", False),
                "first_dragon": obj.get("dragon", {}).get("first", False),
                "first_baron":  obj.get("baron",  {}).get("first", False),
            }

        first_tower_side  = next((s for s, o in objectives.items() if o["first_tower"]),  None)
        first_dragon_side = next((s for s, o in objectives.items() if o["first_dragon"]), None)
        first_baron_side  = next((s for s, o in objectives.items() if o["first_baron"]),  None)

        # ── Durée ─────────────────────────────────────────────
        duration_min = duration_s / 60

        # ── Stats par joueur ──────────────────────────────────
        # { puuid: { kda, damage, is_jungle, champ, side, ... } }
        player_stats: dict[str, dict] = {}
        for p in participants:
            k = p.get("kills",   0)
            d = p.get("deaths",  0)
            a = p.get("assists", 0)
            kda = (k + a) / max(d, 1)

            spells    = {p.get("spell1Id"), p.get("spell2Id")}
            is_jungle = 11 in spells  # Smite

            player_stats[p["puuid"]] = {
                "championName": p.get("championName", ""),
                "side":         "blue" if p.get("teamId") == 100 else "red",
                "kills":        k,
                "deaths":       d,
                "assists":      a,
                "kda":          round(kda, 2),
                "damage":       p.get("totalDamageDealtToChampions", 0),
                "is_jungle":    is_jungle,
                "objectives":   p.get("neutralMinionsKilled", 0),
            }

        # ── KDA positif { puuid: bool } ───────────────────────
        kda_positive = {
            puuid: (s["kills"] + s["assists"]) > s["deaths"]
            for puuid, s in player_stats.items()
        }

        # ── Top dégâts global ─────────────────────────────────
        top_damage_champ = max(
            player_stats.values(),
            key=lambda s: s["damage"],
            default=None,
        )
        top_damage_champ_name = top_damage_champ["championName"] if top_damage_champ else None

        # ── Jungle Gap ────────────────────────────────────────
        # Trouve les deux junglers
        junglers = {puuid: s for puuid, s in player_stats.items() if s["is_jungle"]}
        jungle_gap_side = None   # side du jungler DOMINANT

        if len(junglers) == 2:
            j_list  = list(junglers.values())
            j_blue  = next((s for s in j_list if s["side"] == "blue"), None)
            j_red   = next((s for s in j_list if s["side"] == "red"),  None)

            if j_blue and j_red:
                # Score composite par jungler : KDA normalisé + dégâts normalisés + objectifs normalisés
                def jg_score(j: dict) -> float:
                    return j["kda"] * 0.35 + (j["damage"] / 1000) * 0.35 + j["objectives"] * 0.30

                score_blue = jg_score(j_blue)
                score_red  = jg_score(j_red)
                total      = score_blue + score_red

                if total > 0:
                    ratio = max(score_blue, score_red) / total
                    # Gap détecté si le dominant représente > 62% du total
                    logger.info(f"   🌿 JG scores — blue: {score_blue:.2f} | red: {score_red:.2f} | ratio: {ratio:.2f}")
                    print(f"   🌿 JG scores — blue: {score_blue:.2f} | red: {score_red:.2f} | ratio: {ratio:.2f}")
                    if ratio > 0.55:
                        jungle_gap_side = "blue" if score_blue > score_red else "red"

        return {
            "winner_team":          winner_team,
            "first_blood":          first_blood_champ,
            "first_tower_side":     first_tower_side,
            "first_dragon_side":    first_dragon_side,
            "first_baron_side":     first_baron_side,
            "duration_s":           duration_s,
            "duration_min":         round(duration_min, 2),
            "kda_positive":         kda_positive,
            "player_stats":         player_stats,       # { puuid: {...} }
            "top_damage_champ":     top_damage_champ_name,
            "jungle_gap_side":      jungle_gap_side,    # "blue" | "red" | None
        }

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"get_match_result error: {e}")
        return None