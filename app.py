import logging
from fastapi import FastAPI, Depends
from fastapi.concurrency import asynccontextmanager
from api.auth import get_api_key
from models import ChatRequest, ChatResponse
import llm
from http_client import httpx_client_wrapper

logger = logging.getLogger(__name__)


@asynccontextmanager
async def app_startup(app: FastAPI):
    httpx_client_wrapper.start()
    yield
    await httpx_client_wrapper.stop()


app = FastAPI()


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    _=Depends(get_api_key),
) -> ChatResponse:
    logger.info(f"Received request: {request}")
    response = llm.chat(request.model, request.messages)
    logger.info(f"Response: {response}")
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
