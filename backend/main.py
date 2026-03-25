from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, players, bets, coins, profile, upload, admin, games
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.game_poller import poll_pro_games
import models.user, models.card, models.player, models.match
import models.live_game, models.bet, models.bet_type
import models.transaction, models.user_card, models.pro_player

scheduler = AsyncIOScheduler()

app = FastAPI(title="Jinxit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(players.router)
app.include_router(bets.router)
app.include_router(coins.router)
app.include_router(profile.router)
app.include_router(upload.router)
app.include_router(admin.router)
app.include_router(games.router)

async def startup():
    scheduler.add_job(
        poll_pro_games,
        "interval",
        minutes=3,
        id="poll_games",
        next_run_time=None
    )
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown()

@app.get("/")
def root():
    return {"status": "Jinxit API is running"}