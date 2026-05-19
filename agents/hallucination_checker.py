# agents/hallucination_checker.py
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_sentiment_result(result: dict, reviews: list[str]) -> dict:
    """
    Kiểm tra kết quả sentiment_agent có hợp lệ không.
    Auto-fix những gì có thể, báo lỗi những gì không thể fix.
    """
    if not result:
        return result

    errors = []
    warnings = []
    fixed = result.copy()
    all_reviews_text = " ".join(reviews).lower()

    # 1. Kiểm tra các key bắt buộc
    required_keys = ["positive", "negative", "neutral", "summary",
                     "positive_highlights", "negative_highlights"]
    for key in required_keys:
        if key not in result:
            errors.append(f"Thiếu key '{key}'")
            fixed[key] = [] if "highlights" in key else (0 if key != "summary" else "N/A")

    # 2. Kiểm tra tổng % = 100
    total = result.get("positive", 0) + result.get("negative", 0) + result.get("neutral", 0)
    if total != 100:
        warnings.append(f"Tổng % = {total} (phải = 100) → đã normalize")
        if total > 0:
            fixed["positive"] = round(result.get("positive", 0) / total * 100)
            fixed["negative"] = round(result.get("negative", 0) / total * 100)
            fixed["neutral"]  = 100 - fixed["positive"] - fixed["negative"]
        else:
            fixed["positive"] = 34
            fixed["negative"] = 33
            fixed["neutral"]  = 33

    # 3. Kiểm tra giá trị âm hoặc vượt 100
    for key in ["positive", "negative", "neutral"]:
        val = result.get(key, 0)
        if val < 0:
            errors.append(f"'{key}' = {val} < 0 → fix về 0")
            fixed[key] = 0
        if val > 100:
            errors.append(f"'{key}' = {val} > 100 → fix về 100")
            fixed[key] = 100

    # 4. Kiểm tra summary không rỗng
    if not result.get("summary", "").strip():
        warnings.append("Summary rỗng → dùng giá trị mặc định")
        fixed["summary"] = "Không có tóm tắt"

    # 5. Kiểm tra highlights có trong reviews
    for highlight in result.get("positive_highlights", []):
        words = [w for w in highlight.lower().split() if len(w) > 3]
        if words and not any(w in all_reviews_text for w in words):
            warnings.append(f"Highlight '{highlight}' không tìm thấy trong reviews")

    for highlight in result.get("negative_highlights", []):
        words = [w for w in highlight.lower().split() if len(w) > 3]
        if words and not any(w in all_reviews_text for w in words):
            warnings.append(f"Highlight '{highlight}' không tìm thấy trong reviews")

    # 6. Kiểm tra highlights là list
    if not isinstance(result.get("positive_highlights"), list):
        errors.append("'positive_highlights' không phải list → fix về []")
        fixed["positive_highlights"] = []
    if not isinstance(result.get("negative_highlights"), list):
        errors.append("'negative_highlights' không phải list → fix về []")
        fixed["negative_highlights"] = []

    # In kết quả kiểm tra
    _print_check_result("Sentiment", errors, warnings)

    fixed["hallucination_errors"]   = errors
    fixed["hallucination_warnings"] = warnings
    return fixed


def check_topic_result(result: dict, reviews: list[str]) -> dict:
    """
    Kiểm tra kết quả topic_agent có hợp lệ không.
    Auto-fix những gì có thể, báo lỗi những gì không thể fix.
    """
    if not result:
        return result

    errors = []
    warnings = []
    fixed = result.copy()
    all_reviews_text = " ".join(reviews).lower()

    expected_topics = ["food_quality", "service", "price", "ambiance"]

    # 1. Kiểm tra đủ 4 chủ đề
    for topic in expected_topics:
        if topic not in result:
            errors.append(f"Thiếu topic '{topic}'")
            fixed[topic] = {
                "sentiment": "neutral",
                "score": 3.0,
                "mentions": 0,
                "keywords": [],
                "summary": "Không có dữ liệu",
            }

    for topic in expected_topics:
        data = fixed.get(topic, {})

        # 2. Kiểm tra score trong khoảng 1.0 - 5.0
        score = data.get("score", 3.0)
        if not isinstance(score, (int, float)):
            errors.append(f"'{topic}' score không phải số → fix về 3.0")
            fixed[topic]["score"] = 3.0
        elif not (1.0 <= score <= 5.0):
            warnings.append(f"'{topic}' score={score} ngoài khoảng 1-5 → clamp")
            fixed[topic]["score"] = round(max(1.0, min(5.0, float(score))), 1)

        # 3. Kiểm tra sentiment hợp lệ
        sentiment = data.get("sentiment", "")
        if sentiment not in ["positive", "negative", "neutral"]:
            errors.append(f"'{topic}' sentiment='{sentiment}' không hợp lệ → fix về neutral")
            fixed[topic]["sentiment"] = "neutral"

        # 4. Kiểm tra mentions >= 0
        mentions = data.get("mentions", 0)
        if not isinstance(mentions, int) or mentions < 0:
            warnings.append(f"'{topic}' mentions={mentions} không hợp lệ → fix về 0")
            fixed[topic]["mentions"] = 0

        # 5. Kiểm tra keywords là list
        if not isinstance(data.get("keywords"), list):
            errors.append(f"'{topic}' keywords không phải list → fix về []")
            fixed[topic]["keywords"] = []

        # 6. Kiểm tra keywords có trong reviews
        for kw in data.get("keywords", []):
            if len(kw) > 3 and kw.lower() not in all_reviews_text:
                warnings.append(f"'{topic}' keyword '{kw}' không có trong reviews")

        # 7. Kiểm tra summary không rỗng
        if not data.get("summary", "").strip():
            warnings.append(f"'{topic}' summary rỗng → dùng giá trị mặc định")
            fixed[topic]["summary"] = "Không có mô tả"

        # 8. Kiểm tra sentiment vs score nhất quán
        score = fixed[topic].get("score", 3.0)
        sentiment = fixed[topic].get("sentiment", "neutral")
        if sentiment == "positive" and score < 3.0:
            warnings.append(f"'{topic}' sentiment=positive nhưng score={score} < 3.0 → không nhất quán")
        if sentiment == "negative" and score > 3.5:
            warnings.append(f"'{topic}' sentiment=negative nhưng score={score} > 3.5 → không nhất quán")

    # In kết quả kiểm tra
    _print_check_result("Topic", errors, warnings)

    fixed["hallucination_errors"]   = errors
    fixed["hallucination_warnings"] = warnings
    return fixed


def _print_check_result(agent_name: str, errors: list, warnings: list) -> None:
    """In kết quả kiểm tra ra console."""
    total = len(errors) + len(warnings)

    if total == 0:
        print(f"✅ [{agent_name}] Hallucination check: OK")
        return

    print(f"🔍 [{agent_name}] Hallucination check: {len(errors)} lỗi, {len(warnings)} cảnh báo")

    for e in errors:
        print(f"   ❌ {e}")
    for w in warnings:
        print(f"   ⚠️  {w}")

    if errors:
        print(f"   🔧 Đã auto-fix {len(errors)} lỗi")


if __name__ == "__main__":
    import json

    # Test sentiment checker
    print("=" * 50)
    print("TEST SENTIMENT CHECKER")
    print("=" * 50)

    bad_sentiment = {
        "positive": 80,
        "negative": 40,   # tổng = 140, không phải 100
        "neutral": 20,
        "summary": "",    # rỗng
        "positive_highlights": ["đồ ăn ngon"],
        "negative_highlights": "chờ lâu",  # không phải list
    }
    reviews = ["Đồ ăn ngon", "Chờ lâu quá", "Giá hợp lý"]
    fixed = check_sentiment_result(bad_sentiment, reviews)
    print(json.dumps(fixed, ensure_ascii=False, indent=2))

    # Test topic checker
    print("\n" + "=" * 50)
    print("TEST TOPIC CHECKER")
    print("=" * 50)

    bad_topic = {
        "food_quality": {
            "sentiment": "positive",
            "score": 6.5,        # vượt quá 5.0
            "mentions": -1,      # âm
            "keywords": ["sushi", "ramen"],  # không có trong reviews
            "summary": "Đồ ăn ngon",
        },
        "service": {
            "sentiment": "excellent",  # không hợp lệ
            "score": 4.0,
            "mentions": 2,
            "keywords": ["nhiệt tình"],
            "summary": "",             # rỗng
        },
        # Thiếu price và ambiance
    }

    fixed_topic = check_topic_result(bad_topic, reviews)
    print(json.dumps(fixed_topic, ensure_ascii=False, indent=2))