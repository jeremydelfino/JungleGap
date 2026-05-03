"""
services/leaguepedia_scraper.py
Scrape Leaguepedia (Cargo via mwrogue) pour collecter picks/bans/winrates Pro.

Toute la data est dans ScoreboardGames — pas besoin de jointure.
"""
from __future__ import annotations
import os
import logging
from collections import defaultdict
from datetime import datetime, timezone
import time

from mwrogue.esports_client import EsportsClient

from database import SessionLocal
from models.champion_pro_stats import ChampionProStats

logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────
DECAY_DAYS = 365

TARGET_TOURNAMENTS = [
    # ─── 2026 (poids fort avec décay 365j) ───
    "LEC 2026 Versus",
    "LEC 2026 Versus Playoffs",
    "LEC 2026 Spring",
    "LEC 2026 Spring Playoffs",
    "LCK Cup 2026",
    "LCK 2026 Rounds 1-2",
    "LPL 2026 Split 1",
    "LPL 2026 Split 1 Playoffs",
    "LPL 2026 Split 2",
    "LPL 2026 Split 2 Playoffs",
    "First Stand 2026",
    # ─── 2025 (poids moyen) ───
    "LEC 2025 Summer",
    "LEC 2025 Summer Playoffs",
    "LCK 2025 Rounds 3-5",
    "LCK 2025 Season Playoffs",
    "LPL 2025 Split 3",
    "LPL 2025 Grand Finals",
    "LTA 2025 Championship",
    # ─── International (poids variable selon date) ───
    "Worlds 2025 Main Event",
    "MSI 2025",
]

LANE_BY_INDEX = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]


# ─── Auth client mwrogue ──────────────────────────────────────
_client: EsportsClient | None = None


def _get_client() -> EsportsClient:
    global _client
    if _client is None:
        from mwcleric.auth_credentials import AuthCredentials
        username = os.environ.get("LEAGUEPEDIA_USERNAME")
        password = os.environ.get("LEAGUEPEDIA_PASSWORD")
        if not username or not password:
            raise RuntimeError("LEAGUEPEDIA_USERNAME / LEAGUEPEDIA_PASSWORD manquants")
        creds = AuthCredentials(username=username, password=password)
        _client = EsportsClient("lol", credentials=creds)
        logger.info(f"[leaguepedia] login OK as {username}")
    return _client


# ─── Helpers ──────────────────────────────────────────────────
def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace(" ", "T")).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _decay_weight(game_date: datetime, now: datetime, decay_days: int = DECAY_DAYS) -> float:
    days_ago = (now - game_date).total_seconds() / 86400.0
    if days_ago <= 0:
        return 1.0
    if days_ago >= decay_days:
        return 0.0
    return 1.0 - (days_ago / decay_days)


def _split_csv(s: str | None) -> list[str]:
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]


# ─── Cargo query ──────────────────────────────────────────────
def _fetch_tournament_games(tournament: str, max_retries: int = 3) -> list[dict]:
    """
    Récupère les games d'un tournoi avec retry sur rate limit.
    Backoff exponentiel : 30s, 60s, 120s.
    """
    client = _get_client()

    for attempt in range(max_retries):
        try:
            rows = client.cargo_client.query(
                tables="ScoreboardGames",
                fields=(
                    "Tournament,"
                    "DateTime_UTC=date,"
                    "WinTeam=winner,"
                    "Team1=t1,"
                    "Team2=t2,"
                    "Team1Picks=t1picks,"
                    "Team2Picks=t2picks,"
                    "Team1Bans=t1bans,"
                    "Team2Bans=t2bans"
                ),
                where=f'Tournament="{tournament}"',
                order_by="DateTime_UTC ASC",
                limit="max",
            )
            logger.info(f"[leaguepedia] {tournament}: {len(rows)} games récupérées")
            return [dict(r) for r in rows]

        except Exception as e:
            err_str = str(e)
            is_ratelimit = "ratelimited" in err_str.lower()
            is_last_attempt = (attempt == max_retries - 1)

            if is_ratelimit and not is_last_attempt:
                wait = 30 * (2 ** attempt)   # 30s, 60s, 120s
                logger.warning(f"[leaguepedia] {tournament} rate limited, attente {wait}s (try {attempt+1}/{max_retries})")
                time.sleep(wait)
                continue
            else:
                logger.warning(f"[leaguepedia] {tournament} échec définitif : {e}")
                return []

    return []

# ─── Agrégation ───────────────────────────────────────────────
def _aggregate_games(rows: list[dict], now: datetime) -> tuple[dict, dict, float]:
    picks_data: dict[tuple[str, str], dict] = defaultdict(lambda: {"n_picks_w": 0.0, "n_wins_w": 0.0})
    bans_data:  dict[str, float]            = defaultdict(float)
    total_games_w = 0.0

    for row in rows:
        date = _parse_date(row.get("date"))
        if not date:
            continue
        weight = _decay_weight(date, now)
        if weight <= 0:
            continue

        team1     = (row.get("t1")     or "").strip()
        team2     = (row.get("t2")     or "").strip()
        win_team  = (row.get("winner") or "").strip()

        team1_picks = _split_csv(row.get("t1picks"))
        team2_picks = _split_csv(row.get("t2picks"))
        team1_bans  = _split_csv(row.get("t1bans"))
        team2_bans  = _split_csv(row.get("t2bans"))

        if len(team1_picks) != 5 or len(team2_picks) != 5:
            continue

        total_games_w += weight

        team1_won = (win_team == team1)
        for i, champ in enumerate(team1_picks):
            lane = LANE_BY_INDEX[i]
            picks_data[(champ, lane)]["n_picks_w"] += weight
            if team1_won:
                picks_data[(champ, lane)]["n_wins_w"] += weight

        team2_won = (win_team == team2)
        for i, champ in enumerate(team2_picks):
            lane = LANE_BY_INDEX[i]
            picks_data[(champ, lane)]["n_picks_w"] += weight
            if team2_won:
                picks_data[(champ, lane)]["n_wins_w"] += weight

        for champ in team1_bans + team2_bans:
            bans_data[champ] += weight

    return dict(picks_data), dict(bans_data), total_games_w


def _persist(picks_data: dict, bans_data: dict, total_games_w: float, db) -> int:
    if total_games_w <= 0:
        logger.warning("[leaguepedia] total_games_w=0, skip persist")
        return 0

    total_picks_per_champ: dict[str, float] = defaultdict(float)
    for (champ, lane), d in picks_data.items():
        total_picks_per_champ[champ] += d["n_picks_w"]

    db.query(ChampionProStats).delete()
    written = 0

    for (champ, lane), d in picks_data.items():
        n_picks_w = d["n_picks_w"]
        n_wins_w  = d["n_wins_w"]

        total_picks_for_champ = total_picks_per_champ[champ]
        lane_share = (n_picks_w / total_picks_for_champ) if total_picks_for_champ > 0 else 0.0
        n_bans_w_for_lane = bans_data.get(champ, 0.0) * lane_share

        pickrate = n_picks_w / total_games_w
        banrate  = n_bans_w_for_lane / total_games_w
        presence = pickrate + banrate
        winrate  = (n_wins_w / n_picks_w) if n_picks_w > 0 else 0.50

        db.add(ChampionProStats(
            champion       = champ,
            lane           = lane,
            n_picks        = int(round(n_picks_w)),
            n_bans         = int(round(n_bans_w_for_lane)),
            n_games_total  = int(round(total_games_w)),
            pickrate       = round(pickrate, 4),
            banrate        = round(banrate,  4),
            presence       = round(presence, 4),
            winrate        = round(winrate,  4),
        ))
        written += 1

    full_ban_only = set(bans_data.keys()) - set(total_picks_per_champ.keys())
    for champ in full_ban_only:
        n_bans_w = bans_data[champ]
        if n_bans_w < 1:
            continue
        banrate = n_bans_w / total_games_w
        db.add(ChampionProStats(
            champion       = champ,
            lane           = "ALL",
            n_picks        = 0,
            n_bans         = int(round(n_bans_w)),
            n_games_total  = int(round(total_games_w)),
            pickrate       = 0.0,
            banrate        = round(banrate, 4),
            presence       = round(banrate, 4),
            winrate        = 0.50,
        ))
        written += 1

    db.commit()
    return written


# ─── Job principal ────────────────────────────────────────────
def refresh_pro_stats(
    tournaments: list[str] | None = None,
    sleep_between: float = 15.0,   # 15s entre chaque tournoi
) -> dict:
    """
    Sync les picks/bans Pro depuis Leaguepedia avec retry par tournoi
    et pause entre chaque pour éviter le rate limit anonyme.
    """
    targets = tournaments or TARGET_TOURNAMENTS
    now = _now_utc()

    all_rows: list[dict] = []
    per_tournament_count: dict[str, int] = {}

    for i, tournament in enumerate(targets):
        rows = _fetch_tournament_games(tournament)
        per_tournament_count[tournament] = len(rows)
        all_rows.extend(rows)

        # Pause entre tournois (sauf après le dernier)
        if i < len(targets) - 1:
            time.sleep(sleep_between)

    if not all_rows:
        return {
            "error":               "Aucune game récupérée",
            "tournaments_queried": targets,
            "per_tournament":      per_tournament_count,
        }

    picks_data, bans_data, total_games_w = _aggregate_games(all_rows, now)

    db = SessionLocal()
    try:
        written = _persist(picks_data, bans_data, total_games_w, db)
    finally:
        db.close()

    return {
        "tournaments":          targets,
        "per_tournament":       per_tournament_count,
        "total_games_raw":      len(all_rows),
        "total_games_weighted": round(total_games_w, 1),
        "rows_written":         written,
        "synced_at":            now.isoformat(),
    }