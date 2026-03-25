from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class BetType(Base):
    __tablename__ = "bet_types"

    id          = Column(Integer, primary_key=True)
    slug        = Column(String(50), unique=True, nullable=False)
    label       = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category    = Column(String(20), nullable=False)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(TIMESTAMP, server_default=func.now())