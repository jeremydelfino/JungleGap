# test_leaguepedia_scraper.py
import sys
sys.path.insert(0, ".")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from services.leaguepedia_scraper import refresh_pro_stats


def main():
    # 1 tournoi connu pour valider
    result = refresh_pro_stats() 
    print("\n=== RESULT ===")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()