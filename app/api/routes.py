from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_pipeline
from app.models.schemas import SummarizeRequest, SummarizeResponse
from app.services.pipeline import NewsPipeline

router = APIRouter()


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_news(
    request: SummarizeRequest,
    pipeline: NewsPipeline = Depends(get_pipeline),
) -> SummarizeResponse:
    try:
        return await pipeline.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
