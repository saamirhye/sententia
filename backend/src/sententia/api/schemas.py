from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str


class ResumeRequest(BaseModel):
    thread_id: str
    approved: bool
