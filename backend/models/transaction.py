from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    type        = Column(String(30), nullable=False)
    amount      = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    created_at  = Column(TIMESTAMP, server_default=func.now())