# Benchmarkdown Documentation Index

Welcome to the Benchmarkdown documentation! This guide helps you find the right documentation for your needs.

## 📚 Main Documentation

### For Users

- **[README.md](../README.md)** - Start here!
  - Quick start guide
  - Installation instructions
  - Basic usage and features
  - Project structure overview

- **[CONFIG_UI_README.md](../CONFIG_UI_README.md)** - Configuration Guide
  - Detailed UI walkthrough
  - Profile management
  - Configuration options for each extractor
  - Best practices and tips

### For Developers

- **[CLAUDE.md](../CLAUDE.md)** - Developer Guide
  - Architecture overview
  - Plugin system explained
  - Adding new extractors (step-by-step)
  - API reference
  - Development workflow

- **[tests/README.md](../tests/README.md)** - Testing Documentation
  - Test suite overview
  - How to run tests
  - Test categories and coverage
  - Writing new tests

- **[ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md)** - Environment Configuration
  - All extractor environment variables
  - Authentication setup
  - System-level performance settings
  - Usage examples and .env file setup

### Task Management

- **[TODO.md](../TODO.md)** - Current Tasks
  - Planned features
  - Pending improvements
  - Known issues

- **[DONE.md](../DONE.md)** - Completed Tasks
  - Implementation history
  - Architecture decisions
  - Lessons learned

## 🗄️ Archive

Historical documentation (work completed, kept for reference):

### `/docs/archive/`

- **IMPLEMENTATION_GAPS.md** - Analysis of what was incomplete before plugin system completion
- **PLUGIN_IMPLEMENTATION_SUMMARY.md** - Summary of plugin infrastructure implementation
- **UI_REFACTORING_GUIDE.md** - Step-by-step guide for the UI refactoring
- **FINAL_ACHIEVEMENT_SUMMARY.md** - Achievement summary (now part of DONE.md)
- **UI_README.md** - Old UI documentation (superseded by README.md and CONFIG_UI_README.md)

**Note**: These files document the journey to the current plugin-based architecture and are preserved for historical reference.

## 🚀 Quick Navigation

### I want to...

**Use the application**
→ Start with [README.md](../README.md), then [CONFIG_UI_README.md](../CONFIG_UI_README.md)

**Add a new extractor**
→ See [CLAUDE.md - Adding New Extractors](../CLAUDE.md#adding-new-extractors)

**Understand the architecture**
→ Read [CLAUDE.md - Architecture](../CLAUDE.md#architecture)

**Run tests**
→ Check [tests/README.md](../tests/README.md)

**Contribute**
→ Review [CLAUDE.md](../CLAUDE.md) and [TODO.md](../TODO.md)

**Debug an issue**
→ Check [TODO.md](../TODO.md) for known issues, or create a new issue

## 📖 Documentation Standards

When contributing documentation:

1. **User docs** (README, CONFIG_UI_README) - Focus on HOW to use
2. **Developer docs** (CLAUDE.md) - Focus on HOW it works and HOW to extend
3. **Task docs** (TODO, DONE) - Follow workflow in CLAUDE.md instructions
4. **Archive** - Move outdated implementation docs here, don't delete

## 🎯 Current Status (as of 2025)

- ✅ **Plugin Architecture**: 100% complete
  - Automatic extractor discovery
  - Dynamic UI generation
  - Nested configuration support
  - Zero code changes to add extractors

- ✅ **UI**: Redesigned with progressive disclosure
  - Two-column task management layout
  - Profile-based configuration
  - Queue-based workflow

- ✅ **Extractors**: 5 available
  - Docling (local processing)
  - AWS Textract (cloud service)
  - LlamaParse (cloud service)
  - TensorLake (cloud service)
  - Azure Document Intelligence (cloud service)

See [DONE.md](../DONE.md) for complete implementation history.

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0 (Plugin Architecture Complete)
