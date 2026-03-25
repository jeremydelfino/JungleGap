from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.bet import Bet
from models.live_game import LiveGame
from models.user import User
from models.bet_type import BetType
from services import riot
from datetime import datetime

router = APIRouter(prefix="/bets", tags=["bets"])

class PlaceBetSchema(BaseModel):
    live_game_id: int
    bet_type_slug: str
    bet_value: str
    amount: int
    card_used_id: int | None = None

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

@router.post("/place")
def place_bet(
    body: PlaceBetSchema,
    authorization: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(authorization.replace("Bearer ", ""), db)

    # Vérifier que le type de pari existe et est actif
    bet_type = db.query(BetType).filter(
        BetType.slug == body.bet_type_slug,
        BetType.is_active == True
    ).first()
    if not bet_type:
        raise HTTPException(400, "Type de pari invalide ou inactif")

    # Vérifier que la partie est toujours live
    game = db.query(LiveGame).filter(
        LiveGame.id == body.live_game_id,
        LiveGame.status == "live"
    ).first()
    if not game:
        raise HTTPException(400, "Partie introuvable ou déjà terminée")

    # Vérifier que l'user n'a pas déjà parié sur cette partie avec ce type
    existing = db.query(Bet).filter(
        Bet.user_id == user.id,
        Bet.live_game_id == body.live_game_id,
        Bet.bet_type_slug == body.bet_type_slug
    ).first()
    if existing:
        raise HTTPException(400, "Tu as déjà placé ce type de pari sur cette partie")

    # Vérifier que l'user a assez de coins
    if user.coins < body.amount:
        raise HTTPException(400, f"Pas assez de coins (tu as {user.coins}, tu mises {body.amount})")

    # Calculer le boost si une carte est utilisée
    boost = 0.0
    if body.card_used_id:
        from models.card import Card
        from models.user_card import UserCard
        user_card = db.query(UserCard).filter(
            UserCard.user_id == user.id,
            UserCard.card_id == body.card_used_id
        ).first()
        if not user_card:
            raise HTTPException(400, "Tu ne possèdes pas cette carte")
        boost = user_card.card.boost_value or 0.0

    # Déduire les coins + créer le pari
    user.coins -= body.amount

    bet = Bet(
        user_id=user.id,
        live_game_id=body.live_game_id,
        card_used_id=body.card_used_id,
        bet_type_slug=body.bet_type_slug,
        bet_value=body.bet_value,
        amount=body.amount,
        boost_applied=boost,
        status="pending"
    )
    db.add(bet)

    # Enregistrer la transaction
    from models.transaction import Transaction
    transaction = Transaction(
        user_id=user.id,
        type="bet_placed",
        amount=-body.amount,
        description=f"Pari placé sur {bet_type.label}"
    )
    db.add(transaction)
    db.commit()
    db.refresh(bet)

    return {
        "bet_id": bet.id,
        "amount": body.amount,
        "boost_applied": boost,
        "coins_restants": user.coins
    }


@router.get("/my-bets")
def get_my_bets(authorization: str, db: Session = Depends(get_db)):
    user = get_current_user(authorization.replace("Bearer ", ""), db)
    bets = db.query(Bet).filter(Bet.user_id == user.id).order_by(Bet.created_at.desc()).all()
    return [
        {
            "id": b.id,
            "bet_type": b.bet_type_slug,
            "bet_value": b.bet_value,
            "amount": b.amount,
            "boost_applied": b.boost_applied,
            "status": b.status,
            "payout": b.payout,
            "created_at": b.created_at,
        }
        for b in bets
    ]