
from langchain_ollama import ChatOllama

from langchain_core.messages import (
    SystemMessage
)

from langgraph.graph import (
    StateGraph,
    MessagesState,
    START,
    END
)

from langgraph.prebuilt import (
    ToolNode,
    tools_condition
)

from langgraph.checkpoint.memory import MemorySaver

from app.agents.tools import create_agent_tools
from app.agents.prompts import SYSTEM_PROMPT


# Shared conversation memory for this running application
memory = MemorySaver()


def create_agent_graph(db, candidate_id: int):
    """
    Create a LangGraph recruitment agent
    for a particular candidate.
    """

    # Load tools for this candidate
    tools = create_agent_tools(
        db=db,
        candidate_id=candidate_id
    )

    # Initialize local Ollama model
    llm = ChatOllama(
        model="llama3.1:8b",
        temperature=0
    )

    # Enable tool calling
    llm_with_tools = llm.bind_tools(tools)

    # Agent node
    def agent_node(state: MessagesState):

        messages = state["messages"]

        # Add system instructions only once per conversation
        has_system_message = any(
            isinstance(message, SystemMessage)
            for message in messages
        )

        if not has_system_message:
            messages = [
                SystemMessage(content=SYSTEM_PROMPT)
            ] + messages

        response = llm_with_tools.invoke(messages)

        return {
            "messages": [response]
        }

    # Create graph
    workflow = StateGraph(MessagesState)

    workflow.add_node(
        "agent",
        agent_node
    )

    workflow.add_node(
        "tools",
        ToolNode(tools)
    )

    workflow.add_edge(
        START,
        "agent"
    )

    # Agent decides whether to call tools or finish
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
        {
            "tools": "tools",
            END: END
        }
    )

    # Return tool results to the agent
    workflow.add_edge(
        "tools",
        "agent"
    )

    # Compile graph with conversational memory
    app = workflow.compile(
        checkpointer=memory
    )

    return app
