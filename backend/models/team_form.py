"""
Forme récente d'une équipe esports : last 5 results, streak, dernière date de match.
Évite de recalculer ça à la volée à chaque request /esports/schedule.
"""
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class TeamForm(Base):
    __tablename__ = "team_form"

    id              = Column(Integer, primary_key=True)
    team_code       = Column(String(20), unique=True, nullable=False, index=True)
    league_slug     = Column(String(50), nullable=False)

    last_5_results  = Column(String(10), default="")    # ex: "WWLWL" (W=win, L=loss)
    streak          = Column(Integer, default=0)         # +N = N wins / -N = N losses
    forme_score     = Column(Float, default=0.50)        # ratio wins sur 5 dernières
    last_match_date = Column(TIMESTAMP, nullable=True)

    updated_at      = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())