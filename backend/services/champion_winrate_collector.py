"""
services/champion_winrate_collector.py
Collecte les winrates de champions à partir d'un échantillon Master+.

Pipeline :
  1. Pull leaderboards Master+ via LEAGUE-V4 (max ~300 puuids par région)
  2. Pull les 30 dernières games en queue 420 par puuid (capped pour rate limit)
  3. Dédupliquer les match_ids
  4. Pull les détails de chaque match (parallélisé avec semaphore)
  5. Agréger par (champion, lane, region), par paires (synergies par lanes), et par matchups (par lane)
  6. Upsert en DB

Cadence recommandée : 1x par semaine (mercredi 6h UTC).
"""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime
import httpx

from database import SessionLocal
from models.champion_stats import ChampionStats
from models.champion_synergy import ChampionSynergy
from models.champion_matchups import ChampionMatchup
from services.riot import ROUTING, get_headers
from services.riot_league import get_master_plus_puuids
from services.job_runner import tracked_job

logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────
REGIONS_TO_SAMPLE   = ["EUW", "KR"]
PUUIDS_PER_TIER     = 100
MATCHES_PER_PUUID   = 30
MAX_CONCURRENT_API  = 10
MIN_GAMES_PER_CHAMP = 20
MIN_PAIR_GAMES      = 15    # ← 50 → 15
MIN_MATCHUP_GAMES   = 10    # ← 30 → 10

LANE_MAPPING = {
    "TOP":     "TOP",
    "JUNGLE":  "JUNGLE",
    "MIDDLE":  "MID",
    "BOTTOM":  "ADC",
    "UTILITY": "SUPPORT",
}


# ─── Factories defaultdict (corrige le bug dmg_share_sum manquant) ───
def _champ_factory():
    return {"wins": 0, "total": 0, "kda_sum": 0.0, "kp_sum": 0.0, "dmg_share_sum": 0.0}

def _synergy_factory():
    return {"wins": 0, "total": 0}

def _matchup_factory():
    return {"a_wins": 0, "total": 0}


# ─── Fetch Riot API ───────────────────────────────────────────
async def _fetch_match_ids(puuid: str, region: str, count: int = MATCHES_PER_PUUID) -> list[str]:
    routing = ROUTING.get(region.upper(), "europe")
    url = (
        f"https://{routing}.api.riotgames.com"
        f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        f"?queue=420&count={count}"
    )
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(url, headers=get_headers())
            return r.json() if r.status_code == 200 else []
    except Exception:
        return []


async def _fetch_match_detail(match_id: str, routing: str, sem: asyncio.Semaphore) -> dict | None:
    async with sem:
        url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(url, headers=get_headers())
                if r.status_code == 200:
                    return r.json()
                if r.status_code == 429:
                    retry_after = int(r.headers.get("Retry-After", 5))
                    logger.warning(f"429 sur {match_id}, attente {retry_after}s")
                    await asyncio.sleep(retry_after)
                    async with httpx.AsyncClient(timeout=10) as c2:
                        r2 = await c2.get(url, headers=get_headers())
                        return r2.json() if r2.status_code == 200 else None
        except Exception:
            return None
    return None


# ─── Collection par région ────────────────────────────────────
async def _collect_for_region(region: str) -> tuple[dict, dict, dict]:
    """
    Retourne (champion_data, synergy_data, matchup_data) pour une région.
      - champion_data : (champ, lane) → {wins,total,kda_sum,kp_sum,dmg_share_sum}
      - synergy_data  : (champA, champB, laneA, laneB) → {wins,total}  (clé triée alpha sur (champ, lane))
      - matchup_data  : (champA, champB, lane)        → {a_wins,total} (clé triée alpha sur champ)
    """
    logger.info(f"[champ_collector] région {region} — start")

    puuids = await get_master_plus_puuids(region, max_per_tier=PUUIDS_PER_TIER)
    if not puuids:
        logger.warning(f"[champ_collector] {region}: aucun puuid récupéré, skip")
        return {}, {}, {}

    logger.info(f"[champ_collector] {region}: {len(puuids)} puuids")

    sem_ids = asyncio.Semaphore(MAX_CONCURRENT_API)
    async def get_ids_throttled(p):
        async with sem_ids:
            return await _fetch_match_ids(p, region)

    all_match_id_lists = await asyncio.gather(*[get_ids_throttled(p) for p in puuids])
    unique_match_ids: set[str] = set()
    for ml in all_match_id_lists:
        unique_match_ids.update(ml)

    logger.info(f"[champ_collector] {region}: {len(unique_match_ids)} match_ids uniques")

    routing = ROUTING.get(region.upper(), "europe")
    sem_match = asyncio.Semaphore(MAX_CONCURRENT_API)

    matches: list[dict] = []
    BATCH_SIZE = 500
    match_id_list = list(unique_match_ids)

    for i in range(0, len(match_id_list), BATCH_SIZE):
        batch    = match_id_list[i:i + BATCH_SIZE]
        results  = await asyncio.gather(*[_fetch_match_detail(mid, routing, sem_match) for mid in batch])
        matches.extend(m for m in results if m)
        logger.info(f"[champ_collector] {region}: batch {i // BATCH_SIZE + 1} fetched, total={len(matches)}")
        if i + BATCH_SIZE < len(match_id_list):
            await asyncio.sleep(2)

    logger.info(f"[champ_collector] {region}: {len(matches)} matches détaillés récupérés")

    champion_data: dict[tuple[str, str], dict]                    = defaultdict(_champ_factory)
    synergy_data:  dict[tuple[str, str, str, str], dict]          = defaultdict(_synergy_factory)
    matchup_data:  dict[tuple[str, str, str], dict]               = defaultdict(_matchup_factory)

    for match in matches:
        info         = match.get("info", {})
        participants = info.get("participants", [])
        if len(participants) != 10:
            continue
        if info.get("gameDuration", 0) < 300:
            continue

        # Group par teamId
        teams: dict[int, list[dict]] = defaultdict(list)
        for p in participants:
            teams[p.get("teamId")].append(p)
        if 100 not in teams or 200 not in teams or len(teams[100]) != 5 or len(teams[200]) != 5:
            continue

        # ── Stats par champion + synergies par lane ──
        for team_id, team_players in teams.items():
            team_kills     = sum(p.get("kills", 0) for p in team_players)
            team_total_dmg = sum(p.get("totalDamageDealtToChampions", 0) for p in team_players)

            # On annote chaque joueur avec sa lane normalisée
            annotated = []
            for p in team_players:
                champ = p.get("championName", "")
                pos   = p.get("teamPosition", "") or p.get("individualPosition", "")
                lane  = LANE_MAPPING.get(pos, "")
                if not champ or not lane:
                    continue
                annotated.append({**p, "_champ": champ, "_lane": lane})

                kills   = p.get("kills",   0)
                deaths  = p.get("deaths",  0)
                assists = p.get("assists", 0)
                win     = bool(p.get("win", False))
                dmg     = p.get("totalDamageDealtToChampions", 0)

                kda        = (kills + assists) / max(deaths, 1)
                kp         = (kills + assists) / max(team_kills, 1)
                dmg_share  = dmg / max(team_total_dmg, 1)

                key = (champ, lane)
                champion_data[key]["total"]         += 1
                champion_data[key]["wins"]          += int(win)
                champion_data[key]["kda_sum"]       += kda
                champion_data[key]["kp_sum"]        += kp
                champion_data[key]["dmg_share_sum"] += dmg_share

            # Synergies AVEC lane — paires de l'équipe, clé triée sur (champ, lane)
            for i in range(len(annotated)):
                for j in range(i + 1, len(annotated)):
                    p1, p2 = annotated[i], annotated[j]
                    a, la = p1["_champ"], p1["_lane"]
                    b, lb = p2["_champ"], p2["_lane"]
                    if (a, la) > (b, lb):
                        a, la, b, lb = b, lb, a, la
                    key = (a, b, la, lb)
                    synergy_data[key]["total"] += 1
                    synergy_data[key]["wins"]  += int(p1.get("win", False))

        # ── Matchups par lane (blue vs red) ──
        blue_by_lane = {}
        red_by_lane  = {}
        for p in teams[100]:
            lane = LANE_MAPPING.get(p.get("teamPosition", "") or p.get("individualPosition", ""), "")
            if lane:
                blue_by_lane[lane] = p
        for p in teams[200]:
            lane = LANE_MAPPING.get(p.get("teamPosition", "") or p.get("individualPosition", ""), "")
            if lane:
                red_by_lane[lane] = p

        for lane in ("TOP", "JUNGLE", "MID", "ADC", "SUPPORT"):
            bp = blue_by_lane.get(lane)
            rp = red_by_lane.get(lane)
            if not bp or not rp:
                continue
            c_blue = bp.get("championName", "")
            c_red  = rp.get("championName", "")
            if not c_blue or not c_red or c_blue == c_red:
                continue

            if c_blue < c_red:
                a, b   = c_blue, c_red
                a_won  = bool(bp.get("win", False))
            else:
                a, b   = c_red, c_blue
                a_won  = bool(rp.get("win", False))

            key = (a, b, lane)
            matchup_data[key]["total"]  += 1
            matchup_data[key]["a_wins"] += int(a_won)

    return dict(champion_data), dict(synergy_data), dict(matchup_data)


# ─── Persist ──────────────────────────────────────────────────
def _persist_champion_stats(champion_data: dict, region: str, db) -> int:
    total_games_by_lane: dict[str, int] = defaultdict(int)
    for (champ, lane), data in champion_data.items():
        total_games_by_lane[lane] += data["total"]

    written = 0
    for (champ, lane), data in champion_data.items():
        if data["total"] < MIN_GAMES_PER_CHAMP:
            continue

        winrate       = data["wins"] / data["total"]
        avg_kda       = data["kda_sum"]       / data["total"]
        avg_kp        = data["kp_sum"]        / data["total"]
        avg_dmg_share = data["dmg_share_sum"] / data["total"]
        pickrate      = data["total"] / max(total_games_by_lane[lane] / 5, 1)

        existing = db.query(ChampionStats).filter(
            ChampionStats.champion == champ,
            ChampionStats.tier     == "MASTER",
            ChampionStats.lane     == lane,
            ChampionStats.region   == region,
        ).first()

        if existing:
            existing.n_games       = data["total"]
            existing.wins          = data["wins"]
            existing.winrate       = round(winrate, 4)
            existing.pickrate      = round(pickrate, 4)
            existing.avg_kda       = round(avg_kda, 3)
            existing.avg_kp        = round(avg_kp, 3)
            existing.avg_dmg_share = round(avg_dmg_share, 3)
        else:
            db.add(ChampionStats(
                champion=champ, tier="MASTER", lane=lane, region=region,
                n_games=data["total"], wins=data["wins"],
                winrate=round(winrate, 4), pickrate=round(pickrate, 4),
                avg_kda=round(avg_kda, 3), avg_kp=round(avg_kp, 3),
                avg_dmg_share=round(avg_dmg_share, 3),
            ))
        written += 1

    db.commit()
    return written


def _persist_synergies(synergy_data: dict, champion_data: dict, region: str, db) -> int:
    """
    Synergies par lane. WR de référence = WR du champion sur sa lane (plus précis qu'avant).
    """
    # WR par (champ, lane)
    solo_wr: dict[tuple[str, str], float] = {}
    for (champ, lane), data in champion_data.items():
        if data["total"] >= MIN_GAMES_PER_CHAMP:
            solo_wr[(champ, lane)] = data["wins"] / data["total"]

    written = 0
    for (a, b, la, lb), data in synergy_data.items():
        if data["total"] < MIN_PAIR_GAMES:
            continue
        wr_pair = data["wins"] / data["total"]

        wr_a = solo_wr.get((a, la), 0.50)
        wr_b = solo_wr.get((b, lb), 0.50)
        wr_avg = (wr_a + wr_b) / 2
        synergy_score = wr_pair - wr_avg

        existing = db.query(ChampionSynergy).filter(
            ChampionSynergy.champion_a == a,
            ChampionSynergy.champion_b == b,
            ChampionSynergy.lane_a     == la,
            ChampionSynergy.lane_b     == lb,
            ChampionSynergy.tier       == "MASTER",
            ChampionSynergy.region     == region,
        ).first()

        if existing:
            existing.n_games       = data["total"]
            existing.wins          = data["wins"]
            existing.winrate       = round(wr_pair, 4)
            existing.synergy_score = round(synergy_score, 4)
        else:
            db.add(ChampionSynergy(
                champion_a=a, champion_b=b, lane_a=la, lane_b=lb,
                tier="MASTER", region=region,
                n_games=data["total"], wins=data["wins"],
                winrate=round(wr_pair, 4),
                synergy_score=round(synergy_score, 4),
            ))
        written += 1

    db.commit()
    return written


def _persist_matchups(matchup_data: dict, region: str, db) -> int:
    written = 0
    for (a, b, lane), data in matchup_data.items():
        if data["total"] < MIN_MATCHUP_GAMES:
            continue

        winrate_a = data["a_wins"] / data["total"]

        existing = db.query(ChampionMatchup).filter(
            ChampionMatchup.champion_a == a,
            ChampionMatchup.champion_b == b,
            ChampionMatchup.lane       == lane,
            ChampionMatchup.tier       == "MASTER",
            ChampionMatchup.region     == region,
        ).first()

        if existing:
            existing.n_games   = data["total"]
            existing.a_wins    = data["a_wins"]
            existing.winrate_a = round(winrate_a, 4)
        else:
            db.add(ChampionMatchup(
                champion_a=a, champion_b=b, lane=lane,
                tier="MASTER", region=region,
                n_games=data["total"], a_wins=data["a_wins"],
                winrate_a=round(winrate_a, 4),
            ))
        written += 1

    db.commit()
    return written


# ─── Job principal ────────────────────────────────────────────
@tracked_job("refresh_champion_winrates")
async def refresh_champion_winrates() -> dict:
    """
    Sample Master+ EUW + KR, écrit ChampionStats + ChampionSynergy + ChampionMatchup.
    """
    db = SessionLocal()
    total_champ_rows    = 0
    total_synergy_rows  = 0
    total_matchup_rows  = 0

    try:
        all_champ_data:   dict[tuple[str, str], dict]               = defaultdict(_champ_factory)
        all_synergy_data: dict[tuple[str, str, str, str], dict]     = defaultdict(_synergy_factory)
        all_matchup_data: dict[tuple[str, str, str], dict]          = defaultdict(_matchup_factory)

        for region in REGIONS_TO_SAMPLE:
            try:
                champ_data, synergy_data, matchup_data = await _collect_for_region(region)
            except Exception as e:
                logger.error(f"[champ_collector] {region} échec : {e}", exc_info=True)
                continue

            total_champ_rows   += _persist_champion_stats(champ_data, region, db)
            total_synergy_rows += _persist_synergies(synergy_data, champ_data, region, db)
            total_matchup_rows += _persist_matchups(matchup_data, region, db)

            for k, v in champ_data.items():
                all_champ_data[k]["wins"]          += v["wins"]
                all_champ_data[k]["total"]         += v["total"]
                all_champ_data[k]["kda_sum"]       += v["kda_sum"]
                all_champ_data[k]["kp_sum"]        += v["kp_sum"]
                all_champ_data[k]["dmg_share_sum"] += v["dmg_share_sum"]
            for k, v in synergy_data.items():
                all_synergy_data[k]["wins"]  += v["wins"]
                all_synergy_data[k]["total"] += v["total"]
            for k, v in matchup_data.items():
                all_matchup_data[k]["a_wins"] += v["a_wins"]
                all_matchup_data[k]["total"]  += v["total"]

        # Région ALL
        total_champ_rows   += _persist_champion_stats(dict(all_champ_data),   "ALL", db)
        total_synergy_rows += _persist_synergies(dict(all_synergy_data),      dict(all_champ_data), "ALL", db)
        total_matchup_rows += _persist_matchups(dict(all_matchup_data),       "ALL", db)

    finally:
        db.close()

    return {
        "records_processed": total_champ_rows + total_synergy_rows + total_matchup_rows,
        "metadata": {
            "champion_rows": total_champ_rows,
            "synergy_rows":  total_synergy_rows,
            "matchup_rows":  total_matchup_rows,
            "regions":       REGIONS_TO_SAMPLE,
            "sampled_at":    datetime.utcnow().isoformat(),
        },
    }