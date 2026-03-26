from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator
from database import get_db
from models.bet import Bet
from models.live_game import LiveGame
from models.user import User
from models.bet_type import BetType
from models.transaction import Transaction
from deps import get_current_user

router = APIRouter(prefix="/bets", tags=["bets"])

VALID_BET_TYPES = {"who_wins", "first_blood"}
VALID_WIN_VALUES = {"blue", "red"}


class PlaceBetSchema(BaseModel):
    live_game_id:  int
    bet_type_slug: str
    bet_value:     str
    amount:        int
    card_used_id:  int | None = None

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v < 1:
            raise ValueError("Le montant doit être >= 1")
        if v > 100_000:
            raise ValueError("Le montant ne peut pas dépasser 100 000 coins")
        return v

    @validator("bet_type_slug")
    def valid_bet_type(cls, v):
        if v not in VALID_BET_TYPES:
            raise ValueError(f"Type de pari invalide : {v}")
        return v


@router.post("/place")
def place_bet(
    body: PlaceBetSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bet_type = db.query(BetType).filter(
        BetType.slug == body.bet_type_slug,
        BetType.is_active == True,
    ).first()
    if not bet_type:
        raise HTTPException(400, "Type de pari invalide ou inactif")

    # Validation de bet_value selon le type
    if body.bet_type_slug == "who_wins" and body.bet_value not in VALID_WIN_VALUES:
        raise HTTPException(400, "Valeur invalide pour who_wins (blue ou red)")

    game = db.query(LiveGame).filter(
        LiveGame.id == body.live_game_id,
        LiveGame.status == "live",
    ).first()
    if not game:
        raise HTTPException(400, "Partie introuvable ou déjà terminée")

    # Validation de bet_value pour first_blood (doit être un champion de la game)
    if body.bet_type_slug == "first_blood":
        all_champs = [
            p.get("championName") for p in (game.blue_team or []) + (game.red_team or [])
            if p.get("championName")
        ]
        if body.bet_value not in all_champs:
            raise HTTPException(400, f"Champion '{body.bet_value}' introuvable dans cette partie")

    existing = db.query(Bet).filter(
        Bet.user_id == current_user.id,
        Bet.live_game_id == body.live_game_id,
        Bet.bet_type_slug == body.bet_type_slug,
    ).first()
    if existing:
        raise HTTPException(400, "Tu as déjà placé ce type de pari sur cette partie")

    # ✅ SELECT FOR UPDATE — évite la race condition sur les coins
    user = db.query(User).filter(User.id == current_user.id).with_for_update().first()

    if user.coins < body.amount:
        raise HTTPException(400, f"Pas assez de coins ({user.coins} disponibles, {body.amount} requis)")

    boost = 0.0
    if body.card_used_id:
        from models.card import Card
        from models.user_card import UserCard
        user_card = db.query(UserCard).filter(
            UserCard.user_id == current_user.id,
            UserCard.card_id == body.card_used_id,
        ).first()
        if not user_card:
            raise HTTPException(400, "Tu ne possèdes pas cette carte")
        boost = user_card.card.boost_value or 0.0

    user.coins -= body.amount

    bet = Bet(
        user_id=user.id,
        live_game_id=body.live_game_id,
        card_used_id=body.card_used_id,
        bet_type_slug=body.bet_type_slug,
        bet_value=body.bet_value,
        amount=body.amount,
        boost_applied=boost,
        status="pending",
    )
    db.add(bet)

    db.add(Transaction(
        user_id=user.id,
        type="bet_placed",
        amount=-body.amount,
        description=f"Pari placé sur {bet_type.label} — {body.bet_value}",
    ))

    db.commit()
    db.refresh(bet)

    return {
        "bet_id":         bet.id,
        "amount":         body.amount,
        "boost_applied":  boost,
        "coins_restants": user.coins,
    }


@router.get("/my-bets")
def get_my_bets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bets = (
        db.query(Bet)
        .filter(Bet.user_id == current_user.id)
        .order_by(Bet.created_at.desc())
        .all()
    )

    # ✅ Une seule requête pour toutes les games (évite le N+1)
    game_ids = {b.live_game_id for b in bets}
    games = {
        g.id: g for g in db.query(LiveGame).filter(LiveGame.id.in_(game_ids)).all()
    } if game_ids else {}

    return [
        {
            "id":            b.id,
            "live_game_id":  b.live_game_id,
            "game_status":   games[b.live_game_id].status if b.live_game_id in games else "ended",
            "bet_type":      b.bet_type_slug,
            "bet_value":     b.bet_value,
            "amount":        b.amount,
            "boost_applied": b.boost_applied,
            "status":        b.status,
            "payout":        b.payout,
            "created_at":    b.created_at,
        }
        for b in bets
    ]