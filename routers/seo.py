from fastapi import APIRouter, HTTPException

from models.seo import AnalyzeRequest, AnalyzeResponse
from services.seo_analyzer import analyze

router = APIRouter(prefix="/api/seo", tags=["seo"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(payload: AnalyzeRequest) -> AnalyzeResponse:
    """Fetch *url*, run SEO checks against *search_query*, and return hints."""
    try:
        return await analyze(str(payload.url), payload.search_query)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not analyze URL: {exc}") from exc
