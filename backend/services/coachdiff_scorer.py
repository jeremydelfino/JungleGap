"""
services/coachdiff_scorer.py
Score une draft (5 champs + lanes) sur 100. Compare 2 drafts pour CoachDiff.

Composantes :
  - Tier (WR + Pro fusionnés)        → 50 pts
  - Matchup vs équipe adverse        → 30 pts  (avec fallback proxy)
  - Synergie interne                 → 20 pts  (avec fallback top-2)

Pénalités off-lane :
  - troll (0-4 games):    -8 pts
  - risky (5-19 games):   -3 pts
  - off_meta (20-49):     -1 pt
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from models.champion_stats     import ChampionStats
from models.champion_synergy   import ChampionSynergy
from models.champion_matchups  import ChampionMatchup
from models.champion_pro_stats import ChampionProStats

logger = logging.getLogger(__name__)


# ─── Pondérations ─────────────────────────────────────────────
WEIGHTS = {
    "tier":    50,   # WR SoloQ + Pro fusionnés
    "matchup": 30,
    "synergy": 20,
}

# ─── Seuils Pro ───────────────────────────────────────────────
PRO_PICKRATE_THRESHOLD = 0.02     # ≥2% pickrate Pro = "ce champ est Pro"
NON_PRO_TIER_MALUS     = 0.05
NON_PRO_TIER_CAP       = 0.40     # cap pour les champs non-Pro
PRO_TEAM_BONUS         = 5.0      # bonus si ≥3 picks Pro dans la compo
PRO_TEAM_BONUS_THRESHOLD = 3

TIER_W_WR_SOLO   = 0.20    # 20% du tier basé sur WR SoloQ Master+
TIER_W_WR_PRO    = 0.40    # 40% si data Pro dispo (sinon redistribué)
TIER_W_PICKRATE  = 0.40    # 40% basé sur pickrate Pro (proxy "ce champ est joué")

# Bornes de normalisation
WR_MIN, WR_MAX  = 0.42, 0.56
MU_MIN, MU_MAX  = 0.42, 0.58
SYN_MIN, SYN_MAX = -0.04, 0.04
PR_MIN, PR_MAX  = 0.0, 0.30   # ← était 0.40, top pickrate Pro réel ~25-30%

# Pénalités off-lane (points retirés du total)
OFF_LANE_PENALTY = {
    "troll":     8.0,
    "risky":     3.0,
    "off_meta":  1.0,
    "meta":      0.0,
}


@dataclass
class TeamPick:
    champion: str
    lane:     str


# ─── Helpers ──────────────────────────────────────────────────
def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _norm(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.5
    return _clamp01((value - lo) / (hi - lo))


def _classify_pick(n_games: int) -> str:
    if n_games >= 50:  return "meta"
    if n_games >= 20:  return "off_meta"
    if n_games >= 5:   return "risky"
    return "troll"


# ─── Lookups DB ───────────────────────────────────────────────
def _get_champion_solo_stats(db: Session, champion: str, lane: str, region: str = "ALL") -> tuple[float, float, int]:
    """Retourne (winrate_solo, pickrate_solo, n_games). Fallback (0.50, 0.0, 0)."""
    row = db.query(ChampionStats).filter(
        ChampionStats.champion == champion,
        ChampionStats.lane     == lane,
        ChampionStats.tier     == "MASTER",
        ChampionStats.region   == region,
    ).first()
    if not row and region != "ALL":
        row = db.query(ChampionStats).filter(
            ChampionStats.champion == champion,
            ChampionStats.lane     == lane,
            ChampionStats.tier     == "MASTER",
            ChampionStats.region   == "ALL",
        ).first()
    if not row:
        return 0.50, 0.0, 0
    return float(row.winrate), float(row.pickrate), int(row.n_games)


def _get_champion_pro_stats(db: Session, champion: str, lane: str) -> tuple[float, float, int] | None:
    """Retourne (winrate_pro, pickrate_pro, n_picks) ou None si pas de data Pro."""
    row = db.query(ChampionProStats).filter(
        ChampionProStats.champion == champion,
        ChampionProStats.lane     == lane,
    ).first()
    if not row or row.n_picks == 0:
        return None
    return float(row.winrate), float(row.pickrate), int(row.n_picks)


def _get_matchup_wr(db: Session, champ_a: str, champ_b: str, lane: str, region: str = "ALL") -> tuple[float, bool]:
    """
    Retourne (winrate_a_vs_b, has_real_data).
    Si pas de vraie data → fallback proxy basé sur WR solo de A et B sur cette lane.
    """
    if champ_a == champ_b:
        return 0.50, False

    # Lookup direct
    if champ_a < champ_b:
        a, b, invert = champ_a, champ_b, False
    else:
        a, b, invert = champ_b, champ_a, True

    row = db.query(ChampionMatchup).filter(
        ChampionMatchup.champion_a == a,
        ChampionMatchup.champion_b == b,
        ChampionMatchup.lane       == lane,
        ChampionMatchup.tier       == "MASTER",
        ChampionMatchup.region     == region,
    ).first()
    if not row and region != "ALL":
        row = db.query(ChampionMatchup).filter(
            ChampionMatchup.champion_a == a,
            ChampionMatchup.champion_b == b,
            ChampionMatchup.lane       == lane,
            ChampionMatchup.tier       == "MASTER",
            ChampionMatchup.region     == "ALL",
        ).first()

    if row:
        wr_a = float(row.winrate_a)
        return ((1.0 - wr_a) if invert else wr_a), True

    # Fallback proxy : différence des WR solo individuels sur cette lane
    wr_a_solo, _, _ = _get_champion_solo_stats(db, champ_a, lane, region)
    wr_b_solo, _, _ = _get_champion_solo_stats(db, champ_b, lane, region)
    proxy = 0.50 + (wr_a_solo - wr_b_solo) / 2.0
    return _clamp01(proxy), False


def _get_synergy_for_pair(
    db: Session,
    a: str, la: str,
    b: str, lb: str,
    region: str = "ALL",
) -> tuple[float, bool]:
    """
    Retourne (synergy_score, has_real_data).
    Lookup avec lanes → fallback sans lanes → fallback top-2 du champion → 0.0
    """
    # 1) Avec lanes (clé triée)
    if (a, la) <= (b, lb):
        a1, l1, b1, l2 = a, la, b, lb
    else:
        a1, l1, b1, l2 = b, lb, a, la

    row = db.query(ChampionSynergy).filter(
        ChampionSynergy.champion_a == a1,
        ChampionSynergy.champion_b == b1,
        ChampionSynergy.lane_a     == l1,
        ChampionSynergy.lane_b     == l2,
        ChampionSynergy.tier       == "MASTER",
        ChampionSynergy.region     == region,
    ).first()
    if row:
        return float(row.synergy_score), True

    # 2) Fallback sans lanes (anciennes lignes ou data lane non encore agrégée)
    row = db.query(ChampionSynergy).filter(
        ChampionSynergy.champion_a == a1,
        ChampionSynergy.champion_b == b1,
        ChampionSynergy.lane_a.is_(None),
        ChampionSynergy.lane_b.is_(None),
        ChampionSynergy.tier       == "MASTER",
        ChampionSynergy.region     == region,
    ).first()
    if row:
        return float(row.synergy_score), True

    # 3) Pas de data pour cette paire → 0 (neutre)
    return 0.0, False


def _get_top_synergies_for_champion(
    db: Session, champion: str, region: str = "ALL", n: int = 2,
) -> list[float]:
    """
    Retourne les n meilleurs synergy_score de ce champion (toutes paires confondues).
    Sert de fallback global si on a 0 vraie synergie sur la team.
    """
    rows = db.query(ChampionSynergy).filter(
        ((ChampionSynergy.champion_a == champion) | (ChampionSynergy.champion_b == champion)),
        ChampionSynergy.tier   == "MASTER",
        ChampionSynergy.region == region,
    ).order_by(ChampionSynergy.synergy_score.desc()).limit(n).all()
    return [float(r.synergy_score) for r in rows]


# ─── Composante "tier" (WR + Pro fusionnés) ───────────────────
def _component_tier(
    db: Session,
    picks: list[TeamPick],
    region: str,
) -> tuple[float, list, dict]:
    """
    Tier d'un champion sur sa lane :
      - Si pickrate Pro ≥ 5% ET n_picks_pro ≥ 15 → "pro" : 0.7 × pickrate + 0.3 × WR Pro
      - Si pickrate Pro ≥ 5% mais n_picks_pro < 15 → "pro_low_sample" : 100% pickrate Pro
        (sample trop petit pour le WR, on se fie juste à la présence)
      - Sinon → "solo_with_malus" : WR SoloQ - 5%, capé à 0.50 max
      - Si troll → tier capé à 0.20
    """
    tier_scores: list[float] = []
    details = []
    counts = {"meta": 0, "off_meta": 0, "risky": 0, "troll": 0}

    for p in picks:
        wr_solo, pr_solo, n_games_solo = _get_champion_solo_stats(db, p.champion, p.lane, region)
        category = _classify_pick(n_games_solo)

        pro_data = _get_champion_pro_stats(db, p.champion, p.lane)
        is_pro_validated = bool(pro_data and pro_data[2] >= 15)

        # Override catégorie : un champion validé Pro ne peut pas être troll/risky
        if is_pro_validated and category in ("troll", "risky"):
            category = "off_meta"
        counts[category] += 1

        if pro_data and pro_data[1] >= PRO_PICKRATE_THRESHOLD:
            wr_pro, pr_pro, n_picks_pro = pro_data
            pr_norm = _norm(pr_pro, PR_MIN, PR_MAX)

            if n_picks_pro >= 15:
                # Sample suffisant : un pick Pro vaut au moins 0.5
                wr_norm = _norm(wr_pro, WR_MIN, WR_MAX)
                tier    = 0.5 + 0.5 * (0.5 * pr_norm + 0.5 * wr_norm)
                tier_source = "pro"
            else:
                # Sample trop petit : on se fie juste au signal "ce champ est joué"
                tier = pr_norm
                tier_source = "pro_low_sample"
        else:
            # Pas de présence Pro → fallback solo capé
            wr_norm = _norm(wr_solo, WR_MIN, WR_MAX)
            tier    = min(NON_PRO_TIER_CAP, wr_norm - NON_PRO_TIER_MALUS)
            tier_source = "solo_with_malus"

        # Troll cap ne s'applique QUE si le champion n'est pas validé Pro
        if category == "troll" and not is_pro_validated:
            tier = min(tier, 0.20)
            tier_source = "troll_capped"

        tier = _clamp01(tier)
        tier_scores.append(tier)

        details.append({
            "champion":    p.champion,
            "lane":        p.lane,
            "wr_solo":     round(wr_solo, 4),
            "pr_solo":     round(pr_solo, 4),
            "n_games":     n_games_solo,
            "category":    category,
            "wr_pro":      round(pro_data[0], 4) if pro_data else None,
            "pr_pro":      round(pro_data[1], 4) if pro_data else None,
            "n_picks_pro": pro_data[2] if pro_data else 0,
            "tier":        round(tier, 4),
            "source":      tier_source,
        })

    avg_tier = sum(tier_scores) / len(tier_scores)
    return avg_tier, details, counts


# ─── Composante matchup ───────────────────────────────────────
def _component_matchup(
    db: Session,
    picks:     list[TeamPick],
    opponents: list[TeamPick],
    region:    str,
) -> tuple[float, list, float]:
    opp_by_lane = {o.lane: o.champion for o in opponents}
    matchup_wrs = []
    details = []
    n_real = 0

    for p in picks:
        opp = opp_by_lane.get(p.lane)
        if not opp:
            continue
        wr, has_data = _get_matchup_wr(db, p.champion, opp, p.lane, region)
        if has_data:
            n_real += 1
        matchup_wrs.append(wr)
        details.append({
            "champion":   p.champion, "lane": p.lane,
            "matchup_vs": opp,        "matchup_wr": round(wr, 4),
            "has_data":   has_data,
        })

    if not matchup_wrs:
        return 0.5, details, 0.0
    avg_mu = sum(matchup_wrs) / len(matchup_wrs)
    coverage = n_real / len(matchup_wrs)
    return _norm(avg_mu, MU_MIN, MU_MAX), details, coverage


# ─── Composante synergy ───────────────────────────────────────
def _component_synergy(
    db: Session,
    picks: list[TeamPick],
    region: str,
) -> tuple[float, dict, float]:
    """
    Pour chaque paire : tente lookup direct, sinon fallback (sans lane).
    Si la team a 0 synergie trouvée pour aucune paire, fallback global :
    moyenne des "top-2 synergies" de chaque champion.
    """
    pair_scores: list[float] = []
    n_pairs_with_data = 0
    n_total_pairs = 0

    for i in range(len(picks)):
        for j in range(i + 1, len(picks)):
            n_total_pairs += 1
            p1, p2 = picks[i], picks[j]
            score, has_data = _get_synergy_for_pair(
                db, p1.champion, p1.lane, p2.champion, p2.lane, region,
            )
            if has_data:
                pair_scores.append(score)
                n_pairs_with_data += 1

    # Fallback global : si aucune paire trouvée, on prend les top-2 synergies de chaque champion
    if n_pairs_with_data == 0:
        all_top = []
        for p in picks:
            all_top.extend(_get_top_synergies_for_champion(db, p.champion, region, n=2))
        if all_top:
            syn_avg = sum(all_top) / len(all_top)
            return _norm(syn_avg, SYN_MIN, SYN_MAX), {"synergy_avg": round(syn_avg, 4), "fallback": "top2"}, 0.5
        return 0.5, {"synergy_avg": 0.0, "fallback": "none"}, 0.0

    syn_avg = sum(pair_scores) / len(pair_scores)
    coverage = n_pairs_with_data / n_total_pairs
    return _norm(syn_avg, SYN_MIN, SYN_MAX), {"synergy_avg": round(syn_avg, 4), "fallback": None}, coverage


# ─── API publique ─────────────────────────────────────────────
def score_team(
    db: Session,
    picks:     list[TeamPick],
    opponents: list[TeamPick],
    region: str = "ALL",
) -> dict:
    if len(picks) != 5 or len(opponents) != 5:
        raise ValueError("score_team attend 5 picks de chaque côté")

    s_tier,  d_tier,  cat_counts = _component_tier(db, picks, region)
    s_mu,    d_mu,    cov_mu     = _component_matchup(db, picks, opponents, region)
    s_syn,   d_syn,   cov_syn    = _component_synergy(db, picks, region)

    # Rebalancing : redistribue le poids des composantes sans data
    components = [
        ("tier",    s_tier, WEIGHTS["tier"],    1.0),
        ("matchup", s_mu,   WEIGHTS["matchup"], cov_mu),
        ("synergy", s_syn,  WEIGHTS["synergy"], cov_syn),
    ]
    effective_weights = {name: w * cov for name, _, w, cov in components}
    total_weight      = sum(effective_weights.values())
    if total_weight <= 0:
        effective_weights = {"tier": WEIGHTS["tier"]}
        total_weight      = WEIGHTS["tier"]

    scale = 100.0 / total_weight
    pts = {name: 0.0 for name in ("tier", "matchup", "synergy")}
    for name, score, _, _ in components:
        if name in effective_weights:
            pts[name] = score * effective_weights[name] * scale

    raw_total = sum(pts.values())

    # Pénalité off-lane
# Compte les picks "Pro" pour le bonus team
    n_pro_picks = sum(1 for d in d_tier if d["source"] in ("pro", "pro_low_sample"))
    team_bonus  = PRO_TEAM_BONUS if n_pro_picks >= PRO_TEAM_BONUS_THRESHOLD else 0.0

    # Pénalité off-lane
    penalty = (
        cat_counts["troll"]    * OFF_LANE_PENALTY["troll"]
      + cat_counts["risky"]    * OFF_LANE_PENALTY["risky"]
      + cat_counts["off_meta"] * OFF_LANE_PENALTY["off_meta"]
    )

    total = max(0.0, min(100.0, raw_total - penalty + team_bonus))

    return {
        "total":         round(total, 4),
        "total_display": int(round(total)),
        "raw_total":     round(raw_total, 4),
        "penalty":       round(penalty, 2),
        "team_bonus":    round(team_bonus, 2),
        "n_pro_picks":   n_pro_picks,
        "breakdown": {
            "tier":    round(pts["tier"],    2),
            "matchup": round(pts["matchup"], 2),
            "synergy": round(pts["synergy"], 2),
        },
        "coverage": {
            "matchup": round(cov_mu,  2),
            "synergy": round(cov_syn, 2),
        },
        "categories": cat_counts,
        "details": {
            "tier":    d_tier,
            "matchup": d_mu,
            "synergy": d_syn,
        },
    }


def compare_drafts(
    db: Session,
    blue_picks: list[TeamPick],
    red_picks:  list[TeamPick],
    region: str = "ALL",
) -> dict:
    blue = score_team(db, blue_picks, red_picks,  region)
    red  = score_team(db, red_picks,  blue_picks, region)

    if   blue["total"] > red["total"]:
        winner = "BLUE"
    elif red["total"]  > blue["total"]:
        winner = "RED"
    else:
        winner = "DRAW"

    return {"blue": blue, "red": red, "winner": winner}