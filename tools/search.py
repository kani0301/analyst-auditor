import re
import json
import urllib.request
import urllib.parse
from html import unescape
from typing import List, Dict, Any
from core.models import SourceEvidence
from core.config import REQUEST_TIMEOUT_SECONDS, MAX_SEARCH_RESULTS_PER_QUERY


def sanitize_search_query(q: str) -> str:
    """Strip punctuation and stop words to formulate high-density keyword queries."""
    clean = re.sub(r"[?!,'\"():;]", " ", q)
    stop = {"when", "was", "who", "are", "its", "what", "their", "under", "which", "following", "compare"}
    words = [w for w in clean.split() if w.lower() not in stop]
    return " ".join(words[:7]) if words else q


def search_duckduckgo_lite(query: str, max_results: int = MAX_SEARCH_RESULTS_PER_QUERY) -> List[SourceEvidence]:
    """Execute live search against DuckDuckGo Lite."""
    cleaned_query = sanitize_search_query(query)
    data = urllib.parse.urlencode({"q": cleaned_query}).encode("utf-8")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    results = []
    try:
        req = urllib.request.Request("https://lite.duckduckgo.com/lite/", data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_html = response.read().decode("utf-8", errors="replace")

        # Parse links and snippets
        matches = re.findall(
            r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*class=[\'"]result-link[\'"][^>]*>(.*?)</a>.*?(?:<td[^>]+class=[\'"]result-snippet[\'"][^>]*>(.*?)</td>)?',
            raw_html,
            re.DOTALL
        )

        seen_domains = set()
        for m in matches:
            url = m[0].strip()
            if not url.startswith("http"):
                continue

            domain = urllib.parse.urlparse(url).netloc
            title = unescape(re.sub(r"<[^>]+>", "", m[1])).strip()
            snippet = unescape(re.sub(r"<[^>]+>", "", m[2])).strip() if len(m) > 2 and m[2] else ""

            if domain not in seen_domains:
                seen_domains.add(domain)
                results.append(SourceEvidence(
                    url=url,
                    title=title,
                    snippet=snippet,
                    domain=domain
                ))
            if len(results) >= max_results:
                break
    except Exception:
        pass

    return results


def search_wikipedia_fulltext(query: str, max_results: int = 3) -> List[SourceEvidence]:
    """Live search using Wikipedia Full-Text Search API."""
    cleaned = sanitize_search_query(query)
    results = []
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote_plus(cleaned)}&utf8=&format=json"
        req = urllib.request.Request(url, headers={"User-Agent": "ResearchAgent/1.0 (academic research)"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
            items = data.get("query", {}).get("search", [])
            for item in items[:max_results]:
                title = item["title"]
                slug = urllib.parse.quote(title.replace(" ", "_"))
                page_url = f"https://en.wikipedia.org/wiki/{slug}"
                clean_snip = unescape(re.sub(r"<[^>]+>", "", item.get("snippet", ""))).strip()
                results.append(SourceEvidence(
                    url=page_url,
                    title=f"{title} - Wikipedia",
                    snippet=clean_snip,
                    domain="en.wikipedia.org"
                ))
    except Exception:
        pass
    return results


def search_wikipedia_opensearch(query: str, max_results: int = 2) -> List[SourceEvidence]:
    """Fallback search using Wikipedia OpenSearch API."""
    results = []
    try:
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote_plus(query)}&limit={max_results}&namespace=0&format=json"
        req = urllib.request.Request(wiki_url, headers={"User-Agent": "ResearchAgent/1.0 (academic research)"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
            if len(data) >= 4:
                titles = data[1]
                snippets = data[2]
                urls = data[3]
                for title, snip, u in zip(titles, snippets, urls):
                    results.append(SourceEvidence(
                        url=u,
                        title=title,
                        snippet=snip,
                        domain="en.wikipedia.org"
                    ))
    except Exception:
        pass
    return results


class WebSearchTool:
    """Multi-tier search tool with live DuckDuckGo and Wikipedia full-text API."""
    def __init__(self):
        pass

    def search(self, query: str, max_results: int = MAX_SEARCH_RESULTS_PER_QUERY) -> List[SourceEvidence]:
        # Tier 1: DuckDuckGo Lite
        results = search_duckduckgo_lite(query, max_results=max_results)

        # Tier 2: Wikipedia Full-Text Search if DDG yielded fewer than 2 results
        if len(results) < 2:
            wiki_results = search_wikipedia_fulltext(query, max_results=max_results)
            seen_urls = set(r.url for r in results)
            for wr in wiki_results:
                if wr.url not in seen_urls:
                    seen_urls.add(wr.url)
                    results.append(wr)

        # Tier 3: Wikipedia OpenSearch on first keywords
        if not results:
            first_term = query.split()[0] if query.split() else query
            results = search_wikipedia_opensearch(first_term, max_results=max_results)

        return results[:max_results]
