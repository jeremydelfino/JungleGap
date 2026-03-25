from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class SearchedPlayer(Base):
    __tablename__ = "searched_players"

    id                = Column(Integer, primary_key=True)
    riot_puuid        = Column(String(100), unique=True, nullable=False)
    summoner_name     = Column(String(50), nullable=False)
    tag_line          = Column(String(10), nullable=False)
    region            = Column(String(10), nullable=False)
    tier              = Column(String(20), nullable=True)
    rank              = Column(String(5), nullable=True)
    lp                = Column(Integer, default=0)
    profile_icon_url  = Column(String, nullable=True)
    last_updated      = Column(TIMESTAMP, server_default=func.now())
    created_at        = Column(TIMESTAMP, server_default=func.now())