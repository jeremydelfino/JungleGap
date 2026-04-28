"""
routers/admin_jobs.py
Endpoints admin pour piloter et monitorer les jobs.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database import get_db
from deps import get_admin_user
from models.user import User
from models.job_run import JobRun
from models.champion_stats import ChampionStats
from models.champion_synergy import ChampionSynergy
from models.team_form import TeamForm

# Imports lazy pour les jobs (évite circularité)
router = APIRouter(prefix="/admin/jobs", tags=["admin_jobs"])


JOB_REGISTRY = {
    "refresh_champion_winrates": "services.champion_winrate_collector:refresh_champion_winrates",
    "refresh_team_form":         "services.team_form_collector:refresh_team_form",
    "refresh_team_winrates":     "routers.esports:refresh_all_standings",  # existe déjà
    "sync_esports_teams":        "services.esports_sync:sync_all_teams",   # existe déjà
}


def _import_job(spec: str):
    module_path, func_name = spec.split(":")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, func_name)


@router.post("/run/{job_name}")
async def run_job_manually(
    job_name: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Trigger manuel d'un job. Utile pour debug ou premier seed."""
    if job_name not in JOB_REGISTRY:
        raise HTTPException(404, f"Job inconnu : {job_name}. Disponibles : {list(JOB_REGISTRY)}")

    spec = JOB_REGISTRY[job_name]
    fn   = _import_job(spec)

    # Certains jobs ont besoin de db (refresh_all_standings)
    import inspect
    sig = inspect.signature(fn)
    try:
        if "db" in sig.parameters:
            result = await fn(db)
        else:
            result = await fn()
    except Exception as e:
        raise HTTPException(500, f"Erreur lors du run : {e}")

    return {"status": "started_or_completed", "job": job_name, "result": result}


@router.get("/status")
def jobs_status(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Dernier run de chaque job."""
    out = {}
    for job_name in JOB_REGISTRY:
        last = (
            db.query(JobRun)
            .filter(JobRun.job_name == job_name)
            .order_by(desc(JobRun.started_at))
            .first()
        )
        if last:
            out[job_name] = {
                "status":            last.status,
                "started_at":        last.started_at,
                "finished_at":       last.finished_at,
                "duration_seconds":  last.duration_seconds,
                "records_processed": last.records_processed,
                "error_message":     last.error_message,
                "metadata":          json.loads(last.metadata_json) if last.metadata_json else None,
            }
        else:
            out[job_name] = {"status": "never_run"}
    return out


@router.get("/history")
def jobs_history(
    job_name: str | None = None,
    limit: int = 20,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(JobRun)
    if job_name:
        q = q.filter(JobRun.job_name == job_name)
    runs = q.order_by(desc(JobRun.started_at)).limit(min(limit, 200)).all()
    return [
        {
            "id":                r.id,
            "job_name":          r.job_name,
            "status":            r.status,
            "started_at":        r.started_at,
            "duration_seconds":  r.duration_seconds,
            "records_processed": r.records_processed,
            "error_message":     r.error_message,
        }
        for r in runs
    ]


# ─── Endpoints de preview des données ────────────────────────

@router.get("/champion-winrates")
def get_champion_winrates(
    tier: str = "MASTER",
    region: str = "ALL",
    lane: str | None = None,
    limit: int = 50,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(ChampionStats).filter(
        ChampionStats.tier   == tier.upper(),
        ChampionStats.region == region.upper(),
    )
    if lane:
        q = q.filter(ChampionStats.lane == lane.upper())

    rows = q.order_by(desc(ChampionStats.winrate)).limit(min(limit, 200)).all()
    return [
        {
            "champion":  r.champion,
            "lane":      r.lane,
            "winrate":   round(r.winrate * 100, 2),
            "pickrate":  round(r.pickrate * 100, 2),
            "n_games":   r.n_games,
            "avg_kda":   r.avg_kda,
            "updated_at": r.updated_at,
        }
        for r in rows
    ]


@router.get("/team-form")
def get_team_form(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    rows = db.query(TeamForm).order_by(TeamForm.league_slug, TeamForm.team_code).all()
    return [
        {
            "team_code":       r.team_code,
            "league":          r.league_slug,
            "last_5_results":  r.last_5_results,
            "streak":          r.streak,
            "forme_score":     r.forme_score,
            "last_match_date": r.last_match_date,
        }
        for r in rows
    ]