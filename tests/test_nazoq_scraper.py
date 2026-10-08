from __future__ import annotations

from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from nazoq_scraper import collect_entry_urls, parse_detail_page

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "nazoq_detail_sample.html"
LIST_SNIPPET = (
    '<a href="https://nazoq.com/easy/Q035154.html">Q1</a>'
    '<a href="https://nazoq.com/easy/Q035154.html">dup</a>'
    '<a href="https://nazoq.com/easy/Q035145.html">Q2</a>'
)


def test_collect_entry_urls_dedupes() -> None:
    urls = collect_entry_urls(LIST_SNIPPET)
    assert urls == [
        "https://nazoq.com/easy/Q035154.html",
        "https://nazoq.com/easy/Q035145.html",
    ]


def test_parse_detail_page() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    item = parse_detail_page(html, "https://nazoq.com/easy/Q035154.html")
    assert item.qid == "nazoq_035154"
    assert "さいてい" in item.question
    assert "ふかく" in item.hint and "かんがえる" in item.hint
    assert item.answer == "「と」"
    assert item.site_level == "easy"
