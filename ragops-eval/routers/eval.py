import logging
from fastapi import APIRouter, HTTPException
from models import EvalRequest, EvalResponse, SingleEvalRequest
from evaluator.runner import run_evaluation, run_single

logger = logging.getLogger(__name__)
eval_router = APIRouter()


@eval_router.post("/run", response_model=EvalResponse)
async def eval_run(request: EvalRequest) -> EvalResponse:
    try:
        return await run_evaluation(request)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("Eval run failed")
        raise HTTPException(status_code=500, detail=str(e))


@eval_router.post("/single", response_model=EvalResponse)
async def eval_single(request: SingleEvalRequest) -> EvalResponse:
    try:
        return await run_single(request)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("Single eval failed")
        raise HTTPException(status_code=500, detail=str(e))
