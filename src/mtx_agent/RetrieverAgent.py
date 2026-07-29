from typing import Annotated, Any, List, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from llm_model import bedrock_llm_model
from prompts import (
    generate_answer_system_message,
    generate_query_system_message,
)
from RetrieverTool import knowledge_base_retriever


class AgentState(TypedDict):
    """Custom state for the agent"""

    messages: Annotated[List[Any], add_messages]


class RetrieverAgent:
    def __init__(self, logger):
        self.logger = logger

    def __generate_query(self, state: AgentState):
        """Call the model to generate a query or just respond to the user based on the user query."""

        system_message = SystemMessage(content=generate_query_system_message())
        messages_with_system_message = [system_message] + state["messages"]
        response = (
            bedrock_llm_model(temperature=1.0)
            .bind_tools([knowledge_base_retriever])
            .invoke(messages_with_system_message)
        )
        if not response.tool_calls:
            return

        return {
            "messages": [response],
        }

    def __generate_answer(self, state: AgentState):
        messages = state["messages"]
        contexts = []
        for message in reversed(messages):
            if (
                isinstance(message, ToolMessage)
                and message.name == "knowledge_base_retriever"
            ):
                contexts.append(message.content)

        merged_context = "\n\n".join([c for c in contexts if c])

        system_message = SystemMessage(
            content=generate_answer_system_message(merged_context)
        )
        conversation_messages = [system_message]

        for message in messages:
            if isinstance(message, HumanMessage):
                conversation_messages.append(message)
            elif isinstance(message, AIMessage) and len(message.tool_calls) == 0:
                conversation_messages.append(message)

        response = bedrock_llm_model(temperature=0.1).invoke(conversation_messages)
        return {"messages": [response]}

    def get_agent_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("generate_query", self.__generate_query)
        workflow.add_node("retrieve", ToolNode([knowledge_base_retriever]))
        workflow.add_node("generate_answer", self.__generate_answer)

        workflow.add_edge(START, "generate_query")
        workflow.add_conditional_edges(
            "generate_query",
            tools_condition,
            {
                "tools": "retrieve",
                END: "generate_answer",
            },
        )
        workflow.add_edge("retrieve", "generate_answer")
        workflow.add_edge("generate_answer", END)

        return workflow.compile()
