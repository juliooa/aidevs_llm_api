from typing import Literal
from pydantic import BaseModel


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


class Email(BaseModel):
    sender: str
    subject: str
    body: str


class EmailCategory(BaseModel):
    category: str
