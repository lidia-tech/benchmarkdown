# ROUGE-2 Bigram Overlap Metric

**Status:** ✅ Complete
**Date:** 2026-04-24
**Issue:** #6

## Overview

Added a ROUGE-2 style word bigram overlap metric for evaluating extraction quality. Unlike the existing count-based metrics (char_count, word_count) which only compare document sizes, this metric measures actual **content overlap** between extracted text and ground truth.

## Problem

Existing metrics can't distinguish between an extraction that captured the right content versus one that has the right length but wrong text. A 10K document of boilerplate scores identically to a 10K faithful extraction under word/char count similarity.

## Solution

Word bigram (consecutive word pair) multiset overlap, following the ROUGE-2 methodology:

- **Recall** = fraction of reference bigrams found in extraction (content completeness)
- **Precision** = fraction of extraction bigrams found in reference (content cleanliness)
- **F1** = harmonic mean (single summary score, used as MetricResult.value)

### Why Bigrams Over Alternatives

- **Unigrams** — too loose; common words inflate scores between unrelated documents
- **SequenceMatcher** — O(n*m) complexity, penalizes paragraph reordering
- **Character-level** — too sensitive to whitespace and formatting noise
- **TF-IDF/cosine** — overkill, requires cross-document vocabulary

## Architecture

### Data Flow

```
1. Input texts (ground_truth, extracted)
   └─> normalize_for_comparison()
       - Strip markdown: headings, bold/italic, links, code blocks, tables, etc.
       - Strip HTML entities
       - Collapse whitespace, lowercase
   └─> Tokenize (split on whitespace)
   └─> Build bigram multiset (Counter of consecutive pairs)
   └─> Compute intersection, recall, precision, F1
   └─> Return MetricResult(value=F1, details={recall, precision, ...})
```

### Key Design Decisions

- **Markdown normalization** ensures formatting differences don't affect scores (same content in `**bold**` vs plain scores identically)
- **Multiset overlap** (Counter intersection) correctly handles repeated bigrams
- **Both-empty edge case** returns 1.0 (perfect match), consistent with other metrics
- **No external dependencies** — uses only `re` and `collections.Counter`

## Related Files

- `benchmarkdown/metrics/rouge2/__init__.py` — plugin exports
- `benchmarkdown/metrics/rouge2/metric.py` — implementation
- `tests/test_rouge2_metric.py` — test suite
- `benchmarkdown/metrics/base.py` — Metric protocol and MetricResult

## Testing

```bash
uv run python tests/test_rouge2_metric.py
```

Covers: identical text, empty extraction, both empty, truncated text, boilerplate, markdown formatting, fenced code blocks, single token, and details accuracy.

## Extensibility

The `normalize_for_comparison` function can be reused by future content-overlap metrics. The same bigram approach could be extended to n-grams of different sizes (ROUGE-1, ROUGE-3, etc.) by parameterizing `_bigrams`.
