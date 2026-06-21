#import os
#import json
#import asyncio
#from openai import AsyncOpenAI
#from mcp.client.stdio import stdio_client, StdioServerParameters
#from mcp.client.session import ClientSession
#
#OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
#llm_client = AsyncOpenAI(base_url=OLLAMA_URL, api_key="ollama")
#MODEL = "llama3.1"
#
#async def main():
#    print("Starting native MCP Server via stdio...")
#    
#    # Spawn the MCP server as a local subprocess
#    server_params = StdioServerParameters(
#        command="python",
#        args=["server.py"]
#    )
#    
#    async with stdio_client(server_params) as (read, write):
#        async with ClientSession(read, write) as session:
#            await session.initialize()
#            print("Connected successfully. Airgapped MCP System Online.")
#            
#            mcp_tools = await session.list_tools()
#            
#            tools_spec = [
#                {
#                    "type": "function",
#                    "function": {
#                        "name": tool.name,
#                        "description": tool.description,
#                        "parameters": tool.inputSchema
#                    }
#                } for tool in mcp_tools.tools
#            ]
#
#            messages = [
#                {"role": "system", "content": "You are an expert NetApp storage administrator. You have access to local tools to extract and parse log data. Always use the provided tools to fetch data before answering."}
#            ]
#
#            while True:
#                user_input = input("\nNetApp Admin > ")
#                if user_input.lower() in ['exit', 'quit']:
#                    break
#                    
#                messages.append({"role": "user", "content": user_input})
#                
#                response = await llm_client.chat.completions.create(
#                    model=MODEL,
#                    messages=messages,
#                    tools=tools_spec
#                )
#                
#                msg = response.choices[0].message
#                
#                if msg.tool_calls:
#                    print("\n[Agent executing tool...]")
#                    messages.append(msg)
#                    
#                    for tool_call in msg.tool_calls:
#                        args = json.loads(tool_call.function.arguments)
#                        print(f"-> Calling: {tool_call.function.name} with {args}")
#                        
#                        result = await session.call_tool(tool_call.function.name, arguments=args)
#                        tool_result_str = str(result.content[0].text)
#                        
#                        messages.append({
#                            "role": "tool",
#                            "tool_call_id": tool_call.id,
#                            "content": tool_result_str
#                        })
#                        
#                    final_response = await llm_client.chat.completions.create(
#                        model=MODEL,
#                        messages=messages
#                    )
#                    print(f"\n{final_response.choices[0].message.content}")
#                    messages.append(final_response.choices[0].message)
#                    
#                else:
#                    print(f"\n{msg.content}")
#                    messages.append(msg)
#
#if __name__ == "__main__":
#    asyncio.run(main())

import os, json, asyncio
from openai import AsyncOpenAI
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
llm_client = AsyncOpenAI(base_url=OLLAMA_URL, api_key="ollama")
MODEL = "llama3.1"

async def main():
    print("Starting Autonomous Voyager Agent...")
    server_params = StdioServerParameters(command="python", args=["-u", "server.py"])
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected successfully. System Online.")
            
            mcp_tools = await session.list_tools()
            tools_spec = [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}} for t in mcp_tools.tools]

            messages = [
                {"role": "system", "content": """You are the Master IT Infrastructure Agent. You have two modes:

TRAINING MODE:
If the user asks you to learn a new file format:
1. Ask the user to paste a sample of the raw log file.
2. Use `consult_big_brother_and_learn` to send that sample to the Cloud AI.
3. Once learned, use `auto_ingest_directory` to process all files and build the database.

OFFLINE QUERY MODE:
If the user asks a question about the infrastructure:
1. Use `get_database_schema` to see what tables the Cloud AI dynamically built.
2. Use `execute_sql_query` to answer the question based on the indexed data.

If a tool fails, read the error, fix your JSON, and try again."""}
            ]

            while True:
                try:
                    user_input = input("\nMaster Agent > ")
                    if user_input.lower() in ['exit', 'quit']: break

                    # ==========================================
                    # ADMIN OVERRIDE: Bypass the LLM entirely
                    # ==========================================
                    if user_input.lower().startswith("/run "):
                        tool_name = user_input[5:].strip()
                        print(f"\n[ADMIN OVERRIDE] Forcing execution of: {tool_name}...")
                        try:
                            # Execute the tool directly via the MCP session
                            result = await session.call_tool(tool_name, arguments={})
                            print(f"-> Result:\n{result.content[0].text}")
                        except Exception as e:
                            print(f"-> Execution Error: {e}")
                        continue
                    # ==========================================
                        
                    messages.append({"role": "user", "content": user_input})
                    
                    response = await llm_client.chat.completions.create(
                        model=MODEL, messages=messages, tools=tools_spec, temperature=0.0
                    )
                    msg = response.choices[0].message
                    
                    while msg.tool_calls:
                        print("\n[Agent is processing...]")
                        messages.append(msg)
                        for tool_call in msg.tool_calls:
                            try:
                                args = json.loads(tool_call.function.arguments)
                                print(f"-> Executing: {tool_call.function.name}")
                                result = await session.call_tool(tool_call.function.name, arguments=args)
                                tool_result_str = str(result.content[0].text)
                            except Exception as e:
                                tool_result_str = f"[SYSTEM ERROR]: {str(e)}"
                            
                            preview = tool_result_str.replace('\n', ' ')[:100] + "..." if len(tool_result_str) > 100 else tool_result_str
                            print(f"-> Result: {preview}")
                            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": tool_result_str})
                            
                        response = await llm_client.chat.completions.create(
                            model=MODEL, messages=messages, tools=tools_spec, temperature=0.0
                        )
                        msg = response.choices[0].message
                        
                    print(f"\n[Agent]: {msg.content}")
                    messages.append(msg)
                except Exception as e:
                    print(f"Critical Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())