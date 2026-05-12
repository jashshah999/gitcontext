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

## What it detects

- Languages and their proportions
- Frameworks (Python, JS/TS, Rust, C++)
- Build systems and package managers
- CI/CD configuration
- Test frameworks and patterns
- Project architecture and entry points
