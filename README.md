# LangGraph MCP Agent

An agentic AI assistant built with LangGraph and the Model Context Protocol (MCP). The agent has access to five tools — filesystem access, weather lookup, web search, a RAG-based knowledge base search, and web scraping — and decides for itself which tool(s) a request needs, chaining multiple tools together when necessary.


![Architecture diagram](docs/architecture.png)

## Architecture

The project is split into three independently-run blocks, each its own process:

```
User
 │
 ▼
React Frontend (frontend/) ── talks to ──▶ FastAPI Backend (backend/api.py)
                                                │
                                                ▼
                                        LangGraph Agent (backend/graph.py)
                                                │
                                    ┌───────────┴───────────┐
                                    │                       │
                              Agent node               Tool node
                         (LLM decides: tool           (executes the
                          or answer?)                  selected tool)
                                    │                       │
                                    └──────── loop ─────────┘
                                                │
                                                ▼
                                   MCP Server (mcp_tools/server.py)
                                   ── list_directory, get_weather,
                                      web_search, rag_search,
                                      scrape_webpage
```

- **`mcp_tools/`** — one consolidated MCP server exposing all 5 tools, run as its own long-lived HTTP process (streamable-http transport, port 8002). Fully decoupled from the backend — restarting or crashing one does not affect the other.
- **`backend/`** — the FastAPI API, the LangGraph agent definition, thread/document management.
- **`frontend/`** — a React + Vite single-page app (landing screen, sidebar of saved chats, chat view, document upload, Insights panel).
- **`rag/`** — shared library used by both the global knowledge base and per-chat document uploads (PDF/diagram extraction, chunking, embeddings, vector store).

**Graph state**: a growing list of messages, persisted per conversation via a LangGraph SQLite checkpointer (`checkpoints.db`), keyed by `thread_id` — genuinely resumable across backend restarts, not just within one session.

**Routing**: after each agent turn, a conditional edge checks whether the LLM's response includes a tool call. If yes, execution goes to the tool node, the result is added to state, and control returns to the agent — which may call another tool or give a final answer. If no, the turn ends. This loop is what enables multi-tool chaining (e.g., web search → scrape a result page → summarize).

## Two knowledge sources

1. **Global knowledge base** — documents dropped into `data/documents/` and indexed once via `python ingest_documents.py`. Persistent, shared across every conversation, searched via the `rag_search` tool (the agent decides when to use it).
2. **Per-chat uploaded documents** — uploaded live through the UI's 📎 button, scoped to that one conversation only. Persistent on disk (`thread_vectors/{thread_id}/`, `thread_images/{thread_id}/`) so they survive a backend restart, but fully deleted the moment that specific chat is deleted. Retrieval for these runs automatically on every turn (not agent-chosen), injected as context — with the model required to confirm (`[FROM_DOCUMENT]`) it actually used that context before any citation is shown, since similarity scores alone aren't reliable enough to trust blindly.

If the knowledge base (global or per-chat) returns nothing genuinely relevant, the agent falls back to `web_search` automatically, and makes clear in its answer that the information came from the web, not the documents.

## Setup

### 1. Install dependencies

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt
```

Frontend (requires Node.js):
```bash
cd frontend
npm install
```

### 2. Environment variables

Copy `.env.example` to `.env` and fill in real values:

```
GROQ_API_KEY=your_groq_key_here
OPENWEATHER_API_KEY=your_openweathermap_key_here
TAVILY_API_KEY=your_tavily_key_here
MCP_HOST=127.0.0.1
MCP_PORT=8002
```

- **Groq** — https://console.groq.com/keys (LLM: `openai/gpt-oss-120b`)
- **OpenWeatherMap** — https://openweathermap.org/api (free tier; new keys can take up to ~2 hours to activate)
- **Tavily** — https://tavily.com (free tier, 1,000 searches/month)
- **MCP_HOST** — set to `0.0.0.0` instead of `127.0.0.1` if you want the MCP server reachable by another device on your local network (e.g., for a shared demo). No authentication is implemented on the MCP server, so only do this on a trusted network.

### 3. Ollama (for embeddings and diagram captioning)

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5vl:7b
```
Ollama must be running locally (`ollama list` to confirm) before starting the backend.

## Running it

Three separate terminals, in this order:

**Terminal 1 — MCP server:**
```bash
python mcp_tools/server.py
```

**Terminal 2 — Backend:**
```bash
uvicorn backend.api:app --port 8001
```

**Terminal 3 — Frontend:**
```bash
cd frontend
npm run dev
```
Open the printed local URL (typically `http://localhost:5173`).

A simpler terminal-only chat is also available for quick testing (no upload, uses only the global knowledge base):
```bash
python app.py
```

## Ingesting documents into the global knowledge base

Drop files (`.pdf`, `.md`, `.txt`, `.docx`) into `data/documents/`, then run:
```bash
python ingest_documents.py
```
For uploading documents into a single conversation instead, use the 📎 button in the UI — no script needed, indexed immediately.

## Example queries

- `List all files inside ./data/documents`
- `What's the weather in Bangalore?` → `How about tomorrow?` (tests conversation memory; weather only returns current conditions, so the follow-up correctly falls back to `web_search`)
- `Search the web for the latest developments in LangGraph`
- `According to our documents, what is discussed about laser diodes?`
- `Read this page and tell me the key points: https://en.wikipedia.org/wiki/Optical_fiber`
- `Search the web for the latest LangGraph release and scrape the official release page to summarize the changes` (tests multi-tool chaining)
- `Hi, what can you do?` (tests no-tool-needed routing)
- `List files in /some/nonexistent/path` (tests error handling)
- Upload a PDF with a table, then ask `give me the table` (tests verbatim table reproduction)
- Ask something unrelated to an uploaded document (e.g., a finance question in a chat with a DSA PDF attached) — should fall back to `web_search` rather than answering from irrelevant document content

## Logging and observability

All MCP servers and the agent log to both the console (stderr, never stdout — MCP's stdio-adjacent protocol details require this) and `logs/agent.log`. Each entry records the user request, which tool was selected (with arguments), success/failure, retrieval similarity scores, and any errors — no API keys or secrets are ever logged. The UI's "🔍 Insights" button shows the most recent log lines live, and each AI response shows which tools were used for that turn.

## Testing

Start the MCP server first (`python mcp_tools/server.py`), then in a separate terminal:
```bash
pytest -v
```
13 tests across all 5 tools, calling the running MCP server over the real protocol (not mocked), covering both success paths and required error cases: nonexistent directory, path outside the allowed root, invalid URL format, unreachable domain, and RAG queries with no relevant results.

## Known limitations

- The weather tool only returns **current** conditions, not a multi-day forecast — the agent falls back to `web_search` for forecast-type follow-ups.
- Groq's free tier enforces an 8,000 tokens/minute limit. Conversation history sent per call is trimmed by actual character budget (not just message count) and tool result sizes are capped to stay within this — heavy multi-tool-chaining conversations can still occasionally hit the limit, in which case one automatic retry is attempted before surfacing an error.
- OpenWeatherMap free-tier keys can take time to activate after signup; a `401 Invalid API key` error immediately after creating a key does not necessarily mean the key is wrong.
- RAG diagram extraction crops real embedded images directly, but falls back to rendering the entire page when a figure is referenced with no detectable embedded image (common for vector-drawn diagrams) — less precisely cropped, but avoids showing nothing or hallucinating a description.
- The MCP server has no authentication. Fine for local use or a trusted local-network demo; not suitable for exposing on the open internet as-is.
- Relevance for per-chat uploaded documents uses a similarity threshold as a coarse first filter, plus a second, more reliable check where the model itself must confirm (via an explicit tag) that it genuinely used the retrieved content before any citation is shown — this was added after finding threshold-only filtering could still occasionally surface irrelevant chunks with a deceptively high score.