"""
Live Online Web Search Engine for Auspify AI Chatbot.

Enables the chatbot to fetch real-time data from DuckDuckGo Instant Answers
and Wikipedia API using standard library urllib with zero external dependencies.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 AuspifyBot/1.0"


class WebSearchEngine:
    """Provides live online knowledge retrieval and web searching."""

    def __init__(self, timeout: int = 5):
        """Initialize search engine with request timeout in seconds."""
        self.timeout = timeout

    def clean_query(self, text: str) -> str:
        """Strip conversational prefixes to extract search keywords."""
        cleaned = text.strip()
        prefixes = [
            r"^(search online for|search the web for|search online|search web for|search for|search|google)\s+",
            r"^(online data about|online data for|live data for|latest info on|latest news on|latest news about)\s+",
            r"^(can you search for|please search for|look up|find information on|find info on)\s+",
            r"^(who is|who was|what is|what was|tell me about)\s+",
        ]
        for p in prefixes:
            cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned.rstrip("?.!")

    def search_duckduckgo(self, query: str) -> Optional[Dict[str, str]]:
        """Query DuckDuckGo Instant Answer API for instant summaries."""
        if not query:
            return None

        clean_q = self.clean_query(query)
        if not clean_q:
            clean_q = query

        encoded = urllib.parse.quote(clean_q)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    abstract = data.get("AbstractText", "").strip()
                    source_url = data.get("AbstractURL", "")
                    heading = data.get("Heading", clean_q)

                    if abstract:
                        return {
                            "title": heading,
                            "summary": abstract,
                            "source": source_url or "DuckDuckGo",
                            "engine": "DuckDuckGo Instant Answer",
                        }

                    # Check RelatedTopics if direct abstract is empty
                    related = data.get("RelatedTopics", [])
                    for item in related:
                        if isinstance(item, dict) and item.get("Text"):
                            return {
                                "title": heading,
                                "summary": item["Text"].strip(),
                                "source": item.get("FirstURL", "DuckDuckGo"),
                                "engine": "DuckDuckGo Related Topics",
                            }
        except Exception:
            pass

        return None

    def search_wikipedia(self, query: str) -> Optional[Dict[str, str]]:
        """Query Wikipedia REST/action API for authoritative encyclopedic extracts."""
        clean_q = self.clean_query(query)
        if not clean_q:
            clean_q = query

        encoded = urllib.parse.quote(clean_q)
        # Search query first
        search_url = (
            f"https://en.wikipedia.org/w/api.php?action=query&list=search"
            f"&srsearch={encoded}&utf8=&format=json"
        )
        req = urllib.request.Request(search_url, headers={"User-Agent": USER_AGENT})

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    search_data = json.loads(resp.read().decode("utf-8"))
                    results = search_data.get("query", {}).get("search", [])
                    if not results:
                        return None

                    top_page_title = results[0]["title"]

                    # Fetch page summary extract
                    extract_url = (
                        f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts"
                        f"&exintro=1&explaintext=1&titles={urllib.parse.quote(top_page_title)}&format=json"
                    )
                    req_extract = urllib.request.Request(extract_url, headers={"User-Agent": USER_AGENT})
                    with urllib.request.urlopen(req_extract, timeout=self.timeout) as ext_resp:
                        if ext_resp.status == 200:
                            ext_data = json.loads(ext_resp.read().decode("utf-8"))
                            pages = ext_data.get("query", {}).get("pages", {})
                            for page_id, page_info in pages.items():
                                if page_id != "-1" and page_info.get("extract"):
                                    extract_text = page_info["extract"].strip()
                                    # Limit extract to first 2-3 paragraphs / 600 characters
                                    if len(extract_text) > 600:
                                        extract_text = extract_text[:600].rsplit(".", 1)[0] + "."

                                    page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(top_page_title.replace(' ', '_'))}"
                                    return {
                                        "title": top_page_title,
                                        "summary": extract_text,
                                        "source": page_url,
                                        "engine": "Wikipedia",
                                    }
        except Exception:
            pass

        return None

    def search_online(self, query: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Search the web across DuckDuckGo and Wikipedia.

        Returns:
            Tuple of (summary_text, source_url, engine_name).
        """
        # 1. Try DuckDuckGo
        ddg_res = self.search_duckduckgo(query)
        if ddg_res and len(ddg_res.get("summary", "")) > 40:
            return ddg_res["summary"], ddg_res["source"], ddg_res["engine"]

        # 2. Try Wikipedia
        wiki_res = self.search_wikipedia(query)
        if wiki_res and wiki_res.get("summary"):
            return wiki_res["summary"], wiki_res["source"], wiki_res["engine"]

        # Fallback to DuckDuckGo if it had any snippet
        if ddg_res and ddg_res.get("summary"):
            return ddg_res["summary"], ddg_res["source"], ddg_res["engine"]

        return None, None, None
