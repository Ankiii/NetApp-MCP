from mcp.server.fastmcp import FastMCP
import sqlite3, os, zipfile, tempfile, re, json, time
import pandas as pd
import google.generativeai as genai

# Setup
mcp = FastMCP("Autonomous_Learner_Agent")
BASE_LOG_DIR = "/logs"
DB_PATH = "/app/db/universal_index.db"
LEARNED_PARSERS_FILE = "/app/db/learned_parsers.py"

# Configure Google SDK
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable is not set!")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('models/gemini-3.5-flash')

# Ensure directories exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
if not os.path.exists(LEARNED_PARSERS_FILE):
    with open(LEARNED_PARSERS_FILE, "w") as f:
        f.write("# This file contains AI-generated parsers.\nimport re\n")

@mcp.tool()
def consult_big_brother_and_learn(log_sample: str, log_type_name: str) -> str:
    """ONLINE ONLY: Consults Gemini directly to write a Python parser."""
    prompt = f"""
    I am building an automated log parser. I have a log type I call '{log_type_name}'.
    Write a Python function named `parse_{log_type_name}(text_content)` that parses this raw text and returns a list of dictionaries.
    - Return ONLY raw python code. No markdown.
    Sample: {log_sample[:2000]}
    """
    try:
        response = model.generate_content(prompt)
        python_code = response.text.replace('```python', '').replace('```', '').strip()
        with open(LEARNED_PARSERS_FILE, "a") as f:
            f.write(f"\n\n{python_code}\n")
        return f"Success! Learned {log_type_name}."
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def unsupervised_auto_discovery() -> str:
    """Scans logs, identifies new formats, and consults Gemini (Rate-Limited)."""
    parsers = {}
    try: exec(open(LEARNED_PARSERS_FILE).read(), globals(), parsers)
    except: pass
    known_types = [p.replace('parse_', '') for p in parsers.keys() if p.startswith('parse_')]
    
    discovered_patterns = {}
    for root, _, files in os.walk(BASE_LOG_DIR):
        for file in files:
            if file.endswith(('.txt', '.log')):
                base = re.sub(r'[\d\W_]+', '', file.split('.')[0]).lower()
                if base not in known_types and base not in discovered_patterns:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        discovered_patterns[base] = f.read(3000)

    if not discovered_patterns: return "No new formats found."
    
    results = []
    for log_type, sample in discovered_patterns.items():
        # Throttling without printing to stdout (prevents JSONRPC crash)
        time.sleep(70) 
        results.append(consult_big_brother_and_learn(sample, log_type))
    return "\n".join(results)

@mcp.tool()
def auto_ingest_directory() -> str:
    """Applies learned parsers to build the database."""
    parsers = {}
    try: exec(open(LEARNED_PARSERS_FILE).read(), globals(), parsers)
    except Exception as e: return f"Error: {e}"

    conn = sqlite3.connect(DB_PATH)
    processed = 0
    for root, _, files in os.walk(BASE_LOG_DIR):
        for file in files:
            if file.endswith(('.txt', '.log')):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()
                    for name, func in parsers.items():
                        if name.startswith('parse_') and name.replace('parse_','').lower() in file.lower():
                            try:
                                df = pd.DataFrame(func(content))
                                df.to_sql(name.replace('parse_',''), conn, if_exists='append', index=False)
                                processed += 1
                            except: continue
    conn.close()
    return f"Ingestion complete. Processed {processed} files."

@mcp.tool()
def get_database_schema() -> str:
    """Returns database structure."""
    conn = sqlite3.connect(DB_PATH)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    schema = "\n".join([f"Table {t[0]} | Columns: {', '.join([c[1] for c in conn.execute(f'PRAGMA table_info({t[0]})')])}" for t in tables])
    conn.close()
    return schema if schema else "Empty DB."

@mcp.tool()
def execute_sql_query(query: str) -> str:
    """Executes READ-ONLY SQL."""
    if any(k in query.lower() for k in ["drop", "delete", "update", "insert", "alter"]): return "Access Denied."
    conn = sqlite3.connect(DB_PATH)
    try: return pd.read_sql_query(query, conn).to_string(index=False)
    finally: conn.close()

if __name__ == "__main__":
    mcp.run(transport="stdio")