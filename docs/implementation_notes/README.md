# Implementation Notes

This directory contains detailed implementation documentation for significant features and architectural patterns in Benchmarkdown.

## Purpose

Implementation notes serve as:
- **Developer reference** for understanding complex features
- **Onboarding documentation** for new contributors
- **Historical record** of architectural decisions
- **Implementation guide** for extending similar patterns

## Guidelines

### When to Write Implementation Notes

Create an implementation note when:
- ✅ Implementing a new architectural pattern
- ✅ Adding a complex feature spanning multiple files
- ✅ Making significant changes to the plugin system
- ✅ Creating reusable patterns for other features
- ✅ Completing work that needs detailed documentation

### What to Include

Each implementation note should cover:
1. **Overview** - Problem, solution, status
2. **Architecture** - Data flow, key components
3. **Implementation Details** - Code structure, patterns used
4. **Examples** - Concrete usage examples
5. **Extensibility** - How to use/extend the pattern
6. **Testing** - How to verify correct operation
7. **Related Files** - Where to find the code

### Format

- Use Markdown format
- Include code examples
- Add diagrams using ASCII art or Mermaid
- Link to relevant git commits
- Keep examples concrete and testable
- Update when the implementation changes significantly

## Available Notes

### [conditional_fields.md](./conditional_fields.md)
**Progressive Disclosure for Configuration UIs**

Implements dynamic show/hide of dependent configuration fields based on parent field values. Reduces initial UI complexity by 24% while preserving all configuration options.

- Status: ✅ Complete
- Commits: f9d930a, f2c6be4, 925eb7f
- Use case: Any extractor with field dependencies

### [rouge2_metric.md](./rouge2_metric.md)
**ROUGE-2 Bigram Overlap Metric**

Word bigram multiset overlap (ROUGE-2 style) for measuring content recall, precision, and F1 between extracted markdown and ground truth. No external dependencies.

- Status: ✅ Complete
- Issue: #6
- Use case: Evaluating content fidelity of document extraction

### [s_score_metric.md](./s_score_metric.md)
**Structural S-Score Metric**

Generalized Jaccard (Ruzicka) similarity over document heading-tree "bush" matrices, with a provable upper-bound normaliser (bounded, symmetric [0, 1]). Fuses adjacency + heading-level channels; shares a unified rapidfuzz heading matcher with heading_f1.

- Status: ✅ Complete
- Branch: metrics-update
- Use case: Evaluating structural/heading fidelity of document extraction

### [heading_f1_metric.md](./heading_f1_metric.md)
**Heading F1 Metric**

Flat-structure check: precision/recall/F1 over fuzzy-matched heading sets, ignoring hierarchy. Shares the rapidfuzz heading matcher with heading_s. Use as a supportive detection signal alongside the S-score, or standalone when nesting doesn't matter.

- Status: ✅ Complete
- Branch: metrics-update
- Use case: Checking heading/section detection independent of nesting depth

---

## Contributing

When adding new implementation notes:
1. Use the existing notes as templates
2. Place in `docs/implementation_notes/`
3. Add entry to this README
4. Link from CLAUDE.md if it defines a pattern Claude should follow
5. Update when making significant changes to the feature
