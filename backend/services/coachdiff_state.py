"""
services/coachdiff_state.py

State machine pour la draft CoachDiff (1v1 vs bot, format tournoi LCK).

Séquence fixe (20 actions) :
  Phase BAN_1   (6 bans):  B R B R B R
  Phase PICK_1  (6 picks): B R R B B R
  Phase BAN_2   (4 bans):  R B R B
  Phase PICK_2  (4 picks): R B B R

Le user joue UN seul côté (BLUE ou RED). Le bot joue l'autre.
Après les 20 actions, on passe en ROLE_ASSIGN puis FINISHED.

Le state est stocké en JSONB dans coachdiff_games.draft_state.
"""
from __future__ import annotations
from typing import Literal, Optional

# ─── Séquence ─────────────────────────────────────────────────
# (action_type, side) — 20 entrées
DRAFT_SEQUENCE: list[tuple[str, str]] = [
    # Phase BAN_1
    ("ban",  "BLUE"), ("ban",  "RED"),
    ("ban",  "BLUE"), ("ban",  "RED"),
    ("ban",  "BLUE"), ("ban",  "RED"),
    # Phase PICK_1
    ("pick", "BLUE"),
    ("pick", "RED"),  ("pick", "RED"),
    ("pick", "BLUE"), ("pick", "BLUE"),
    ("pick", "RED"),
    # Phase BAN_2
    ("ban",  "RED"),  ("ban",  "BLUE"),
    ("ban",  "RED"),  ("ban",  "BLUE"),
    # Phase PICK_2
    ("pick", "RED"),
    ("pick", "BLUE"), ("pick", "BLUE"),
    ("pick", "RED"),
]

PHASE_BOUNDARIES = {
    "BAN_1":  (0,  6),
    "PICK_1": (6,  12),
    "BAN_2":  (12, 16),
    "PICK_2": (16, 20),
}


# ─── Helpers de phase ─────────────────────────────────────────
def _phase_for_step(step: int) -> str:
    if step < 0 or step >= len(DRAFT_SEQUENCE):
        return "FINISHED"
    for name, (lo, hi) in PHASE_BOUNDARIES.items():
        if lo <= step < hi:
            return name
    return "FINISHED"


# ─── State init ───────────────────────────────────────────────
def init_state(user_side: Literal["BLUE", "RED"]) -> dict:
    """Crée un draft_state vide pour un nouveau game."""
    return {
        "step":         0,                 # index dans DRAFT_SEQUENCE
        "phase":        "BAN_1",
        "user_side":    user_side,
        "bot_side":     "RED" if user_side == "BLUE" else "BLUE",
        "blue":         {"bans": [], "picks": [], "lanes": {}},
        "red":          {"bans": [], "picks": [], "lanes": {}},
        "history":      [],                # [{step, actor, action, side, champion}]
    }


# ─── Lecture du state ─────────────────────────────────────────
def current_turn(state: dict) -> Optional[dict]:
    """
    Retourne {action, side, actor} pour le tour courant, ou None si terminé.
    actor = "USER" ou "BOT" selon le side.
    """
    step = state["step"]
    if step >= len(DRAFT_SEQUENCE):
        return None
    action, side = DRAFT_SEQUENCE[step]
    actor = "USER" if side == state["user_side"] else "BOT"
    return {"step": step, "action": action, "side": side, "actor": actor}


def is_draft_done(state: dict) -> bool:
    return state["step"] >= len(DRAFT_SEQUENCE)


def all_taken(state: dict) -> set[str]:
    """Set de tous les champions déjà ban OU pick (les deux côtés)."""
    out = set()
    for s in ("blue", "red"):
        out.update(state[s]["bans"])
        out.update(state[s]["picks"])
    return out


# ─── Application d'une action ─────────────────────────────────
def apply_action(state: dict, champion: str, expected_actor: str) -> dict:
    """
    Applique une action pour le tour courant.
      - expected_actor: "USER" ou "BOT" (pour vérifier qu'on appelle au bon moment)
    Mutates `state` et retourne le state updaté.
    Lève ValueError si action invalide.
    """
    if is_draft_done(state):
        raise ValueError("Draft déjà terminée")

    turn = current_turn(state)
    if turn["actor"] != expected_actor:
        raise ValueError(f"Tour de {turn['actor']}, pas de {expected_actor}")

    if not champion or not isinstance(champion, str):
        raise ValueError("Champion invalide")

    if champion in all_taken(state):
        raise ValueError(f"{champion} déjà sélectionné")

    side_key = "blue" if turn["side"] == "BLUE" else "red"
    if turn["action"] == "ban":
        state[side_key]["bans"].append(champion)
    else:
        state[side_key]["picks"].append(champion)

    state["history"].append({
        "step":     turn["step"],
        "actor":    turn["actor"],
        "action":   turn["action"],
        "side":     turn["side"],
        "champion": champion,
    })

    state["step"] += 1
    state["phase"] = _phase_for_step(state["step"]) if not is_draft_done(state) else "ROLE_ASSIGN"
    return state


# ─── Assignation des rôles ────────────────────────────────────
LANES = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]


def apply_role_assignment(state: dict, side: str, lane_map: dict[str, str]) -> dict:
    """
    Assigne les rôles d'un côté.
      lane_map = {"TOP": "Aatrox", "JUNGLE": "Viego", ...}
    Vérifie que les 5 champs assignés correspondent aux 5 picks de ce côté.
    """
    side_key = side.lower()
    if side_key not in ("blue", "red"):
        raise ValueError(f"Side invalide: {side}")

    picks = state[side_key]["picks"]
    if len(picks) != 5:
        raise ValueError(f"Side {side} a {len(picks)} picks, attendu 5")

    if set(lane_map.keys()) != set(LANES):
        raise ValueError(f"Lanes invalides, attendu {LANES}")

    if set(lane_map.values()) != set(picks):
        raise ValueError(f"Champions assignés ne correspondent pas aux picks {picks}")

    state[side_key]["lanes"] = dict(lane_map)
    return state


def is_role_assignment_complete(state: dict) -> bool:
    """True si BLUE et RED ont leurs 5 lanes assignées."""
    return (
        len(state["blue"]["lanes"]) == 5 and
        len(state["red"]["lanes"]) == 5
    )


# ─── Helpers pour le scorer ───────────────────────────────────
def picks_with_lanes(state: dict, side: str) -> list[dict]:
    """Retourne [{champion, lane}, ...] pour un side, prêt à passer au scorer."""
    side_key = side.lower()
    lanes = state[side_key]["lanes"]
    return [{"champion": champ, "lane": lane} for lane, champ in lanes.items()]