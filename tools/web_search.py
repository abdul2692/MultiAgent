"""
Web Search Tool for Multi-Agent Research Assistant.
Zero Budget: Uses DuckDuckGo HTML scraping and Wikipedia search fallback.
No paid APIs, no credit cards, zero rate limits.
"""
import os
import sys
import logging
import urllib.parse
import re
from typing import List
import requests
from bs4 import BeautifulSoup

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.schemas import WebSearchResult

logger = logging.getLogger("multi_agent.tools.web_search")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def _search_ddg_html(query: str, max_results: int = 4) -> List[WebSearchResult]:
    """Scrapes DuckDuckGo HTML version directly."""
    results: List[WebSearchResult] = []
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code != 200:
        return results
        
    soup = BeautifulSoup(response.text, "html.parser")
    result_divs = soup.find_all("div", class_="result")
    
    for div in result_divs:
        if len(results) >= max_results:
            break
            
        title_tag = div.find("a", class_="result__url") or div.find("a", class_="result__title")
        snippet_tag = div.find("a", class_="result__snippet")
        
        if not title_tag:
            continue
            
        title = title_tag.get_text(strip=True)
        raw_href = title_tag.get("href", "")
        
        # Unpack DuckDuckGo redirect link e.g. //duckduckgo.com/l/?uddg=https...
        clean_url = raw_href
        if "uddg=" in raw_href:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
            if "uddg" in parsed:
                clean_url = parsed["uddg"][0]
        elif raw_href.startswith("//"):
            clean_url = "https:" + raw_href
            
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else "No snippet available."
        
        if clean_url and "duckduckgo.com" not in clean_url:
            results.append(
                WebSearchResult(
                    title=title,
                    url=clean_url,
                    snippet=snippet
                )
            )
            
    return results

def _search_wikipedia(query: str, max_results: int = 2) -> List[WebSearchResult]:
    """Queries free open Wikipedia REST API as an authoritative backup."""
    results: List[WebSearchResult] = []
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": max_results
        }
        resp = requests.get(url, params=params, headers=HEADERS, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            search_items = data.get("query", {}).get("search", [])
            for item in search_items:
                title = item.get("title", "")
                snippet_html = item.get("snippet", "")
                clean_snippet = re.sub(r"<[^>]+>", "", snippet_html)
                page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                results.append(
                    WebSearchResult(
                        title=f"{title} (Wikipedia)",
                        url=page_url,
                        snippet=clean_snippet
                    )
                )
    except Exception as e:
        logger.warning(f"Wikipedia fallback failed: {e}")
        
    return results

def search_web(query: str, max_results: int = 4) -> List[WebSearchResult]:
    """
    Unified free web search.
    Tries DuckDuckGo HTML first; if sparse, supplements with Wikipedia.
    """
    logger.info(f"Initiating free web search for '{query}'...")
    results: List[WebSearchResult] = []
    
    try:
        results = _search_ddg_html(query, max_results=max_results)
    except Exception as e:
        logger.warning(f"DuckDuckGo search encountered an issue: {e}")
        
    # If results are sparse or zero, supplement with Wikipedia
    if len(results) < max_results:
        wiki_results = _search_wikipedia(query, max_results=max_results - len(results))
        results.extend(wiki_results)
        
    logger.info(f"Collected total of {len(results)} verified web sources.")
    return results

if __name__ == "__main__":
    print("Testing Unified Free Web Search Tool...")
    hits = search_web("Solid-state battery in aviation", max_results=3)
    for idx, hit in enumerate(hits, 1):
        print(f"\n[{idx}] {hit.title}")
        print(f"    URL: {hit.url}")
        print(f"    Snippet: {hit.snippet[:150]}...")
