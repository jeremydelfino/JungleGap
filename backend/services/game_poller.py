import asyncio
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from models.pro_player import ProPlayer
from models.live_game import LiveGame
from services.riot import get_live_game_by_puuid

logger = logging.getLogger(__name__)

async def poll_pro_games():
    db: Session = SessionLocal()
    try:
        # Seulement les pros avec puuid, max 20 à la fois
        pros = db.query(ProPlayer).filter(
            ProPlayer.riot_puuid != None,
            ProPlayer.is_active == True
        ).limit(20).all()

        logger.info(f"🎮 Poll: vérification de {len(pros)} pros...")

        puuids_in_game = set()

        for pro in pros:
            try:
                live = await get_live_game_by_puuid(pro.riot_puuid, pro.region)

                if live:
                    riot_game_id = str(live.get("gameId"))
                    puuids_in_game.add(pro.riot_puuid)

                    # Vérifier si la partie est déjà en base
                    existing = db.query(LiveGame).filter(
                        LiveGame.riot_game_id == riot_game_id
                    ).first()

                    if not existing:
                        # Séparer blue/red team
                        participants = live.get("participants", [])
                        blue_team = [
                            {
                                "puuid": p.get("puuid", ""),
                                "summonerName": p.get("summonerName", ""),
                                "championId": p.get("championId"),
                                "championName": p.get("championName", ""),
                                "teamId": p.get("teamId"),
                            }
                            for p in participants if p.get("teamId") == 100
                        ]
                        red_team = [
                            {
                                "puuid": p.get("puuid", ""),
                                "summonerName": p.get("summonerName", ""),
                                "championId": p.get("championId"),
                                "championName": p.get("championName", ""),
                                "teamId": p.get("teamId"),
                            }
                            for p in participants if p.get("teamId") == 200
                        ]

                        game = LiveGame(
                            searched_player_id=1,  # placeholder
                            riot_game_id=riot_game_id,
                            queue_type=str(live.get("gameQueueConfigId", "")),
                            blue_team=blue_team,
                            red_team=red_team,
                            duration_seconds=live.get("gameLength", 0),
                            status="live",
                        )
                        db.add(game)
                        logger.info(f"   ✅ Nouvelle partie détectée pour {pro.name}")

                    else:
                        # Mettre à jour la durée
                        existing.duration_seconds = live.get("gameLength", 0)

                await asyncio.sleep(0.5)  # Rate limit

            except Exception as e:
                logger.error(f"   ❌ Erreur pour {pro.name}: {e}")
                continue

        # Marquer comme terminées les parties où le pro n'est plus détecté
        active_games = db.query(LiveGame).filter(LiveGame.status == "live").all()
        for game in active_games:
            all_puuids = [p.get("puuid") for p in game.blue_team + game.red_team]
            still_live = any(puuid in puuids_in_game for puuid in all_puuids if puuid)
            if not still_live:
                game.status = "ended"
                logger.info(f"   🏁 Partie {game.riot_game_id} terminée")

        db.commit()
        logger.info(f"✅ Poll terminé — {len(puuids_in_game)} pros en game")

    except Exception as e:
        logger.error(f"❌ Erreur poll global: {e}")
        db.rollback()
    finally:
        db.close()