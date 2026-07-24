# Structural S-Score Metric

**Status:** ✅ Complete
**Date:** 2026-07-24
**Branch:** metrics-update
**Authors:** Tregubov Vasilii, Janos Tolgyesi

> **Intellectual property.** The S-score metric and this implementation are the
> intellectual property of Vasilii Tregubov and Janos Tolgyesi, as authors of
> its implementation.

## Overview

The structural similarity metric (`heading_s`, "S-score") compares the
**document structure** — the heading tree / table of contents — of an
extraction against ground truth. Unlike ROUGE-2 (text content) and
char/word_count (length), this metric asks: *did the extractor reproduce the
document's sectioning and hierarchy?*

The implementation lives in `benchmarkdown/metrics/s_score.py` and is consumed
by the `heading_s` plugin.

## Problem

Documents extracted from PDFs, scans, or OCR are not flat text — they carry a
**hierarchy**: parts, sections, subsections, nested clauses. For legal and
technical documents this structure is meaningful content in its own right; a
faithful extraction has to reproduce not just the words but *where sections
begin, how they nest, and at what depth*.

Measuring that faithfully is harder than it looks:

- **Content overlap and length metrics are blind to structure.** An extraction
  can contain all the right words yet flatten every heading, merge sections, or
  misplace them in the hierarchy — and still score well on text/length metrics.
- **Headings rarely match verbatim.** OCR noise, wording drift, and numbering
  differences ("3. Methods" vs "Methods") mean the same logical section appears
  under slightly different titles in the two documents, so exact matching
  under-counts real correspondences.
- **Both presence and depth matter.** A section that exists but sits at the
  wrong nesting level is a partial error, not a match; a good measure has to
  penalise misplaced depth without treating it as a total miss.
- **The score must be comparable.** To rank extractors it has to be bounded in
  [0, 1] and symmetric in the two documents, so identical inputs score 1.0 and
  the value means the same thing across documents of very different sizes.

The S-score targets exactly this: a bounded, symmetric measure of how well an
extraction reproduces a document's heading hierarchy, robust to fuzzy heading
wording and sensitive to both section presence and nesting depth.

## Approach

A **generalized Jaccard (Ruzicka) similarity** over two per-document "text
bush" matrices, with a provable upper-bound normaliser that keeps the score
bounded and symmetric.

### Pipeline

```
1. toc_extract(text)          → heading list + dict  (lines starting with '#')
2. toc_fuzzy_unify(...)       → merge both ToCs onto one shared node index
                                (rapidfuzz WRatio, 0–100 threshold)
3. graph construction
     disconnected_sparse_graph → parent → direct children
     disconnected_full_graph   → node → all descendants (memoised DFS)
     connected_graph           → + forward edges between consecutive headings
                                 ("text bush"); cycle guard falls back to sparse
4. matrices (sparse CSR, per document)
     adjacency  : edge present (1)                       graph_to_sparse_matrix
     hierarchy  : edge weighted by |level gap|           graph_to_level_diff_sparse_matrix
5. score
     distance   = Σ |A − B|            (cell-wise 1-norm of the difference)
     normaliser = Σ max(A, B)          (cell-wise union of both docs' mass)
     S-score    = 1 − distance / normaliser   (clamped at 0)
```

### Normalization method

The score is the **generalized Jaccard (Ruzicka) similarity**:

```
S = 1 − Σ|Aij − Bij| / Σ max(Aij, Bij)   =   Σ min(Aij, Bij) / Σ max(Aij, Bij)
```

- `Σ|A − B| / Σ max(A, B)` is the **Soergel distance** (a true metric).
- Because `|a − b| ≤ max(a, b)` cell-wise, the distance is bounded by the
  normaliser, so **S ∈ [0, 1]** and is **symmetric** in the two documents.
- On the binary adjacency channel this reduces to the classic **Jaccard index
  (IoU)** over graph edges.

This is documented in the `structure_metric` docstring, which is the single
source of truth for the formula.

### Channel diffusion (`difs`)

`proc(..., difs=True)` (the **default**) fuses the two channels with an
element-wise `max` for both the distance and the normaliser, so the score
reflects **both** edge presence and heading-level gaps. `difs=False` uses only
the adjacency channel (edge present/absent).

## Key Design Decisions

- **Hamming distance over matrices instead of GED/TED** → the two hierarchies
  are unified onto a shared node index and compared as fixed-size matrices, so
  the structural difference is a cell-wise (Hamming-style) matrix distance —
  computable in time quadratic in the number of headings. This sidesteps the
  **exponential / NP-hard** cost of graph/tree edit distance (GED/TED), which
  must search over node correspondences. The one-time fuzzy unification that
  fixes those correspondences is itself only quadratic, so the whole evaluation
  stays cheap enough to run across a large benchmark suite.
- **Provable upper-bound normaliser** (`Σ max`) → score is guaranteed in
  [0, 1] and symmetric.
- **Linear similarity** → the score is interpretable directly as a fraction of
  shared structure.
- **Two channels, fused by default** — adjacency (does the section exist) plus
  hierarchy (is it at the right depth).
- **Sparse CSR matrices** (`scipy.sparse`) → handles large, deeply nested legal
  documents without dense O(n²) allocation.
- **Cycle guard** — the connected "bush" graph is checked for cycles and falls
  back to the acyclic sparse graph if needed; `sys.setrecursionlimit(50000)`
  covers deep DFS on nested documents.
- **Error resilience** — `proc` returns `(0, {'error': ...})` on failure
  instead of raising, so one bad document can't abort a benchmark run.

## Unified heading matcher

Heading matching is shared across the two structure metrics via a single
helper in `s_score.py`:

```python
HEADING_SCORER    = rf_fuzz.WRatio       # rapidfuzz, 0–100 scale
HEADING_PROCESSOR = rf_default_process
def heading_similarity(a, b): ...        # used by the unifier AND heading_f1
```

- **Threshold convention is the 0–100 scale** across both metrics; default
  cutoff **80** (headings unify when similarity is *strictly greater* than the
  cutoff).
- `heading_f1` uses this same shared helper, so both metrics agree on what
  counts as a heading match.

## Public API

```python
proc(toc1, toc2, toc_dict1, toc_dict2, fuzzy_th, difs=True, sim=True)
    → (s_score, debug_info)

final_score(text1, text2, fuzzy_th)          # parses both docs, then proc()
    → (s_score, debug_info)
```

`debug_info` carries diagnostics: `total_nodes`, `distance`, `norm_factor`,
`node_recall`, `toc_coverage`. The `heading_s` plugin surfaces the score as
`MetricResult.value` and merges `debug_info` into `details`.

## Related Files

- `benchmarkdown/metrics/s_score.py` — implementation (extraction, unification, graphs, matrices, metric, entry points)
- `benchmarkdown/metrics/heading_s/metric.py` — `StructureSimilarityMetric` plugin (calls `proc`, `difs=True`, `fuzzy_threshold=80`)
- `benchmarkdown/metrics/heading_s/__init__.py` — plugin exports
- `benchmarkdown/metrics/heading_f1/metric.py` — heading-F1 plugin (shares `heading_similarity`)
- `pyproject.toml` — `numpy`, `pandas`, `scipy` dependencies
- `benchmarkdown/metrics/base.py` — Metric protocol and MetricResult

## Extensibility

- `heading_similarity` is the single place to change the fuzzy matcher; both
  structure metrics follow it automatically.
- Additional per-edge channels (beyond adjacency + level gap) could be fused
  into `merged_diff` / `merged_norm` in `proc` using the same element-wise-max
  pattern.
