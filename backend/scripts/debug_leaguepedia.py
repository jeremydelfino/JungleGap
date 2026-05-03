"""
Debug — quelles tables ont vraiment les picks/bans en 2024-2026 ?
"""
import sys
import os
import time
sys.path.insert(0, ".")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from mwcleric.auth_credentials import AuthCredentials
from mwrogue.esports_client import EsportsClient

creds = AuthCredentials(
    username=os.environ["LEAGUEPEDIA_USERNAME"],
    password=os.environ["LEAGUEPEDIA_PASSWORD"],
)
client = EsportsClient("lol", credentials=creds)
print("✅ Login OK\n")


def run(label, **kwargs):
    print(f"--- {label} ---")
    try:
        rows = client.cargo_client.query(**kwargs)
        print(f"  ✅ {len(rows)} rows")
        for r in rows[:1]:
            print(f"    {dict(r)}")
    except Exception as e:
        print(f"  ❌ {e}")
    print()
    time.sleep(8)


# 1. Lister TOUS les fields disponibles dans ScoreboardGames (peut contenir picks/bans directement)
run(
    "1 — ScoreboardGames champs limités, voir si Team1Bans existe",
    tables="ScoreboardGames",
    fields="Tournament,WinTeam,Team1Bans,Team2Bans,Team1Picks,Team2Picks",
    where='Tournament="LEC 2025 Summer"',
    limit=2,
)

# 2. Tester MatchScheduleGame qui parfois a les picks
run(
    "2 — MatchScheduleGame",
    tables="MatchScheduleGame",
    fields="GameId,Tournament",
    limit=2,
)

# 3. Tester si la table 'Picks' existe (sans S7)
run(
    "3 — Picks table?",
    tables="Picks",
    fields="GameId",
    limit=2,
)