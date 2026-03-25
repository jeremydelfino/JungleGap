import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.pro_player import ProPlayer

TEAM_COLORS = {
    "T1": "#C89B3C",
    "Gen.G": "#9B0D0D",
    "Hanwha Life Esports": "#FF6B00",
    "KT Rolster": "#FF0000",
    "DRX": "#1E73BE",
    "Dplus KIA": "#5B2D8E",
    "Nongshim RedForce": "#CC0000",
    "FEARX": "#00A86B",
    "HANJIN BRION": "#888888",
    "DN SOOPers": "#1E90FF",
}

LCK_2026 = [
    # T1
    {"name": "Doran",     "team": "T1",                  "role": "TOP",     "region": "KR"},
    {"name": "Oner",      "team": "T1",                  "role": "JUNGLE",  "region": "KR"},
    {"name": "Faker",     "team": "T1",                  "role": "MID",     "region": "KR"},
    {"name": "Peyz",      "team": "T1",                  "role": "ADC",     "region": "KR"},
    {"name": "Keria",     "team": "T1",                  "role": "SUPPORT", "region": "KR"},
    # Gen.G
    {"name": "Kiin",      "team": "Gen.G",               "role": "TOP",     "region": "KR"},
    {"name": "Canyon",    "team": "Gen.G",               "role": "JUNGLE",  "region": "KR"},
    {"name": "Chovy",     "team": "Gen.G",               "role": "MID",     "region": "KR"},
    {"name": "Ruler",     "team": "Gen.G",               "role": "ADC",     "region": "KR"},
    {"name": "Lehends",   "team": "Gen.G",               "role": "SUPPORT", "region": "KR"},
    # Hanwha Life Esports
    {"name": "Zeus",      "team": "Hanwha Life Esports", "role": "TOP",     "region": "KR"},
    {"name": "Kanavi",    "team": "Hanwha Life Esports", "role": "JUNGLE",  "region": "KR"},
    {"name": "Zeka",      "team": "Hanwha Life Esports", "role": "MID",     "region": "KR"},
    {"name": "Gumayusi",  "team": "Hanwha Life Esports", "role": "ADC",     "region": "KR"},
    {"name": "Delight",   "team": "Hanwha Life Esports", "role": "SUPPORT", "region": "KR"},
    # KT Rolster
    {"name": "Kingen",    "team": "KT Rolster",          "role": "TOP",     "region": "KR"},
    {"name": "Cuzz",      "team": "KT Rolster",          "role": "JUNGLE",  "region": "KR"},
    {"name": "Bdd",       "team": "KT Rolster",          "role": "MID",     "region": "KR"},
    {"name": "Aiming",    "team": "KT Rolster",          "role": "ADC",     "region": "KR"},
    {"name": "Ghost",     "team": "KT Rolster",          "role": "SUPPORT", "region": "KR"},
    # DRX
    {"name": "Rich",      "team": "DRX",                 "role": "TOP",     "region": "KR"},
    {"name": "Vincenzo",  "team": "DRX",                 "role": "JUNGLE",  "region": "KR"},
    {"name": "ucal",      "team": "DRX",                 "role": "MID",     "region": "KR"},
    {"name": "Jiwoo",     "team": "DRX",                 "role": "ADC",     "region": "KR"},
    {"name": "Andil",     "team": "DRX",                 "role": "SUPPORT", "region": "KR"},
    # Dplus KIA
    {"name": "Siwoo",     "team": "Dplus KIA",           "role": "TOP",     "region": "KR"},
    {"name": "Lucid",     "team": "Dplus KIA",           "role": "JUNGLE",  "region": "KR"},
    {"name": "ShowMaker", "team": "Dplus KIA",           "role": "MID",     "region": "KR"},
    {"name": "Smash",     "team": "Dplus KIA",           "role": "ADC",     "region": "KR"},
    {"name": "Career",    "team": "Dplus KIA",           "role": "SUPPORT", "region": "KR"},
    # Nongshim RedForce
    {"name": "Kingen",    "team": "Nongshim RedForce",   "role": "TOP",     "region": "KR"},
    {"name": "Sponge",    "team": "Nongshim RedForce",   "role": "JUNGLE",  "region": "KR"},
    {"name": "Scout",     "team": "Nongshim RedForce",   "role": "MID",     "region": "KR"},
    {"name": "Taeyoon",   "team": "Nongshim RedForce",   "role": "ADC",     "region": "KR"},
    {"name": "Lehends",   "team": "Nongshim RedForce",   "role": "SUPPORT", "region": "KR"},
    # FEARX
    {"name": "Raptor",    "team": "FEARX",               "role": "JUNGLE",  "region": "KR"},
    {"name": "VicLa",     "team": "FEARX",               "role": "MID",     "region": "KR"},
    {"name": "Clear",     "team": "FEARX",               "role": "ADC",     "region": "KR"},
    {"name": "Kellin",    "team": "FEARX",               "role": "SUPPORT", "region": "KR"},
    # DN SOOPers (ex Kwangdong Freecs / DN Freecs)
    {"name": "DuDu",      "team": "DN SOOPers",          "role": "TOP",     "region": "KR"},
    {"name": "Pyosik",    "team": "DN SOOPers",          "role": "JUNGLE",  "region": "KR"},
    {"name": "Clozer",    "team": "DN SOOPers",          "role": "MID",     "region": "KR"},
    {"name": "deokdam",   "team": "DN SOOPers",          "role": "ADC",     "region": "KR"},
    {"name": "Peter",     "team": "DN SOOPers",          "role": "SUPPORT", "region": "KR"},
]

def fix_lck():
    db = SessionLocal()

    print("🗑️  Suppression de tous les joueurs KR...")
    deleted = db.query(ProPlayer).filter(ProPlayer.region == "KR").delete()
    db.commit()
    print(f"   → {deleted} joueurs supprimés\n")

    print("✅ Insertion des vrais rosters LCK 2026...")
    added = 0
    for pro in LCK_2026:
        player = ProPlayer(
            name=pro["name"],
            team=pro["team"],
            role=pro["role"],
            region=pro["region"],
            accent_color=TEAM_COLORS.get(pro["team"], "#00e5ff"),
            riot_puuid=None,
            photo_url=None,
            is_active=True,
        )
        db.add(player)
        added += 1
        print(f"   ✅ {pro['name']} ({pro['team']} · {pro['role']})")

    db.commit()
    db.close()
    print(f"\n🎮 LCK mis à jour — {added} joueurs ajoutés")

if __name__ == "__main__":
    fix_lck()