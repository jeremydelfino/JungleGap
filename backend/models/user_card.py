from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class UserCard(Base):
    __tablename__ = "user_cards"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id     = Column(Integer, ForeignKey("cards.id"), nullable=False)
    equipped    = Column(Boolean, default=False)
    obtained_at = Column(TIMESTAMP, server_default=func.now())

    card = relationship("Card")