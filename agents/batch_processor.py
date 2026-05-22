# agents/batch_processor.py
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from config import AGENT_VERBOSE

BATCH_SIZE = 100  # mỗi batch tối đa 100 reviews


def _merge_sentiment_results(results: list[dict]) -> dict:
    """
    Tổng hợp nhiều sentiment results thành 1.
    Dùng trung bình có trọng số theo số reviews mỗi batch.
    """
    if not results:
        return {}

    if len(results) == 1:
        return results[0]

    total_reviews = sum(r.get("_batch_size", 1) for r in results)

    # Tính trung bình có trọng số cho %
    positive = sum(r.get("positive", 0) * r.get("_batch_size", 1) for r in results) / total_reviews
    negative = sum(r.get("negative", 0) * r.get("_batch_size", 1) for r in results) / total_reviews
    neutral  = sum(r.get("neutral", 0)  * r.get("_batch_size", 1) for r in results) / total_reviews

    # Normalize về 100%
    total_pct = positive + negative + neutral
    if total_pct > 0:
        positive = round(positive / total_pct * 100)
        negative = round(negative / total_pct * 100)
        neutral  = 100 - positive - negative

    # Gộp highlights (dedup)
    pos_highlights = []
    neg_highlights = []
    seen_pos = set()
    seen_neg = set()

    for r in results:
        for h in r.get("positive_highlights", []):
            if h not in seen_pos:
                seen_pos.add(h)
                pos_highlights.append(h)
        for h in r.get("negative_highlights", []):
            if h not in seen_neg:
                seen_neg.add(h)
                neg_highlights.append(h)

    # Lấy summary từ batch có nhiều reviews nhất
    best_batch = max(results, key=lambda r: r.get("_batch_size", 0))

    return {
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "summary": best_batch.get("summary", ""),
        "positive_highlights": pos_highlights[:5],
        "negative_highlights": neg_highlights[:5],
        "total_reviews_analyzed": total_reviews,
        "batches_processed": len(results),
    }


def _merge_topic_results(results: list[dict]) -> dict:
    """
    Tổng hợp nhiều topic results thành 1.
    Tính trung bình có trọng số cho score, gộp keywords.
    """
    if not results:
        return {}

    if len(results) == 1:
        # Xoá key nội bộ
        r = results[0].copy()
        r.pop("_batch_size", None)
        return r

    topics = ["food_quality", "service", "price", "ambiance"]
    merged = {}
    total_reviews = sum(r.get("_batch_size", 1) for r in results)

    for topic in topics:
        topic_results = [r for r in results if topic in r]
        if not topic_results:
            continue

        # Score trung bình có trọng số
        weighted_score = sum(
            r[topic].get("score", 3.0) * r.get("_batch_size", 1)
            for r in topic_results
        ) / total_reviews

        # Tổng mentions
        total_mentions = sum(r[topic].get("mentions", 0) for r in topic_results)

        # Sentiment theo đa số (weighted)
        sentiment_scores = {"positive": 0, "negative": 0, "neutral": 0}
        for r in topic_results:
            s = r[topic].get("sentiment", "neutral")
            weight = r.get("_batch_size", 1)
            if s in sentiment_scores:
                sentiment_scores[s] += weight
        dominant_sentiment = max(sentiment_scores, key=sentiment_scores.get)

        # Gộp keywords (dedup, lấy top 4)
        all_keywords = []
        seen_kw = set()
        for r in topic_results:
            for kw in r[topic].get("keywords", []):
                if kw not in seen_kw:
                    seen_kw.add(kw)
                    all_keywords.append(kw)

        # Summary từ batch lớn nhất
        best = max(topic_results, key=lambda r: r.get("_batch_size", 0))

        merged[topic] = {
            "sentiment": dominant_sentiment,
            "score": round(weighted_score, 1),
            "mentions": total_mentions,
            "keywords": all_keywords[:4],
            "summary": best[topic].get("summary", ""),
        }

    merged["total_reviews_analyzed"] = total_reviews
    merged["batches_processed"] = len(results)
    return merged


def run_batch_sentiment(df: pd.DataFrame) -> dict:
    """
    Chạy sentiment analysis theo batch.
    Tự động chia df thành các batch BATCH_SIZE reviews.
    """
    from agents.sentiment_agent import analyze_sentiment

    total = len(df)
    batches = [df.iloc[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    n_batches = len(batches)

    print(f"🔄 Batch Processor: {total} reviews → {n_batches} batches "
          f"(mỗi batch tối đa {BATCH_SIZE} reviews)")

    results = []
    for i, batch_df in enumerate(batches):
        print(f"\n   📦 Batch {i+1}/{n_batches} ({len(batch_df)} reviews)...")
        result = analyze_sentiment(batch_df)
        if result:
            result["_batch_size"] = len(batch_df)
            results.append(result)
        else:
            print(f"   ⚠️  Batch {i+1} thất bại, bỏ qua")

    if not results:
        return {}

    merged = _merge_sentiment_results(results)
    print(f"\n✅ Sentiment tổng hợp từ {n_batches} batches: "
          f"{merged['positive']}% positive, "
          f"{merged['negative']}% negative, "
          f"{merged['neutral']}% neutral")
    return merged


def run_batch_topic(df: pd.DataFrame) -> dict:
    """
    Chạy topic analysis theo batch.
    Tự động chia df thành các batch BATCH_SIZE reviews.
    """
    from agents.topic_agent import analyze_topics

    total = len(df)
    batches = [df.iloc[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    n_batches = len(batches)

    print(f"🔄 Batch Processor: {total} reviews → {n_batches} batches")

    results = []
    for i, batch_df in enumerate(batches):
        print(f"\n   📦 Batch {i+1}/{n_batches} ({len(batch_df)} reviews)...")
        result = analyze_topics(batch_df)
        if result:
            result["_batch_size"] = len(batch_df)
            results.append(result)
        else:
            print(f"   ⚠️  Batch {i+1} thất bại, bỏ qua")

    if not results:
        return {}

    merged = _merge_topic_results(results)
    print(f"\n✅ Topic tổng hợp từ {n_batches} batches xong")
    return merged


if __name__ == "__main__":
    # Test với 250 reviews giả
    import random
    sample_texts = [
        "Đồ ăn rất ngon, nhân viên nhiệt tình!",
        "Chờ quá lâu, thái độ tệ.",
        "Giá hợp lý, không gian đẹp.",
        "Món ăn nguội, không như kỳ vọng.",
        "Tuyệt vời, sẽ quay lại!",
    ]

    df_large = pd.DataFrame({
        "text": [random.choice(sample_texts) for _ in range(250)],
        "stars": [random.randint(1, 5) for _ in range(250)],
    })

    print(f"Test với {len(df_large)} reviews\n")

    sentiment = run_batch_sentiment(df_large)
    print("\n📊 Sentiment:")
    print(json.dumps(
        {k: v for k, v in sentiment.items() if not k.startswith("_")},
        ensure_ascii=False, indent=2
    ))

    topic = run_batch_topic(df_large)
    print("\n📊 Topic:")
    print(json.dumps(
        {k: v for k, v in topic.items() if not k.startswith("_")},
        ensure_ascii=False, indent=2
    ))