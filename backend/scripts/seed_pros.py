import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.pro_player import ProPlayer

TEAM_COLORS = {
    "T1": "#c89b3c", "Gen.G": "#d946a8", "KT Rolster": "#ef4444",
    "Hanwha Life Esports": "#ff6b35", "DRX": "#378add", "Dplus KIA": "#a78bfa",
    "Nongshim RedForce": "#ef4444", "HANJIN BRION": "#22c55e",
    "OKSavingsBank BRION": "#22c55e", "Kwangdong Freecs": "#00e5ff",
    "G2 Esports": "#00e5ff", "Fnatic": "#f97316", "Team Vitality": "#facc15",
    "Karmine Corp": "#00e5ff", "MAD Lions KOI": "#ef4444", "Team BDS": "#378add",
    "SK Gaming": "#22c55e", "Team Heretics": "#d946a8", "GIANTX": "#ef4444",
    "Rogue": "#a78bfa",
    "JDG": "#c89b3c", "BLG": "#378add", "Top Esports": "#00e5ff",
    "Weibo Gaming": "#d946a8", "EDG": "#378add", "LNG": "#a78bfa",
    "Team WE": "#22c55e", "Invictus Gaming": "#ef4444", "FPX": "#c89b3c",
    "NIP": "#22c55e", "RNG": "#ef4444", "OMG": "#f97316",
}

PROS_2026 = [
    # ── LCK ──────────────────────────────────────────────────────
    # T1
    { "name": "Zeus",      "team": "T1",              "role": "TOP",     "region": "KR", "league": "LCK" },
    { "name": "Oner",      "team": "T1",              "role": "JUNGLE",  "region": "KR", "league": "LCK" },
    { "name": "Faker",     "team": "T1",              "role": "MID",     "region": "KR", "league": "LCK" },
    { "name": "Peyz",      "team": "T1",              "role": "ADC",     "region": "KR", "league": "LCK" },
    { "name": "Keria",     "team": "T1",              "role": "SUPPORT", "region": "KR", "league": "LCK" },
    # Gen.G
    { "name": "Kiin",      "team": "Gen.G",           "role": "TOP",     "region": "KR", "league": "LCK" },
    { "name": "Canyon",    "team": "Gen.G",           "role": "JUNGLE",  "region": "KR", "league": "LCK" },
    { "name": "Chovy",     "team": "Gen.G",           "role": "MID",     "region": "KR", "league": "LCK" },
    { "name": "Ruler",     "team": "Gen.G",           "role": "ADC",     "region": "KR", "league": "LCK" },
    { "name": "Lehends",   "team": "Gen.G",           "role": "SUPPORT", "region": "KR", "league": "LCK" },
    # Hanwha Life Esports
    { "name": "Zeus",      "team": "Hanwha Life Esports", "role": "TOP",    "region": "KR", "league": "LCK" },
    { "name": "Kanavi",    "team": "Hanwha Life Esports", "role": "JUNGLE", "region": "KR", "league": "LCK" },
    { "name": "Zeka",      "team": "Hanwha Life Esports", "role": "MID",    "region": "KR", "league": "LCK" },
    { "name": "Gumayusi",  "team": "Hanwha Life Esports", "role": "ADC",    "region": "KR", "league": "LCK" },
    { "name": "Delight",   "team": "Hanwha Life Esports", "role": "SUPPORT","region": "KR", "league": "LCK" },
    # KT Rolster
    { "name": "Kingen",    "team": "KT Rolster",      "role": "TOP",     "region": "KR", "league": "LCK" },
    { "name": "Cuzz",      "team": "KT Rolster",      "role": "JUNGLE",  "region": "KR", "league": "LCK" },
    { "name": "Bdd",       "team": "KT Rolster",      "role": "MID",     "region": "KR", "league": "LCK" },
    { "name": "Aiming",    "team": "KT Rolster",      "role": "ADC",     "region": "KR", "league": "LCK" },
    { "name": "Effort",    "team": "KT Rolster",      "role": "SUPPORT", "region": "KR", "league": "LCK" },
    # DRX
    { "name": "Rascal",    "team": "DRX",             "role": "TOP",     "region": "KR", "league": "LCK" },
    { "name": "Pyosik",    "team": "DRX",             "role": "JUNGLE",  "region": "KR", "league": "LCK" },
    { "name": "Quad",      "team": "DRX",             "role": "MID",     "region": "KR", "league": "LCK" },
    { "name": "Deft",      "team": "DRX",             "role": "ADC",     "region": "KR", "league": "LCK" },
    { "name": "BeryL",     "team": "DRX",             "role": "SUPPORT", "region": "KR", "league": "LCK" },
    # Dplus KIA
    { "name": "Burdol",    "team": "Dplus KIA",       "role": "TOP",     "region": "KR", "league": "LCK" },
    { "name": "Lucid",     "team": "Dplus KIA",       "role": "JUNGLE",  "region": "KR", "league": "LCK" },
    { "name": "ShowMaker", "team": "Dplus KIA",       "role": "MID",     "region": "KR", "league": "LCK" },
    { "name": "Smash",     "team": "Dplus KIA",       "role": "ADC",     "region": "KR", "league": "LCK" },
    { "name": "Career",    "team": "Dplus KIA",       "role": "SUPPORT", "region": "KR", "league": "LCK" },
    # Nongshim RedForce
    { "name": "DuDu",      "team": "Nongshim RedForce","role": "TOP",    "region": "KR", "league": "LCK" },
    { "name": "Sponge",    "team": "Nongshim RedForce","role": "JUNGLE", "region": "KR", "league": "LCK" },
    { "name": "Scout",     "team": "Nongshim RedForce","role": "MID",    "region": "KR", "league": "LCK" },
    { "name": "Taeyoon",   "team": "Nongshim RedForce","role": "ADC",    "region": "KR", "league": "LCK" },
    { "name": "Peter",     "team": "Nongshim RedForce","role": "SUPPORT","region": "KR", "league": "LCK" },
    # Kwangdong Freecs
    { "name": "Roamer",    "team": "Kwangdong Freecs","role": "TOP",     "region": "KR", "league": "LCK" },
    { "name": "GIDEON",    "team": "Kwangdong Freecs","role": "JUNGLE",  "region": "KR", "league": "LCK" },
    { "name": "Fisher",    "team": "Kwangdong Freecs","role": "MID",     "region": "KR", "league": "LCK" },
    { "name": "Tafo",      "team": "Kwangdong Freecs","role": "ADC",     "region": "KR", "league": "LCK" },
    { "name": "Lehends",   "team": "Kwangdong Freecs","role": "SUPPORT", "region": "KR", "league": "LCK" },

    # ── LEC ──────────────────────────────────────────────────────
    # G2 Esports
    { "name": "BrokenBlade","team": "G2 Esports",    "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Yike",      "team": "G2 Esports",     "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "Caps",      "team": "G2 Esports",     "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "Hans Sama", "team": "G2 Esports",     "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Mikyx",     "team": "G2 Esports",     "role": "SUPPORT", "region": "EUW", "league": "LEC" },
    # Fnatic
    { "name": "Empyros",   "team": "Fnatic",          "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Razork",    "team": "Fnatic",          "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "Vladi",     "team": "Fnatic",          "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "Upset",     "team": "Fnatic",          "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Lospa",     "team": "Fnatic",          "role": "SUPPORT", "region": "EUW", "league": "LEC" },
    # Karmine Corp
    { "name": "Canna",     "team": "Karmine Corp",    "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Yike",      "team": "Karmine Corp",    "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "Caliste",   "team": "Karmine Corp",    "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "Neon",      "team": "Karmine Corp",    "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Kyeahoo",   "team": "Karmine Corp",    "role": "SUPPORT", "region": "EUW", "league": "LEC" },
    # Team Vitality
    { "name": "Photon",    "team": "Team Vitality",   "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Jankos",    "team": "Team Vitality",   "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "Vetheo",    "team": "Team Vitality",   "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "Neon",      "team": "Team Vitality",   "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Kaiser",    "team": "Team Vitality",   "role": "SUPPORT", "region": "EUW", "league": "LEC" },
    # MAD Lions KOI
    { "name": "Irrelevant","team": "MAD Lions KOI",   "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Elyoya",    "team": "MAD Lions KOI",   "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "Humanoid",  "team": "MAD Lions KOI",   "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "UNF0RGIVEN","team": "MAD Lions KOI",   "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Hylissang", "team": "MAD Lions KOI",   "role": "SUPPORT", "region": "EUW", "league": "LEC" },
    # SK Gaming
    { "name": "Wunder",    "team": "SK Gaming",       "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Markoon",   "team": "SK Gaming",       "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "Reeker",    "team": "SK Gaming",       "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "Exakick",   "team": "SK Gaming",       "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Mikyx",     "team": "SK Gaming",       "role": "SUPPORT", "region": "EUW", "league": "LEC" },
    # Team Heretics
    { "name": "Odoamne",   "team": "Team Heretics",   "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Daglas",    "team": "Team Heretics",   "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "Ruby",      "team": "Team Heretics",   "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "Jackies",   "team": "Team Heretics",   "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Trymbi",    "team": "Team Heretics",   "role": "SUPPORT", "region": "EUW", "league": "LEC" },
    # Team BDS
    { "name": "Adam",      "team": "Team BDS",        "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Sheo",      "team": "Team BDS",        "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "nuc",       "team": "Team BDS",        "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "Paduck",    "team": "Team BDS",        "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Trymbi",    "team": "Team BDS",        "role": "SUPPORT", "region": "EUW", "league": "LEC" },
    # GIANTX
    { "name": "Finn",      "team": "GIANTX",          "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Malrang",   "team": "GIANTX",          "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "Fabian",    "team": "GIANTX",          "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "Patrik",    "team": "GIANTX",          "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Labrov",    "team": "GIANTX",          "role": "SUPPORT", "region": "EUW", "league": "LEC" },
    # Rogue
    { "name": "Thiago",    "team": "Rogue",           "role": "TOP",     "region": "EUW", "league": "LEC" },
    { "name": "Inspired",  "team": "Rogue",           "role": "JUNGLE",  "region": "EUW", "league": "LEC" },
    { "name": "Larssen",   "team": "Rogue",           "role": "MID",     "region": "EUW", "league": "LEC" },
    { "name": "Comp",      "team": "Rogue",           "role": "ADC",     "region": "EUW", "league": "LEC" },
    { "name": "Targamas",  "team": "Rogue",           "role": "SUPPORT", "region": "EUW", "league": "LEC" },

    # ── LPL ──────────────────────────────────────────────────────
    # JDG
    { "name": "369",       "team": "JDG",             "role": "TOP",     "region": "CN", "league": "LPL" },
    { "name": "Kanavi",    "team": "JDG",             "role": "JUNGLE",  "region": "CN", "league": "LPL" },
    { "name": "knight",    "team": "JDG",             "role": "MID",     "region": "CN", "league": "LPL" },
    { "name": "Ruler",     "team": "JDG",             "role": "ADC",     "region": "CN", "league": "LPL" },
    { "name": "Missing",   "team": "JDG",             "role": "SUPPORT", "region": "CN", "league": "LPL" },
    # BLG
    { "name": "Bin",       "team": "BLG",             "role": "TOP",     "region": "CN", "league": "LPL" },
    { "name": "XUN",       "team": "BLG",             "role": "JUNGLE",  "region": "CN", "league": "LPL" },
    { "name": "Yagao",     "team": "BLG",             "role": "MID",     "region": "CN", "league": "LPL" },
    { "name": "Elk",       "team": "BLG",             "role": "ADC",     "region": "CN", "league": "LPL" },
    { "name": "ON",        "team": "BLG",             "role": "SUPPORT", "region": "CN", "league": "LPL" },
    # Top Esports
    { "name": "369",       "team": "Top Esports",     "role": "TOP",     "region": "CN", "league": "LPL" },
    { "name": "Tian",      "team": "Top Esports",     "role": "JUNGLE",  "region": "CN", "league": "LPL" },
    { "name": "Creme",     "team": "Top Esports",     "role": "MID",     "region": "CN", "league": "LPL" },
    { "name": "JackeyLove","team": "Top Esports",     "role": "ADC",     "region": "CN", "league": "LPL" },
    { "name": "Hang",      "team": "Top Esports",     "role": "SUPPORT", "region": "CN", "league": "LPL" },
    # Weibo Gaming
    { "name": "Zika",      "team": "Weibo Gaming",    "role": "TOP",     "region": "CN", "league": "LPL" },
    { "name": "JieJie",    "team": "Weibo Gaming",    "role": "JUNGLE",  "region": "CN", "league": "LPL" },
    { "name": "Xiaohu",    "team": "Weibo Gaming",    "role": "MID",     "region": "CN", "league": "LPL" },
    { "name": "Elk",       "team": "Weibo Gaming",    "role": "ADC",     "region": "CN", "league": "LPL" },
    { "name": "Crisp",     "team": "Weibo Gaming",    "role": "SUPPORT", "region": "CN", "league": "LPL" },
    # EDG
    { "name": "Flandre",   "team": "EDG",             "role": "TOP",     "region": "CN", "league": "LPL" },
    { "name": "Jiejie",    "team": "EDG",             "role": "JUNGLE",  "region": "CN", "league": "LPL" },
    { "name": "Scout",     "team": "EDG",             "role": "MID",     "region": "CN", "league": "LPL" },
    { "name": "Viper",     "team": "EDG",             "role": "ADC",     "region": "CN", "league": "LPL" },
    { "name": "Meiko",     "team": "EDG",             "role": "SUPPORT", "region": "CN", "league": "LPL" },
    # LNG
    { "name": "Breathe",   "team": "LNG",             "role": "TOP",     "region": "CN", "league": "LPL" },
    { "name": "Tarzan",    "team": "LNG",             "role": "JUNGLE",  "region": "CN", "league": "LPL" },
    { "name": "Rookie",    "team": "LNG",             "role": "MID",     "region": "CN", "league": "LPL" },
    { "name": "GALA",      "team": "LNG",             "role": "ADC",     "region": "CN", "league": "LPL" },
    { "name": "Hang",      "team": "LNG",             "role": "SUPPORT", "region": "CN", "league": "LPL" },
    # RNG
    { "name": "Breathe",   "team": "RNG",             "role": "TOP",     "region": "CN", "league": "LPL" },
    { "name": "Wei",       "team": "RNG",             "role": "JUNGLE",  "region": "CN", "league": "LPL" },
    { "name": "Xiaohu",    "team": "RNG",             "role": "MID",     "region": "CN", "league": "LPL" },
    { "name": "GALA",      "team": "RNG",             "role": "ADC",     "region": "CN", "league": "LPL" },
    { "name": "Ming",      "team": "RNG",             "role": "SUPPORT", "region": "CN", "league": "LPL" },
]

def seed():
    db = SessionLocal()
    added = 0
    skipped = 0

    for pro in PROS_2026:
        existing = db.query(ProPlayer).filter(
            ProPlayer.name == pro["name"],
            ProPlayer.team == pro["team"]
        ).first()

        if existing:
            skipped += 1
            continue

        accent = TEAM_COLORS.get(pro["team"], "#00e5ff")
        player = ProPlayer(
            name=pro["name"],
            team=pro["team"],
            role=pro["role"],
            region=pro["region"],
            accent_color=accent,
            riot_puuid=None,
            photo_url=None,
            is_active=True,
        )
        db.add(player)
        added += 1
        print(f"✅ {pro['name']} ({pro['team']} · {pro['role']} · {pro['league']})")

    db.commit()
    db.close()
    print(f"\n🎮 Seed terminé — {added} ajoutés, {skipped} ignorés")

if __name__ == "__main__":
    seed()