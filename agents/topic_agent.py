# agents/topic_agent.py
import os
import sys
import json
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, AGENT_VERBOSE
from agents.hallucination_checker import check_topic_result


client = Groq(api_key=GROQ_API_KEY)


def analyze_topics(df: pd.DataFrame) -> dict:
    if df.empty:
        print("⚠️  DataFrame rỗng, không có gì để phân tích")
        return {}

    reviews = df["text"].dropna().tolist()
    if not reviews:
        print("⚠️  Không có reviews nào")
        return {}

    print(f"🔍 Topic Agent đang phân tích {len(reviews)} reviews...")

    reviews_text = "\n".join([f"- {r}" for r in reviews])

    prompt = f"""Bạn là chuyên gia phân tích trải nghiệm khách hàng trong ngành F&B.
Bạn có khả năng nhận diện và phân loại các chủ đề được đề cập trong reviews nhà hàng.

Phân tích các reviews sau và gom nhóm theo 4 chủ đề chính.

REVIEWS:
{reviews_text}

YÊU CẦU:
Phân tích từng chủ đề dựa trên nội dung reviews:
1. food_quality    - chất lượng món ăn, hương vị, phần ăn
2. service         - thái độ phục vụ, tốc độ, sự nhiệt tình
3. price           - giá cả, tính xứng đáng, khuyến mãi
4. ambiance        - không gian, âm thanh, vệ sinh, vị trí

Với mỗi chủ đề:
- sentiment: "positive", "negative", hoặc "neutral"
- score: điểm từ 1.0 đến 5.0
- mentions: số lần được đề cập trong reviews
- keywords: tối đa 4 từ khoá nổi bật
- summary: 1 câu mô tả ngắn

CHỈ trả về JSON hợp lệ, không thêm text nào khác, không dùng markdown:
{{
    "food_quality": {{
        "sentiment": "<positive/negative/neutral>",
        "score": <1.0-5.0>,
        "mentions": <số nguyên>,
        "keywords": ["<từ 1>", "<từ 2>", ...],
        "summary": "<1 câu mô tả>"
    }},
    "service": {{
        "sentiment": "<positive/negative/neutral>",
        "score": <1.0-5.0>,
        "mentions": <số nguyên>,
        "keywords": ["<từ 1>", "<từ 2>", ...],
        "summary": "<1 câu mô tả>"
    }},
    "price": {{
        "sentiment": "<positive/negative/neutral>",
        "score": <1.0-5.0>,
        "mentions": <số nguyên>,
        "keywords": ["<từ 1>", "<từ 2>", ...],
        "summary": "<1 câu mô tả>"
    }},
    "ambiance": {{
        "sentiment": "<positive/negative/neutral>",
        "score": <1.0-5.0>,
        "mentions": <số nguyên>,
        "keywords": ["<từ 1>", "<từ 2>", ...],
        "summary": "<1 câu mô tả>"
    }}
}}"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )

        raw = response.choices[0].message.content

        # Xoá markdown code block nếu có
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        if AGENT_VERBOSE:
            print(f"   Raw output: {raw[:200]}...")

        # Parse JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            json_str = raw[start:end]
            parsed = json.loads(json_str)
            parsed = check_topic_result(parsed, reviews)
            print(f"✅ Topic xong:")
            for topic, data in parsed.items():
                if isinstance(data, dict) and "sentiment" in data:
                    print(f"   {topic}: {data['sentiment']} "
                          f"(score: {data['score']}, mentions: {data['mentions']})")
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
        "Khá ổn, món ăn vừa miệng, giá hợp lý.",
        "Nhân viên thân thiện nhưng món ăn nguội.",
        "Không gian sạch sẽ, thoáng mát, dịch vụ tốt.",
    ]

    sample_df = pd.DataFrame({"text": sample_reviews})
    result = analyze_topics(sample_df)

    if result:
        print("\n📊 Kết quả chi tiết:")
        print(json.dumps(result, ensure_ascii=False, indent=2))