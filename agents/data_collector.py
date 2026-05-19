# agents/data_collector.py
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config import AGENT_VERBOSE, MAX_REVIEWS_PER_RUN

from data.yelp_loader import load_yelp_reviews
from data.google_scraper import scrape_google_reviews
from data.csv_handler import load_from_csv


def collect_reviews(
    business_name: str,
    csv_path: str = None,
    limit: int = MAX_REVIEWS_PER_RUN,
) -> tuple[pd.DataFrame, str]:
    """
    Hàm chính: thu thập reviews từ nhiều nguồn theo thứ tự ưu tiên.
    Trả về (DataFrame, source) — source là nguồn dữ liệu đã dùng.

    Thứ tự ưu tiên:
    1. CSV upload (nếu có)
    2. Yelp Dataset
    3. Google Maps scraping
    """
    print(f"🤖 Data Collector: Thu thập reviews cho '{business_name}'...")

    # ── Nguồn 1: CSV upload ───────────────────────────────────────────────────
    if csv_path:
        print(f"   📂 Thử nguồn 1: CSV upload ({csv_path})")
        try:
            df = load_from_csv(csv_path)
            if not df.empty:
                print(f"   ✅ Lấy được {len(df)} reviews từ CSV")
                return df, "csv"
        except Exception as e:
            print(f"   ❌ CSV lỗi: {e}")

    # ── Nguồn 2: Yelp Dataset ─────────────────────────────────────────────────
    print(f"   📂 Thử nguồn 2: Yelp Dataset")
    try:
        df = load_yelp_reviews(business_name, limit=limit)
        if not df.empty:
            print(f"   ✅ Lấy được {len(df)} reviews từ Yelp")
            return df, "yelp"
    except Exception as e:
        print(f"   ❌ Yelp lỗi: {e}")

    # ── Nguồn 3: Google Maps scraping ─────────────────────────────────────────
    print(f"   📂 Thử nguồn 3: Google Maps")
    try:
        df = scrape_google_reviews(business_name, limit=limit)
        if not df.empty:
            print(f"   ✅ Lấy được {len(df)} reviews từ Google Maps")
            return df, "google"
    except Exception as e:
        print(f"   ❌ Google Maps lỗi: {e}")

    # ── Không tìm thấy ────────────────────────────────────────────────────────
    print(f"   ❌ Không tìm thấy reviews cho '{business_name}' từ bất kỳ nguồn nào")
    return pd.DataFrame(), "none"


def collect_from_multiple_sources(
    business_name: str,
    limit: int = MAX_REVIEWS_PER_RUN,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Thu thập reviews từ TẤT CẢ các nguồn có thể rồi gộp lại.
    Dùng khi muốn tối đa hoá số lượng reviews.
    Trả về (DataFrame gộp, list các nguồn đã dùng).
    """
    print(f"🤖 Data Collector: Thu thập từ tất cả nguồn cho '{business_name}'...")

    all_dfs = []
    sources_used = []

    # Yelp
    try:
        df_yelp = load_yelp_reviews(business_name, limit=limit)
        if not df_yelp.empty:
            df_yelp["source"] = "yelp"
            all_dfs.append(df_yelp)
            sources_used.append("yelp")
            print(f"   ✅ Yelp: {len(df_yelp)} reviews")
    except Exception as e:
        print(f"   ❌ Yelp: {e}")

    # Google Maps
    try:
        df_google = scrape_google_reviews(business_name, limit=limit // 2)
        if not df_google.empty:
            df_google["source"] = "google"
            all_dfs.append(df_google)
            sources_used.append("google")
            print(f"   ✅ Google: {len(df_google)} reviews")
    except Exception as e:
        print(f"   ❌ Google: {e}")

    if not all_dfs:
        print(f"   ❌ Không có reviews từ nguồn nào")
        return pd.DataFrame(), []

    # Gộp và dedup
    df_combined = pd.concat(all_dfs, ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=["text"], keep="first")

    print(f"✅ Tổng cộng: {len(df_combined)} reviews từ {sources_used}")
    return df_combined, sources_used


if __name__ == "__main__":
    # Test nguồn ưu tiên
    print("=" * 50)
    print("TEST: Thu thập theo thứ tự ưu tiên")
    print("=" * 50)
    df, source = collect_reviews("McDonald's", limit=10)
    print(f"Nguồn dùng: {source}")
    if not df.empty:
        print(df[["text", "stars"]].head(3))    