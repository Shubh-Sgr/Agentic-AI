import asyncio
import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

# Load environment variables from .env
load_dotenv()

async def main():
    openai_key = os.getenv('OPENAI_API_KEY')
    owm_key = os.getenv('OWM_API_KEY')

    project_root = os.path.dirname(os.path.abspath(__file__))
    
    mcp_dir = os.path.join(project_root, "mcp-openweather")

    client = MultiServerMCPClient(
        {
            "weather": {
                "transport": "stdio",
                "command": "go",
                "args": ["run", "-C", mcp_dir, "main.go"],
                "env": {
                    "OWM_API_KEY": owm_key or "",
                    "PATH": os.getenv("PATH", "")  # System PATH to help Python find 'go'
                }
            }
        }
    )

    tools = await client.get_tools()

    model = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)

    def call_model(state: MessagesState):
        response = model.bind_tools(tools).invoke(state["messages"])
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")

    graph = builder.compile()

    result = await graph.ainvoke({
        "messages": [{"role": "user", "content": "Whats the weather in banglore?"}]
    })

    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())