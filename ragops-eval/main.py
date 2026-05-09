from fastapi import FastAPI
from routers import api_router
from config.settings import settings
import uvicorn

app = FastAPI(
    title="RAGOps Eval Service",
    description="Retrieval quality evaluation for search-service via RAGAS metrics.",
)
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.EVAL_SERVICE_HOST,
        port=settings.EVAL_SERVICE_PORT,
        reload=settings.EVAL_SERVICE_RELOAD,
        log_level=settings.EVAL_SERVICE_LOG_LEVEL,
    )
