from pydantic import BaseModel, HttpUrl
from typing import Literal


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    search_query: str


class SEOHint(BaseModel):
    category: Literal["title", "meta", "headings", "content", "performance", "links", "structured_data", "other"]
    severity: Literal["critical", "warning", "info"]
    message: str
    recommendation: str


class AnalyzeResponse(BaseModel):
    url: str
    search_query: str
    score: int  # 0–100
    hints: list[SEOHint]
    page_image: str | None = None  # base64-encoded PNG screenshot
