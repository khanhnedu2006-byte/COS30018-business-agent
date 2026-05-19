# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ─── LLM ─────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# ─── Data ────────────────────────────────────────────────────────────
DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")
YELP_DATASET_PATH: str = os.path.join(DATA_DIR, "yelp_reviews.csv")
MAX_REVIEWS_PER_RUN: int = int(os.getenv("MAX_REVIEWS_PER_RUN", "100"))

# ─── Backend ─────────────────────────────────────────────────────────
BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

# ─── Agent ───────────────────────────────────────────────────────────
AGENT_VERBOSE: bool = os.getenv("AGENT_VERBOSE", "true").lower() == "true"
MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))

# ─── Validation ──────────────────────────────────────────────────────
def validate_config() -> None:
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY chưa được thiết lập.\n"
            "Mở file .env và thêm: GROQ_API_KEY=your_key_here"
        )
    print(f"✅ Config OK | Model: {LLM_MODEL} | Backend: {BACKEND_HOST}:{BACKEND_PORT}")


if __name__ == "__main__":
    validate_config()