from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")

@mcp.tool()
def add(a:int, b: int)->int:
    """Add two numbers"""
    return a+b

@mcp.tool()
def substract(a:int, b: int)->int:
    """substract two numbers"""
    return a-b

@mcp.tool()
def multiply(a:int, b: int)->int:
    """multiply two numbers"""
    return a*b

print("yess")
if __name__ == "__main__":
    mcp.run(transport="stdio")
    #mcp.run(transport="streamable-http") #if server is on brower or any network
#if client and server are in same machine then for their communcation stdio is used