from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.transaction import Transaction
from datetime import datetime, timedelta

router = APIRouter(prefix="/coins", tags=["coins"])

DAILY_REWARD = 100

def get_current_user(token: str, db: Session) -> User:
    from jose import jwt, JWTError
    import os
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(401, "Utilisateur introuvable")
        return user
    except JWTError:
        raise HTTPException(401, "Token invalide")


@router.post("/daily")
def claim_daily(authorization: str, db: Session = Depends(get_db)):
    user = get_current_user(authorization.replace("Bearer ", ""), db)

    now = datetime.utcnow()

    # Vérifier si le daily a déjà été réclamé aujourd'hui
    if user.last_daily and (now - user.last_daily) < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - user.last_daily)
        hours = int(remaining.seconds / 3600)
        minutes = int((remaining.seconds % 3600) / 60)
        raise HTTPException(400, f"Daily déjà réclamé, reviens dans {hours}h{minutes}m")

    user.coins += DAILY_REWARD
    user.last_daily = now

    transaction = Transaction(
        user_id=user.id,
        type="daily_reward",
        amount=DAILY_REWARD,
        description="Daily reward"
    )
    db.add(transaction)
    db.commit()

    return {
        "coins_gagnés": DAILY_REWARD,
        "coins_total": user.coins,
        "prochain_daily": "dans 24h"
    }


@router.get("/balance")
def get_balance(authorization: str, db: Session = Depends(get_db)):
    user = get_current_user(authorization.replace("Bearer ", ""), db)
    return {
        "coins": user.coins,
        "last_daily": user.last_daily,
        "daily_disponible": not user.last_daily or (datetime.utcnow() - user.last_daily) >= timedelta(hours=24)
    }


@router.get("/history")
def get_history(authorization: str, db: Session = Depends(get_db)):
    user = get_current_user(authorization.replace("Bearer ", ""), db)
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user.id
    ).order_by(Transaction.created_at.desc()).limit(50).all()

    return [
        {
            "type": t.type,
            "amount": t.amount,
            "description": t.description,
            "created_at": t.created_at
        }
        for t in transactions
    ]