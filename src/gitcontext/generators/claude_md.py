"""Generate CLAUDE.md content from RepoContext."""

from __future__ import annotations

from gitcontext.analyzer import RepoContext


def generate_claude_md(ctx: RepoContext) -> str:
    """Generate CLAUDE.md markdown content."""
    sections = []

    # Project Overview
    overview = f"## Project Overview\n\n"
    if ctx.description:
        primary_lang = ctx.languages[0][0] if ctx.languages else "software"
        overview += f"{ctx.name} — {ctx.description}\n"
    else:
        overview += f"{ctx.name}\n"
    sections.append(overview)

    # Tech Stack
    if ctx.languages or ctx.frameworks:
        parts = []
        if ctx.languages:
            # Show top 3 languages
            for lang, pct in ctx.languages[:3]:
                if pct > 5:
                    parts.append(lang)
        parts.extend(ctx.frameworks[:8])
        if ctx.build.system and ctx.build.system not in parts:
            parts.append(ctx.build.system)
        if parts:
            sections.append(f"## Tech Stack\n\n{' · '.join(parts)}\n")

    # Development Setup
    setup_lines = []
    if ctx.build.install_cmd:
        setup_lines.append(ctx.build.install_cmd)
    if ctx.build.build_cmd:
        setup_lines.append(ctx.build.build_cmd)
    if setup_lines:
        code = "\n".join(setup_lines)
        sections.append(f"## Development Setup\n\n```bash\n{code}\n```\n")

    # Key Commands
    cmd_lines = []
    if ctx.test.test_command:
        cmd_lines.append(f"{ctx.test.test_command}")
    if ctx.build.lint_cmd:
        cmd_lines.append(f"{ctx.build.lint_cmd}")
    if ctx.build.run_cmd and ctx.build.run_cmd not in ("python", "uv run python"):
        cmd_lines.append(f"{ctx.build.run_cmd}")
    for name, cmd in ctx.build.extra_commands.items():
        if cmd not in cmd_lines:
            cmd_lines.append(cmd)
    if cmd_lines:
        code = "\n".join(cmd_lines)
        sections.append(f"## Key Commands\n\n```bash\n{code}\n```\n")

    # Architecture
    if ctx.architecture:
        arch_lines = []
        for dirname, desc in ctx.architecture:
            arch_lines.append(f"- **`{dirname}/`** — {desc}")
        sections.append(f"## Architecture\n\n" + "\n".join(arch_lines) + "\n")

    # Entry Points (cap at 6 to keep concise)
    if ctx.entry_points:
        shown = ctx.entry_points[:6]
        ep_lines = [f"- `{ep}`" for ep in shown]
        if len(ctx.entry_points) > 6:
            ep_lines.append(f"- ... and {len(ctx.entry_points) - 6} more (see pyproject.toml)")
        sections.append(f"## Entry Points\n\n" + "\n".join(ep_lines) + "\n")

    # CI
    if ctx.ci.provider:
        ci_text = f"CI: {ctx.ci.provider}"
        if ctx.ci.workflows:
            ci_text += f" ({', '.join(ctx.ci.workflows[:5])})"
        sections.append(f"## CI/CD\n\n{ci_text}\n")

    # Notes
    notes = []
    if ctx.notable_files:
        notes.append(f"Notable files: {', '.join(ctx.notable_files)}")
    if ctx.ci.env_vars:
        notes.append(f"Required env vars: {', '.join(sorted(set(ctx.ci.env_vars))[:5])}")
    if notes:
        note_lines = [f"- {n}" for n in notes]
        sections.append(f"## Notes\n\n" + "\n".join(note_lines) + "\n")

    return "\n".join(sections)


def generate_agents_md(ctx: RepoContext) -> str:
    """Generate AGENTS.md format (slightly different structure)."""
    # AGENTS.md uses a more directive tone
    sections = []

    sections.append(f"# {ctx.name}\n")
    if ctx.description:
        sections.append(f"{ctx.description}\n")

    # Setup
    if ctx.build.install_cmd:
        sections.append(f"## Setup\n\n```bash\n{ctx.build.install_cmd}\n```\n")

    # Commands
    cmd_lines = []
    if ctx.test.test_command:
        cmd_lines.append(f"# Run tests\n{ctx.test.test_command}")
    if ctx.build.lint_cmd:
        cmd_lines.append(f"# Lint\n{ctx.build.lint_cmd}")
    if ctx.build.build_cmd:
        cmd_lines.append(f"# Build\n{ctx.build.build_cmd}")
    if cmd_lines:
        code = "\n\n".join(cmd_lines)
        sections.append(f"## Commands\n\n```bash\n{code}\n```\n")

    # Structure
    if ctx.architecture:
        arch_lines = [f"- `{d}/` — {desc}" for d, desc in ctx.architecture]
        sections.append(f"## Structure\n\n" + "\n".join(arch_lines) + "\n")

    return "\n".join(sections)
