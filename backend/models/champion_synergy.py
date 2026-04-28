"""
Synergies champion-champion : paires de champions qui gagnent plus ensemble.
Calcule le winrate joint quand les 2 champions sont dans la même équipe.
"""
from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class ChampionSynergy(Base):
    __tablename__ = "champion_synergies"

    id          = Column(Integer, primary_key=True)
    champion_a  = Column(String(50), nullable=False)   # ordonné alphabétiquement
    champion_b  = Column(String(50), nullable=False)
    tier        = Column(String(20), nullable=False)
    region      = Column(String(10), nullable=False)

    n_games     = Column(Integer, default=0)
    wins        = Column(Integer, default=0)
    winrate     = Column(Float, default=0.50)

    # Score de synergie = winrate joint - winrate moyen des 2 champions seuls
    # Ex: Caitlyn(51%) + Lux(53%) → moyenne 52%. Si joints = 56%, synergy = +0.04
    synergy_score = Column(Float, default=0.0)

    updated_at  = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("champion_a", "champion_b", "tier", "region", name="uq_champ_synergy"),
        Index("idx_synergy_lookup", "champion_a", "champion_b"),
    )