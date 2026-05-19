# agents/report_agent.py
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, AGENT_VERBOSE


client = Groq(api_key=GROQ_API_KEY)


def generate_report(
    business_name: str,
    sentiment_result: dict,
    topic_result: dict,
    total_reviews: int,
) -> dict:
    """
    Nhận kết quả từ sentiment + topic agent → tạo báo cáo cuối cùng.
    Đây là hàm chính được gọi từ bên ngoài.
    """
    if not sentiment_result or not topic_result:
        print("⚠️  Thiếu dữ liệu để tạo báo cáo")
        return {}

    print(f"📝 Report Agent đang tạo báo cáo cho '{business_name}'...")

    # Chuẩn bị context cho LLM
    sentiment_summary = json.dumps(sentiment_result, ensure_ascii=False, indent=2)
    topic_summary = json.dumps(topic_result, ensure_ascii=False, indent=2)

    prompt = f"""Bạn là chuyên gia tư vấn kinh doanh F&B với 15 năm kinh nghiệm.
Dựa trên kết quả phân tích reviews, hãy tạo báo cáo cải thiện kinh doanh chi tiết.

THÔNG TIN:
- Tên quán: {business_name}
- Tổng số reviews phân tích: {total_reviews}

KẾT QUẢ SENTIMENT:
{sentiment_summary}

KẾT QUẢ PHÂN TÍCH CHỦ ĐỀ:
{topic_summary}

YÊU CẦU:
Tạo báo cáo kinh doanh với các mục sau:
1. overall_score: điểm tổng thể 1.0-5.0 (tính từ topic scores)
2. strengths: tối đa 3 điểm mạnh cụ thể (dựa trên positive topics)
3. weaknesses: tối đa 3 điểm yếu cụ thể (dựa trên negative topics)
4. recommendations: tối đa 4 đề xuất cải thiện cụ thể, có thể thực hiện được
5. executive_summary: đoạn tóm tắt 2-3 câu cho ban quản lý
6. priority_action: 1 hành động ưu tiên cần làm ngay nhất

CHỈ trả về JSON hợp lệ, không thêm text nào khác:
{{
    "business_name": "{business_name}",
    "total_reviews": {total_reviews},
    "overall_score": <1.0-5.0>,
    "sentiment_overview": {{
        "positive": <số>,
        "negative": <số>,
        "neutral": <số>
    }},
    "strengths": [
        "<điểm mạnh 1>",
        "<điểm mạnh 2>",
        "<điểm mạnh 3>"
    ],
    "weaknesses": [
        "<điểm yếu 1>",
        "<điểm yếu 2>",
        "<điểm yếu 3>"
    ],
    "recommendations": [
        "<đề xuất 1>",
        "<đề xuất 2>",
        "<đề xuất 3>",
        "<đề xuất 4>"
    ],
    "executive_summary": "<2-3 câu tóm tắt>",
    "priority_action": "<1 hành động ưu tiên>"
}}"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
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
            print(f"✅ Báo cáo xong cho '{business_name}' "
                  f"(overall score: {parsed.get('overall_score', 'N/A')}/5.0)")
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
    # Test với data mẫu từ sentiment + topic agent
    sample_sentiment = {
        "positive": 58,
        "negative": 25,
        "neutral": 17,
        "summary": "Khách hàng hài lòng về đồ ăn nhưng phàn nàn về dịch vụ",
        "positive_highlights": ["đồ ăn ngon", "không gian đẹp", "giá hợp lý"],
        "negative_highlights": ["chờ lâu", "thái độ nhân viên", "món nguội"],
    }

    sample_topic = {
        "food_quality": {
            "sentiment": "positive",
            "score": 4.2,
            "mentions": 8,
            "keywords": ["ngon", "tươi", "đậm đà", "đa dạng"],
            "summary": "Khách hàng đánh giá cao chất lượng món ăn",
        },
        "service": {
            "sentiment": "negative",
            "score": 2.5,
            "mentions": 6,
            "keywords": ["chậm", "thái độ", "chờ lâu", "thiếu nhiệt tình"],
            "summary": "Dịch vụ phục vụ là điểm yếu lớn nhất",
        },
        "price": {
            "sentiment": "neutral",
            "score": 3.2,
            "mentions": 4,
            "keywords": ["hợp lý", "bình thường", "đắt"],
            "summary": "Giá cả ở mức chấp nhận được",
        },
        "ambiance": {
            "sentiment": "positive",
            "score": 4.0,
            "mentions": 3,
            "keywords": ["đẹp", "thoáng", "sạch sẽ"],
            "summary": "Không gian được đánh giá tốt",
        },
    }

    result = generate_report(
        business_name="Quán Nhậu Tự Do",
        sentiment_result=sample_sentiment,
        topic_result=sample_topic,
        total_reviews=20,
    )

    if result:
        print("\n📊 Báo cáo đầy đủ:")
        print(json.dumps(result, ensure_ascii=False, indent=2))