
from pydantic import BaseModel, Field
from typing import Optional


class AgentChatRequest(BaseModel):

    candidate_id: int = Field(gt=0)

    message: str = Field(
        min_length=1,
        max_length=3000
    )

    conversation_id: Optional[str] = Field(
        default="default",
        min_length=1,
        max_length=100
    )
