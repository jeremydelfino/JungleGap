"""
role_detector.py
────────────────
Détection de rôle depuis les données Spectator V5.

Summoner spells IDs :
  1  = Cleanse
  3  = Exhaust
  4  = Flash
  6  = Ghost
  7  = Heal
  11 = Smite
  12 = Teleport / TPE
  14 = Ignite
  21 = Barrier
  32 = Mark (ARAM)
  39 = Mark (jungle mode)
"""

SMITE   = 11
EXHAUST = 3
HEAL    = 7
BARRIER = 21
IGNITE  = 14
TP      = 12
GHOST   = 6
CLEANSE = 1

# Rôles canoniques
TOP     = "TOP"
JUNGLE  = "JUNGLE"
MIDDLE  = "MIDDLE"
BOTTOM  = "BOTTOM"
SUPPORT = "UTILITY"


def _spells(p: dict) -> set[int]:
    return {p.get("spell1Id"), p.get("spell2Id")} - {None}


def assign_roles(team: list[dict]) -> list[str]:
    """
    Prend une liste de 5 participants d'une même équipe (format Spectator V5).
    Retourne une liste de rôles dans le même ordre.

    Algorithme :
      1. Smite → JUNGLE
      2. Exhaust → SUPPORT (fiable à ~95%)
      3. Parmi les non-assignés : si Heal/Barrier/Cleanse ET pas Ignite → candidat BOT
         Si un seul Exhaust trouvé et un seul Heal/Barrier → celui avec Heal/Barrier = BOT
      4. Les 2 restants non classés → TOP et MID selon position dans la liste
         (Riot tend à mettre TOP avant MID dans la liste même si pas garanti)
    """
    n = len(team)
    roles = [None] * n

    # ── PASS 1 : Smite → JUNGLE ──────────────────────────────
    for i, p in enumerate(team):
        if SMITE in _spells(p):
            roles[i] = JUNGLE
            break   # une seule jungle par équipe

    # ── PASS 2 : Exhaust → SUPPORT ───────────────────────────
    # Si plusieurs joueurs ont Exhaust (rare mais possible), prendre le premier non-assigné
    for i, p in enumerate(team):
        if roles[i]:
            continue
        if EXHAUST in _spells(p):
            roles[i] = SUPPORT
            break

    # ── PASS 3 : Heal/Barrier/Cleanse sans Ignite → BOT ─────
    # Un ADC prend typiquement Heal ou Barrier. Rarement Ignite.
    # Un support peut aussi prendre Heal (Soraka, etc.), mais si Exhaust déjà pris → c'est l'ADC.
    for i, p in enumerate(team):
        if roles[i]:
            continue
        sp = _spells(p)
        has_healing   = bool(sp & {HEAL, BARRIER, CLEANSE})
        has_ignite    = IGNITE in sp
        if has_healing and not has_ignite:
            roles[i] = BOTTOM
            break

    # ── PASS 4 : TOP et MID pour les 2 non assignés ─────────
    # On leur attribue TOP puis MID dans l'ordre d'apparition dans la liste.
    remaining = [TOP, MIDDLE]
    for i, p in enumerate(team):
        if roles[i]:
            continue
        if remaining:
            roles[i] = remaining.pop(0)

    # ── Fallback : si un rôle manque encore (équipe < 5, données corrompues) ──
    fallback = [TOP, JUNGLE, MIDDLE, BOTTOM, SUPPORT]
    used = [r for r in roles if r]
    for i in range(n):
        if roles[i] is None:
            for f in fallback:
                if f not in used:
                    roles[i] = f
                    used.append(f)
                    break
            if roles[i] is None:
                roles[i] = ""

    return roles