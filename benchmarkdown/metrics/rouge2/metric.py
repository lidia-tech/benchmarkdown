"""Bigram overlap (ROUGE-2 style) quality metric.

Compares extracted text against ground truth using word bigram multiset
overlap. Produces recall, precision, and F1 scores in [0, 1].

No external dependencies — uses stdlib only.
"""
from __future__ import annotations

import re
from collections import Counter

from benchmarkdown.metrics.base import MetricResult


def normalize_for_comparison(text: str) -> str:
    """Strip markdown formatting, URLs, and normalize whitespace."""
    # Fenced code blocks (``` ... ```)
    text = re.sub(r"```[^\n]*\n.*?```", "", text, flags=re.DOTALL)
    # Headings
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Bold / italic markers
    text = re.sub(r"\*{1,3}|_{1,3}", "", text)
    # Links: [text](url) → text
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Standalone URLs
    text = re.sub(r"https?://\S+", "", text)
    # Horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Blockquotes
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # List markers (bullet and numbered)
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Inline code backticks
    text = re.sub(r"`([^`]*)`", r"\1", text)
    # Table separators (|---|---|)
    text = re.sub(r"^\|[-:| ]+\|\s*$", "", text, flags=re.MULTILINE)
    # Remaining pipe chars from table cells
    text = text.replace("|", " ")
    # HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def _bigrams(tokens: list[str]) -> Counter:
    return Counter(zip(tokens, tokens[1:]))


def compute_bigram_overlap(ground_truth: str, extracted: str) -> dict:
    """Compute bigram overlap scores between ground truth and extracted text.

    Returns dict with recall, precision, f1, ref_bigrams, ext_bigrams, overlap.
    """
    ext_tokens = normalize_for_comparison(extracted).split()
    ref_tokens = normalize_for_comparison(ground_truth).split()

    ext_bg = _bigrams(ext_tokens)
    ref_bg = _bigrams(ref_tokens)

    ref_total = sum(ref_bg.values())
    ext_total = sum(ext_bg.values())

    if ref_total == 0 and ext_total == 0:
        return {
            "recall": 1.0, "precision": 1.0, "f1": 1.0,
            "ref_bigrams": 0, "ext_bigrams": 0, "overlap": 0,
        }

    overlap = sum((ext_bg & ref_bg).values())
    recall = overlap / ref_total if ref_total > 0 else 0.0
    precision = overlap / ext_total if ext_total > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "f1": round(f1, 4),
        "ref_bigrams": ref_total,
        "ext_bigrams": ext_total,
        "overlap": overlap,
    }


class Rouge2Metric:
    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        scores = compute_bigram_overlap(ground_truth, extracted)
        return MetricResult(
            value=scores["f1"],
            description=f"ROUGE-2 F1 (bigram overlap: {scores['overlap']} / ref:{scores['ref_bigrams']} ext:{scores['ext_bigrams']})",
            details=scores,
            formatted_value=f"{scores['f1'] * 100:.1f}%",
        )


class Rouge2RecallMetric:
    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        scores = compute_bigram_overlap(ground_truth, extracted)
        return MetricResult(
            value=scores["recall"],
            description=f"ROUGE-2 Recall (content completeness: {scores['overlap']}/{scores['ref_bigrams']} ref bigrams found)",
            details=scores,
            formatted_value=f"{scores['recall'] * 100:.1f}%",
        )


class Rouge2PrecisionMetric:
    async def compute(self, ground_truth: str, extracted: str) -> MetricResult:
        scores = compute_bigram_overlap(ground_truth, extracted)
        return MetricResult(
            value=scores["precision"],
            description=f"ROUGE-2 Precision (content cleanliness: {scores['overlap']}/{scores['ext_bigrams']} ext bigrams matched)",
            details=scores,
            formatted_value=f"{scores['precision'] * 100:.1f}%",
        )
