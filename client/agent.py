import os, json, asyncio
from openai import AsyncOpenAI
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
MODEL = os.getenv("AGENT_MODEL", "llama3.1")
llm_client = AsyncOpenAI(base_url=OLLAMA_URL, api_key="ollama")

SYSTEM_PROMPT = """You are the Master IT Infrastructure Agent. Everything you do runs
fully offline against a local Ollama model - there is no cloud AI involved anywhere
in this system. The log directory may contain plain files, JSON/NDJSON files, or
archives (.zip/.tar/.tar.gz/.tgz/.tar.bz2/.gz/.7z, including nested archives) - all
of this is handled transparently by the tools, you don't need to unpack anything
yourself. You have two modes:

LEARNING MODE:
If unsupervised_auto_discovery reports new command/log formats to learn, or the
user asks you to learn a new format:
1. Call `unsupervised_auto_discovery` - it finds CLI/transcript-style logs (e.g.
   PuTTY session logs), splits them into command blocks, and learns one parser
   per distinct COMMAND automatically. JSON/NDJSON logs need no learning at all.
2. If the user wants to teach a format manually instead, ask them to paste a
   sample (ideally one command and its output, or a representative log excerpt)
   and a short name, then call `learn_log_format`.
3. Once learned, use `auto_ingest_directory` to apply it to all matching sources.

OFFLINE QUERY MODE:
If the user asks a question about the infrastructure:
1. Use `get_database_schema` to see what tables exist (tables are named after the
   command family or JSON event type they came from, e.g. volume_show, s3_audit).
2. Use `execute_sql_query` to answer the question based on the indexed data.
3. Use `get_ingest_status` if the user asks what's been ingested or what's pending.

If a tool fails, read the error, fix your JSON, and try again."""


async def main():
    print("Starting Autonomous Voyager Agent...")
    server_params = StdioServerParameters(command="python", args=["-u", "server.py"])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected successfully. System Online.")

            mcp_tools = await session.list_tools()
            tools_spec = [
                {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}}
                for t in mcp_tools.tools
            ]

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            while True:
                try:
                    user_input = input("\nMaster Agent > ")
                    if user_input.lower() in ["exit", "quit"]:
                        break

                    # ==========================================
                    # ADMIN OVERRIDE: Bypass the LLM entirely
                    # ==========================================
                    if user_input.lower().startswith("/run "):
                        tool_name = user_input[5:].strip()
                        print(f"\n[ADMIN OVERRIDE] Forcing execution of: {tool_name}...")
                        try:
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

                            preview = tool_result_str.replace("\n", " ")[:100] + "..." if len(tool_result_str) > 100 else tool_result_str
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
