import sys
sys.path.insert(0, ".")

from database import SessionLocal
from services.coachdiff_scorer import TeamPick, score_team


def show_tier_details(label, picks, opponents):
    db = SessionLocal()
    result = score_team(db, picks, opponents, region="ALL")
    print(f"\n=== {label} — total {result['total_display']}/100 ===")
    print(f"  breakdown: {result['breakdown']}")
    print(f"  categories: {result['categories']}")
    print(f"\n  Tier details:")
    print(f"    {'Champion':12s} {'Lane':8s} {'WR_solo':8s} {'WR_pro':8s} {'PR_pro':8s} {'n_pro':6s} {'tier':6s} {'source':20s}")
    for d in result['details']['tier']:
        wr_pro = f"{d['wr_pro']:.3f}" if d['wr_pro'] is not None else "-"
        pr_pro = f"{d['pr_pro']:.3f}" if d['pr_pro'] is not None else "-"
        print(f"    {d['champion']:12s} {d['lane']:8s} {d['wr_solo']:.3f}    {wr_pro:8s} {pr_pro:8s} {d['n_picks_pro']:<6d} {d['tier']:.3f}  {d['source']}")
    db.close()


def main():
    meta = [
        TeamPick("Aatrox","TOP"), TeamPick("Xin Zhao","JUNGLE"), TeamPick("Azir","MID"),
        TeamPick("Yunara","ADC"),   TeamPick("Lulu","SUPPORT"),
    ]
    offmeta = [
        TeamPick("Sylas","TOP"),  TeamPick("Karthus","JUNGLE"), TeamPick("Akshan","MID"),
        TeamPick("Senna","ADC"),  TeamPick("Pantheon","SUPPORT"),
    ]
    show_tier_details("META",    meta,    offmeta)
    show_tier_details("OFFMETA", offmeta, meta)


if __name__ == "__main__":
    main()