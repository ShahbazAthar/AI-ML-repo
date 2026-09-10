# LangGraph MCP Agent

An agentic AI assistant built with LangGraph and the Model Context Protocol (MCP). The agent has access to five tools — filesystem access, weather lookup, web search, a RAG-based knowledge base search, and web scraping — and decides for itself which tool(s) a request needs, chaining multiple tools together when necessary.

The RAG tool ingests documents into a local vector store and retrieves relevant chunks to answer knowledge-base questions, cited by source document.

![Architecture diagram](docs/architecture.png)


## Architecture

The diagram above shows the overall flow: the user interacts through a terminal or web UI, requests go through a FastAPI backend to the LangGraph agent, which decides whether a tool is needed and, if so, routes to a tool node that calls the appropriate MCP server.


Each tool is a **separate MCP server**, launched over stdio by the agent at startup. The agent connects to each server independently — if one server fails to start, the others still work; the failure is logged and that tool simply isn't available for that session.

**Graph state**: a single growing list of messages (`MessagesState`) — human messages, AI responses, and tool call/result messages — persisted per conversation via a LangGraph SQLite checkpointer (`checkpoints.db`), keyed by `thread_id`. This is what makes conversations resumable across restarts and lets a "how about tomorrow?" follow-up correctly refer back to an earlier "what's the weather in Bangalore?" question.

**Routing**: after each agent turn, a conditional edge checks whether the LLM's response includes a tool call. If yes, execution goes to the tool node, the result is added to state, and control returns to the agent — which may call another tool or give a final answer. If no, the conversation ends for that turn. This loop is what enables multi-tool chaining (e.g., web search → scrape a result page → summarize).

## Setup

### 1. Clone and install

python -m venv venv
.\venv\Scripts\Activate.ps1 # Windows
pip install -r requirements.txt


### 2. Environment variables

Copy `.env.example` to `.env` and fill in real values:

GROQ_API_KEY=your_groq_key_here
OPENWEATHER_API_KEY=your_openweathermap_key_here
TAVILY_API_KEY=your_tavily_key_here


- **Groq** — https://console.groq.com/keys (used for the LLM itself, `openai/gpt-oss-120b`)
- **OpenWeatherMap** — https://openweathermap.org/api (free tier; new keys can take up to ~2 hours to activate)
- **Tavily** — https://tavily.com (free tier, 1,000 searches/month)

### 3. Ollama (for embeddings)

The RAG tool uses a local Ollama model for embeddings:

ollama pull nomic-embed-text

Ollama must be running locally (`ollama list` to confirm) before starting the agent.

## Running it

**MCP servers do not need to be started manually.** The agent (`graph.py`) launches each one automatically as a subprocess when it starts.

**Terminal chat** (simplest way to interact):

python app.py

Leave the thread ID prompt blank for a new conversation, or paste a previous thread ID to resume one.

**Web UI + API** (chat sidebar, live document upload, source citations):

uvicorn api:app --reload --port 8001

Then open `http://127.0.0.1:8001/ui/` in a browser.

## Ingesting documents into the RAG system

Two ways:
- **Batch**: drop files (`.pdf`, `.md`, `.txt`, `.docx`) into `data/documents/`, then run:

python ingest_documents.py

- **Live, via the web UI**: click the 📎 icon and upload a document mid-chat — it's indexed immediately and searchable right away, no restart needed.

## Example queries

- `List all files inside ./data/documents`
- `What's the weather in Bangalore?` → `How about tomorrow?` (tests conversation memory)
- `Search the web for the latest developments in LangGraph`
- `According to our documents, what is discussed about laser diodes?`
- `Read this page and tell me the key points: https://en.wikipedia.org/wiki/Optical_fiber`
- `Search the web for the latest LangGraph release and scrape the official release page to summarize the changes` (tests multi-tool chaining)
- `Hi, what can you do?` (tests no-tool-needed routing)
- `List files in /some/nonexistent/path` (tests error handling)

## Logging

All MCP servers and the agent node log to both the console (stderr) and `logs/agent.log`. Each entry records the user request, which tool was selected (with arguments), success/failure, and any errors. No API keys or secrets are logged.

**Important implementation note**: MCP servers using stdio transport communicate over stdout — any `print()` statement inside a server corrupts the protocol stream. All logging in this project deliberately writes to stderr, never stdout.

## Testing

pytest -v


13 tests across all 5 tools, calling each MCP server over the real protocol (not mocked), covering both success paths and the required error cases: nonexistent directory, path outside the allowed root, invalid URL format, unreachable domain, and RAG queries with no relevant results.

## Known limitations

- The weather tool only returns **current** conditions, not a real multi-day forecast — follow-up questions like "how about tomorrow?" are answered by falling back to the web search tool instead, which the agent does automatically.
- The RAG tool's document chunking is paragraph-based and text-only — it does not extract or describe embedded diagrams/images within documents.
- OpenWeatherMap free-tier keys can take time to activate after signup; a `401 Invalid API key` error immediately after creating a key does not necessarily mean the key is wrong.
- The agent currently answers with general knowledge (falling back from tool results) rather than a hard refusal when no tool result is relevant — this is a deliberate design choice, not a bug, matching how general-purpose assistants like ChatGPT behave.

