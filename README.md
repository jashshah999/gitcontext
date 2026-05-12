# gitcontext

Auto-generate AI context docs (CLAUDE.md / AGENTS.md) for any codebase.

## Install

```bash
pip install .
```

## Usage

```bash
# Analyze local directory
gitcontext .
gitcontext /path/to/repo

# Analyze GitHub repo (clones shallow)
gitcontext https://github.com/user/repo

# Write to file
gitcontext . --output CLAUDE.md

# AGENTS.md format
gitcontext . --format agents

# Verbose output (show detections)
gitcontext . --verbose
```

## Deep Mode (Claude-powered)

For richer, more insightful output, use `--deep` which sends key source files to Claude for analysis:

```bash
# Requires ANTHROPIC_API_KEY env var
pip install '.[deep]'
export ANTHROPIC_API_KEY=sk-ant-...

gitcontext . --deep
gitcontext . --deep --output CLAUDE.md
```

Deep mode reads the top ~15-20 most important files and uses Claude to generate a comprehensive CLAUDE.md with architecture explanations, conventions, gotchas, and contributor notes.

## What it detects

- Languages and their proportions
- Frameworks (Python, JS/TS, Rust, C++)
- Build systems and package managers
- CI/CD configuration
- Test frameworks and patterns
- Project architecture and entry points
