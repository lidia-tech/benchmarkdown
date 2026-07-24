# The TSH-Approach: General Text Extraction Quality Measuring Pattern

**Date:** 2026-07-24
**Branch:** `metrics-update`

## Context

Extracting structured, semantically correct content from documents (PDFs, scans,
OCR) is a foundational step for modern document-processing systems. It is not a
flat text problem: documents carry a hierarchy — parts, sections,
subsections, nested clauses — and downstream AI systems increasingly rely on
that structure. Hierarchical chunking, retrieval, graph-based knowledge
extraction, and document-grounded reasoning all depend on the extraction
preserving both the document's **structure** and its **semantic** content, not just
the words on the page.

### The semantic/structural pair

A useful way to frame extraction quality is as a **paired task**: an extraction
is good only if it preserves *both*

- the **semantic** content — the actual text, the words and their meaning, and
- the **structural** organization — how that text is arranged into a hierarchy
  of sections.

These two dimensions are complementary and largely independent: an extractor can
get the prose right while destroying the section layout, or reproduce a clean
outline while garbling the text. Measuring only one gives a misleading verdict.
Yet most existing evaluation focuses on one side — content-overlap scores on the
semantic side, or local layout/segmentation checks — with little that assesses
the *global preservation of structure and semantics together*. There is no
widely accepted metric that captures the pair at once.

### The tsh-approach

The **tsh-approach** is our concrete realization of that semantic/structural
pair. It keeps the semantic dimension as one component (**T**) and refines the
structural dimension into two complementary resolutions — flat detection (**H**)
and deep hierarchy (**S**) — so that structure, the harder and more neglected
half of the pair, can be analyzed in the detail it needs. This story records
that pattern.

## Why

Assessing extraction quality means answering three *different* questions, and
any single metric conflates them:

- **Did we get the right words?** (semantic / content fidelity)
- **Is the section hierarchy correct?** (deep structural fidelity)
- **Were the sections detected at all?** (flat structural fidelity)

A content-overlap metric can be high while every heading is flattened. A
structural metric can be high while the prose is garbled. A flat heading check
can pass while sections are nested under the wrong parents. Measuring only one
axis produces misleading comparisons between extractors.

The insight behind the tsh-approach is that these axes are **complementary**,
and that their *combination* is diagnostic: characteristic patterns across the
three components point to specific failure modes.

## What

The **tsh-approach** decomposes extraction quality into three complementary
components, evaluated between a reference text and an extracted text:

| Component | Axis | Question | Basis |
|-----------|------|----------|-------|
| **T** — text | Semantic quality | Are the right words present? | Word-bigram (ROUGE-2 style) content overlap |
| **S** — structure | Hierarchical quality (deep) | Is the section hierarchy correct? | Structural similarity of the heading hierarchy (S-score) |
| **H** — headings | Hierarchical quality (flat) | Were the sections detected? | Heading-detection F1 |

The key relationship is between **S and H**: both concern hierarchical quality,
but at different resolutions. **H is the flat check** — it treats headings as an
unordered set and asks only whether the right ones were detected. **S is the
deep check** — it scores how those headings nest (parent/child relationships and
depth). Used **in combination**, flat + deep let us analyze hierarchical quality
more finely than either alone: H tells you *whether* sections exist, S tells you
*whether they're in the right place*.

T stands apart on the semantic axis, capturing content fidelity independent of
structure.

### Diagnostic patterns

Because the three components are orthogonal, their combined signature diagnoses
the failure mode (following the pattern table in the source paper):

| T | S | H | Interpretation |
|---|---|---|----------------|
| High | High | High | Ideal extraction |
| High | Low | Low | Text captured, structure lost |
| Med | Low | High | Headings found, but hierarchy broken |
| Low | Low | Low | Complete failure |

The `H high / S low` row is exactly the case a single structural metric would
miss and the flat+deep split makes visible: the extractor recognised the
sections but nested them wrong.

## The three components

**T — semantic quality.** Word-bigram (ROUGE-2 style) content overlap over
formatting-normalized text, decomposable into recall (completeness) and
precision (cleanliness). Measures whether the right words are present, blind to
structure. See [ROUGE-2 Bigram Overlap Metric](../implementation_notes/rouge2_metric.md).

**S — deep hierarchical quality.** The heading hierarchy of each document is
represented as a dense "text bush" graph — headings as vertices, with edges for
ancestor/descendant and consecutive-heading relationships — and the two graphs
are compared as matrices. The resulting structural similarity is sensitive to
both section presence and nesting depth. See [Structural S-Score Metric](../implementation_notes/s_score_metric.md).

**H — flat hierarchical quality.** Precision/recall/F1 over fuzzy-matched
heading *sets*, deliberately discarding heading levels. It asks only whether the
right sections were detected as headings, not how they nest. See [Heading F1 Metric](../implementation_notes/heading_f1_metric.md).

S and H rely on the same fuzzy heading matching, so both agree on what counts as
"the same heading" — the flat and deep views are consistent with each other.

## Findings

- **The S/H split is the crux of hierarchical analysis.** H alone can't tell a
  correctly-nested document from a flattened one; S alone can't cleanly separate
  "missing section" from "misplaced section." Reporting both turns hierarchical
  quality from one opaque number into a two-part diagnosis.
- **Text-bush over trees increases structural sensitivity.** Representing the
  hierarchy as a denser graph (ancestor/descendant + adjacency edges) rather
  than a bare tree makes S more sensitive to structural perturbations while
  keeping the comparison computationally tractable (matrix difference rather
  than NP-hard graph edit distance).
- **Components are meant to be read together, not averaged blindly.** The
  diagnostic value is in the *pattern* of T/S/H, though a task may combine them
  into a single (possibly weighted) score when a scalar is needed.

