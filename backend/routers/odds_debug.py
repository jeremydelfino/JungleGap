"""
Route de debug : détail complet du calcul des côtes pour une live game.
GET /games/{game_id}/odds-debug
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.live_game import LiveGame
from services.live_odds_engine import (
    WEIGHTS, PLAYER_SUB, FIXED_ODDS,
    MARGIN, EXPONENT, MIN_ODDS, MAX_ODDS,
    PROB_FLOOR, PROB_CEIL, SPREAD_GAIN,
)

router = APIRouter(tags=["debug"])


@router.get("/games/{game_id}/odds-debug")
def odds_debug(game_id: int, db: Session = Depends(get_db)):
    game = db.query(LiveGame).filter(LiveGame.id == game_id).first()
    if not game:
        raise HTTPException(404, f"Game {game_id} introuvable")

    od = game.odds_data
    if not od:
        raise HTTPException(
            404,
            f"Game {game_id} n'a pas d'odds_data. "
            "Soit le calcul a échoué au démarrage, soit la game est trop ancienne. "
            "Aucun recalcul à la volée — relance une nouvelle game."
        )

    # ── Recompose le calcul final pour montrer la chaîne ──────
    score_blue = od.get("score_blue")
    score_red  = od.get("score_red")
    s_blue_pow = round(max(score_blue or 0.01, 0.01) ** EXPONENT, 6)
    s_red_pow  = round(max(score_red  or 0.01, 0.01) ** EXPONENT, 6)
    total_pow  = s_blue_pow + s_red_pow

    return {
        "game_id":      game.id,
        "riot_game_id": game.riot_game_id,
        "region":       game.region,
        "status":       game.status,

        # ── Paramètres du moteur (constantes actuelles) ───────
        "engine_params": {
            "weights":      WEIGHTS,
            "player_sub":   PLAYER_SUB,
            "margin":       MARGIN,
            "exponent":     EXPONENT,
            "min_odds":     MIN_ODDS,
            "max_odds":     MAX_ODDS,
            "prob_floor":   PROB_FLOOR,
            "prob_ceil":    PROB_CEIL,
            "spread_gain":  SPREAD_GAIN,
            "fixed_odds":   FIXED_ODDS,
        },

        # ── Score & probabilité finaux ────────────────────────
        "scores": {
            "blue":           score_blue,
            "red":            score_red,
            "blue_pow_exp":   s_blue_pow,
            "red_pow_exp":    s_red_pow,
            "total_pow":      round(total_pow, 6),
            "prob_blue":      od.get("prob_blue"),
            "prob_red":       od.get("prob_red"),
            "favor_blue":     round((od.get("prob_blue") or 0.5) - 0.50, 3),
        },

        # ── Détail composantes par équipe ─────────────────────
        "blue_team_detail": od.get("detail_blue"),
        "red_team_detail":  od.get("detail_red"),

        # ── Côtes calculées ───────────────────────────────────
        "computed_odds": {
            "who_wins":              od.get("who_wins"),
            "first_blood":           od.get("first_blood"),
            "first_tower":           od.get("first_tower"),
            "first_dragon":          od.get("first_dragon"),
            "first_baron":           od.get("first_baron"),
            "jungle_gap":            od.get("jungle_gap"),
            "game_duration_under25": od.get("game_duration_under25"),
            "game_duration_25_35":   od.get("game_duration_25_35"),
            "game_duration_over35":  od.get("game_duration_over35"),
            "player_positive_kda":   od.get("player_positive_kda"),
            "champion_kda_over25":   od.get("champion_kda_over25"),
            "champion_kda_over5":    od.get("champion_kda_over5"),
            "champion_kda_over10":   od.get("champion_kda_over10"),
            "top_damage":            od.get("top_damage"),
        },

        # ── Détail jungle_gap (champions, scores, etc.) ───────
        "jungle_gap_detail": od.get("jungle_gap_detail"),
    }