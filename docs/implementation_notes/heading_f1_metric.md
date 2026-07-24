# Heading F1 Metric

**Status:** ✅ Complete
**Date:** 2026-07-24
**Branch:** metrics-update

## Overview

The heading F1 metric (`heading_f1`) checks whether an extraction reproduces the
**set of headings** present in the ground truth — a **flat-structure check**. It
answers a deliberately narrow question: *were the right sections detected, as
headings, at all?* — regardless of how those headings nest.

It is the flat counterpart to the S-score (`heading_s`): where the S-score
scores the heading **hierarchy** (nesting depth and parent/child relationships),
heading F1 ignores hierarchy entirely and treats the headings as an unordered
set. It can serve either as a **supportive metric alongside the S-score** — to
separate "were sections detected?" from "were they nested correctly?" — or as a
**standalone alternative** in tasks where hierarchical representation does not
matter.

The implementation lives in `benchmarkdown/metrics/heading_f1/metric.py`.

## Problem

Headings are the backbone of a document's sectioning, but reproducing them has
two distinct failure modes that a single number tends to blur together:

- **Detection** — was a section recognised as a heading at all? An extractor may
  drop a heading (turning it into body text) or invent one that isn't there.
- **Placement** — is a detected heading at the right nesting depth, under the
  right parent?

For many tasks only the first question matters. When the goal is simply to
confirm that the extractor found the document's sections — a table-of-contents
sanity check, a flat outline, content that has no meaningful nesting — measuring
hierarchy is unnecessary and can obscure a clean detection signal. Heading F1
isolates the detection axis: it measures how completely and how cleanly the
extraction's heading set matches the ground truth's, with no credit or penalty
for nesting.

Because headings rarely match verbatim (OCR noise, wording drift, numbering
like "3. Methods" vs "Methods"), the match must be fuzzy rather than exact.

## Approach

Standard **precision / recall / F1** over fuzzy-matched heading sets.

```
1. toc_extract(text)   → heading list  (lines starting with '#')
                         only the header titles are used; levels are ignored
2. normalize           → strip + lowercase each heading title
3. greedy match        → for each ground-truth heading, find the first extracted
                         heading whose fuzzy similarity > threshold; mark both matched
4. score
     tp = matched ground-truth headings
     fn = unmatched ground-truth headings   (missed sections)
     fp = unmatched extracted headings       (spurious headings)
     precision = tp / (tp + fp)      recall = tp / (tp + fn)
     F1        = harmonic mean
```

Only the header **titles** feed the metric — the level (`#` depth) from
`toc_extract` is intentionally discarded. That is what makes this a flat check.

### Precision / recall / F1

- **Recall** = fraction of ground-truth headings that were detected → *did the
  extractor miss sections?*
- **Precision** = fraction of extracted headings that are real → *did the
  extractor invent spurious headings?*
- **F1** = harmonic mean, surfaced as `MetricResult.value`.

### Fuzzy matching

Heading matching uses the shared `heading_similarity` helper from `s_score.py`
(rapidfuzz WRatio, 0–100 scale), so `heading_f1` and `heading_s` agree on what
counts as "the same heading":

```python
from benchmarkdown.metrics.s_score import heading_similarity
...
if heading_similarity(a, b) > similarity_threshold:  # default 80
```

Matching is **greedy** and **strictly-greater-than** the threshold, consistent
with the structural metric's unifier.

## Key Design Decisions

- **Flat by design** — heading levels from `toc_extract` are dropped; the metric
  scores heading *presence* only, leaving hierarchy to the S-score.
- **Shared fuzzy matcher** — reuses `heading_similarity`, so both heading
  metrics apply the same scorer, scale, and cutoff.
- **0–100 threshold, default 80** — the same convention as `heading_s`.
- **Set semantics via greedy one-to-one matching** — each ground-truth heading
  claims at most one extracted heading, so duplicates don't inflate the score.
- **Empty edge cases** — when there are no headings to match, precision/recall
  fall back to 0 rather than raising.

## Public API

```python
compute_header_f1(text1, text2, similarity_threshold=80.0) → float

HeadingF1Metric(similarity_threshold=80.0)
    .compute(ground_truth, extracted) → MetricResult   # value = F1
```

`MetricResult.details` carries `f1` and the `threshold` used.

## Relationship to the S-Score

| | `heading_f1` | `heading_s` (S-score) |
|---|---|---|
| Question | Were the right sections detected? | Is the section hierarchy correct? |
| Uses heading levels | No (flat) | Yes (nesting depth) |
| Output | Precision / Recall / F1 over heading sets | Generalized Jaccard over hierarchy graphs |
| Use as | Supportive detection signal, or standalone when nesting doesn't matter | Full structural fidelity |

Run both together to distinguish "sections missing/spurious" (heading F1) from
"sections misplaced in the hierarchy" (S-score). Run heading F1 alone when the
document has no meaningful nesting.

## Related Files

- `benchmarkdown/metrics/heading_f1/metric.py` — implementation (`compute_header_f1`, `HeadingF1Metric`)
- `benchmarkdown/metrics/heading_f1/__init__.py` — plugin exports
- `benchmarkdown/metrics/s_score.py` — provides `toc_extract` and the shared `heading_similarity`
- `benchmarkdown/metrics/base.py` — Metric protocol and MetricResult

## Extensibility

- The fuzzy matcher is centralised in `heading_similarity`; changing it updates
  both heading metrics at once.
- The same precision/recall/F1 skeleton could be applied to other flat sets
  extracted from a document (e.g. list items, table captions) by swapping what
  `toc_extract` feeds in.
