# agents/rag_agent.py
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from config import DATA_DIR, AGENT_VERBOSE

# Thư mục lưu vector DB
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")

# Dùng sentence-transformers để embed
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Các query mặc định cho từng chủ đề
TOPIC_QUERIES = {
    "food_quality": "food quality taste delicious menu dish meal",
    "service":      "service staff waiter attitude speed helpful",
    "price":        "price cost expensive cheap value worth money",
    "ambiance":     "ambiance atmosphere decor noise clean location",
}


def build_vector_db(df: pd.DataFrame, collection_name: str = "reviews") -> chromadb.Collection:
    """
    Nhận DataFrame reviews → embed → lưu vào ChromaDB.
    Trả về collection để query sau.
    """
    reviews = df["text"].dropna().tolist()
    if not reviews:
        raise ValueError("❌ Không có reviews để index")

    print(f"📦 RAG Agent: Đang index {len(reviews)} reviews vào vector DB...")

    # Tạo embedding function
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )

    # Tạo ChromaDB client
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Xoá collection cũ nếu có (để tránh conflict khi chạy lại)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    # Tạo collection mới
    collection = client.create_collection(
        name=collection_name,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    # Thêm reviews vào collection
    collection.add(
        documents=reviews,
        ids=[f"review_{i}" for i in range(len(reviews))],
        metadatas=[
            {
                "stars": float(df.iloc[i].get("stars", 0)) if "stars" in df.columns else 0.0,
                "business_name": str(df.iloc[i].get("business_name", "")) if "business_name" in df.columns else "",
            }
            for i in range(len(reviews))
        ],
    )

    print(f"✅ Index xong: {len(reviews)} reviews trong collection '{collection_name}'")
    return collection


def query_reviews(
    collection: chromadb.Collection,
    query: str,
    top_k: int = 10,
) -> list[str]:
    """
    Query vector DB → trả về top-k reviews liên quan nhất.
    """
    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
    )

    docs = results["documents"][0] if results["documents"] else []

    if AGENT_VERBOSE:
        print(f"   🔎 Query '{query[:40]}...' → {len(docs)} reviews")

    return docs


def get_reviews_by_topic(
    collection: chromadb.Collection,
    top_k: int = 10,
) -> dict[str, list[str]]:
    """
    Query reviews cho từng chủ đề.
    Trả về dict: topic → list reviews liên quan
    """
    print(f"🔍 RAG Agent: Đang query reviews theo từng chủ đề...")
    topic_reviews = {}

    for topic, query in TOPIC_QUERIES.items():
        reviews = query_reviews(collection, query, top_k=top_k)
        topic_reviews[topic] = reviews
        print(f"   ✅ {topic}: {len(reviews)} reviews liên quan")

    return topic_reviews


def build_and_query(
    df: pd.DataFrame,
    top_k: int = 10,
    collection_name: str = "reviews",
) -> dict[str, list[str]]:
    """
    Hàm chính gọi từ bên ngoài.
    Nhận DataFrame → build vector DB → query theo topic → trả về dict
    """
    collection = build_vector_db(df, collection_name)
    return get_reviews_by_topic(collection, top_k=top_k)


if __name__ == "__main__":
    # Test với data mẫu
    sample_reviews = [
        "Đồ ăn rất ngon, hương vị đậm đà, phần ăn vừa đủ.",
        "Nhân viên phục vụ chậm, thái độ không nhiệt tình.",
        "Giá cả hợp lý, xứng đáng với chất lượng.",
        "Không gian sạch sẽ, thoáng mát, nhạc vừa phải.",
        "Món ăn nguội, không ngon như kỳ vọng.",
        "Staff rất thân thiện và chuyên nghiệp.",
        "Hơi đắt so với khẩu phần ăn nhận được.",
        "Quán ồn ào, khó nói chuyện.",
        "Thức ăn tươi ngon, menu đa dạng.",
        "Chờ đợi quá lâu dù không đông khách.",
    ]

    sample_df = pd.DataFrame({
        "text": sample_reviews,
        "stars": [5, 2, 4, 4, 2, 5, 3, 2, 5, 2],
        "business_name": ["Test Restaurant"] * 10,
    })

    topic_reviews = build_and_query(sample_df, top_k=5)

    print("\n📊 Kết quả RAG:")
    for topic, reviews in topic_reviews.items():
        print(f"\n🏷️  {topic.upper()}:")
        for r in reviews:
            print(f"   → {r[:80]}...")