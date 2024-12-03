from fastapi import FastAPI, Depends
from api.auth import get_api_key
from models import ChatRequest, ChatResponse
import llm

app = FastAPI()


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    _=Depends(get_api_key),
) -> ChatResponse:
    response = llm.chat(request.model, request.messages)
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
