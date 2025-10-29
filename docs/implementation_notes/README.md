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

---

## Contributing

When adding new implementation notes:
1. Use the existing notes as templates
2. Place in `docs/implementation_notes/`
3. Add entry to this README
4. Link from CLAUDE.md if it defines a pattern Claude should follow
5. Update when making significant changes to the feature
