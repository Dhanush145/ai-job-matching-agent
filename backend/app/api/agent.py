
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from langchain_core.messages import HumanMessage

from app.database.database import get_db
from app.database.models import Candidate

from app.schemas.agent import AgentChatRequest

from app.agents.graph import create_agent_graph


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent",
    tags=["AI Career Agent"]
)


@router.post("/chat")
def chat_with_agent(
    request: AgentChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with the LangGraph-powered AI recruitment agent.
    """

    # Check candidate
    candidate = db.query(Candidate).filter(
        Candidate.id == request.candidate_id
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    try:

        # Build agent graph
        agent = create_agent_graph(
            db=db,
            candidate_id=request.candidate_id
        )

        # Isolate conversation memory by candidate and conversation
        thread_id = (
            f"candidate-{request.candidate_id}-"
            f"conversation-{request.conversation_id}"
        )

        config = {
            "configurable": {
                "thread_id": thread_id
            },
            "recursion_limit": 15
        }

        # Execute LangGraph
        result = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=request.message
                    )
                ]
            },
            config=config
        )

        # Extract final assistant response
        final_message = result["messages"][-1]

        return {
            "candidate_id": candidate.id,
            "conversation_id": request.conversation_id,
            "user_message": request.message,
            "assistant_response": final_message.content
        }

    except HTTPException:
        raise

    except Exception as exc:

        logger.exception("AI agent execution failed")

        raise HTTPException(
            status_code=500,
            detail="AI agent failed. Check backend logs."
        ) from exc
