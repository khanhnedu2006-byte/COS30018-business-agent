# agents/data_validator.py
import os
import sys
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config import AGENT_VERBOSE


# ─── Cấu hình ────────────────────────────────────────────────────────────────
MIN_TEXT_LENGTH  = 10    # review quá ngắn (dưới 10 ký tự) → loại
MAX_TEXT_LENGTH  = 5000  # review quá dài (trên 5000 ký tự) → cắt bớt
MIN_STAR_VALUE   = 1
MAX_STAR_VALUE   = 5
MAX_DUPLICATE_RATIO = 0.8  # 2 reviews giống nhau 80% → coi là trùng


def validate_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hàm chính: nhận raw DataFrame → trả về clean DataFrame.
    Thực hiện toàn bộ các bước validate và làm sạch.
    """
    if df.empty:
        print("⚠️  DataFrame rỗng")
        return df

    original_count = len(df)
    print(f"🔍 Data Validator: Bắt đầu validate {original_count} reviews...")

    # Chạy từng bước
    df = _validate_columns(df)
    df = _clean_text(df)
    df = _filter_short_reviews(df)
    df = _filter_long_reviews(df)
    df = _validate_stars(df)
    df = _remove_duplicates(df)
    df = _remove_spam(df)
    df = df.reset_index(drop=True)

    final_count = len(df)
    removed = original_count - final_count
    print(f"✅ Validate xong: {final_count} reviews hợp lệ "
          f"(đã loại {removed} reviews, tỉ lệ giữ: "
          f"{final_count/original_count*100:.1f}%)")

    return df


def _validate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Đảm bảo có đủ các cột cần thiết."""
    if "text" not in df.columns:
        raise ValueError("❌ DataFrame thiếu cột 'text'")

    if "stars" not in df.columns:
        print("   ⚠️  Thiếu cột 'stars' → thêm giá trị mặc định 3")
        df["stars"] = 3

    if "review_id" not in df.columns:
        df["review_id"] = [f"r_{i}" for i in range(len(df))]

    if "business_name" not in df.columns:
        df["business_name"] = "Unknown"

    if "date" not in df.columns:
        df["date"] = None

    return df


def _clean_text(df: pd.DataFrame) -> pd.DataFrame:
    """Làm sạch text cơ bản."""
    before = len(df)

    # Xoá dòng text null
    df = df.dropna(subset=["text"])

    # Convert về string
    df["text"] = df["text"].astype(str)

    # Strip whitespace
    df["text"] = df["text"].str.strip()

    # Xoá dòng text rỗng sau khi strip
    df = df[df["text"] != ""]
    df = df[df["text"] != "nan"]

    # Cắt text quá dài
    df["text"] = df["text"].apply(
        lambda x: x[:MAX_TEXT_LENGTH] if len(x) > MAX_TEXT_LENGTH else x
    )

    removed = before - len(df)
    if removed > 0 and AGENT_VERBOSE:
        print(f"   🧹 _clean_text: loại {removed} dòng null/rỗng")

    return df


def _filter_short_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Loại reviews quá ngắn — không đủ thông tin."""
    before = len(df)
    df = df[df["text"].str.len() >= MIN_TEXT_LENGTH]
    removed = before - len(df)

    if removed > 0:
        print(f"   🧹 Loại {removed} reviews quá ngắn (< {MIN_TEXT_LENGTH} ký tự)")

    return df


def _filter_long_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Cắt reviews quá dài — tránh tốn token khi gọi LLM."""
    long_count = len(df[df["text"].str.len() > MAX_TEXT_LENGTH])
    if long_count > 0:
        print(f"   ✂️  Cắt {long_count} reviews quá dài (> {MAX_TEXT_LENGTH} ký tự)")
    return df


def _validate_stars(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hoá và validate cột stars."""
    before = len(df)

    # Convert về số
    df["stars"] = pd.to_numeric(df["stars"], errors="coerce")

    # Loại dòng có stars = NaN
    df = df.dropna(subset=["stars"])

    # Loại dòng ngoài khoảng 1-5
    df = df[df["stars"].between(MIN_STAR_VALUE, MAX_STAR_VALUE)]

    # Round về .0 hoặc .5
    df["stars"] = df["stars"].apply(lambda x: round(x * 2) / 2)

    removed = before - len(df)
    if removed > 0:
        print(f"   🧹 Loại {removed} reviews có stars không hợp lệ")

    return df


def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Loại reviews trùng lặp hoàn toàn."""
    before = len(df)

    df = df.drop_duplicates(subset=["text"], keep="first")

    removed = before - len(df)
    if removed > 0:
        print(f"   🧹 Loại {removed} reviews trùng lặp hoàn toàn")

    return df


def _remove_spam(df: pd.DataFrame) -> pd.DataFrame:
    """Loại reviews spam: chỉ có số, ký tự đặc biệt, hoặc lặp ký tự."""
    before = len(df)

    def is_spam(text: str) -> bool:
        # Chỉ có số và ký tự đặc biệt
        if re.match(r'^[\d\s\W]+$', text):
            return True
        # Lặp cùng 1 ký tự quá nhiều: "aaaaaaa", "!!!!!!"
        if re.match(r'^(.)\1{4,}$', text.strip()):
            return True
        # Quá ít chữ cái thực sự (< 5 chữ cái)
        letters = re.findall(r'[a-zA-ZÀ-ỹ]', text)
        if len(letters) < 5:
            return True
        return False

    spam_mask = df["text"].apply(is_spam)
    df = df[~spam_mask]

    removed = before - len(df)
    if removed > 0:
        print(f"   🧹 Loại {removed} reviews spam")

    return df


def get_validation_stats(df_before: pd.DataFrame, df_after: pd.DataFrame) -> dict:
    """Trả về thống kê sau khi validate."""
    return {
        "total_before": len(df_before),
        "total_after": len(df_after),
        "removed": len(df_before) - len(df_after),
        "kept_ratio": round(len(df_after) / len(df_before) * 100, 1) if len(df_before) > 0 else 0,
        "avg_stars_before": round(df_before["stars"].mean(), 2) if "stars" in df_before.columns else None,
        "avg_stars_after": round(df_after["stars"].mean(), 2) if "stars" in df_after.columns else None,
        "avg_text_length": round(df_after["text"].str.len().mean(), 1) if not df_after.empty else 0,
    }


if __name__ == "__main__":
    import json

    # Test với data có nhiều vấn đề
    raw_data = {
        "text": [
            "Đồ ăn rất ngon, nhân viên nhiệt tình!",   # ✅ hợp lệ
            "ok",                                         # ❌ quá ngắn
            "",                                           # ❌ rỗng
            "123456789",                                  # ❌ spam
            "!!!!!!!!!!",                                 # ❌ spam
            "Giá cả hợp lý, không gian đẹp.",            # ✅ hợp lệ
            "Đồ ăn rất ngon, nhân viên nhiệt tình!",    # ❌ trùng lặp
            "Chờ lâu quá, thái độ nhân viên tệ.",        # ✅ hợp lệ
            None,                                         # ❌ null
            "Không gian thoáng mát, món ăn đa dạng.",    # ✅ hợp lệ
        ],
        "stars": [5, 3, 4, 2, 1, 4, 5, 2, 3, 99],  # 99 → ❌ không hợp lệ
    }

    df_raw = pd.DataFrame(raw_data)
    print("📋 Data trước khi validate:")
    print(df_raw.to_string())
    print()

    df_clean = validate_reviews(df_raw.copy())

    print("\n📋 Data sau khi validate:")
    print(df_clean[["text", "stars"]].to_string())

    stats = get_validation_stats(df_raw, df_clean)
    print("\n📊 Thống kê:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))