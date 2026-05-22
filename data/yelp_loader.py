# data/yelp_loader.py
import os
import sys
import json
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR


def search_businesses(business_name: str) -> list[dict]:
    """
    Bước 1: Tìm kiếm tất cả chi nhánh theo tên.
    Sort theo review_count giảm dần để chi nhánh có nhiều reviews lên đầu.
    Trả về list các chi nhánh để user chọn.
    """
    business_path = os.path.join(DATA_DIR, "yelp_academic_dataset_business.json")

    if not os.path.exists(business_path):
        print("⚠️  Không tìm thấy Yelp business dataset")
        return []

    print(f"🔍 Tìm kiếm '{business_name}' trong Yelp Dataset...")
    matches = []

    with open(business_path, "r", encoding="utf-8") as f:
        for line in f:
            biz = json.loads(line)
            if business_name.lower() in biz.get("name", "").lower():
                review_count = biz.get("review_count", 0)
                matches.append({
                    "business_id": biz["business_id"],
                    "name":         biz.get("name", ""),
                    "city":         biz.get("city", ""),
                    "state":        biz.get("state", ""),
                    "address":      biz.get("address", ""),
                    "stars":        biz.get("stars", 0),
                    "review_count": review_count,
                    "categories":   biz.get("categories", ""),
                    "reliability": (
                        "🟢 Cao"        if review_count >= 100 else
                        "🟡 Trung bình" if review_count >= 50  else
                        "🟠 Thấp"       if review_count >= 10  else
                        "🔴 Rất thấp"
                    ),
                })

    # Sort theo review_count giảm dần
    matches.sort(key=lambda x: x["review_count"], reverse=True)
    print(f"   → Tìm thấy {len(matches)} chi nhánh")
    return matches


def load_reviews_by_business_id(
    business_id: str,
    business_name: str,
    limit: int = None,
    min_reviews: int = 10,
) -> pd.DataFrame:
    """
    Bước 2: Lấy reviews của 1 chi nhánh cụ thể theo business_id.
    limit=None → load toàn bộ reviews (dùng cho batch processing).
    Cảnh báo nếu số lượng reviews ít hơn ngưỡng tối thiểu.
    """
    json_path = os.path.join(DATA_DIR, "yelp_academic_dataset_review.json")

    if not os.path.exists(json_path):
        print("⚠️  Không tìm thấy Yelp review dataset")
        return pd.DataFrame()

    limit_str = f"tối đa {limit}" if limit else "toàn bộ"
    print(f"📥 Đang load reviews cho '{business_name}' ({limit_str})...")
    reviews = []

    with open(json_path, "r", encoding="utf-8") as f:
        for line in f:
            if limit and len(reviews) >= limit:
                break
            review = json.loads(line)
            if review.get("business_id") == business_id:
                reviews.append({
                    "review_id":     review.get("review_id"),
                    "business_id":   business_id,
                    "business_name": business_name,
                    "stars":         review.get("stars"),
                    "text":          review.get("text"),
                    "date":          review.get("date"),
                    "useful":        review.get("useful", 0),
                })

    if not reviews:
        print(f"   ❌ Không có reviews nào cho business_id: {business_id}")
        return pd.DataFrame()

    df = pd.DataFrame(reviews)
    count = len(df)

    # Đánh giá độ tin cậy theo số lượng reviews
    if count >= 100:
        reliability = "🟢 Cao"
        note = f"{count} reviews — đủ để phân tích chính xác"
    elif count >= 50:
        reliability = "🟡 Trung bình"
        note = f"{count} reviews — kết quả tương đối tin cậy"
    elif count >= 10:
        reliability = "🟠 Thấp"
        note = f"Chỉ có {count} reviews — kết quả có thể chưa đại diện"
    else:
        reliability = "🔴 Rất thấp"
        note = f"Chỉ có {count} reviews — không đủ để phân tích đáng tin cậy"

    print(f"✅ Load xong: {count} reviews")
    print(f"   Độ tin cậy: {reliability} ({note})")

    # Gắn metadata vào DataFrame
    df.attrs["reliability"]      = reliability
    df.attrs["reliability_note"] = note
    df.attrs["review_count"]     = count

    return df


def load_yelp_reviews(
    business_name: str,
    limit: int = None,
    business_id: str = None,
    city: str = None,
) -> pd.DataFrame:
    """
    Hàm chính gọi từ bên ngoài.

    Nếu có business_id → lấy reviews của chi nhánh đó luôn.
    Nếu không → tìm kiếm:
        - 1 kết quả  → lấy luôn
        - Nhiều kết quả → trả về DataFrame rỗng,
          caller cần gọi search_businesses để cho user chọn
    """
    # Đã có business_id cụ thể → lấy luôn
    if business_id:
        return load_reviews_by_business_id(business_id, business_name, limit)

    # Tìm kiếm chi nhánh
    matches = search_businesses(business_name)

    if not matches:
        return pd.DataFrame()

    # Lọc theo city nếu có
    if city:
        matches = [m for m in matches if city.lower() in m["city"].lower()]
        print(f"   → Sau khi lọc theo city '{city}': {len(matches)} chi nhánh")

    # Chỉ 1 kết quả → lấy luôn
    if len(matches) == 1:
        biz = matches[0]
        return load_reviews_by_business_id(biz["business_id"], biz["name"], limit)

    # Nhiều kết quả → cần user chọn
    print(f"   ⚠️  Tìm thấy {len(matches)} chi nhánh, cần user chọn cụ thể")
    return pd.DataFrame()


def load_from_csv(csv_path: str) -> pd.DataFrame:
    """Load reviews từ file CSV do user upload."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Không tìm thấy file: {csv_path}")

    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1")

    required = {"text", "stars"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"CSV thiếu cột bắt buộc: {missing}\n"
            f"Cột hiện có: {list(df.columns)}\n"
            f"Cần có ít nhất: {required}"
        )

    print(f"✅ Load CSV xong: {len(df)} reviews")
    return df


if __name__ == "__main__":
    # Test tìm kiếm
    matches = search_businesses("McDonald's")

    print("\n📋 Danh sách chi nhánh (top 10):")
    for i, biz in enumerate(matches[:10]):
        print(f"  [{i+1}] {biz['name']:<20} | {biz['city']:<15}, {biz['state']} "
              f"| ⭐{biz['stars']} | {biz['review_count']:>4} reviews "
              f"| {biz['reliability']}")

    # Test load toàn bộ reviews của chi nhánh đầu tiên
    if matches:
        chosen = matches[0]
        print(f"\n→ Chọn: {chosen['name']} tại {chosen['city']} "
              f"({chosen['review_count']} reviews)")
        df = load_reviews_by_business_id(
            chosen["business_id"],
            chosen["name"],
            limit=None,  # load toàn bộ
        )
        if not df.empty:
            print(f"\n📊 Thống kê:")
            print(f"   Tổng reviews: {len(df)}")
            print(f"   Stars trung bình: {df['stars'].mean():.2f}")
            print(f"   Phân bố stars:\n{df['stars'].value_counts().sort_index()}")