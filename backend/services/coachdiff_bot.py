"""
services/coachdiff_bot.py

Bot CoachDiff : aléatoire pondéré par la tier list pro.
  - Bans : pick aléatoire dans le top 20 par pickrate Pro (toutes lanes confondues)
  - Picks : pick aléatoire dans le top 30 par pickrate Pro (toutes lanes confondues)
  - Assignation rôles : greedy par pickrate Pro de lane

Pas de stratégie counter-pick / synergy en V1.
"""
from __future__ import annotations
import random
import logging
from sqlalchemy.orm import Session

from models.champion_pro_stats import ChampionProStats
from models.champion_stats     import ChampionStats
from services.coachdiff_state  import (
    current_turn, all_taken, apply_action, LANES,
)

logger = logging.getLogger(__name__)

BAN_POOL_SIZE  = 20
PICK_POOL_SIZE = 30
SOLO_FALLBACK_SIZE = 50  # si pro_stats vide, fallback sur soloQ


def _get_pro_pool(db: Session, top_n: int) -> list[tuple[str, float]]:
    """
    Top N champions par pickrate Pro (peu importe la lane).
    Retourne [(champion, pickrate), ...] dédupliqué (un champ = max pickrate de ses lanes).
    """
    rows = (
        db.query(ChampionProStats)
        .order_by(ChampionProStats.pickrate.desc())
        .limit(top_n * 3)  # marge pour dédup
        .all()
    )
    seen: dict[str, float] = {}
    for r in rows:
        if r.champion not in seen or r.pickrate > seen[r.champion]:
            seen[r.champion] = float(r.pickrate)
    pool = sorted(seen.items(), key=lambda x: -x[1])[:top_n]
    return pool


def _get_solo_pool(db: Session, top_n: int) -> list[tuple[str, float]]:
    """Fallback : top N par pickrate SoloQ Master."""
    rows = (
        db.query(ChampionStats)
        .filter(ChampionStats.tier == "MASTER")
        .order_by(ChampionStats.pickrate.desc())
        .limit(top_n * 3)
        .all()
    )
    seen: dict[str, float] = {}
    for r in rows:
        if r.champion not in seen or r.pickrate > seen[r.champion]:
            seen[r.champion] = float(r.pickrate)
    pool = sorted(seen.items(), key=lambda x: -x[1])[:top_n]
    return pool


def _choose_weighted(pool: list[tuple[str, float]], excluded: set[str]) -> str:
    """Choix pondéré par pickrate. Filtre les exclus. Fallback uniform si pool vide."""
    candidates = [(c, w) for c, w in pool if c not in excluded]
    if not candidates:
        return None
    total = sum(w for _, w in candidates)
    if total <= 0:
        return random.choice(candidates)[0]
    r = random.uniform(0, total)
    acc = 0.0
    for champ, w in candidates:
        acc += w
        if acc >= r:
            return champ
    return candidates[-1][0]


def bot_decide(db: Session, state: dict) -> str:
    """
    Décide le prochain pick/ban du bot.
    Retourne le nom du champion choisi.
    """
    turn = current_turn(state)
    if turn is None or turn["actor"] != "BOT":
        raise ValueError("Pas le tour du bot")

    pool_size = BAN_POOL_SIZE if turn["action"] == "ban" else PICK_POOL_SIZE
    pool = _get_pro_pool(db, pool_size)

    if len(pool) < 5:
        logger.warning(f"[bot] pool pro trop petit ({len(pool)}), fallback solo")
        pool = _get_solo_pool(db, SOLO_FALLBACK_SIZE)

    excluded = all_taken(state)
    choice = _choose_weighted(pool, excluded)

    if choice is None:
        logger.error(f"[bot] aucun candidat dispo, pool={len(pool)} excluded={len(excluded)}")
        # Fallback ultime : random parmi un large pool solo
        large_pool = _get_solo_pool(db, 100)
        choice = _choose_weighted(large_pool, excluded)

    if choice is None:
        raise RuntimeError("Bot n'a aucun candidat possible")

    return choice


def bot_play_turn(db: Session, state: dict) -> tuple[dict, str]:
    """
    Joue UN tour pour le bot. Retourne (state_updaté, champion_choisi).
    """
    champion = bot_decide(db, state)
    apply_action(state, champion, expected_actor="BOT")
    return state, champion


# ─── Assignation des rôles côté bot ───────────────────────────
def bot_assign_roles(db: Session, picks: list[str]) -> dict[str, str]:
    """
    Assigne les rôles aux 5 picks du bot, greedy par pickrate Pro de lane.
    Retourne {"TOP": champ, "JUNGLE": champ, ...}
    """
    if len(picks) != 5:
        raise ValueError(f"bot_assign_roles attend 5 picks, reçu {len(picks)}")

    # Pour chaque (champ, lane), récupère le pickrate Pro (ou soloQ en fallback)
    scores: dict[tuple[str, str], float] = {}
    for champ in picks:
        for lane in LANES:
            pro = db.query(ChampionProStats).filter(
                ChampionProStats.champion == champ,
                ChampionProStats.lane     == lane,
            ).first()
            if pro and pro.pickrate > 0:
                scores[(champ, lane)] = float(pro.pickrate) * 100  # priorité Pro
                continue
            # Fallback solo
            solo = db.query(ChampionStats).filter(
                ChampionStats.champion == champ,
                ChampionStats.lane     == lane,
                ChampionStats.tier     == "MASTER",
            ).first()
            if solo and solo.pickrate > 0:
                scores[(champ, lane)] = float(solo.pickrate)
            else:
                scores[(champ, lane)] = 0.0

    # Greedy : assigner les plus gros scores en premier
    sorted_pairs = sorted(scores.items(), key=lambda kv: -kv[1])
    used_champs: set[str] = set()
    used_lanes:  set[str] = set()
    assignment: dict[str, str] = {}

    for (champ, lane), _ in sorted_pairs:
        if champ in used_champs or lane in used_lanes:
            continue
        assignment[lane] = champ
        used_champs.add(champ)
        used_lanes.add(lane)
        if len(assignment) == 5:
            break

    # Garantir qu'on a bien les 5 lanes (au cas où le greedy a manqué un cas pathologique)
    remaining_lanes  = [l for l in LANES   if l not in used_lanes]
    remaining_champs = [c for c in picks   if c not in used_champs]
    for lane, champ in zip(remaining_lanes, remaining_champs):
        assignment[lane] = champ

    return assignment