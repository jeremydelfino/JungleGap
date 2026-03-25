import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.pro_player import ProPlayer

TEAM_COLORS = {
    # ── LEC ─────────────────────────────────────────
    "G2 Esports":      "#FF0000",  # Rouge vif G2
    "Fnatic":          "#FF6600",  # Orange Fnatic
    "Karmine Corp":    "#00BFFF",  # Bleu électrique KC
    "Movistar KOI":   "#E4003B",  # Rouge KOI/Movistar
    "GIANTX":          "#FFD700",  # Jaune GIANTX
    "Team Vitality":   "#FFE135",  # Jaune Vitality
    "Shifters":        "#1E90FF",  # Bleu Shifters (ex BDS)
    "SK Gaming":       "#00AA00",  # Vert SK
    "Team Heretics":   "#8B0000",  # Rouge foncé Heretics
    "Natus Vincere":   "#F5C400",  # Jaune or NAVI

    # ── LCK ─────────────────────────────────────────
    "T1":                    "#9B0D0D",  # Rouge T1
    "Gen.G":                 "#C89B3C",  # Or Gen.G
    "Hanwha Life Esports":   "#FF6B00",  # Orange HLE
    "KT Rolster":            "#FF0000",  # Rouge KT
    "DRX":                   "#1E73BE",  # Bleu DRX
    "Dplus KIA":             "#5B2D8E",  # Violet DK
    "Nongshim RedForce":     "#CC0000",  # Rouge NS
    "HANJIN BRION":          "#00A86B",  # Vert BRION
    "Kwangdong Freecs":      "#00BFFF",  # Bleu cyan KDF

    # ── LPL ─────────────────────────────────────────
    "JDG":           "#CC0000",  # Rouge JDG
    "BLG":           "#0057A8",  # Bleu BLG
    "Top Esports":   "#00C8FF",  # Cyan TES
    "Weibo Gaming":  "#CC0033",  # Rouge Weibo
    "EDG":           "#003087",  # Bleu foncé EDG
    "LNG":           "#FF4500",  # Rouge orangé LNG
    "RNG":           "#C8A951",  # Or RNG
}

LEC_2026 = [
    
    
    # G2 Esports
    {"name": "BrokenBlade", "team": "G2 Esports",   "role": "TOP",     "region": "EUW"},
    {"name": "SkewMond",    "team": "G2 Esports",   "role": "JUNGLE",  "region": "EUW"},
    {"name": "Caps",        "team": "G2 Esports",   "role": "MID",     "region": "EUW"},
    {"name": "Hans Sama",   "team": "G2 Esports",   "role": "ADC",     "region": "EUW"},
    {"name": "Labrov",      "team": "G2 Esports",   "role": "SUPPORT", "region": "EUW"},
    # Fnatic
    {"name": "Empyros",     "team": "Fnatic",       "role": "TOP",     "region": "EUW"},
    {"name": "Razork",      "team": "Fnatic",       "role": "JUNGLE",  "region": "EUW"},
    {"name": "Vladi",       "team": "Fnatic",       "role": "MID",     "region": "EUW"},
    {"name": "Upset",       "team": "Fnatic",       "role": "ADC",     "region": "EUW"},
    {"name": "Lospa",       "team": "Fnatic",       "role": "SUPPORT", "region": "EUW"},
    # Karmine Corp
    {"name": "Canna",       "team": "Karmine Corp", "role": "TOP",     "region": "EUW"},
    {"name": "Yike",        "team": "Karmine Corp", "role": "JUNGLE",  "region": "EUW"},
    {"name": "Kyeahoo",     "team": "Karmine Corp", "role": "MID",     "region": "EUW"},
    {"name": "Caliste",     "team": "Karmine Corp", "role": "ADC",     "region": "EUW"},
    {"name": "Busio",       "team": "Karmine Corp", "role": "SUPPORT", "region": "EUW"},
    # Movistar KOI
    {"name": "Myrwn",       "team": "Movistar KOI", "role": "TOP",     "region": "EUW"},
    {"name": "Elyoya",      "team": "Movistar KOI", "role": "JUNGLE",  "region": "EUW"},
    {"name": "Jojopyun",    "team": "Movistar KOI", "role": "MID",     "region": "EUW"},
    {"name": "Supa",        "team": "Movistar KOI", "role": "ADC",     "region": "EUW"},
    {"name": "Alvaro",      "team": "Movistar KOI", "role": "SUPPORT", "region": "EUW"},
    # GIANTX
    {"name": "Lot",         "team": "GIANTX",       "role": "TOP",     "region": "EUW"},
    {"name": "ISMA",        "team": "GIANTX",       "role": "JUNGLE",  "region": "EUW"},
    {"name": "Jackies",     "team": "GIANTX",       "role": "MID",     "region": "EUW"},
    {"name": "Noah",        "team": "GIANTX",       "role": "ADC",     "region": "EUW"},
    {"name": "Jun",         "team": "GIANTX",       "role": "SUPPORT", "region": "EUW"},
    # Team Vitality
    {"name": "Naak Nako",   "team": "Team Vitality","role": "TOP",     "region": "EUW"},
    {"name": "Lyncas",      "team": "Team Vitality","role": "JUNGLE",  "region": "EUW"},
    {"name": "Humanoid",    "team": "Team Vitality","role": "MID",     "region": "EUW"},
    {"name": "Carzzy",      "team": "Team Vitality","role": "ADC",     "region": "EUW"},
    {"name": "Fleshy",      "team": "Team Vitality","role": "SUPPORT", "region": "EUW"},
    # Shifters (ex Team BDS)
    {"name": "Rooster",     "team": "Shifters",     "role": "TOP",     "region": "EUW"},
    {"name": "Boukada",     "team": "Shifters",     "role": "JUNGLE",  "region": "EUW"},
    {"name": "nuc",         "team": "Shifters",     "role": "MID",     "region": "EUW"},
    {"name": "Paduck",      "team": "Shifters",     "role": "ADC",     "region": "EUW"},
    {"name": "Trymbi",      "team": "Shifters",     "role": "SUPPORT", "region": "EUW"},
    # SK Gaming
    {"name": "Wunder",      "team": "SK Gaming",    "role": "TOP",     "region": "EUW"},
    {"name": "Markoon",     "team": "SK Gaming",    "role": "JUNGLE",  "region": "EUW"},
    {"name": "Reeker",      "team": "SK Gaming",    "role": "MID",     "region": "EUW"},
    {"name": "Exakick",     "team": "SK Gaming",    "role": "ADC",     "region": "EUW"},
    {"name": "Mikyx",       "team": "SK Gaming",    "role": "SUPPORT", "region": "EUW"},
    # Team Heretics
    {"name": "Odoamne",     "team": "Team Heretics","role": "TOP",     "region": "EUW"},
    {"name": "Daglas",      "team": "Team Heretics","role": "JUNGLE",  "region": "EUW"},
    {"name": "Tracyn",      "team": "Team Heretics","role": "MID",     "region": "EUW"},
    {"name": "Jackies",     "team": "Team Heretics","role": "ADC",     "region": "EUW"},
    {"name": "Alvaro",      "team": "Team Heretics","role": "SUPPORT", "region": "EUW"},
    # Natus Vincere
    {"name": "Maynter",     "team": "Natus Vincere","role": "TOP",     "region": "EUW"},
    {"name": "Sanchi",      "team": "Natus Vincere","role": "JUNGLE",  "region": "EUW"},
    {"name": "Larssen",     "team": "Natus Vincere","role": "MID",     "region": "EUW"},
    {"name": "Patrik",      "team": "Natus Vincere","role": "ADC",     "region": "EUW"},
    {"name": "Poby",        "team": "Natus Vincere","role": "SUPPORT", "region": "EUW"},
]

LEC_WRONG_TEAMS = [
    "MAD Lions", "MAD Lions KOI", "Rogue", "Team BDS",
    "BrokenBlade", "Jankos", "Jackies", "Humanoid",
    "Irrelevant", "UNF0RGIVEN", "Hylissang", "Finn",
    "Malrang", "Fabian", "Patrik", "Comp", "Targamas",
    "Thiago", "Inspired", "Larssen",
]

def update_lec():
    db = SessionLocal()

    print("🗑️  Suppression des anciens joueurs LEC incorrects...")
    deleted = db.query(ProPlayer).filter(
        ProPlayer.region == "EUW"
    ).delete()
    print(f"   → {deleted} joueurs EUW supprimés")
    db.commit()

    print("\n✅ Insertion des vrais rosters LEC 2026...")
    added = 0
    for pro in LEC_2026:
        existing = db.query(ProPlayer).filter(
            ProPlayer.name == pro["name"],
            ProPlayer.team == pro["team"]
        ).first()
        if existing:
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
        print(f"   ✅ {pro['name']} ({pro['team']} · {pro['role']})")

    db.commit()
    db.close()
    print(f"\n🎮 LEC mis à jour — {added} joueurs ajoutés")

if __name__ == "__main__":
    update_lec()