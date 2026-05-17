import json
import re
from pathlib import Path
from typing import Any, Dict


def clean_llm_text(text: str) -> str:
    """Strip common model wrappers before JSON/markdown parsing."""
    cleaned = text.strip()
    cleaned = re.sub(r"^assistant\w*\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def extract_json_from_llm_text(text: str) -> Dict[str, Any]:
    cleaned = clean_llm_text(text)
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            data = json.loads(cleaned[start : end + 1])
        else:
            raise
    return _normalize_parsed_payload(data)


def _normalize_parsed_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize diagram strings and summary text after JSON parse."""
    if "diagrams" in data and isinstance(data["diagrams"], dict):
        data["diagrams"] = normalize_diagram_dict(data["diagrams"])
    if "summary_markdown" in data and isinstance(data["summary_markdown"], str):
        data["summary_markdown"] = data["summary_markdown"].replace("\\n", "\n")
    if "workflows" in data and isinstance(data["workflows"], list):
        for wf in data["workflows"]:
            if isinstance(wf.get("diagrams"), dict):
                wf["diagrams"] = normalize_diagram_dict(wf["diagrams"])
    return data


def normalize_diagram_dict(diagrams: Dict[str, str]) -> Dict[str, str]:
    return {key: normalize_mermaid(str(code)) for key, code in diagrams.items() if code}


def build_fallback_architecture_diagrams(
    entry_points: list,
    dependencies: list,
) -> Dict[str, str]:
    """Deterministic Mermaid when the LLM does not return valid JSON."""
    lines = ["graph TB", "    Dev[Developer] --> App[Application]"]
    for i, ep in enumerate(entry_points[:5]):
        path = ep.get("path", f"entry{i}")
        node_id = re.sub(r"[^a-zA-Z0-9]", "", path)[:20] or f"E{i}"
        label = path.replace('"', "'")
        lines.append(f"    App --> {node_id}[{label}]")
    for i, dep in enumerate(dependencies[:5]):
        name = dep.get("name", f"dep{i}")
        node_id = re.sub(r"[^a-zA-Z0-9]", "", name)[:20] or f"D{i}"
        lines.append(f"    App --> {node_id}[{name}]")
    c4 = "\n".join(lines)
    flow = (
        "flowchart LR\n"
        "    Start([Start]) --> Entry[Entry Point]\n"
        "    Entry --> Logic[Application Logic]\n"
        "    Logic --> End([End])"
    )
    dep_lines = ["graph LR", "    App[Application]"]
    for i, dep in enumerate(dependencies[:8]):
        name = dep.get("name", f"dep{i}")
        node_id = re.sub(r"[^a-zA-Z0-9]", "", name)[:20] or f"D{i}"
        dep_lines.append(f"    App --> {node_id}[{name}]")
    return {
        "c4_context": c4,
        "request_flow": flow,
        "dependency_graph": "\n".join(dep_lines),
    }


def build_fallback_workflow_diagram(name: str = "Development workflow") -> Dict[str, Any]:
    return {
        "workflows": [
            {
                "name": name,
                "steps": [
                    "Install dependencies",
                    "Run the application or tests",
                    "Commit and push changes",
                ],
                "diagrams": {
                    "sequence": (
                        "sequenceDiagram\n"
                        "    participant Dev as Developer\n"
                        "    participant App as Application\n"
                        "    participant CI as CI Pipeline\n"
                        "    Dev->>App: run / test\n"
                        "    App-->>Dev: result\n"
                        "    Dev->>CI: push\n"
                        "    CI-->>Dev: pass/fail"
                    )
                },
            }
        ]
    }


def build_fallback_hotspot_diagrams(hotspots: list) -> Dict[str, Any]:
    lines = ["graph TB", "    subgraph Hotspots"]
    for i, h in enumerate(hotspots[:10]):
        path = h.get("path", h.get("file", f"file{i}"))
        node_id = f"F{i}"
        risk = h.get("risk_level", h.get("risk", "medium"))
        label = path.split("/")[-1].split("\\")[-1][:30]
        lines.append(f"        {node_id}[{label}<br/>{risk}]")
    lines.append("    end")
    return {
        "hotspots": [
            {
                "file": h.get("path", ""),
                "risk": h.get("risk_level", "medium"),
                "advice": "Review changes carefully; high churn area.",
            }
            for h in hotspots[:10]
        ],
        "diagrams": {
            "heatmap": "\n".join(lines),
            "timeline": (
                "timeline\n"
                "    title Repository activity\n"
                "    section Analysis : Active development on hotspot files"
            ),
        },
    }


def normalize_mermaid(mermaid_code: str) -> str:
    """Turn JSON-escaped newlines into real newlines for rendering."""
    code = mermaid_code.strip()
    while "\\n" in code:
        code = code.replace("\\n", "\n")
    return code


def read_mermaid_file(path: Path) -> str:
    if path.exists():
        return normalize_mermaid(path.read_text(encoding="utf-8"))
    return ""


def write_mermaid_file(output_dir: Path, name: str, mermaid_code: str) -> Path:
    diagrams_dir = output_dir / "diagrams"
    diagrams_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", name).strip("-").lower() or "diagram"
    path = diagrams_dir / f"{safe}.mmd"
    path.write_text(normalize_mermaid(mermaid_code) + "\n", encoding="utf-8")
    return path


def embed_mermaid_in_markdown(
    title: str, mermaid_code: str, heading_level: int = 2
) -> str:
    hashes = "#" * heading_level
    return (
        f"{hashes} {title}\n\n"
        f"```mermaid\n{normalize_mermaid(mermaid_code)}\n```\n"
    )


def persist_diagrams(
    output_dir: Path,
    diagrams: Dict[str, str],
    prefix: str = "",
) -> Dict[str, Path]:
    written: Dict[str, Path] = {}
    for key, code in diagrams.items():
        if not code or not str(code).strip():
            continue
        name = f"{prefix}-{key}" if prefix else key
        written[key] = write_mermaid_file(output_dir, name, str(code))
    return written
