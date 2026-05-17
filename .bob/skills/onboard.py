"""Bob Skill: Full repo onboarding. Usage: @onboard [path]"""
import subprocess
import sys
from pathlib import Path


def _normalize_repo_path(repo_path: str) -> str:
    """Map user phrases like 'test repo' to test_repo."""
    cleaned = (repo_path or ".").strip().strip("@")
    aliases = {
        "test repo": "test_repo",
        "test-repo": "test_repo",
        "testrepo": "test_repo",
    }
    return aliases.get(cleaned.lower(), cleaned)


async def onboard(repo_path: str = ".", context=None) -> str:
    """
    Run the DevRamp multi-agent onboarding pipeline.

    Usage:
        @onboard
        @onboard test_repo
    """
    repo_path = _normalize_repo_path(repo_path)
    root = Path(__file__).resolve().parents[2]
    runner = root / "scripts" / "onboard_runner.py"
    target = root / repo_path
    if repo_path != "." and not target.is_dir():
        return (
            f"## Onboarding failed\n\n"
            f"Repository path `{repo_path}` not found under `{root}`.\n\n"
            "Try: `@onboard test_repo` or `@onboard .` for the workspace root."
        )

    proc = subprocess.run(
        [sys.executable, str(runner), "--repo-path", repo_path, "--output-dir", "docs"],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return (
            "## Onboarding failed\n\n"
            f"```\n{(proc.stderr or proc.stdout)[-2000:]}\n```\n\n"
            "Check:\n"
            "- `cd src/mcp-servers && npm run build`\n"
            "- `.env` watsonx keys\n"
            "- Run once locally: `python scripts/onboard_runner.py --repo-path test_repo`"
        )
    onboarding = root / "docs" / "ONBOARDING.md"
    diagrams_dir = root / "docs" / "diagrams"
    mmd_count = len(list(diagrams_dir.glob("*.mmd"))) if diagrams_dir.exists() else 0
    body = onboarding.read_text(encoding="utf-8") if onboarding.exists() else ""
    preview = body[:6000]
    return (
        "## Onboarding complete (DevRamp pipeline)\n\n"
        "Generated on disk:\n"
        "- `docs/ONBOARDING.md`\n"
        "- `docs/ARCHITECTURE.md`\n"
        "- `docs/WORKFLOWS.md`\n"
        f"- `docs/diagrams/` ({mmd_count} `.mmd` files)\n"
        "- `generated/analysis.json`\n\n"
        "Export this Bob session to `bob_sessions/02_onboarding/` for judges.\n\n"
        "---\n\n"
        f"{preview}"
    )


__skill_metadata__ = {
    "name": "onboard",
    "description": "Run full DevRamp onboarding (MCP + watsonx) and write docs with Mermaid diagrams",
    "usage": "@onboard [repo_path]",
    "aliases": ["onboard_me", "onboard_repo"],
    "category": "onboarding",
    "requires_mcp": ["code-analyzer", "git-analyzer", "documentation-generator"],
    "version": "1.0.0",
}
