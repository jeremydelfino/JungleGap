from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.transaction import Transaction
from deps import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/coins", tags=["coins"])

DAILY_REWARD = 100

@router.post ("/add")
def add_coins(
    amount: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if amount < 1:
        raise HTTPException(400, "Le montant doit être positif")

    current_user.coins += amount
    db.add(Transaction(
        user_id=current_user.id,
        type="admin_add",
        amount=amount,
        description="Ajout de coins par admin",
    ))
    db.commit()

    return {
        "message": f"{amount} coins ajoutés. Nouveau solde : {current_user.coins} coins."
    }

@router.post("/daily")
def claim_daily(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()

    # ✅ SELECT FOR UPDATE pour éviter le double claim en parallèle
    user = db.query(User).filter(User.id == current_user.id).with_for_update().first()

    if user.last_daily and (now - user.last_daily) < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - user.last_daily)
        hours = int(remaining.seconds / 3600)
        minutes = int((remaining.seconds % 3600) / 60)
        raise HTTPException(400, f"Daily déjà réclamé, reviens dans {hours}h{minutes}m")

    user.coins += DAILY_REWARD
    user.last_daily = now

    db.add(Transaction(
        user_id=user.id,
        type="daily_reward",
        amount=DAILY_REWARD,
        description="Daily reward",
    ))
    db.commit()

    return {
        "coins_gagnés":   DAILY_REWARD,
        "coins_total":    user.coins,
        "prochain_daily": "dans 24h",
    }


@router.get("/balance")
def get_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {
        "coins": current_user.coins,
        "last_daily": current_user.last_daily,
        "daily_disponible": (
            not current_user.last_daily
            or (datetime.utcnow() - current_user.last_daily) >= timedelta(hours=24)
        ),
    }


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "type":        t.type,
            "amount":      t.amount,
            "description": t.description,
            "created_at":  t.created_at,
        }
        for t in transactions
    ]