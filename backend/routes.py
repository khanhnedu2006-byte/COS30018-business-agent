# backend/routes.py
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, HTTPException, UploadFile, File
import shutil

from models import AnalyzeRequest, SearchRequest
from agents.manager_agent import run_analysis
from data.yelp_loader import search_businesses

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/search")
def search(request: SearchRequest):
    """Tìm kiếm chi nhánh theo tên trong Yelp Dataset."""
    if not request.business_name.strip():
        raise HTTPException(status_code=400, detail="Tên quán không được rỗng")

    try:
        matches = search_businesses(request.business_name)
        if not matches:
            return {"businesses": [], "message": "Không tìm thấy chi nhánh nào"}
        return {"businesses": matches, "total": len(matches)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Phân tích reviews của một quán.
    - Có business_id → lấy đúng chi nhánh Yelp
    - Có csv_path    → đọc từ file CSV
    - Không có gì    → Google Maps
    """
    print(f"DEBUG request: business_name={request.business_name}, "
          f"business_id={request.business_id}, "
          f"csv_path={request.csv_path}")

    if not request.business_name.strip():
        raise HTTPException(status_code=400, detail="Tên quán không được rỗng")

    try:
        result = run_analysis(
            business_name=request.business_name,
            business_id=request.business_id,
            csv_path=request.csv_path,
            use_rag=request.use_rag,
        )

        if result.get("error"):
            raise HTTPException(status_code=404, detail=result.get("reason"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/google")
def analyze_google(request: SearchRequest):
    """Phân tích reviews từ Google Maps."""
    
    if not request.business_name.strip():
        raise HTTPException(status_code=400, detail="Tên quán không được rỗng")

    try:
        result = run_analysis(
            business_name=request.business_name,
            use_rag=True,
        )

        if result.get("error"):
            raise HTTPException(status_code=404, detail=result.get("reason"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload file CSV reviews."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .csv")

    upload_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "uploads"
    )
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "message": "Upload thành công",
        "file_path": file_path,
        "filename": file.filename,
    }