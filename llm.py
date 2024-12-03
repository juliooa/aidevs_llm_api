import logging
import requests
from models import Message, ChatResponse

logger = logging.getLogger(__name__)

LLM_ENDPOINT = "http://127.0.0.1:11434"


def chat(model: str, messages: list[Message]):

    messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]

    url = LLM_ENDPOINT + "/api/chat"
    try:
        response = requests.post(
            url,
            json={
                "model": model,
                "messages": messages_dict,
                "stream": False,
            },
        )
        if response.status_code != 200:
            logger.error(f"Error: {response.json()}")
            raise Exception(f"Error: {response.json()}")

        response_json = response.json()
        logger.info(f"Response json: {response_json}")
        return ChatResponse(**response_json)
    except requests.RequestException as e:
        logger.error(f"Error: {e}")
        raise e
