from fastapi import APIRouter
from routers.eval import eval_router
from routers.health import health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(eval_router, prefix="/eval", tags=["eval"])
