"""CLI entrypoint for gitcontext."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import click

from gitcontext.analyzer import RepoAnalyzer
from gitcontext.generators.claude_md import generate_agents_md, generate_claude_md
from gitcontext.github import cleanup_clone, clone_repo, is_github_url


@click.command()
@click.argument("target", default=".")
@click.option("--output", "-o", default=None, help="Write to file (default: stdout)")
@click.option("--format", "fmt", type=click.Choice(["claude", "agents"]), default="claude", help="Output format")
@click.option("--verbose", "-v", is_flag=True, help="Show detection details")
@click.option("--deep", is_flag=True, help="Use LLM API for rich analysis (requires GEMINI_API_KEY or ANTHROPIC_API_KEY)")
@click.option("--model", default=None, help="Model to use for --deep (e.g. gemini-2.5-flash, claude-sonnet-4-20250514)")
def main(target: str, output: str | None, fmt: str, verbose: bool, deep: bool, model: str | None) -> None:
    """Generate AI context docs (CLAUDE.md / AGENTS.md) for a codebase.

    TARGET can be a local path or a GitHub URL.
    """
    cloned_path = None

    try:
        if is_github_url(target):
            # Check git is available
            if not shutil.which("git"):
                click.echo("Error: git is not installed or not on PATH. Install git to clone remote repos.", err=True)
                click.echo("Alternatively, clone the repo manually and pass the local path.", err=True)
                sys.exit(1)
            if verbose:
                click.echo(f"Cloning {target}...", err=True)
            try:
                repo_path = clone_repo(target)
            except RuntimeError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)
            cloned_path = repo_path
        else:
            repo_path = Path(target).resolve()
            if not repo_path.is_dir():
                click.echo(f"Error: {target} is not a directory", err=True)
                sys.exit(1)

        analyzer = RepoAnalyzer(repo_path)
        ctx = analyzer.analyze()

        if verbose:
            click.echo(f"Name: {ctx.name}", err=True)
            click.echo(f"Languages: {ctx.languages[:5]}", err=True)
            click.echo(f"Frameworks: {ctx.frameworks}", err=True)
            click.echo(f"Build: {ctx.build.system}", err=True)
            click.echo(f"Test: {ctx.test.framework}", err=True)
            click.echo(f"CI: {ctx.ci.provider}", err=True)
            click.echo("---", err=True)

        if deep:
            try:
                from gitcontext.deep import deep_analyze

                content = deep_analyze(ctx, repo_path, model=model)
            except Exception as e:
                click.echo(f"Warning: --deep failed ({e}). Falling back to static analysis.", err=True)
                if fmt == "agents":
                    content = generate_agents_md(ctx)
                else:
                    content = generate_claude_md(ctx)
        elif fmt == "agents":
            content = generate_agents_md(ctx)
        else:
            content = generate_claude_md(ctx)

        if output:
            Path(output).write_text(content)
            if verbose:
                click.echo(f"Written to {output}", err=True)
        else:
            click.echo(content)

    finally:
        if cloned_path:
            cleanup_clone(cloned_path)


if __name__ == "__main__":
    main()
