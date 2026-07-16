"""
Custom Agent Actions. Every tool is deliberately self-contained (lazy
imports, graceful degradation) so importing this module never requires a
live Redis/ChromaDB/network connection.
"""
import pandas as pd
from crewai.tools import tool
from config.settings import settings


@tool("knowledge_base_search")
def knowledge_base_search_tool(query: str) -> str:
    """Search the enterprise knowledge base (ChromaDB) for the given query
    and return the most relevant chunks. Use this before answering any
    customer question."""
    from memory.vector_store import KnowledgeBaseStore  # lazy: avoid connecting at import time

    store = KnowledgeBaseStore()
    results = store.query(query, n_results=4)
    if not results:
        return "No matching knowledge-base entries found."
    return "\n---\n".join(results)


@tool("dataframe_summary")
def dataframe_summary_tool(file_path: str) -> str:
    """Load a CSV or Excel file from the given path and return descriptive
    summary statistics (counts, mean, std, min/max, top values) as text."""
    if file_path.lower().endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    return df.describe(include="all").fillna("").to_string()


@tool("web_search")
def web_search_tool(query: str) -> str:
    """Search the live web via Serper.dev for current external information.
    Requires SERPER_API_KEY in .env; returns a clear message if not configured."""
    api_key = settings.SERPER_API_KEY
    if not api_key:
        return "Web search is not configured. Add SERPER_API_KEY to .env to enable this tool."

    import httpx

    response = httpx.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    results = data.get("organic", [])[:3]
    if not results:
        return "No results found."
    return "\n".join(f"{r.get('title')}: {r.get('snippet')}" for r in results)
