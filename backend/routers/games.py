from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.live_game import LiveGame
from models.pro_player import ProPlayer
from services.game_poller import poll_pro_games

router = APIRouter(prefix="/games", tags=["games"])

QUEUE_NAMES = {
    "420": "Ranked Solo",
    "440": "Ranked Flex",
    "400": "Normal",
    "450": "ARAM",
    "": "Custom",
}

@router.post("/poll")
async def force_poll():
    await poll_pro_games()
    return {"status": "Poll lancé"}

@router.get("/live")
def get_live_games(db: Session = Depends(get_db)):
    games = db.query(LiveGame).filter(
        LiveGame.status == "live"
    ).order_by(LiveGame.fetched_at.desc()).limit(12).all()

    result = []
    for game in games:
        all_participants = game.blue_team + game.red_team
        all_puuids = [p.get("puuid") for p in all_participants]

        pro = db.query(ProPlayer).filter(
            ProPlayer.riot_puuid.in_(all_puuids),
            ProPlayer.is_active == True
        ).first()

        print("GAME:", game.riot_game_id, "PRO:", pro.name if pro else "Aucun")

        result.append({
            "id": game.id,
            "riot_game_id": game.riot_game_id,
            "queue": QUEUE_NAMES.get(game.queue_type, game.queue_type),
            "duration_seconds": game.duration_seconds,
            "blue_team": game.blue_team,
            "red_team": game.red_team,
            "pro": {
                "id": pro.id,
                "name": pro.name,
                "team": pro.team,
                "role": pro.role,
                "photo_url": pro.photo_url,
                "accent_color": pro.accent_color,
            } if pro else None,
            "fetched_at": game.fetched_at,
        })
        
    print("Total live games:", len(result))
    return result