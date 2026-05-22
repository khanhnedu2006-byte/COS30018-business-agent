# agents/manager_agent.py
import os
import sys
import re
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from config import AGENT_VERBOSE, MAX_REVIEWS_PER_RUN

from agents.data_collector import collect_reviews
from agents.data_validator import validate_reviews, get_validation_stats
from agents.rag_agent import build_and_query
from agents.sentiment_agent import analyze_sentiment
from agents.topic_agent import analyze_topics
from agents.report_agent import generate_report


def run_analysis(
    business_name: str,
    csv_path: str = None,
    limit: int = MAX_REVIEWS_PER_RUN,
    use_rag: bool = True,
    top_k_rag: int = 15,
    business_id: str = None,
) -> dict:
    """
    Hàm chính: điều phối toàn bộ pipeline phân tích.
    Trả về báo cáo JSON hoàn chỉnh.

    Luồng:
    1. Data Collector  → thu thập reviews
    2. Data Validator  → làm sạch reviews
    3. RAG Agent       → index + query theo topic (nếu use_rag=True)
    4. Sentiment Agent → phân tích cảm xúc
    5. Topic Agent     → phân tích chủ đề
    6. Report Agent    → tổng hợp báo cáo
    """
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"🚀 Manager Agent: Bắt đầu phân tích '{business_name}'")
    print(f"{'='*60}\n")

    # ── Bước 1: Thu thập reviews ──────────────────────────────────────────────
    print(f"[1/6] 📥 Thu thập reviews...")
    df_raw, source = collect_reviews(
        business_name=business_name,
        csv_path=csv_path,
        limit=limit,
        business_id=business_id,
    )

    if df_raw.empty:
        return _error_response(
            business_name,
            "Không tìm thấy reviews từ bất kỳ nguồn nào"
        )

    # ── Bước 2: Validate + làm sạch ──────────────────────────────────────────
    print(f"\n[2/6] 🧹 Validate và làm sạch reviews...")
    df_clean = validate_reviews(df_raw.copy())

    if df_clean.empty:
        return _error_response(
            business_name,
            "Không còn reviews nào sau khi validate"
        )

    validation_stats = get_validation_stats(df_raw, df_clean)

    # ── Bước 3: RAG indexing ──────────────────────────────────────────────────
    topic_reviews = None
    if use_rag:
        print(f"\n[3/6] 🔍 RAG Agent: Index và query reviews...")
        try:
            # Xoá ký tự đặc biệt khỏi tên collection
            safe_name = re.sub(
                r'[^a-zA-Z0-9._-]', '',
                business_name.replace(' ', '_').lower()
            )
            topic_reviews = build_and_query(
                df=df_clean,
                top_k=top_k_rag,
                collection_name=f"reviews_{safe_name}",
            )
        except Exception as e:
            print(f"   ⚠️  RAG lỗi: {e} → bỏ qua RAG, dùng toàn bộ reviews")
            topic_reviews = None
    else:
        print(f"\n[3/6] ⏭️  Bỏ qua RAG (use_rag=False)")

    # ── Bước 4: Sentiment Analysis ────────────────────────────────────────────
    print(f"\n[4/6] 💬 Sentiment Agent: Phân tích cảm xúc...")
    sentiment_result = analyze_sentiment(df_clean)

    if not sentiment_result:
        return _error_response(business_name, "Sentiment Agent thất bại")

    # ── Bước 5: Topic Analysis ────────────────────────────────────────────────
    print(f"\n[5/6] 🏷️  Topic Agent: Phân tích chủ đề...")

    # Nếu có RAG → dùng reviews đã filter theo topic
    # Nếu không  → dùng toàn bộ reviews
    if topic_reviews:
        all_topic_reviews = []
        for reviews in topic_reviews.values():
            all_topic_reviews.extend(reviews)
        # Dedup giữ thứ tự
        seen = set()
        unique_reviews = []
        for r in all_topic_reviews:
            if r not in seen:
                seen.add(r)
                unique_reviews.append(r)
        df_for_topic = pd.DataFrame({"text": unique_reviews})
    else:
        df_for_topic = df_clean

    topic_result = analyze_topics(df_for_topic)

    if not topic_result:
        return _error_response(business_name, "Topic Agent thất bại")

    # Lọc bỏ key hallucination khỏi topic_result trước khi truyền vào report
    topic_clean = {
        k: v for k, v in topic_result.items()
        if k not in ["hallucination_errors", "hallucination_warnings"]
    }

    # ── Bước 6: Tạo báo cáo ──────────────────────────────────────────────────
    print(f"\n[6/6] 📝 Report Agent: Tạo báo cáo...")
    report = generate_report(
        business_name=business_name,
        sentiment_result=sentiment_result,
        topic_result=topic_clean,
        total_reviews=len(df_clean),
    )

    if not report:
        return _error_response(business_name, "Report Agent thất bại")

    # ── Tổng hợp kết quả cuối ─────────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).seconds
    final_result = {
        **report,
        "metadata": {
            "data_source": source,
            "use_rag": use_rag,
            "validation_stats": validation_stats,
            "sentiment_detail": sentiment_result,
            "topic_detail": topic_result,
            "processing_time_seconds": elapsed,
            "analyzed_at": datetime.now().isoformat(),
        }
    }

    print(f"\n{'='*60}")
    print(f"✅ Phân tích hoàn tất trong {elapsed}s")
    print(f"   Quán     : {business_name}")
    print(f"   Reviews  : {len(df_clean)} (từ {source})")
    print(f"   Score    : {report.get('overall_score', 'N/A')}/5.0")
    print(f"   Sentiment: {sentiment_result.get('positive', 0)}% positive")
    print(f"{'='*60}\n")

    return final_result


def _error_response(business_name: str, reason: str) -> dict:
    """Trả về response lỗi chuẩn."""
    print(f"\n❌ Pipeline thất bại: {reason}")
    return {
        "error": True,
        "reason": reason,
        "business_name": business_name,
        "analyzed_at": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    result = run_analysis(
        business_name="McDonald's",
        limit=20,
        use_rag=True,
        top_k_rag=10,
    )

    print("\n📊 KẾT QUẢ CUỐI:")
    display = {k: v for k, v in result.items() if k != "metadata"}
    print(json.dumps(display, ensure_ascii=False, indent=2))