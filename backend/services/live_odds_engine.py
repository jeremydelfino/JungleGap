"""
services/live_odds_engine.py
Moteur de côtes pour les games live (ranked solo/duo avec pros ou joueurs lambda).

Formule par équipe :
  score = winrate_global * 0.25
        + winrate_champ  * 0.25
        + forme_5        * 0.20
        + winrate_team   * 0.10   (moyenne winrate_global des 5 joueurs)
        + draft_score    * 0.20

  s_blue, s_red = score_blue ** EXPONENT, score_red ** EXPONENT   # POLARISATION
  prob_blue     = s_blue / (s_blue + s_red)
  cote_blue     = (1 / prob_blue) * MARGIN
"""
import asyncio
import logging
from database import SessionLocal
from models.champion_stats import ChampionStats
from models.champion_synergy import ChampionSynergy
from services.riot_stats import get_player_stats

logger = logging.getLogger(__name__)

# ─── Paramètres bookmaker ────────────────────────────────────
MARGIN     = 0.92    # Marge bookmaker (~8%)
EXPONENT   = 3.5     # Polarisation : favorite à 60% → 71%, à 70% → 88%
MIN_ODDS   = 1.05    # Avant : 1.20 (trop plat)
MAX_ODDS   = 12.0    # Avant : 4.00 (impossible d'avoir un vrai outsider)
PROB_FLOOR = 0.05    # Avant : 0.20 (idem, anti-extrême trop dur)
PROB_CEIL  = 0.95

# ─── Poids du score d'équipe ─────────────────────────────────
WEIGHTS = {
    "winrate_global": 0.25,
    "winrate_champ":  0.25,
    "forme_5":        0.20,
    "winrate_team":   0.10,
    "draft":          0.20,
}

# ─── Côtes fixes pour les paris non-victoire ─────────────────
FIXED_ODDS = {
    "first_blood":            8.0,
    "first_tower":            2.5,
    "first_dragon":           2.5,
    "first_baron":            3.0,
    "game_duration_under25":  2.8,
    "game_duration_25_35":    1.8,
    "game_duration_over35":   2.5,
    "player_positive_kda":    2.2,
    "champion_kda_over25":    2.5,
    "champion_kda_over5":     3.5,
    "champion_kda_over10":    6.0,
    "top_damage":             3.0,
    "jungle_gap":             2.0,
}

# ─── Tier list champions (winrate moyen patch actuel) ────────
CHAMP_WINRATE: dict[str, float] = {
    # TOP
    "Darius": 0.52, "Garen": 0.53, "Malphite": 0.52, "Sett": 0.51,
    "Fiora": 0.50, "Camille": 0.49, "Irelia": 0.48, "Riven": 0.49,
    "Jax": 0.51, "Nasus": 0.54, "Teemo": 0.52, "Urgot": 0.52,
    "Aatrox": 0.50, "Gnar": 0.50, "Renekton": 0.49, "Ornn": 0.51,
    "Vladimir": 0.50, "Kennen": 0.50, "Gangplank": 0.49,
    # JUNGLE
    "Lee Sin": 0.47, "Vi": 0.52, "Warwick": 0.54, "Hecarim": 0.52,
    "Nocturne": 0.53, "Amumu": 0.54, "Zac": 0.53, "Jarvan IV": 0.51,
    "Nidalee": 0.47, "Elise": 0.48, "Graves": 0.50, "Kindred": 0.49,
    "Kha'Zix": 0.51, "Rengar": 0.50, "Shaco": 0.51, "Udyr": 0.52,
    "Viego": 0.50, "Lillia": 0.51, "Diana": 0.52, "Evelynn": 0.50,
    # MID
    "Zed": 0.50, "Syndra": 0.51, "Orianna": 0.51, "Viktor": 0.50,
    "Lux": 0.53, "Veigar": 0.53, "Annie": 0.54, "Malzahar": 0.53,
    "Ahri": 0.52, "Yasuo": 0.49, "Yone": 0.50, "Katarina": 0.50,
    "Akali": 0.48, "Fizz": 0.51, "Cassiopeia": 0.51, "Twisted Fate": 0.50,
    # ADC
    "Jinx": 0.53, "Caitlyn": 0.51, "Miss Fortune": 0.53, "Ashe": 0.53,
    "Jhin": 0.52, "Sivir": 0.52, "Xayah": 0.51, "Draven": 0.50,
    "Kai'Sa": 0.51, "Ezreal": 0.49, "Lucian": 0.49, "Tristana": 0.51,
    "Twitch": 0.52, "Kog'Maw": 0.53, "Samira": 0.51, "Zeri": 0.50,
    # SUPPORT
    "Thresh": 0.50, "Lulu": 0.53, "Nautilus": 0.52, "Blitzcrank": 0.52,
    "Soraka": 0.54, "Nami": 0.53, "Janna": 0.54, "Morgana": 0.52,
    "Leona": 0.51, "Alistar": 0.51, "Braum": 0.51, "Pyke": 0.50,
    "Senna": 0.51, "Zyra": 0.52, "Bard": 0.50, "Karma": 0.52,
}

# ─── Synergies connues (paires de champions) ─────────────────
SYNERGIES: dict[frozenset, float] = {
    frozenset({"Yasuo",      "Malphite"}):     0.14,
    frozenset({"Yasuo",      "Wukong"}):       0.12,
    frozenset({"Kalista",    "Thresh"}):       0.13,
    frozenset({"Lucian",     "Nami"}):         0.13,
    frozenset({"Xayah",      "Rakan"}):        0.14,
    frozenset({"Miss Fortune","Leona"}):       0.11,
    frozenset({"Ornn",       "Aphelios"}):     0.11,
    frozenset({"Twisted Fate","Nocturne"}):    0.13,
    frozenset({"Twisted Fate","Zed"}):         0.11,
    frozenset({"Shen",       "Miss Fortune"}): 0.12,
    frozenset({"Shen",       "Jinx"}):         0.11,
}


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


_DB_WR_CACHE: dict = {"data": None, "expires_at": 0}
_DB_WR_TTL_SECONDS = 600  # 10 min

def _load_champion_winrates_from_db() -> dict[str, float] | None:
    """Charge le dict {champion: winrate} depuis la DB (région ALL, lane ALL pondéré).
    Retourne None si la table est vide → fallback sur CHAMP_WINRATE hardcodé."""
    import time
    now = time.time()
    if _DB_WR_CACHE["data"] is not None and _DB_WR_CACHE["expires_at"] > now:
        return _DB_WR_CACHE["data"]

    db = SessionLocal()
    try:
        rows = db.query(ChampionStats).filter(
            ChampionStats.tier   == "MASTER",
            ChampionStats.region == "ALL",
        ).all()
        if not rows:
            return None

        # Agrège toutes lanes confondues, pondéré par n_games
        agg: dict[str, list[tuple[float, int]]] = {}
        for r in rows:
            agg.setdefault(r.champion, []).append((r.winrate, r.n_games))

        result = {}
        for champ, items in agg.items():
            total_games = sum(n for _, n in items)
            if total_games == 0:
                continue
            wr = sum(w * n for w, n in items) / total_games
            result[champ] = wr

        _DB_WR_CACHE["data"]       = result
        _DB_WR_CACHE["expires_at"] = now + _DB_WR_TTL_SECONDS
        logger.info(f"📥 ChampionStats DB → {len(result)} champions chargés en cache")
        return result
    except Exception as e:
        logger.warning(f"_load_champion_winrates_from_db error : {e}, fallback hardcoded")
        return None
    finally:
        db.close()


def _load_synergies_from_db() -> dict[frozenset, float] | None:
    """Charge {frozenset({c1,c2}): synergy_score}. Retourne None si vide."""
    import time
    now = time.time()
    cache_key = "synergies"
    if _DB_WR_CACHE.get(cache_key) is not None and _DB_WR_CACHE.get(f"{cache_key}_exp", 0) > now:
        return _DB_WR_CACHE[cache_key]

    db = SessionLocal()
    try:
        rows = db.query(ChampionSynergy).filter(
            ChampionSynergy.tier   == "MASTER",
            ChampionSynergy.region == "ALL",
            ChampionSynergy.synergy_score > 0.02,  # seuil : on garde que les vraies synergies
        ).all()
        if not rows:
            return None
        result = {frozenset({r.champion_a, r.champion_b}): r.synergy_score for r in rows}
        _DB_WR_CACHE[cache_key]               = result
        _DB_WR_CACHE[f"{cache_key}_exp"]      = now + _DB_WR_TTL_SECONDS
        logger.info(f"📥 ChampionSynergy DB → {len(result)} paires chargées")
        return result
    except Exception:
        return None
    finally:
        db.close()


# ── Remplace ta fonction _draft_score existante par celle-ci ──
def _draft_score(champ_names: list[str]) -> float:
    """
    Score de draft [0, 1] basé sur :
    - Moyenne des winrates champion (DB > fallback hardcodé)
    - Bonus synergies détectées dans la composition (DB > fallback hardcodé)
    """
    champs = [c for c in champ_names if c]

    # Source DB en priorité, fallback sur le dict hardcodé
    db_winrates = _load_champion_winrates_from_db()
    db_synergies = _load_synergies_from_db()

    wr_source       = db_winrates if db_winrates is not None else CHAMP_WINRATE
    synergy_source  = db_synergies if db_synergies is not None else SYNERGIES

    # Winrate moyen des champions
    wr_list = [wr_source.get(c, 0.50) for c in champs]
    wr_mean = sum(wr_list) / len(wr_list) if wr_list else 0.50

    # Bonus synergies
    synergie_bonus = 0.0
    seen = set()
    for i in range(len(champs)):
        for j in range(i + 1, len(champs)):
            pair = frozenset({champs[i], champs[j]})
            if pair in synergy_source and pair not in seen:
                synergie_bonus += synergy_source[pair]
                seen.add(pair)
    synergie_bonus = min(synergie_bonus, 0.15)

    draft = (wr_mean - 0.50) * 2 + 0.50
    return _clamp(draft + synergie_bonus, 0.30, 0.85)

async def _team_score(team: list[dict], region: str) -> tuple[float, list[dict]]:
    tasks = []
    for p in team:
        puuid = p.get("puuid")
        champ = p.get("championName")
        if puuid:
            tasks.append(get_player_stats(puuid, region, champ))
        else:
            tasks.append(_default_stats_coro())

    stats_list = await asyncio.gather(*tasks, return_exceptions=True)

    player_details = []
    valid_stats    = []
    for p, stats in zip(team, stats_list):
        if isinstance(stats, Exception) or stats is None:
            stats = _default_stats_dict()
        valid_stats.append(stats)
        player_details.append({
            "summonerName":   p.get("summonerName", ""),
            "championName":   p.get("championName", ""),
            "winrate_global": stats["winrate_global"],
            "winrate_champ":  stats["winrate_champ"],
            "forme_5":        stats["forme_5"],
            "n_games":        stats["n_games"],
        })

    wr_team_mean = sum(s["winrate_global"] for s in valid_stats) / len(valid_stats) if valid_stats else 0.50

    individual_weight = WEIGHTS["winrate_global"] + WEIGHTS["winrate_champ"] + WEIGHTS["forme_5"]
    def player_score(s: dict) -> float:
        return (
            s["winrate_global"] * WEIGHTS["winrate_global"] / individual_weight
            + s["winrate_champ"]  * WEIGHTS["winrate_champ"]  / individual_weight
            + s["forme_5"]        * WEIGHTS["forme_5"]        / individual_weight
        )
    avg_player_score = sum(player_score(s) for s in valid_stats) / len(valid_stats) if valid_stats else 0.50

    champ_names = [p.get("championName") for p in team]
    draft       = _draft_score(champ_names)

    score = (
        avg_player_score * (WEIGHTS["winrate_global"] + WEIGHTS["winrate_champ"] + WEIGHTS["forme_5"])
        + wr_team_mean   * WEIGHTS["winrate_team"]
        + draft          * WEIGHTS["draft"]
    )
    return _clamp(score, 0.20, 0.80), player_details


async def _default_stats_coro() -> dict:
    return _default_stats_dict()


def _default_stats_dict() -> dict:
    return {"winrate_global": 0.50, "winrate_champ": 0.50, "forme_5": 0.50, "n_games": 0, "n_games_champ": 0}


async def compute_jungle_gap_odds(blue_team: list[dict], red_team: list[dict], region: str = "EUW") -> dict:
    from services.riot_stats import get_player_stats

    def find_jungler(team: list[dict]) -> dict | None:
        for p in team:
            if (p.get("role") or "").upper() == "JUNGLE":
                return p
        for p in team:
            if 11 in {p.get("spell1Id"), p.get("spell2Id")}:
                return p
        return team[1] if len(team) > 1 else None

    jg_blue = find_jungler(blue_team)
    jg_red  = find_jungler(red_team)

    async def get_score(player: dict | None) -> float:
        if not player or not player.get("puuid"):
            return 0.50
        try:
            stats = await asyncio.wait_for(
                get_player_stats(player["puuid"], region, player.get("championName")),
                timeout=8.0,
            )
            return (
                stats["winrate_global"] * 0.40
                + stats["winrate_champ"]  * 0.35
                + stats["forme_5"]        * 0.25
            )
        except Exception:
            return 0.50

    score_blue, score_red = await asyncio.gather(get_score(jg_blue), get_score(jg_red))

    # Polarisation modérée pour le jungle gap
    s_blue = max(score_blue, 0.01) ** 2.5
    s_red  = max(score_red,  0.01) ** 2.5
    total  = s_blue + s_red
    prob_blue = _clamp(s_blue / total, 0.15, 0.85) if total > 0 else 0.50
    prob_red  = 1.0 - prob_blue

    odds_blue = round(_clamp((1.0 / prob_blue) * 0.90, 1.20, 6.00), 2)
    odds_red  = round(_clamp((1.0 / prob_red)  * 0.90, 1.20, 6.00), 2)

    return {"blue": odds_blue, "red": odds_red}


async def compute_live_odds(blue_team: list[dict], red_team: list[dict], region: str = "EUW") -> dict:
    """
    Point d'entrée principal — calcule toutes les côtes pour une game live.
    Polarisation par exposant pour donner des cotes "vraies" sur des matchups inégaux.
    """
    (score_blue, detail_blue), (score_red, detail_red) = await asyncio.gather(
        _team_score(blue_team, region),
        _team_score(red_team,  region),
    )

    # ── POLARISATION : exposant sur les scores ───────────────
    # score_blue / score_red sont dans [0.20, 0.80]. Avec EXPONENT=3.5 :
    #   - 0.55 vs 0.45 → 0.094 vs 0.061 → prob 60.7% (avant : 55%)
    #   - 0.65 vs 0.35 → 0.176 vs 0.027 → prob 86.8% (avant : 65%)
    s_blue = max(score_blue, 0.01) ** EXPONENT
    s_red  = max(score_red,  0.01) ** EXPONENT
    total  = s_blue + s_red

    prob_blue = _clamp(s_blue / total, PROB_FLOOR, PROB_CEIL) if total > 0 else 0.50
    prob_red  = 1.0 - prob_blue

    odds_blue = round(_clamp((1.0 / prob_blue) * MARGIN, MIN_ODDS, MAX_ODDS), 2)
    odds_red  = round(_clamp((1.0 / prob_red)  * MARGIN, MIN_ODDS, MAX_ODDS), 2)

    favor_blue = prob_blue - 0.50

    def obj_odds(base: float, favor: float, side: str) -> float:
        adj = -favor if side == "blue" else favor
        return round(_clamp(base * (1 + adj * 0.30), 1.30, base * 1.5), 2)

    # Jungle gap — passe par compute_jungle_gap_odds (polarisation séparée)
    try:
        jg_odds = await asyncio.wait_for(
            compute_jungle_gap_odds(blue_team, red_team, region),
            timeout=10.0,
        )
    except Exception as e:
        logger.warning(f"jungle_gap odds failed: {e}, fallback fixed")
        jg_odds = {"blue": 2.0, "red": 2.0}

    logger.info(
        f"📊 compute_live_odds → score_blue={score_blue:.3f} score_red={score_red:.3f} "
        f"| ^{EXPONENT} → prob_blue={prob_blue:.3f} | "
        f"odds: blue={odds_blue} red={odds_red}"
    )

    return {
        "who_wins": {"blue": odds_blue, "red": odds_red},
        "first_blood":           {"odds": FIXED_ODDS["first_blood"]},
        "first_tower":           {"blue": obj_odds(FIXED_ODDS["first_tower"],  favor_blue, "blue"),
                                  "red":  obj_odds(FIXED_ODDS["first_tower"],  favor_blue, "red")},
        "first_dragon":          {"blue": obj_odds(FIXED_ODDS["first_dragon"], favor_blue, "blue"),
                                  "red":  obj_odds(FIXED_ODDS["first_dragon"], favor_blue, "red")},
        "first_baron":           {"blue": obj_odds(FIXED_ODDS["first_baron"],  favor_blue, "blue"),
                                  "red":  obj_odds(FIXED_ODDS["first_baron"],  favor_blue, "red")},
        "game_duration_under25": {"odds": FIXED_ODDS["game_duration_under25"]},
        "game_duration_25_35":   {"odds": FIXED_ODDS["game_duration_25_35"]},
        "game_duration_over35":  {"odds": FIXED_ODDS["game_duration_over35"]},
        "player_positive_kda":   {"odds": FIXED_ODDS["player_positive_kda"]},
        "champion_kda_over25":   {"odds": FIXED_ODDS["champion_kda_over25"]},
        "champion_kda_over5":    {"odds": FIXED_ODDS["champion_kda_over5"]},
        "champion_kda_over10":   {"odds": FIXED_ODDS["champion_kda_over10"]},
        "top_damage":            {"odds": FIXED_ODDS["top_damage"]},
        "jungle_gap":            {"blue": jg_odds["blue"], "red": jg_odds["red"]},

        "score_blue": round(score_blue, 3),
        "score_red":  round(score_red,  3),
        "prob_blue":  round(prob_blue, 3),
        "prob_red":   round(prob_red,  3),
        "detail_blue": detail_blue,
        "detail_red":  detail_red,
    }