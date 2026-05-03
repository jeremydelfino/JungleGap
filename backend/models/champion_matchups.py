"""
Matchups par lane : winrate de champion_a contre champion_b sur la même lane.
Stockage en un seul sens : champion_a < champion_b (alphabétique).
Au runtime, inverser (1 - winrate_a) si on cherche dans l'autre sens.
"""
from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class ChampionMatchup(Base):
    __tablename__ = "champion_matchups"

    id          = Column(Integer, primary_key=True)
    champion_a  = Column(String(50), nullable=False)
    champion_b  = Column(String(50), nullable=False)
    lane        = Column(String(20), nullable=False)
    tier        = Column(String(20), nullable=False, default="MASTER")
    region      = Column(String(10), nullable=False, default="EUW")

    n_games     = Column(Integer, nullable=False, default=0)
    a_wins      = Column(Integer, nullable=False, default=0)
    winrate_a   = Column(Float,   nullable=False, default=0.50)

    updated_at  = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("champion_a", "champion_b", "lane", "tier", "region", name="uq_champ_matchup"),
        CheckConstraint("champion_a < champion_b", name="ck_champ_order"),
        Index("idx_matchup_lookup_a", "champion_a", "lane", "tier"),
        Index("idx_matchup_lookup_b", "champion_b", "lane", "tier"),
    )