"""Parse CI configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from gitcontext.utils import read_file_safe


@dataclass
class CIInfo:
    provider: str = ""
    workflows: list[str] = field(default_factory=list)
    test_commands: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)


def detect_ci(repo_path: Path, files: list[str]) -> CIInfo:
    """Detect CI configuration and extract info."""
    info = CIInfo()

    # GitHub Actions
    workflows_dir = repo_path / ".github" / "workflows"
    if workflows_dir.is_dir():
        info.provider = "GitHub Actions"
        for wf_file in sorted(workflows_dir.iterdir()):
            if wf_file.suffix in (".yml", ".yaml"):
                info.workflows.append(wf_file.stem)
                _parse_github_workflow(wf_file, info)

    # GitLab CI
    elif ".gitlab-ci.yml" in files:
        info.provider = "GitLab CI"
        content = read_file_safe(repo_path / ".gitlab-ci.yml")
        if content:
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    info.workflows = [k for k in data if not k.startswith(".") and k != "stages"]
            except yaml.YAMLError:
                pass

    # CircleCI
    elif os.path.join(".circleci", "config.yml") in files:
        info.provider = "CircleCI"

    return info


def _parse_github_workflow(path: Path, info: CIInfo) -> None:
    """Extract test commands and env vars from a GitHub Actions workflow."""
    content = read_file_safe(path)
    if not content:
        return
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return
    if not isinstance(data, dict):
        return

    # Collect env vars
    if "env" in data and isinstance(data["env"], dict):
        info.env_vars.extend(data["env"].keys())

    # Walk jobs for run steps
    jobs = data.get("jobs", {})
    if not isinstance(jobs, dict):
        return
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps", [])
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            run = step.get("run", "")
            if "test" in run.lower() or "pytest" in run or "jest" in run:
                # Take first line only
                cmd = run.strip().splitlines()[0]
                if cmd and cmd not in info.test_commands:
                    info.test_commands.append(cmd)
