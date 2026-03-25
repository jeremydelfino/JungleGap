from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.user import User
from services import riot
import random

router = APIRouter(prefix="/profile", tags=["profile"])

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


class LinkRiotSchema(BaseModel):
    game_name: str
    tag_line: str
    region: str


@router.post("/link-riot/init")
async def link_riot_init(
    body: LinkRiotSchema,
    authorization: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(authorization.replace("Bearer ", ""), db)

    # Vérifier que ce puuid n'est pas déjà lié à un autre compte
    account = await riot.get_account_by_riot_id(body.game_name, body.tag_line, body.region)
    puuid = account["puuid"]

    existing = db.query(User).filter(
        User.riot_puuid == puuid,
        User.id != user.id
    ).first()
    if existing:
        raise HTTPException(400, "Ce compte Riot est déjà lié à un autre compte Jinxit")

    # Générer un icône de vérification aléatoire entre 1 et 28
    # (icônes de base que tous les joueurs peuvent équiper)
    icon_id = random.randint(1, 28)

    # Stocker temporairement le puuid et l'icône en attente de vérification
    user.riot_puuid = puuid
    user.riot_verification_icon = icon_id
    db.commit()

    return {
        "icon_id": icon_id,
        "icon_url": f"https://ddragon.leagueoflegends.com/cdn/14.10.1/img/profileicon/{icon_id}.png",
        "instructions": f"Change ton icône de profil pour l'icône n°{icon_id} dans LoL, puis clique sur Vérifier",
        "game_name": body.game_name,
        "tag_line": body.tag_line,
        "region": body.region,
    }


@router.post("/link-riot/verify")
async def link_riot_verify(
    authorization: str,
    db: Session = Depends(get_db)
):
    user = get_current_user(authorization.replace("Bearer ", ""), db)

    if not user.riot_puuid or not user.riot_verification_icon:
        raise HTTPException(400, "Lance d'abord /link-riot/init")

    # Récupérer l'icône actuelle du joueur via Riot API
    # On a besoin de la région — on la récupère depuis searched_players
    from models.player import SearchedPlayer
    player = db.query(SearchedPlayer).filter(
        SearchedPlayer.riot_puuid == user.riot_puuid
    ).first()

    if not player:
        raise HTTPException(400, "Joueur introuvable en cache, relance /link-riot/init")

    summoner = await riot.get_summoner_by_puuid(user.riot_puuid, player.region)
    current_icon = summoner["profileIconId"]

    if current_icon != user.riot_verification_icon:
        raise HTTPException(400, f"Mauvaise icône détectée (icône actuelle : {current_icon}, attendue : {user.riot_verification_icon}). Change bien ton icône dans LoL et réessaie.")

    # Vérification réussie — on garde le puuid et on nettoie l'icône de vérif
    user.riot_verification_icon = None
    db.commit()

    return {
        "success": True,
        "message": "Compte Riot lié avec succès !",
        "riot_puuid": user.riot_puuid
    }


@router.get("/me")
def get_my_profile(authorization: str, db: Session = Depends(get_db)):
    user = get_current_user(authorization.replace("Bearer ", ""), db)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "coins": user.coins,
        "avatar_url": user.avatar_url,
        "riot_linked": user.riot_puuid is not None,
        "riot_puuid": user.riot_puuid,
        "last_daily": user.last_daily,
    }