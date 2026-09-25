import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from core.models import SourceEvidence
from core.config import REQUEST_TIMEOUT_SECONDS, MAX_PARALLEL_FETCHES


class HTMLTextExtractor(HTMLParser):
    """Extracts clean human-readable text from HTML, stripping non-content tags."""
    PAIRED_SKIP = {"script", "style", "svg", "noscript", "nav", "header", "footer", "head", "aside"}
    BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "li", "tr", "div", "article", "section"}

    def __init__(self):
        super().__init__()
        self.text_parts: List[str] = []
        self._skip_stack: List[str] = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self.PAIRED_SKIP:
            self._skip_stack.append(t)
        elif t in self.BLOCK_TAGS and not self._skip_stack:
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        t = tag.lower()
        if self._skip_stack and self._skip_stack[-1] == t:
            self._skip_stack.pop()
        elif t in self._skip_stack:
            while self._skip_stack and self._skip_stack[-1] != t:
                self._skip_stack.pop()
            if self._skip_stack:
                self._skip_stack.pop()
        elif t in self.BLOCK_TAGS and not self._skip_stack:
            self.text_parts.append("\n")

    def handle_data(self, data):
        if not self._skip_stack:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned + " ")

    def get_text(self) -> str:
        raw_text = "".join(self.text_parts)
        cleaned = re.sub(r"[ \t]+", " ", raw_text)
        cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
        return cleaned.strip()


def fetch_page_content(url: str, max_chars: int = 8000) -> str:
    """Fetch live web page and extract clean article text."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            content_type = response.headers.get("Content-Type", "")
            if "pdf" in content_type.lower():
                return "[PDF content skipped for text processing]"
            raw_html = response.read(250_000).decode("utf-8", errors="replace")

        parser = HTMLTextExtractor()
        parser.feed(raw_html)
        text = parser.get_text()
        return text[:max_chars]
    except Exception as e:
        return f"[Failed to fetch page: {type(e).__name__}]"


class WebPageFetcher:
    """Parallel page fetcher for real live web evidence retrieval."""
    def __init__(self, max_workers: int = MAX_PARALLEL_FETCHES):
        self.max_workers = max_workers

    def fetch_single(self, evidence: SourceEvidence) -> SourceEvidence:
        """Fetch full text for a single SourceEvidence object."""
        if not evidence.full_text or evidence.full_text.startswith("[Failed"):
            evidence.full_text = fetch_page_content(evidence.url)
        return evidence

    def fetch_parallel(self, evidence_list: List[SourceEvidence]) -> List[SourceEvidence]:
        """Fetch multiple URLs concurrently via ThreadPoolExecutor."""
        if not evidence_list:
            return []

        results: List[SourceEvidence] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_ev = {executor.submit(self.fetch_single, ev): ev for ev in evidence_list}
            for future in as_completed(future_to_ev):
                try:
                    res = future.result()
                    results.append(res)
                except Exception:
                    ev = future_to_ev[future]
                    ev.full_text = "[Fetch error]"
                    results.append(ev)

        # Preserve original ordering
        url_order = {ev.url: idx for idx, ev in enumerate(evidence_list)}
        results.sort(key=lambda x: url_order.get(x.url, 999))
        return results
