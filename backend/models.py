# backend/models.py
from pydantic import BaseModel
from typing import Optional


class AnalyzeRequest(BaseModel):
    business_name: str
    business_id: Optional[str] = None
    csv_path: Optional[str] = None
    use_rag: bool = True


class SearchRequest(BaseModel):
    business_name: str


class BusinessResult(BaseModel):
    business_id: str
    name: str
    city: str
    state: str
    address: str
    stars: float
    review_count: int
    categories: str
    reliability: str