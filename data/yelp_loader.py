# data/yelp_loader.py
import os
import json
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MAX_REVIEWS_PER_RUN, DATA_DIR


def load_yelp_reviews(business_name: str, limit: int = MAX_REVIEWS_PER_RUN) -> pd.DataFrame:
    """
    Tìm reviews theo tên quán trong Yelp Dataset.
    Trả về DataFrame với các cột: review_id, business_name, stars, text, date, useful
    """
    json_path = os.path.join(DATA_DIR, "yelp_academic_dataset_review.json")
    business_path = os.path.join(DATA_DIR, "yelp_academic_dataset_business.json")

    if not os.path.exists(json_path) or not os.path.exists(business_path):
        print("⚠️  Không tìm thấy Yelp dataset, chuyển sang nguồn khác...")
        return pd.DataFrame()

    # Bước 1: Tìm business_id từ tên quán
    print(f"🔍 Tìm kiếm '{business_name}' trong Yelp Dataset...")
    matched_ids = {}  # business_id → tên quán thực tế

    with open(business_path, "r", encoding="utf-8") as f:
        for line in f:
            biz = json.loads(line)
            if business_name.lower() in biz.get("name", "").lower():
                matched_ids[biz["business_id"]] = biz["name"]
                print(f"   ✅ Tìm thấy: {biz['name']} | {biz.get('city', '')} | ⭐ {biz.get('stars', '')}")

    if not matched_ids:
        print(f"   ❌ Không tìm thấy '{business_name}' trong Yelp Dataset.")
        return pd.DataFrame()

    print(f"   → Tổng {len(matched_ids)} chi nhánh tìm thấy")

    # Bước 2: Lấy reviews theo business_id
    print(f"📥 Đang load reviews (tối đa {limit})...")
    reviews = []

    with open(json_path, "r", encoding="utf-8") as f:
        for line in f:
            if len(reviews) >= limit:
                break
            review = json.loads(line)
            bid = review.get("business_id")
            if bid in matched_ids:
                reviews.append({
                    "review_id": review.get("review_id"),
                    "business_id": bid,
                    "business_name": matched_ids[bid],  # tên thực tế từ business.json
                    "stars": review.get("stars"),
                    "text": review.get("text"),
                    "date": review.get("date"),
                    "useful": review.get("useful", 0),
                })

    if not reviews:
        print("   ❌ Không có reviews nào.")
        return pd.DataFrame()

    df = pd.DataFrame(reviews)
    print(f"✅ Load xong: {len(df)} reviews cho '{business_name}'")
    return df


def load_from_csv(csv_path: str) -> pd.DataFrame:
    """
    Load reviews từ file CSV do user upload.
    CSV cần có ít nhất 2 cột: text, stars
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Không tìm thấy file: {csv_path}")

    df = pd.read_csv(csv_path)

    required = {"text", "stars"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV thiếu cột: {missing}. Cần có: {required}")

    print(f"✅ Load CSV xong: {len(df)} reviews")
    return df


if __name__ == "__main__":
    df = load_yelp_reviews("Nhậu tự do", limit=10)
    if not df.empty:
        print(df[["business_name", "stars", "text"]].head())