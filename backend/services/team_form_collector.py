"""
services/team_form_collector.py
Calcule la forme récente des équipes esports à partir des completed events.
"""
import logging
from datetime import datetime
from collections import defaultdict

from database import SessionLocal
from models.team_form import TeamForm
from services import lolesports
from services.job_runner import tracked_job

logger = logging.getLogger(__name__)

# Importé depuis routers/esports — duplique au cas où on déplace
COVERED_LEAGUES = {
    "lec":    "98767991302996019",
    "lck":    "98767991310872058",
    "lcs":    "98767991299243165",
    "lpl":    "98767991314006698",
    "lfl":    "105266103462388553",
    "worlds": "98767975604431411",
    "msi":    "98767991325878492",
}


@tracked_job("refresh_team_form")
async def refresh_team_form() -> dict:
    """
    Pour chaque ligue, lit les completed events, calcule pour chaque équipe :
    - last_5_results (ex: "WWLWL")
    - streak (signé : positif = wins consécutives, négatif = losses)
    - forme_score (ratio sur 5 dernières)
    - last_match_date
    """
    db = SessionLocal()
    total_updated = 0

    # team_code -> [(date, won_bool), ...] triés du plus récent au plus ancien
    team_results: dict[str, list[tuple[datetime, bool, str]]] = defaultdict(list)

    try:
        for slug, lid in COVERED_LEAGUES.items():
            try:
                tid = await lolesports.get_current_tournament_id(lid)
                if not tid:
                    continue
                ce     = await lolesports.get_completed_events(tid)
                events = ce.get("data", {}).get("schedule", {}).get("events", [])
            except Exception as e:
                logger.warning(f"[team_form] {slug} fetch erreur : {e}")
                continue

            for ev in events:
                if not ev.get("match"):
                    continue
                match = ev.get("match", {})
                teams = match.get("teams", [])
                if len(teams) < 2:
                    continue

                # Date
                start_str = ev.get("startTime") or ""
                try:
                    match_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                except Exception:
                    match_date = datetime.utcnow()

                t1, t2 = teams[0], teams[1]
                r1     = t1.get("result") or {}
                r2     = t2.get("result") or {}
                t1_w   = r1.get("gameWins", 0) or 0
                t2_w   = r2.get("gameWins", 0) or 0
                t1_out = (r1.get("outcome") or "").lower()
                t2_out = (r2.get("outcome") or "").lower()

                # Détecte le gagnant
                if t1_w > t2_w:
                    won_t1 = True
                elif t2_w > t1_w:
                    won_t1 = False
                elif t1_out == "win":
                    won_t1 = True
                elif t2_out == "win":
                    won_t1 = False
                else:
                    continue  # ambigu, skip

                t1_code = (t1.get("code") or "").upper()
                t2_code = (t2.get("code") or "").upper()
                if t1_code:
                    team_results[t1_code].append((match_date, won_t1, slug))
                if t2_code:
                    team_results[t2_code].append((match_date, not won_t1, slug))

        # ── Construire les TeamForm ──────────────────────────
        for team_code, results in team_results.items():
            results.sort(key=lambda x: x[0], reverse=True)
            recent = results[:5]
            if not recent:
                continue

            last_5_results = "".join("W" if w else "L" for _, w, _ in recent)
            wins_in_5      = sum(1 for _, w, _ in recent if w)
            forme_score    = wins_in_5 / len(recent)

            # Streak : nb de résultats consécutifs identiques au plus récent
            streak     = 0
            first_outcome = recent[0][1]
            for _, w, _ in recent:
                if w == first_outcome:
                    streak += 1
                else:
                    break
            if not first_outcome:
                streak = -streak

            league_slug    = recent[0][2]
            last_match_date = recent[0][0]

            existing = db.query(TeamForm).filter(TeamForm.team_code == team_code).first()
            if existing:
                existing.league_slug     = league_slug
                existing.last_5_results  = last_5_results
                existing.streak          = streak
                existing.forme_score     = round(forme_score, 3)
                existing.last_match_date = last_match_date.replace(tzinfo=None)
            else:
                db.add(TeamForm(
                    team_code       = team_code,
                    league_slug     = league_slug,
                    last_5_results  = last_5_results,
                    streak          = streak,
                    forme_score     = round(forme_score, 3),
                    last_match_date = last_match_date.replace(tzinfo=None),
                ))
            total_updated += 1

        db.commit()
    finally:
        db.close()

    return {
        "records_processed": total_updated,
        "metadata": {"teams_with_form": total_updated},
    }