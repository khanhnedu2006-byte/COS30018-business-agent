# data/csv_handler.py
import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR


REQUIRED_COLUMNS = {"text", "stars"}
OPTIONAL_COLUMNS = {"review_id", "business_name", "date", "useful"}


def load_from_csv(csv_path: str) -> pd.DataFrame:
    """
    Load reviews từ file CSV do user upload.
    Bắt buộc có cột: text, stars
    Tuỳ chọn: review_id, business_name, date, useful
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"❌ Không tìm thấy file: {csv_path}")

    # Đọc file
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding="latin-1")

    print(f"📂 Đọc file: {csv_path}")
    print(f"   → Tổng {len(df)} dòng, {len(df.columns)} cột: {list(df.columns)}")

    # Kiểm tra cột bắt buộc
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"❌ CSV thiếu cột bắt buộc: {missing}\n"
            f"   Cột hiện có: {list(df.columns)}\n"
            f"   Cần có ít nhất: {REQUIRED_COLUMNS}"
        )

    # Thêm cột tuỳ chọn nếu thiếu
    if "review_id" not in df.columns:
        df["review_id"] = [f"csv_{i}" for i in range(len(df))]
    if "business_name" not in df.columns:
        df["business_name"] = "Unknown"
    if "date" not in df.columns:
        df["date"] = None
    if "useful" not in df.columns:
        df["useful"] = 0

    # Làm sạch cơ bản
    df = _clean(df)

    print(f"✅ Load CSV xong: {len(df)} reviews hợp lệ")
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Làm sạch cơ bản: xoá dòng trống, chuẩn hoá kiểu dữ liệu."""

    before = len(df)

    # Xoá dòng không có text
    df = df.dropna(subset=["text"])
    df = df[df["text"].str.strip() != ""]

    # Chuẩn hoá stars về số
    df["stars"] = pd.to_numeric(df["stars"], errors="coerce")
    df = df.dropna(subset=["stars"])
    df = df[df["stars"].between(1, 5)]

    # Reset index
    df = df.reset_index(drop=True)

    removed = before - len(df)
    if removed > 0:
        print(f"   🧹 Đã xoá {removed} dòng không hợp lệ")

    return df


def save_to_csv(df: pd.DataFrame, filename: str) -> str:
    """Lưu DataFrame ra file CSV trong thư mục data/."""
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, filename)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"💾 Đã lưu: {output_path}")
    return output_path


if __name__ == "__main__":
    # Tạo file CSV mẫu để test
    sample_data = {
        "text": [
            "Đồ ăn ngon, phục vụ nhiệt tình!",
            "Giá hơi cao nhưng chất lượng tốt.",
            "",          # dòng trống → sẽ bị xoá
            "Không gian thoải mái, sẽ quay lại.",
        ],
        "stars": [5, 4, 3, "abc"],  # "abc" → sẽ bị xoá
        "business_name": ["Quán Test"] * 4,
    }

    sample_path = os.path.join(DATA_DIR, "sample_reviews.csv")
    os.makedirs(DATA_DIR, exist_ok=True)
    pd.DataFrame(sample_data).to_csv(sample_path, index=False)

    df = load_from_csv(sample_path)
    print(df)