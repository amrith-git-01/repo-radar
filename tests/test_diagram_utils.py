import json
from pathlib import Path

from src.agents.diagram_utils import (
    extract_json_from_llm_text,
    write_mermaid_file,
    embed_mermaid_in_markdown,
)


def test_extract_json_from_llm_text_strips_fences():
    text = '```json\n{"diagrams": {"a": "graph TB\\n  A-->B"}}\n```'
    data = extract_json_from_llm_text(text)
    assert data["diagrams"]["a"].startswith("graph TB")


def test_write_mermaid_file_creates_file(tmp_path: Path):
    path = write_mermaid_file(tmp_path, "arch", "graph TB\n  A-->B")
    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("graph TB")


def test_embed_mermaid_in_markdown():
    md = embed_mermaid_in_markdown("Title", "graph TB\n  A-->B", heading_level=2)
    assert "## Title" in md
    assert "```mermaid" in md
    assert "A-->B" in md


def test_normalize_mermaid_json_escaped_newlines():
    raw = "graph TB\\n  A-->B\\n  B-->C"
    normalized = __import__(
        "src.agents.diagram_utils", fromlist=["normalize_mermaid"]
    ).normalize_mermaid(raw)
    assert "\\n" not in normalized
    assert normalized.count("\n") >= 2
