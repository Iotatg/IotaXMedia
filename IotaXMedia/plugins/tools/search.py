# Authored By Iota Coders © 2025-2026
# SPDX-License-Identifier: MIT
"""
SearXNG real-time web search for the Iota AI chatbot.

Queries a self-hosted SearXNG instance's JSON API. When SEARXNG_URL is empty
the search stack is disabled and chat works as before.

Design goals (systematic, accurate, robust):
  • Multi-query enrichment — one user question is expanded into a few focused
    queries (original + year-aware + keyword variant) so recall stays high.
  • Aggregation + dedupe — results from all queries are merged, near-duplicate
    URLs / titles dropped, and ranked by term overlap with the question.
  • Graceful — any failure returns []; search never raises or blocks chat.
"""
import logging
import re
from datetime import datetime

import httpx

from config import SEARXNG_MAX_RESULTS, SEARXNG_TIMEOUT, SEARXNG_URL

logger = logging.getLogger(__name__)

SEARCH_ENABLED = bool(SEARXNG_URL)



_search_toggle = True


def set_search_on(value: bool) -> None:
    """Owner flips web search on/off at runtime via /searching on|off."""
    global _search_toggle
    _search_toggle = bool(value)


_RESULT_MAX_CONTENT = 320
_MAX_QUERIES = 3

_CURRENT_YEAR = str(datetime.now().year)

_STOPWORDS = {
    "kya", "ka", "ki", "konsa", "kaunsa", "kon", "kahan", "kab", "kaise",
    "kyu", "what", "who", "when", "where", "which", "why", "how", "is",
    "are", "was", "were", "the", "a", "an", "of", "for", "to", "in", "on",
    "at", "me", "my", "hai", "hain", "ho", "tell", "about", "please",
    "can", "you", "do", "does", "did",
}


def _norm_url(u: str) -> str:
    """Normalise a URL for dedupe: scheme-less, no fragment/query, no trailing slash."""
    u = u.strip().split("#", 1)[0].split("?", 1)[0]
    u = re.sub(r"^https?://", "", u, flags=re.IGNORECASE)
    u = re.sub(r"^www\.", "", u, flags=re.IGNORECASE)
    return u.rstrip("/").lower()


def _build_queries(text: str) -> list:
    """Expand one question into up to _MAX_QUERIES focused queries."""
    base = text.strip()
    if not base:
        return []
    queries: list = [base]
    has_year = bool(re.search(r"\b20[12]\d\b", base))
    if not has_year and len(base.split()) <= 12:
        queries.append(f"{base} {_CURRENT_YEAR}")
    toks = [w for w in re.findall(r"[A-Za-z0-9]+", base.lower()) if w not in _STOPWORDS]
    if toks:
        kw = " ".join(toks[:8])
        if kw and kw.lower() != base.lower():
            queries.append(kw)
    seen = set()
    out = []
    for q in queries:
        q = q.strip()
        if q and q.lower() not in seen:
            seen.add(q.lower())
            out.append(q)
    return out[:_MAX_QUERIES]


def _first_str(raw: dict, *keys: str) -> str:
    """Return the first present field coerced to str (bools excluded)."""
    for k in keys:
        v = raw.get(k)
        if v is not None and not isinstance(v, bool):
            return str(v)
    return ""


async def web_search(query: str, max_results: int = SEARXNG_MAX_RESULTS) -> list:
    if not search_enabled():
        return []
    if not query or not query.strip():
        return []
    url = SEARXNG_URL.rstrip("/") + "/search"
    params = {"q": query.strip(), "format": "json"}
    try:
        async with httpx.AsyncClient(
            timeout=max(3, int(SEARXNG_TIMEOUT or 10)), verify=False
        ) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                logger.warning("SearXNG HTTP %s for %r", resp.status_code, query[:60])
                return []
            data = resp.json()
            if not isinstance(data, dict):
                logger.warning("SearXNG returned non-dict JSON for %r", query[:60])
                return []
            results = data.get("results")
            if not isinstance(results, list):
                logger.warning("SearXNG results not a list for %r", query[:60])
                return []
    except Exception as e:
        logger.warning("SearXNG search failed for %r: %s", query[:60], e)
        return []
    out = []
    for raw in results[:max_results]:
        if not isinstance(raw, dict):
            continue
        title = _first_str(raw, "title").strip()
        url = _first_str(raw, "url").strip()
        content = _first_str(raw, "content", "description").strip()
        if len(content) > _RESULT_MAX_CONTENT:
            content = content[:_RESULT_MAX_CONTENT] + "…"
        out.append({"title": title, "url": url, "content": content})
    return out


def _aggregate(per_query: list, question: str, top_n: int) -> list:
    """Merge results from multiple queries, dedupe, rank by term overlap."""
    seen_urls = set()
    seen_titles = set()
    merged = []
    q_terms = {t for t in re.findall(r"[A-Za-z0-9]+", question.lower()) if len(t) > 2}
    for res in per_query:
        for r in res:
            u = r.get("url", "")
            nu = _norm_url(u)
            t = (r.get("title", "") or "").strip().lower()
            if nu and nu in seen_urls:
                continue
            if t and t in seen_titles:
                continue
            if nu:
                seen_urls.add(nu)
            if t:
                seen_titles.add(t)
            blob = f"{r.get('title','')} {r.get('content','')}".lower()
            score = sum(1 for term in q_terms if term in blob)
            merged.append((score, r))
    merged.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in merged[:top_n]]


async def format_results(results: list) -> str:
    if not results:
        return ""
    lines = ["[SEARCH RESULTS]"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r.get('title', '')} — {r.get('url', '')}")
        snippet = r.get("content", "")
        if snippet:
            lines.append(f"   {snippet}")
    lines.append("[END SEARCH RESULTS]")
    return "\n".join(lines)


async def search_summary(query: str, max_results: int = SEARXNG_MAX_RESULTS) -> str:
    if not search_enabled():
        return ""
    if not query or not query.strip():
        return ""
    queries = _build_queries(query)
    per_query = []
    per_cap = min(30, max(3, max_results))
    for q in queries:
        res = await web_search(q, max_results=per_cap)
        if res:
            per_query.append(res)
    if not per_query:
        return ""
    ranked = _aggregate(per_query, query, top_n=max_results)
    return await format_results(ranked)


def search_enabled() -> bool:
    return bool(SEARCH_ENABLED and _search_toggle)
