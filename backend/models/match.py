from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class MatchHistory(Base):
    __tablename__ = "match_history"

    id                  = Column(Integer, primary_key=True)
    searched_player_id  = Column(Integer, nullable=False)
    riot_match_id       = Column(String(100), nullable=False)
    champion_played     = Column(String(50), nullable=False)
    role                = Column(String(20), nullable=True)
    win                 = Column(Boolean, nullable=False)
    kills               = Column(Integer, default=0)
    deaths              = Column(Integer, default=0)
    assists             = Column(Integer, default=0)
    cs                  = Column(Integer, default=0)
    duration_seconds    = Column(Integer, nullable=False)
    played_at           = Column(TIMESTAMP, nullable=False)