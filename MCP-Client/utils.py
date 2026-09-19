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

    # Get absolute path to the directory containing util.py
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the Go MCP folder
    mcp_dir = os.path.join(project_root, "mcp-openweather")

    # Initialize MultiServerMCPClient
    # Uses 'go run -C <mcp_dir> main.go' to locate go.mod correctly
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

    # Fetch tools exposed by the Go MCP server
    tools = await client.get_tools()

    # Initialize OpenAI model
    model = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)

    # Define model invocation node
    def call_model(state: MessagesState):
        response = model.bind_tools(tools).invoke(state["messages"])
        return {"messages": [response]}

    # Build LangGraph state workflow
    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")

    graph = builder.compile()

    # Asynchronously invoke the state graph
    result = await graph.ainvoke({
        "messages": [{"role": "user", "content": "Whats the weather in banglore?"}]
    })

    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())