"""
Synergies entre paires de champions, désormais ventilées par lane (lane_a, lane_b).
Les anciennes lignes sans lane restent en NULL et servent de fallback.
"""
from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class ChampionSynergy(Base):
    __tablename__ = "champion_synergies"

    id              = Column(Integer, primary_key=True)
    champion_a      = Column(String(50), nullable=False)
    champion_b      = Column(String(50), nullable=False)
    lane_a          = Column(String(20))   # NULL = ancienne ligne sans lane
    lane_b          = Column(String(20))
    tier            = Column(String(20), nullable=False, default="MASTER")
    region          = Column(String(10), nullable=False, default="EUW")

    n_games         = Column(Integer, nullable=False, default=0)
    wins            = Column(Integer, nullable=False, default=0)
    winrate         = Column(Float,   nullable=False, default=0.50)
    synergy_score   = Column(Float,   nullable=False, default=0.0)

    updated_at      = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("champion_a", "champion_b", "lane_a", "lane_b", "tier", "region", name="uq_champ_synergy_lanes"),
        Index("idx_synergy_lookup", "champion_a", "champion_b", "lane_a", "lane_b"),
    )