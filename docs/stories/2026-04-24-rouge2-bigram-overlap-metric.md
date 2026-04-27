# Adding ROUGE-2 Bigram Overlap as a Content Quality Metric

**Date:** 2026-04-24
**Branch:** `feature/rouge2-metric`
**Issue:** [#6](https://github.com/lidia-tech/benchmarkdown/issues/6)
**PR:** [#7](https://github.com/lidia-tech/benchmarkdown/pull/7)

## Context

Benchmarkdown is a benchmark suite for comparing document-to-markdown extraction technologies, focused on legal documents. It has a plugin-based metrics system with four existing metrics: character count similarity, word count similarity, heading F1, and structure similarity. These metrics compare extracted markdown against ground truth references.

We needed a metric that could answer a fundamentally different question from the existing ones: not "does the output have the right shape?" but "does the output contain the right words?"

## Why

The existing four metrics measure document *shape* — lengths and heading structure — but none measure actual *content overlap*. A 10K document of boilerplate scores identically to a 10K faithful extraction under word or character count similarity. There was no way to answer "how much of the right content did this extractor capture?" or "how clean is the output?"

Without a content overlap metric, benchmark comparisons between extractors miss the most important dimension: whether they extracted the right text.

## What

Three new metrics plugins, all sharing a single bigram computation:

- `benchmarkdown/metrics/rouge2/` — F1 score (harmonic mean of recall and precision)
- `benchmarkdown/metrics/rouge2_recall/` — content completeness: what fraction of ground truth bigrams appear in the extraction
- `benchmarkdown/metrics/rouge2_precision/` — content cleanliness: what fraction of extraction bigrams match the ground truth

Supporting artifacts:
- `tests/test_rouge2_metric.py` — 12 test cases covering all three metrics
- `docs/implementation_notes/rouge2_metric.md` — implementation note with design rationale

No external dependencies. Uses only `re` and `collections.Counter` from stdlib.

## Why ROUGE-2

The choice of word bigram overlap (ROUGE-2) over other similarity measures was deliberate. Each alternative has a specific failure mode that makes it unsuitable for comparing document extractions:

**Unigrams (ROUGE-1) are too loose.** Single-word overlap inflates scores between unrelated documents that share common vocabulary. This is especially problematic for Italian legal text, where terms like "del", "contratto", "articolo", "comma", "legge" appear in virtually every document. A contract about real estate and a contract about software licenses share hundreds of common single words. Bigrams (consecutive word pairs) verify content appears *in context* — "risoluzione del" and "del contratto" are distinct bigrams that only match if the extraction has the same word sequences as the reference.

**SequenceMatcher (Levenshtein-like) is slow and order-sensitive.** It computes longest common subsequence in O(n*m). For a 47K-character reference vs a 12K extraction, that's ~560M operations per document pair. Across a benchmark suite of 20+ documents and multiple extractors, this becomes minutes instead of seconds. More importantly, SequenceMatcher penalizes paragraph reordering harshly — if an extractor puts a conclusion before the introduction, the score tanks even though all content was captured. Bigram overlap is order-independent at the paragraph level, which better reflects extraction quality.

**Character-level diff is too sensitive to noise.** A single extra newline, a markdown bold marker (`**`), or a different whitespace convention between extractors tanks the score. Word-level comparison with normalization operates at the right granularity for comparing content.

**TF-IDF/cosine similarity is overkill.** It requires building a vocabulary across all documents, adds external dependencies (scikit-learn or similar), and is harder to interpret. "72% cosine similarity" doesn't tell you whether the problem is missing content or extra boilerplate. ROUGE-2's decomposition into recall and precision does.

**LLM-based comparison is expensive and non-deterministic.** Running 20 document pairs through an LLM costs $0.50+ and takes minutes. ROUGE-2 costs nothing, runs in milliseconds, and produces deterministic scores. For a benchmark suite that needs to be run repeatedly across configurations, determinism and speed matter.

The key insight is that recall and precision tell different diagnostic stories. A truncated-but-clean extraction (e.g., first 12K of a 47K page) gets high precision but low recall — the fix is to increase extraction limits. A full-but-junky extraction (navigation bars, cookie banners, sidebars included) gets high recall but low precision — the fix is better content filtering. F1 alone hides which problem you have.

## How

**Markdown normalization before comparison.** A `normalize_for_comparison` function strips headings, bold/italic, links, fenced code blocks, blockquotes, list markers, table syntax, and HTML entities before tokenizing. This ensures formatting differences between extractors don't affect content scores.

**Three separate plugin directories.** The MetricRegistry discovers one metric per plugin directory via `pkgutil`. To expose recall, precision, and F1 as independent metrics, each gets its own directory with an `__init__.py` that imports from the shared `rouge2/metric.py`. The shared `compute_bigram_overlap()` function does the computation once per call.

**Both-empty returns 1.0.** Consistent with char_count and word_count metrics, and with the `MetricResult` contract ("1.0 = perfect match"). Two identical empty strings are a perfect match. This was caught during code review.

## Findings

The automated code review (5 parallel agents scoring independently) surfaced five issues:

| Issue | Score | Action |
|-------|-------|--------|
| Empty-empty returns 0.0 instead of 1.0 | 75 | Fixed: early return for both-empty case |
| `details` dict reports sentinel 1 instead of actual 0 | 75 | Fixed: removed `or 1` guard, explicit division checks |
| Fenced code blocks not stripped | 25 | Fixed: added regex for triple-backtick blocks |
| Missing test file | 75 | Fixed: added 12-test suite |
| Missing implementation note | 25 | Fixed: added docs/implementation_notes/rouge2_metric.md |

The original `or 1` sentinel pattern was a pragmatic shortcut that created two bugs in a metrics framework context: wrong metadata in `details` and wrong score for empty inputs.

Quick validation with test data confirmed expected behavior:
- Identical text: F1 = 100%
- Truncated extraction ("The quick brown fox" from a 13-word sentence): recall = 25%, precision = 100%, F1 = 40%
- Boilerplate prepended: recall = 100%, precision = 53%, F1 = 70%

## Lessons learned

**Edge case assumptions don't transfer between contexts.** The `or 1` division guard was fine in a standalone script where empty inputs don't occur. In a framework with an explicit contract (`MetricResult.value` in [0, 1], where 1.0 = perfect match), it violated invariants. When adapting code to a new context, edge case assumptions need re-evaluation.

**Automated code review with confidence scoring filters noise effectively.** Running 5 parallel review agents generated ~15 raw issues, but confidence scoring (0-100) with a threshold reduced that to actionable items. Lowering the threshold to 25 for fixes caught real improvements (fenced code blocks, implementation notes) that weren't critical but improved quality.

**Separate plugin directories are the cost of auto-discovery.** The MetricRegistry discovers one metric per directory via `pkgutil`. Exposing three related metrics (F1, recall, precision) required three directories with thin `__init__.py` files. The alternative — changing the registry to support multiple metrics per plugin — would have been a larger change for a minor benefit.

## Open questions

- Should `normalize_for_comparison` be promoted to a shared utility? Future content-overlap metrics (ROUGE-1, ROUGE-L, BLEU) would need the same normalization. Currently it lives in `rouge2/metric.py`.
- How do ROUGE-2 scores correlate with human quality judgments for Italian legal documents specifically? Legal text has characteristics (repetitive phrasing, numbered articles, formulaic clauses) that may affect bigram overlap behavior differently from general web content.
- Should the three ROUGE-2 metrics be grouped visually in the Gradio UI? Currently all metrics appear as a flat list. A "ROUGE-2" group might reduce visual clutter as more metrics are added.

## What's next

- Run the metric against existing extraction outputs in `data/raw_markdown/` to establish baselines
- Create ground truth markdown files for the `lidia-anon` dataset to enable metric evaluation
- Consider adding ROUGE-1 (unigram) and ROUGE-L (longest common subsequence) as additional content metrics
