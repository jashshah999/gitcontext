"""Deep analysis using Claude API."""

from __future__ import annotations

import os
import sys
import click

from gitcontext.analyzer import RepoContext
from gitcontext.file_selector import select_files

SYSTEM_PROMPT = """You are analyzing a codebase to generate a CLAUDE.md file that will help AI coding assistants understand this project instantly.

Generate a CLAUDE.md that includes:
1. Project overview (1-2 sentences, what it does and why)
2. Tech stack (concise)
3. Development setup (exact commands)
4. Key commands (test, lint, build, run)
5. Architecture - for each key directory, explain what it contains and WHY (not just file names)
6. Important conventions and patterns (naming, inheritance hierarchies, config systems)
7. Common gotchas and non-obvious behaviors
8. Notes for contributors

Be concise. No fluff. A senior engineer should be able to read this in 2 minutes and start contributing."""


def deep_analyze(ctx: RepoContext, repo_path) -> str:
    """Use Claude API to generate a rich CLAUDE.md from repo context and source files."""
    try:
        import anthropic
    except ImportError:
        click.echo("Error: 'anthropic' package required for --deep mode.", err=True)
        click.echo("Install with: pip install 'gitcontext[deep]'", err=True)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY environment variable not set.", err=True)
        sys.exit(1)

    # Select important files
    click.echo("Selecting key files...", err=True)
    files = select_files(repo_path)

    # Build the user message
    context_parts = []

    # Static analysis summary
    context_parts.append("## Static Analysis Results\n")
    context_parts.append(f"Name: {ctx.name}")
    context_parts.append(f"Description: {ctx.description}")
    context_parts.append(f"Languages: {ctx.languages[:5]}")
    context_parts.append(f"Frameworks: {ctx.frameworks}")
    context_parts.append(f"Build system: {ctx.build.system}")
    context_parts.append(f"Install command: {ctx.build.install_cmd}")
    context_parts.append(f"Test command: {ctx.test.test_command}")
    context_parts.append(f"Test framework: {ctx.test.framework}")
    context_parts.append(f"CI: {ctx.ci.provider}")
    context_parts.append(f"Entry points: {ctx.entry_points}")
    context_parts.append(f"Architecture: {ctx.architecture}")
    context_parts.append(f"Notable files: {ctx.notable_files}")

    # File contents
    context_parts.append("\n\n## Key Source Files\n")
    for filepath, content in files:
        context_parts.append(f"\n### {filepath}\n```\n{content}\n```\n")

    user_message = "\n".join(context_parts)

    # Call Claude API
    click.echo("Analyzing with Claude...", err=True)
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text
