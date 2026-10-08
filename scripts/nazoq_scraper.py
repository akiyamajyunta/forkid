"""nazoq.com からなぞなぞ（問題・ヒント・答え）を取得する。"""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from html import unescape
from typing import Iterable

BASE = "https://nazoq.com"
USER_AGENT = "kidgame-nazoq-import/1.0 (+educational; private use)"

ENTRY_LINK_RE = re.compile(
    r'href="(https://nazoq\.com/(?:easiest|easy|normal|hard|hardest)/Q\d+\.html)"'
)
ENTRY_ID_RE = re.compile(r"/Q(\d+)\.html")
TITLE_RE = re.compile(
    r'<h2 class="asset-name entry-title[^"]*">(.*?)</h2>',
    re.DOTALL | re.IGNORECASE,
)
PANEL_P_RE = re.compile(
    r'id="panel-(h|a)"[^>]*>.*?<p>(.*?)</p>',
    re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class NazoqItem:
    qid: str
    url: str
    question: str
    hint: str
    answer: str
    site_level: str


def _clean_html_fragment(text: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text)
    text = re.sub(r"[ \t\u3000]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def fetch_html(url: str, *, retries: int = 3, delay: float = 0.35) -> str:
    last_err: Exception | None = None
    for attempt in range(retries):
        if attempt:
            time.sleep(delay * (attempt + 1))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_err = exc
    raise RuntimeError(f"Failed to fetch {url}: {last_err}") from last_err


def list_page_urls(site_level: str) -> str:
    return f"{BASE}/{site_level}/all/"


def collect_entry_urls(list_html: str) -> list[str]:
    seen: set[str] = set()
    urls: list[str] = []
    for url in ENTRY_LINK_RE.findall(list_html):
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def parse_detail_page(html: str, url: str) -> NazoqItem:
    m_id = ENTRY_ID_RE.search(url)
    if not m_id:
        raise ValueError(f"Cannot parse question id from {url}")
    qid = f"nazoq_{m_id.group(1)}"

    m_title = TITLE_RE.search(html)
    if not m_title:
        raise ValueError(f"No question title in {url}")
    question = _clean_html_fragment(m_title.group(1))

    hint = ""
    answer = ""
    for panel, raw in PANEL_P_RE.findall(html):
        text = _clean_html_fragment(raw)
        if panel.lower() == "h":
            hint = text
        else:
            answer = text

    if not answer:
        raise ValueError(f"No answer in {url}")

    level_m = re.search(r"nazoq\.com/(easiest|easy|normal|hard|hardest)/", url)
    site_level = level_m.group(1) if level_m else "unknown"

    return NazoqItem(
        qid=qid,
        url=url,
        question=question,
        hint=hint or "もじの 音や 意味を くみ合わせて 考えてみて",
        answer=answer,
        site_level=site_level,
    )


def iter_items(
    urls: Iterable[str],
    *,
    delay: float = 0.35,
    max_count: int | None = None,
) -> list[NazoqItem]:
    items: list[NazoqItem] = []
    for i, url in enumerate(urls):
        if max_count is not None and len(items) >= max_count:
            break
        if i > 0:
            time.sleep(delay)
        html = fetch_html(url)
        try:
            items.append(parse_detail_page(html, url))
        except ValueError:
            continue
    return items
