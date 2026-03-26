import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ✅ Importer TOUS les modèles comme dans le poller
import models.user
import models.card
import models.player
import models.match
import models.live_game
import models.bet
import models.bet_type
import models.transaction
import models.user_card
import models.pro_player

import asyncio
from database import SessionLocal
from models.live_game import LiveGame
from services.riot import get_live_game_by_puuid

async def fix():
    db = SessionLocal()
    games = db.query(LiveGame).filter(LiveGame.status == "live").all()
    
    for game in games:
        all_players = (game.blue_team or []) + (game.red_team or [])
        ref = next((p for p in all_players if p.get("puuid")), None)
        if not ref:
            continue
        
        live = await get_live_game_by_puuid(ref["puuid"], "EUW")
        if not live:
            continue
        
        participants = live.get("participants", [])
        puuid_to_name = {
            p.get("puuid"): (
                p.get("riotIdGameName") or p.get("summonerName") or p.get("gameName", "")
            )
            for p in participants
        }
        
        game.blue_team = [
            {**p, "summonerName": puuid_to_name.get(p.get("puuid"), p.get("summonerName", ""))}
            for p in (game.blue_team or [])
        ]
        game.red_team = [
            {**p, "summonerName": puuid_to_name.get(p.get("puuid"), p.get("summonerName", ""))}
            for p in (game.red_team or [])
        ]

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(game, "blue_team")  # ✅ force SQLAlchemy à détecter le changement JSON
        flag_modified(game, "red_team")
        
        print(f"✅ Game {game.riot_game_id} mise à jour")
    
    db.commit()
    db.close()

asyncio.run(fix())