# NetApp Model Context Protocol (MCP) Agent

An autonomous, LLM-powered Model Context Protocol (MCP) agent designed to dynamically discover, learn, and index NetApp log structures, allowing infrastructure administrators to query their data using natural language.

This project utilizes a **Two-Phase Architecture** designed specifically for high-security, air-gapped data centers. It leverages cloud-based AI (Google Gemini) for the initial unsupervised learning phase, and transitions to a completely offline, local LLM (Ollama / Llama 3.1) for secure, on-premises querying.

---

## 🚀 Key Features

* **Unsupervised Auto-Discovery:** Automatically scans directories for unrecognized log formats without manual schema definitions.
* **Dynamic Parser Generation:** Consults Cloud AI to dynamically write, test, and save Python parsing logic for new log types.
* **Air-Gap Ready:** Completely decoupled from the internet after the training phase. All querying is handled locally.
* **Natural Language to SQL:** Translates complex infrastructure questions into localized SQL queries against the generated universal index.
* **Standardized MCP Tooling:** Built on the emerging Model Context Protocol for easy integration into wider agentic workflows.

---

## 🏗️ Architecture Workflow

1. **Phase 1: Online Training Mode.** The Master Agent connects to the internet, scans raw log files, and uses Google Gemini (3.5-flash) to write custom parsers. It then ingests the logs into a structured SQLite database (`universal_index.db`).
2. **Phase 2: Air-Gapped Deployment.** The populated database, learned parsers, and Docker images are packaged.
3. **Phase 3: Offline Query Mode.** The packaged system is deployed in an internet-restricted environment. The agent uses a local Ollama instance to answer user queries based on the indexed data.

---

## 🛠️ Installation & Setup (Phase 1: Training)

During the initial setup, the agent requires internet access to communicate with the Google Gemini API.

### Prerequisites
* Docker & Docker Compose
* A Google Gemini API Key

### Deployment
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Ankiii/NetApp-MCP.git](https://github.com/Ankiii/NetApp-MCP.git)
   cd NetApp-MCP
   
### Instructions

1. Configure your environment:
Create a .env file in the root directory:


GEMINI_API_KEY=your_gemini_api_key_here
LOG_DIR=/path/to/your/raw/logs

2. Build and start the environment:

docker-compose up -d --build

3. Attach to the interactive agent console:

docker attach netapp_agent

4. Instruct the Master Agent to discover and learn your log formats:

/run unsupervised_auto_discovery

Note: Rate limits may apply depending on your Gemini API tier. The agent has built-in throttling to accommodate standard limits.

5. Build the Database:

Master Agent > /run auto_ingest_directory

6. Once the universal_index.db is built and the parsers are generated, the system is ready for offline use (export latest ollama/ollama and mcp_netapp_project-agent_client images and then load the same)


