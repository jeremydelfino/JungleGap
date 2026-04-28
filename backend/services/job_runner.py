"""
services/job_runner.py
Wrapper pour exécuter un job avec logging automatique en DB.

Usage :
    @tracked_job("refresh_team_winrates")
    async def refresh_team_winrates():
        ...
        return {"records_processed": 42, "metadata": {...}}
"""
import json
import logging
import asyncio
from datetime import datetime
from functools import wraps
from typing import Callable, Awaitable

from database import SessionLocal
from models.job_run import JobRun

logger = logging.getLogger(__name__)


def tracked_job(job_name: str) -> Callable:
    """
    Décorateur pour qu'une fonction async soit auto-trackée en DB.
    La fonction décorée doit retourner soit None, soit un dict avec :
        - records_processed (int)
        - metadata (dict)
    """
    def decorator(func: Callable[..., Awaitable]) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db = SessionLocal()
            job_run = JobRun(job_name=job_name, status="running")
            db.add(job_run)
            db.commit()
            db.refresh(job_run)

            start = datetime.utcnow()
            logger.info(f"[job:{job_name}] ▶️  démarrage (run_id={job_run.id})")

            try:
                result = await func(*args, **kwargs)

                # Récupère metadata si la fonction en a retourné
                records  = 0
                metadata = None
                if isinstance(result, dict):
                    records  = result.get("records_processed", 0)
                    metadata = result.get("metadata")

                end = datetime.utcnow()
                duration = (end - start).total_seconds()

                # Reload depuis db pour éviter les expired sessions
                jr = db.query(JobRun).filter(JobRun.id == job_run.id).first()
                if jr:
                    jr.finished_at       = end
                    jr.duration_seconds  = duration
                    jr.status            = "success"
                    jr.records_processed = records
                    if metadata is not None:
                        jr.metadata_json = json.dumps(metadata, default=str)
                    db.commit()

                logger.info(
                    f"[job:{job_name}] ✅ succès en {duration:.1f}s "
                    f"({records} enregistrements)"
                )
                return result

            except Exception as e:
                end = datetime.utcnow()
                duration = (end - start).total_seconds()

                jr = db.query(JobRun).filter(JobRun.id == job_run.id).first()
                if jr:
                    jr.finished_at      = end
                    jr.duration_seconds = duration
                    jr.status           = "failed"
                    jr.error_message    = str(e)[:2000]
                    db.commit()

                logger.error(f"[job:{job_name}] ❌ échec en {duration:.1f}s : {e}", exc_info=True)
                # On ne re-raise pas : un job qui plante ne doit pas tuer le scheduler
                return None
            finally:
                db.close()

        return wrapper
    return decorator