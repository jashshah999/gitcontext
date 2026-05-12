"""Deep analysis using LLM APIs (Claude or Gemini) with multi-pass architecture discovery."""

from __future__ import annotations

import os
import sys

import click

from gitcontext.analyzer import RepoContext
from gitcontext.cache import get_cached, set_cached
from gitcontext.file_selector import select_files
from gitcontext.utils import read_file_safe, walk_repo

# --- Prompts ---

ARCHITECTURE_DISCOVERY_PROMPT = """You are analyzing a codebase to understand its architecture.

Given the file tree and configuration files below, identify the 10-15 most architecturally important source files in this codebase. These are files that:
- Define core abstractions, base classes, or interfaces
- Implement the main entry points or orchestration logic
- Define the type system or data models
- Implement factory/registry patterns that wire the system together
- Contain the "rules" that all other code must follow

Return ONLY a JSON array of file paths, nothing else. Example:
["src/core/base.py", "src/config/settings.py", ...]

Pick files that would give a senior engineer the fastest understanding of how the system works."""

GENERATION_PROMPT = """You are analyzing a codebase to generate a CLAUDE.md file that will help AI coding assistants understand this project instantly.

Generate a CLAUDE.md that includes:

1. **Project overview** (1-2 sentences, what it does and why it exists)
2. **Tech stack** (concise, with version constraints if notable)
3. **Development setup** (exact commands to get running)
4. **Key commands** (test, lint, build, run — exact commands)
5. **Architecture** — for each key module/directory:
   - What it contains and WHY (not just file names)
   - How it relates to other modules (dependencies, data flow)
   - What patterns it uses (registry, factory, inheritance, etc.)
6. **Important conventions and patterns**:
   - What patterns MUST be followed (e.g., registration decorators, base class inheritance)
   - Config/CLI system and how it works
   - Import patterns (lazy imports, optional deps, etc.)
7. **Non-obvious behaviors and gotchas**:
   - Things that would surprise a new contributor
   - Implicit contracts between modules
   - Performance-sensitive code paths
   - Things that look simple but have hidden complexity
8. **Common pitfalls and debugging tips**:
   - What breaks if you don't follow the patterns
   - How to debug common issues
9. **Repository structure** (brief overview of top-level dirs outside src/)

Be concise but thorough. No fluff. A senior engineer should be able to read this in 3 minutes and start contributing without breaking things. Focus on the "why" and "how things connect" — not just describing what each file does in isolation."""

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"


def _call_llm(user_message: str, provider: str, model: str | None = None, system: str | None = None, max_tokens: int = 4096) -> str:
    """Unified LLM call dispatcher."""
    if provider == "anthropic":
        return _call_anthropic(user_message, model=model, system=system, max_tokens=max_tokens)
    elif provider == "gemini":
        return _call_gemini(user_message, model=model, system=system, max_tokens=max_tokens)
    else:
        click.echo(f"Error: Unknown provider '{provider}'.", err=True)
        sys.exit(1)


def _call_anthropic(user_message: str, model: str | None = None, system: str | None = None, max_tokens: int = 4096) -> str:
    try:
        import anthropic
    except ImportError:
        click.echo("Error: 'anthropic' package required. Install with: pip install 'gitcontext[deep]'", err=True)
        sys.exit(1)

    model = model or DEFAULT_ANTHROPIC_MODEL
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": user_message}],
    }
    if system:
        kwargs["system"] = system

    message = client.messages.create(**kwargs)
    return message.content[0].text


def _call_gemini(user_message: str, model: str | None = None, system: str | None = None, max_tokens: int = 4096) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        click.echo("Error: 'google-generativeai' package required. Install with: pip install 'gitcontext[gemini]'", err=True)
        sys.exit(1)

    model_name = model or DEFAULT_GEMINI_MODEL
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

    # Prepend system prompt to user message for Gemini
    full_message = f"{system}\n\n---\n\n{user_message}" if system else user_message

    genai_model = genai.GenerativeModel(model_name)
    response = genai_model.generate_content(
        full_message,
        generation_config=genai.GenerationConfig(max_output_tokens=max_tokens),
    )
    return response.text


def _detect_provider():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    return None


def _build_file_tree(repo_path) -> str:
    """Build a compact file tree string."""
    all_files = walk_repo(repo_path, max_depth=5)
    # Group by top-level directory
    tree_lines = []
    for f in sorted(all_files):
        tree_lines.append(f)
    return "\n".join(tree_lines)


def _build_discovery_context(ctx: RepoContext, repo_path) -> str:
    """Build context for architecture discovery pass (file tree + configs)."""
    parts = []

    parts.append("## File Tree\n```")
    parts.append(_build_file_tree(repo_path))
    parts.append("```\n")

    parts.append("## Project Info")
    parts.append(f"Name: {ctx.name}")
    parts.append(f"Description: {ctx.description}")
    parts.append(f"Languages: {ctx.languages[:5]}")
    parts.append(f"Frameworks: {ctx.frameworks}")
    parts.append(f"Build system: {ctx.build.system}")
    parts.append(f"Entry points: {ctx.entry_points}")
    parts.append("")

    # Include config files content
    config_files = ["pyproject.toml", "package.json", "Cargo.toml", "go.mod"]
    for cfg in config_files:
        content = read_file_safe(repo_path / cfg)
        if content:
            parts.append(f"## {cfg}\n```\n{content}\n```\n")

    # Include README (truncated)
    for readme_name in ["README.md", "readme.md", "README.rst"]:
        content = read_file_safe(repo_path / readme_name)
        if content:
            # Truncate README to first 150 lines
            lines = content.splitlines()
            truncated = "\n".join(lines[:150])
            parts.append(f"## {readme_name}\n```\n{truncated}\n```\n")
            break

    return "\n".join(parts)


def _parse_file_list(response: str) -> list[str]:
    """Parse LLM response to extract file paths from JSON array."""
    import json

    # Try to find JSON array in the response
    response = response.strip()

    # Try direct parse
    try:
        result = json.loads(response)
        if isinstance(result, list):
            return [f for f in result if isinstance(f, str)]
    except json.JSONDecodeError:
        pass

    # Try to find array in markdown code block
    if "```" in response:
        blocks = response.split("```")
        for block in blocks:
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            try:
                result = json.loads(block)
                if isinstance(result, list):
                    return [f for f in result if isinstance(f, str)]
            except json.JSONDecodeError:
                continue

    # Try to find anything that looks like a JSON array
    import re
    match = re.search(r'\[.*?\]', response, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return [f for f in result if isinstance(f, str)]
        except json.JSONDecodeError:
            pass

    return []


def _build_generation_context(ctx: RepoContext, repo_path, key_files: list[str], file_contents: dict[str, str]) -> str:
    """Build the final context for CLAUDE.md generation."""
    parts = []

    # Static analysis
    parts.append("## Static Analysis Results\n")
    parts.append(f"Name: {ctx.name}")
    parts.append(f"Description: {ctx.description}")
    parts.append(f"Languages: {ctx.languages[:5]}")
    parts.append(f"Frameworks: {ctx.frameworks}")
    parts.append(f"Build system: {ctx.build.system}")
    parts.append(f"Install command: {ctx.build.install_cmd}")
    parts.append(f"Test command: {ctx.test.test_command}")
    parts.append(f"Test framework: {ctx.test.framework}")
    parts.append(f"CI: {ctx.ci.provider}")
    parts.append(f"Entry points: {ctx.entry_points}")
    parts.append(f"Architecture: {ctx.architecture}")
    parts.append(f"Notable files: {ctx.notable_files}")

    # File tree (compact)
    parts.append("\n## File Tree (top-level structure)\n```")
    all_files = walk_repo(repo_path, max_depth=3)
    for f in sorted(all_files)[:200]:
        parts.append(f)
    parts.append("```\n")

    # Key architecturally important files (full content)
    parts.append("\n## Architecturally Important Files (identified by analysis)\n")
    for filepath in key_files:
        if filepath in file_contents:
            parts.append(f"\n### {filepath}\n```\n{file_contents[filepath]}\n```\n")

    # Additional selected files
    parts.append("\n## Additional Source Files\n")
    selected = select_files(repo_path, deep=True)
    for filepath, content in selected:
        if filepath not in file_contents:
            parts.append(f"\n### {filepath}\n```\n{content}\n```\n")

    return "\n".join(parts)


def deep_analyze(ctx: RepoContext, repo_path, provider: str | None = None, model: str | None = None) -> str:
    """Use LLM API with multi-pass analysis to generate a rich CLAUDE.md."""
    if provider is None:
        provider = _detect_provider()

    if provider is None:
        click.echo("Error: No API key found. Set ANTHROPIC_API_KEY or GEMINI_API_KEY.", err=True)
        sys.exit(1)

    # Check cache
    cache_key = _build_file_tree(repo_path)
    cached = get_cached(cache_key)
    if cached:
        click.echo("Using cached analysis result.", err=True)
        return cached

    # --- Pass 1: Architecture Discovery ---
    click.echo("[1/3] Discovering architecture...", err=True)
    discovery_context = _build_discovery_context(ctx, repo_path)
    discovery_response = _call_llm(
        discovery_context,
        provider=provider,
        model=model,
        system=ARCHITECTURE_DISCOVERY_PROMPT,
        max_tokens=2048,
    )

    key_files = _parse_file_list(discovery_response)
    if not key_files:
        # Fallback: use file selector heuristics
        click.echo("  (LLM discovery returned no files, using heuristic selection)", err=True)
        selected = select_files(repo_path, deep=True)
        key_files = [f for f, _ in selected]
    else:
        click.echo(f"  Found {len(key_files)} key files.", err=True)

    # --- Pass 2: Deep Read ---
    click.echo("[2/3] Reading key files and their imports...", err=True)
    file_contents: dict[str, str] = {}
    all_files_set = set(walk_repo(repo_path, max_depth=6))

    # Read key files (full content, higher line limit)
    for filepath in key_files:
        if filepath in all_files_set:
            content = read_file_safe(repo_path / filepath, max_size=512_000)
            if content:
                # Allow up to 500 lines for key files
                lines = content.splitlines(keepends=True)
                if len(lines) > 500:
                    content = "".join(lines[:500]) + f"\n... (truncated, {len(lines) - 500} more lines)\n"
                file_contents[filepath] = content

    # Trace one level of imports for Python files
    try:
        from gitcontext.import_graph import get_imports_of_file

        import_targets: set[str] = set()
        for filepath in key_files:
            if filepath.endswith(".py") and filepath in all_files_set:
                imports = get_imports_of_file(filepath, repo_path)
                import_targets.update(imports)

        # Read imported files (but don't exceed budget)
        chars_used = sum(len(c) for c in file_contents.values())
        max_import_chars = 60_000
        for imp_file in sorted(import_targets):
            if imp_file in file_contents:
                continue
            if chars_used >= max_import_chars:
                break
            content = read_file_safe(repo_path / imp_file, max_size=256_000)
            if content:
                lines = content.splitlines(keepends=True)
                if len(lines) > 300:
                    content = "".join(lines[:300]) + f"\n... (truncated, {len(lines) - 300} more lines)\n"
                if chars_used + len(content) <= max_import_chars + 60_000:
                    file_contents[imp_file] = content
                    chars_used += len(content)
    except Exception:
        pass  # Import tracing is non-critical

    click.echo(f"  Read {len(file_contents)} files total.", err=True)

    # --- Pass 3: Generate CLAUDE.md ---
    click.echo("[3/3] Generating CLAUDE.md...", err=True)
    generation_context = _build_generation_context(ctx, repo_path, key_files, file_contents)

    result = _call_llm(
        generation_context,
        provider=provider,
        model=model,
        system=GENERATION_PROMPT,
        max_tokens=8192,
    )

    # Cache the result
    set_cached(cache_key, result)

    return result
