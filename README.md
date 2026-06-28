# NetApp Model Context Protocol (MCP) Agent

An autonomous, LLM-powered Model Context Protocol (MCP) agent that discovers, learns,
and indexes NetApp-related logs - CLI session transcripts, plain text logs, JSON/NDJSON,
and archives - so infrastructure administrators can query their data in plain English.

Fully local and air-gap friendly. Both the parser-writing step and the query step run
against **local Ollama models** - no cloud API, no API key, no rate limit. The only step
that ever touches the internet is the one-time download of the Ollama model weights.

---

## 🚀 Key Features

* **Archive-transparent ingestion.** Reads `.zip`, `.tar`, `.tar.gz`/`.tgz`, `.tar.bz2`,
  `.gz`, and `.7z` directly - including archives nested inside archives (e.g. a yearly
  `.zip` full of monthly `.tar.gz`s full of daily `.log` files). Nothing needs to be
  manually unpacked first.
* **JSON-native ingestion.** JSON arrays, single JSON objects, REST-API-style wrapper
  responses (e.g. ONTAP's `{"records": [...], "num_records": N}`), and NDJSON
  (one object per line) are detected automatically and indexed with **no learning step
  at all** - the structure is self-describing, so there's nothing for an LLM to write.
  Tables auto-extend their schema as new fields show up later (e.g. a new audit-event
  field, or a new Harvest metric label) instead of breaking.
* **Command-aware learning for CLI session transcripts.** PuTTY/SSH session logs are
  transcripts, not single-format files - they interleave prompts, the commands you
  typed, and each command's (very differently shaped) output. The agent splits each
  transcript into command blocks at prompt boundaries and learns **one parser per
  distinct command** (e.g. `volume show`, `network interface show`) - not per file -
  using a local code model. Plain non-transcript logs (e.g. classic EMS/`messages`
  files with no command prompts) fall back to whole-file learning automatically.
* **Fully offline after setup.** No cloud API, no daily quota. Internet is only needed
  once, to build the Docker image and pull the two Ollama models.
* **Incremental ingestion.** A SQLite manifest tracks every source by content hash
  (including individual files inside archives), so dropping new logs/archives into the
  folder and re-running ingestion never reprocesses or duplicates existing data.
* **Natural Language to SQL.** Ask infrastructure questions in plain English; the agent
  answers via `execute_sql_query` against a **read-only** database connection.
* **Standardized MCP Tooling.** Built on the Model Context Protocol for easy
  integration into wider agentic workflows.

---

## 🏗️ Architecture Workflow

1. **One-time setup.** `docker-compose up` starts Ollama and pulls two local models: a
   general chat model (`llama3.1`) and a code-oriented model (`qwen2.5-coder`, used only
   to write parsers). This is the only step needing internet access.
2. **Discovery & learning** (`/run unsupervised_auto_discovery`):
   - Walks the log directory, transparently opening any archives it finds (recursively).
   - Anything that looks like JSON/NDJSON is set aside - it doesn't need learning.
   - Everything else is split into command blocks at prompt boundaries (or treated as
     one whole-file block, if it isn't a CLI transcript at all).
   - For each **distinct command/format** not already known, the local model writes a
     parser, which is self-tested against a real sample before being trusted.
3. **Ingestion** (`/run auto_ingest_directory`):
   - JSON/NDJSON records are flattened and written straight into tables named after
     their type (inferred from a field like `operation`/`event_type`/`category`, or the
     filename as a fallback).
   - CLI blocks are matched to a learned parser by command and written into a table
     named after that command (e.g. `volume_show`).
   - Every source is recorded in a manifest by content hash - already-ingested sources
     are skipped on the next run.
4. **Querying.** Ask infrastructure questions in plain English; the agent uses
   `get_database_schema` and `execute_sql_query` against the local Ollama model - no
   internet required for any of this.
5. **Adding more logs later.** Drop new files/archives into the same `LOG_DIR` and
   re-run discovery + ingestion. Known formats ingest immediately with no LLM call;
   only genuinely new commands/formats trigger a (local, free) learning step.

---

## 🔭 Designed to grow into

* **NetApp Harvest (the Harvest/Prometheus/Grafana stack).** If you start feeding in
  raw REST API responses Harvest collects from ONTAP, they'll typically arrive as JSON
  (often wrapped in a `"records"`-style envelope) - which the JSON-native path already
  understands with no extra work. If Harvest's payloads use a discriminator field name
  the agent doesn't already check (currently `op_type`, `event_type`, `type`,
  `category`, `object`, `action`, `operation`), just add it to the list in
  `_json_table_name()` in `server.py`.
* **ONTAP S3 object storage audit logs.** Bucket-level audit events are naturally
  record-shaped (one event per operation) and commonly exported as JSON - same path,
  same auto-extending schema, no special-casing needed for now.

These aren't wired up to actively poll any API yet - the agent only reads what's in
`LOG_DIR`. When you're ready to bring in live Harvest/S3-audit data, the simplest path
is to have whatever already exports/collects it drop its JSON output into `LOG_DIR`
(or a subfolder of it) and run ingestion as usual.

---

## 🛠️ Installation & Setup

### Prerequisites
* Docker & Docker Compose

### Deployment
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Ankiii/NetApp-MCP.git
   cd NetApp-MCP
   ```

2. **Configure your environment.** Create a `.env` file in the root directory:
   ```
   AGENT_MODEL=llama3.1
   PARSER_MODEL=qwen2.5-coder:7b
   LOG_DIR=/path/to/your/raw/logs
   ```
   A few optional tuning variables (CLI prompt pattern, archive size/depth limits) are
   documented with sensible defaults in the provided `.env` - you usually won't need to
   touch them.

3. **Build and start the environment:**
   ```bash
   docker-compose up -d --build
   ```
   The `ollama-init` service pulls both models on first run (needs internet, ~10GB
   total). This only happens once - the models are cached in the `ollama_data` volume
   for every future run, including fully air-gapped ones.

4. **Attach to the interactive agent console:**
   ```bash
   docker attach netapp_agent
   ```

5. **Discover and learn your log/command formats:**
   ```
   Master Agent > /run unsupervised_auto_discovery
   ```

6. **Build the database:**
   ```
   Master Agent > /run auto_ingest_directory
   ```

7. **Check status any time:**
   ```
   Master Agent > /run get_ingest_status
   ```

8. Once `universal_index.db` is built, the system can be moved to a fully air-gapped
   environment (export the `ollama/ollama` and `mcp_netapp_project-agent_client`
   images, plus the `db` and `ollama_data` volumes, and load them there). No further
   internet access is ever required, including for learning new formats going forward.

### Teaching a format manually
Paste a sample (ideally one command plus its output, for CLI-style logs) into the
agent and ask it to learn the format - it will call `learn_log_format` for you.

### Tuning the CLI prompt pattern
If your session logs use a different prompt style than `cluster1::> command`, set
`PROMPT_REGEX` in `.env` (capture group 1 must be the command text). Anything that
doesn't match any prompt line is treated as a single whole-file block instead, so
non-transcript logs (EMS events, `messages`-style files, etc.) keep working either way.

### Known limitations
* Command clustering is based on the literal command typed (e.g. `volume show` vs the
  abbreviated `vol show` are treated as two separate, separately-learned commands).
  This is usually harmless - it just costs one extra small learning step - but isn't
  true command-alias awareness.
* A single JSON source is parsed in memory as a whole (after the per-source size cap),
  rather than streamed - fine for typical log/export sizes, but very large single-file
  JSON dumps may need `MAX_EXTRACT_SIZE_MB` raised.
