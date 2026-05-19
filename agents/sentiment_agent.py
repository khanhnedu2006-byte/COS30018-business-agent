# agents/sentiment_agent.py
import os
import sys
import json
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, AGENT_VERBOSE
from agents.hallucination_checker import check_sentiment_result


client = Groq(api_key=GROQ_API_KEY)


def analyze_sentiment(df: pd.DataFrame) -> dict:
    """
    Nhận DataFrame reviews → trả về kết quả sentiment.
    Đây là hàm chính được gọi từ bên ngoài.
    """
    if df.empty:
        print("⚠️  DataFrame rỗng, không có gì để phân tích")
        return {}

    reviews = df["text"].dropna().tolist()
    if not reviews:
        print("⚠️  Không có reviews nào")
        return {}

    print(f"🔍 Sentiment Agent đang phân tích {len(reviews)} reviews...")

    reviews_text = "\n".join([f"- {r}" for r in reviews])

    prompt = f"""Bạn là chuyên gia phân tích cảm xúc với 10 năm kinh nghiệm trong ngành F&B.
Bạn hiểu sâu về tâm lý khách hàng, nhận biết cảm xúc tinh tế trong từng đánh giá bằng tiếng Việt và tiếng Anh.

Phân tích cảm xúc của các reviews nhà hàng sau đây.

REVIEWS:
{reviews_text}

YÊU CẦU:
1. Phân loại TỪNG review là: positive, negative, hoặc neutral
2. Tính % tổng cho mỗi loại (tổng = 100%)
3. Liệt kê tối đa 5 điểm nổi bật tích cực (positive_highlights)
4. Liệt kê tối đa 5 điểm nổi bật tiêu cực (negative_highlights)
5. Viết 1 câu tóm tắt tổng quan cảm xúc

CHỈ trả về JSON hợp lệ, không thêm text nào khác:
{{
    "positive": <số nguyên 0-100>,
    "negative": <số nguyên 0-100>,
    "neutral": <số nguyên 0-100>,
    "summary": "<1 câu tóm tắt>",
    "positive_highlights": ["<điểm 1>", "<điểm 2>", ...],
    "negative_highlights": ["<điểm 1>", "<điểm 2>", ...]
}}"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )

        raw = response.choices[0].message.content

        if AGENT_VERBOSE:
            print(f"   Raw output: {raw[:200]}...")

        # Parse JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            json_str = raw[start:end]
            parsed = json.loads(json_str)
            parsed = check_sentiment_result(parsed, reviews)
            print(f"✅ Sentiment xong: {parsed['positive']}% positive, "
                  f"{parsed['negative']}% negative, "
                  f"{parsed['neutral']}% neutral")
            return parsed
        else:
            print("❌ Không tìm thấy JSON trong kết quả")
            return {}

    except json.JSONDecodeError as e:
        print(f"❌ Lỗi parse JSON: {e}")
        return {}
    except Exception as e:
        print(f"❌ Lỗi gọi Groq API: {e}")
        return {}
    

if __name__ == "__main__":
    sample_reviews = [
        "Đồ ăn rất ngon, nhân viên nhiệt tình, sẽ quay lại!",
        "Chờ đợi quá lâu, thái độ phục vụ tệ, không hài lòng.",
        "Giá cả bình thường, không có gì đặc biệt.",
        "Không gian đẹp, đồ ăn ngon nhưng hơi đắt.",
        "Tệ nhất từ trước đến nay, không bao giờ quay lại.",
        "Khá ổn, món ăn vừa miệng.",
    ]

    sample_df = pd.DataFrame({"text": sample_reviews})
    result = analyze_sentiment(sample_df)

    if result:
        print("\n📊 Kết quả:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from data.yelp_loader import load_yelp_reviews

    # Test với data thật từ Yelp
    df = load_yelp_reviews("McDonald's", limit=20)

    if df.empty:
        # Fallback sang data mẫu nếu chưa có dataset
        print("⚠️  Không có Yelp data, dùng data mẫu...")
        sample_reviews = [
            "Đồ ăn rất ngon, nhân viên nhiệt tình, sẽ quay lại!",
            "Chờ đợi quá lâu, thái độ phục vụ tệ, không hài lòng.",
            "Giá cả bình thường, không có gì đặc biệt.",
            "Không gian đẹp, đồ ăn ngon nhưng hơi đắt.",
            "Tệ nhất từ trước đến nay, không bao giờ quay lại.",
            "Khá ổn, món ăn vừa miệng.",
        ]
        df = pd.DataFrame({"text": sample_reviews})

    result = analyze_sentiment(df)
    if result:
        print("\n📊 Kết quả:")
        print(json.dumps(result, ensure_ascii=False, indent=2))