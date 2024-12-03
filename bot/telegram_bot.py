import asyncio
import logging
import os
import re
from typing import Literal

from pydantic import BaseModel
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv
from system_prompt import system_prompt
from http_client import httpx_client_wrapper

load_dotenv()

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
LLM_API_URL = os.getenv("LLM_API_URL")


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[Message]


class ResponseMessage(BaseModel):
    role: Literal["assistant"]
    content: str


class ChatResponse(BaseModel):
    model: str
    message: ResponseMessage
    done: bool


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def is_authorized_user(user_id: int) -> bool:
    return True


def enforce_limit_splitting(message: str, limit: int) -> list[str]:
    words = message.split(" ")
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 > limit:
            chunks.append(current_chunk.strip())
            current_chunk = word
        else:
            current_chunk += " " + word

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.effective_chat:
        user = update.message.from_user
        chat = update.effective_chat
        if user:
            username = user.username
            first_name = user.first_name
            last_name = user.last_name
            user_id = user.id
            logger.info(f"Received start command from user {username} ({user_id})")
            authorized_user = is_authorized_user(user_id)
            if authorized_user:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=f"Hola {first_name} {last_name} (@{username})! ¡Bienvenido a la primera conferencia de IADevs!",
                )
            else:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=f"No estás autorizado para usar este bot. Por favor, contacta al administrador del bot y proporciona tu id de usuario. Tu id de usuario es: {user_id}",
                )


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message and update.effective_chat:
        user = message.from_user
        chat = update.effective_chat
        if user:
            user_name = user.username
            user_id = user.id
            logger.info(f"Received message from user {user_id}")
            authorized_user = is_authorized_user(user_id)
            if authorized_user:
                user_message = message.text
                if not user_message:
                    return  # ignore non-text messages

                answer = await send_message(
                    message=user_message,
                    user_id=user_id,
                    user_name=user_name or "",
                )
                response_chunks = enforce_limit_splitting(answer, 4096)

                for chunk in response_chunks:
                    escaped_chunk = escape_markdown_v2(chunk)
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=escaped_chunk,
                        parse_mode="MarkdownV2",
                    )
                    # sleep for 100 milliseconds to avoid rate limiting
                    if len(response_chunks) > 1:
                        await asyncio.sleep(0.3)
            else:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text="You are not authorized to use this bot.",
                )


def escape_markdown_v2(text: str) -> str:
    # List of characters that need to be escaped in MarkdownV2
    escape_chars = r"_`*[]()~>#+-=|{}.!"
    # Regular expression to detect markdown links
    link_regex = r"(\[.*?\]\(.*?\))"

    # Function to escape text except for links
    def escape_non_link_parts(part):
        return re.sub(r"([%s])" % re.escape(escape_chars), r"\\\1", part)

    # Split the text by Markdown links and escape the non-link parts
    parts = re.split(link_regex, text)
    # Process each part: escape non-link parts, keep links unchanged
    escaped_text = "".join(
        [
            part if re.match(link_regex, part) else escape_non_link_parts(part)
            for part in parts
        ]
    )

    return escaped_text


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ese comando no lo conozco, puedes usar /help para ver los comandos disponibles.",
        )


async def send_message_to_user(user_id: int, message: str):
    bot = Bot(token=TELEGRAM_API_KEY or "")
    try:
        await bot.send_message(chat_id=user_id, text=message)
        return True
    except Exception as e:
        print(f"Error sending message to user {user_id}: {str(e)}")
        return False


def start_bot():

    httpx_client_wrapper.start()
    application = ApplicationBuilder().token(TELEGRAM_API_KEY or "").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.add_handler(MessageHandler(filters.TEXT | filters.VOICE, on_message))

    application.run_polling()


def request_slots_api(url: str, method: str, payload: dict | None = None):
    headers = {
        "X-API-Key": f"{API_KEY}",
        "Content-Type": "application/json",
    }
    http_client = httpx_client_wrapper()

    return http_client.request(method, url, json=payload, headers=headers)


async def send_message(
    message: str,
    user_id: int,
    user_name: str,
) -> str:

    system_message = get_system_message()
    user_message = Message(role="user", content=message)

    payload = ChatRequest(
        model=MODEL or "",
        messages=[system_message, user_message],
    )

    try:

        if not LLM_API_URL:
            raise ValueError("LLM_API_URL must be set in .env file")

        endpoint = LLM_API_URL + "/api/chat"
        logger.info(f"Sending message to {endpoint}")
        logger.info(f"Payload: {payload.model_dump()}")
        response = await request_slots_api(
            endpoint,
            method="POST",
            payload=payload.model_dump(),
        )

        if response.status_code == 200:
            api_response = ChatResponse(**response.json())
            return api_response.message.content
        else:
            error = f"Failed to send message, error: {response.content}"
            logger.error(f"Failed to send message, error: {response.content}")
            return error

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return ""


def get_system_message() -> Message:
    return Message(role="system", content=system_prompt)


if __name__ == "__main__":
    start_bot()
