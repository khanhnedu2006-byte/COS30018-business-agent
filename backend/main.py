# backend/main.py
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router
from config import BACKEND_HOST, BACKEND_PORT, validate_config

validate_config()

app = FastAPI(
    title="Business Improvement Agent API",
    description="LLM-powered multiagent system phân tích reviews nhà hàng",
    version="1.0.0",
)

# Lấy allowed origins từ env
FRONTEND_URL = os.getenv("FRONTEND_URL", "")
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
if FRONTEND_URL:
    allowed_origins.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "Business Improvement Agent API",
        "docs": "/docs",
        "health": "/api/health",
        "environment": os.getenv("ENVIRONMENT", "development"),
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", BACKEND_PORT))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )