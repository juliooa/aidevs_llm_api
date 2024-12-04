import logging
from models import Message, ChatResponse, ResponseMessage
from http_client import httpx_client_wrapper

logger = logging.getLogger(__name__)

LLM_ENDPOINT = "http://127.0.0.1:11434"


async def chat(model: str, messages: list[Message]):
    logger.info(f"Sending message to {LLM_ENDPOINT}")
    async_client = httpx_client_wrapper()
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]

    url = LLM_ENDPOINT + "/api/chat"
    try:
        response = await async_client.post(
            url,
            json={
                "model": model,
                "messages": messages_dict,
                "stream": False,
                "options": {
                    "num_ctx": 2048,
                },
            },
        )
        logger.info(f"Response: {response}")
        if response.status_code != 200:
            logger.error(f"Error: {response.json()}")
            raise Exception(f"Error: {response.json()}")

        response_json = response.json()
        logger.info(f"Response json: {response_json}")
        return ChatResponse(**response_json)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        if isinstance(e, TimeoutError):
            logger.error("Request timed out")
        return ChatResponse(
            model=model,
            done=True,
            message=ResponseMessage(
                role="assistant",
                content="Oops, ocurrió un error. Por favor, intenta de nuevo.",
            ),
        )
