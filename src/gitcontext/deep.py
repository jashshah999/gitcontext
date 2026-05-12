"""Deep analysis using LLM APIs (Claude or Gemini)."""

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

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"


def _build_context(ctx: RepoContext, repo_path) -> str:
    click.echo("Selecting key files...", err=True)
    files = select_files(repo_path)

    context_parts = []
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

    context_parts.append("\n\n## Key Source Files\n")
    for filepath, content in files:
        context_parts.append(f"\n### {filepath}\n```\n{content}\n```\n")

    return "\n".join(context_parts)


def _detect_provider():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    return None


def _call_anthropic(user_message: str, model: str | None = None) -> str:
    try:
        import anthropic
    except ImportError:
        click.echo("Error: 'anthropic' package required. Install with: pip install 'gitcontext[deep]'", err=True)
        sys.exit(1)

    model = model or DEFAULT_ANTHROPIC_MODEL
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    click.echo(f"Analyzing with Claude ({model})...", err=True)

    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def _call_gemini(user_message: str, model: str | None = None) -> str:
    try:
        import google.generativeai as genai
    except ImportError:
        click.echo("Error: 'google-generativeai' package required. Install with: pip install 'gitcontext[gemini]'", err=True)
        sys.exit(1)

    model_name = model or DEFAULT_GEMINI_MODEL
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    click.echo(f"Analyzing with Gemini ({model_name})...", err=True)

    genai_model = genai.GenerativeModel(model_name)
    response = genai_model.generate_content(
        f"{SYSTEM_PROMPT}\n\n---\n\n{user_message}",
        generation_config=genai.GenerationConfig(max_output_tokens=4096),
    )
    return response.text


def deep_analyze(ctx: RepoContext, repo_path, provider: str | None = None, model: str | None = None) -> str:
    """Use LLM API to generate a rich CLAUDE.md from repo context and source files."""
    if provider is None:
        provider = _detect_provider()

    if provider is None:
        click.echo("Error: No API key found. Set ANTHROPIC_API_KEY or GEMINI_API_KEY.", err=True)
        sys.exit(1)

    user_message = _build_context(ctx, repo_path)

    if provider == "anthropic":
        return _call_anthropic(user_message, model=model)
    elif provider == "gemini":
        return _call_gemini(user_message, model=model)
    else:
        click.echo(f"Error: Unknown provider '{provider}'.", err=True)
        sys.exit(1)
