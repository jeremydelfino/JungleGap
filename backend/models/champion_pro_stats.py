"""
Stats Pro agrégées (tous splits actifs confondus) — alimenté depuis l'esports API.
"""
from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class ChampionProStats(Base):
    __tablename__ = "champion_pro_stats"

    id              = Column(Integer, primary_key=True)
    champion        = Column(String(50), nullable=False)
    lane            = Column(String(20), nullable=False)

    n_picks         = Column(Integer, nullable=False, default=0)
    n_bans          = Column(Integer, nullable=False, default=0)
    n_games_total   = Column(Integer, nullable=False, default=0)

    pickrate        = Column(Float, nullable=False, default=0.0)
    banrate         = Column(Float, nullable=False, default=0.0)
    presence        = Column(Float, nullable=False, default=0.0)
    winrate         = Column(Float, nullable=False, default=0.50)

    last_synced_at  = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("champion", "lane", name="uq_pro_stats"),
        Index("idx_pro_stats_lookup", "champion", "lane"),
    )