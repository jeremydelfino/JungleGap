"""
Historique des runs de jobs périodiques.
Permet de monitorer ce qui tourne, ce qui plante, et ce qui prend du temps.
"""
from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class JobRun(Base):
    __tablename__ = "job_runs"

    id                = Column(Integer, primary_key=True)
    job_name          = Column(String(80), nullable=False, index=True)
    started_at        = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    finished_at       = Column(TIMESTAMP, nullable=True)
    duration_seconds  = Column(Float, nullable=True)
    status            = Column(String(20), default="running")  # running | success | failed
    records_processed = Column(Integer, default=0)
    error_message     = Column(Text, nullable=True)
    metadata_json     = Column(Text, nullable=True)  # JSON libre pour stocker des stats