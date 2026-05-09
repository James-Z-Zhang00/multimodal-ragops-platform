from fastapi import APIRouter
from evaluator.client import SearchServiceClient
from config.settings import settings

health_router = APIRouter()


@health_router.get("/health")
async def health():
    client = SearchServiceClient(base_url=settings.SEARCH_SERVICE_URL)
    search_ok = await client.is_healthy()
    return {
        "status": "ok",
        "service": "ragops-eval",
        "search_service": "reachable" if search_ok else "unreachable",
    }
