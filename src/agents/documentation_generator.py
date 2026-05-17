"""
Documentation Generator Agent

Aggregates results from all other agents and generates comprehensive onboarding
documentation including guides, API references, and FAQs.
"""

import json
from typing import Dict, Any, List
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.agents.diagram_utils import (
    embed_mermaid_in_markdown,
    read_mermaid_file,
    normalize_mermaid,
)


class DocumentationGenerator(BaseAgent):
    """
    Agent that generates comprehensive onboarding documentation.
    
    Aggregates analysis results from other agents and uses watsonx.ai to
    generate polished, comprehensive documentation for new developers.
    """
    
    def __init__(self):
        """Initialize the Documentation Generator agent."""
        super().__init__(name="DocumentationGenerator")
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive documentation.
        
        Args:
            context: Analysis context containing:
                - repo_path: Path to repository
                - output_dir: Directory for output files
                - architecture_result: Results from architecture analyzer
                - workflow_result: Results from workflow extractor
                - hotspot_result: Results from hotspot detector
                
        Returns:
            dict: Analysis results with paths to generated files
        """
        repo_path = context.get('repo_path', '.')
        docs_root = Path(context.get("output_dir", "docs"))
        docs_root.mkdir(parents=True, exist_ok=True)

        architecture_result = context.get("architecture_result", {})
        workflow_result = context.get("workflow_result", {})
        hotspot_result = context.get("hotspot_result", {})

        self.log_info("Assembling onboarding guide from agent results...")
        onboarding_guide = self._assemble_onboarding_markdown(
            docs_root, architecture_result, workflow_result, hotspot_result, repo_path
        )

        onboarding_path = docs_root / "ONBOARDING.md"
        onboarding_path.write_text(onboarding_guide, encoding="utf-8")
        self.log_info(f"Onboarding guide saved to {onboarding_path}")

        return {"onboarding_guide": str(onboarding_path)}

    def _assemble_onboarding_markdown(
        self,
        docs_root: Path,
        architecture_result: Dict[str, Any],
        workflow_result: Dict[str, Any],
        hotspot_result: Dict[str, Any],
        repo_path: str,
    ) -> str:
        """Build ONBOARDING.md deterministically with embedded Mermaid (no LLM meta)."""
        arch = architecture_result.get("parsed", {})
        arch_diagrams = arch.get("diagrams", {})
        pattern = arch.get("pattern", "layered")
        summary = arch.get("summary_markdown", "").strip()
        tech = ", ".join(arch.get("tech_stack", [])) or "See ARCHITECTURE.md"

        lines = [
            "# Onboarding Guide\n\n",
            f"Welcome! This guide helps you onboard to **`{repo_path}`**.\n\n",
            f"**Architecture pattern:** {pattern}  \n",
            f"**Tech stack:** {tech}\n\n",
            "See also: [ARCHITECTURE.md](ARCHITECTURE.md) | [WORKFLOWS.md](WORKFLOWS.md)\n\n",
            "## Project overview\n\n",
            summary or "_See [ARCHITECTURE.md](ARCHITECTURE.md) for the full architecture summary._\n\n",
            "## Architecture\n\n",
        ]

        for title, key in [
            ("System context", "c4_context"),
            ("Request flow", "request_flow"),
        ]:
            code = arch_diagrams.get(key) or read_mermaid_file(
                docs_root / "diagrams" / f"architecture-{key}.mmd"
            )
            if code:
                lines.append(embed_mermaid_in_markdown(title, code, heading_level=3))

        lines.append("\n## Common workflows\n\n")
        workflows_path = docs_root / "WORKFLOWS.md"
        if workflows_path.exists():
            wf_body = workflows_path.read_text(encoding="utf-8")
            if wf_body.startswith("# Workflows"):
                wf_body = wf_body.split("\n", 1)[-1].strip()
            lines.append(wf_body)
            lines.append("\n")
        else:
            for wf in workflow_result.get("parsed", {}).get("workflows", []):
                lines.append(f"### {wf.get('name', 'Workflow')}\n\n")
                seq = wf.get("diagrams", {}).get("sequence")
                if seq:
                    lines.append(embed_mermaid_in_markdown("Sequence", seq, heading_level=4))

        lines.append("\n## Code hotspots\n\n")
        hotspot_parsed = hotspot_result.get("parsed", {})
        for h in hotspot_parsed.get("hotspots", [])[:5]:
            lines.append(
                f"- **`{h.get('file', 'unknown')}`** ({h.get('risk', 'medium')}): "
                f"{h.get('advice', 'Review before editing.')}\n"
            )
        heatmap = hotspot_parsed.get("diagrams", {}).get("heatmap") or read_mermaid_file(
            docs_root / "diagrams" / "hotspot-heatmap.mmd"
        )
        if heatmap:
            lines.append("\n")
            lines.append(embed_mermaid_in_markdown("Hotspot map", heatmap, heading_level=3))

        lines.extend(
            [
                "\n## Getting started\n\n",
                "```bash\n",
                "pip install -r requirements.txt\n",
                "python src/main.py\n",
                "pytest tests/\n",
                "```\n\n",
                "## First week checklist\n\n",
                "- [ ] Read this guide and [ARCHITECTURE.md](ARCHITECTURE.md)\n",
                "- [ ] Run the app and tests locally\n",
                "- [ ] Trace the main entry point (`src/main.py` or equivalent)\n",
                "- [ ] Review [WORKFLOWS.md](WORKFLOWS.md) for CI and dev commands\n",
                "- [ ] Note hotspot files before your first PR\n",
            ]
        )
        return "".join(lines)
    
    async def _generate_onboarding_guide(
        self,
        architecture_result: Dict[str, Any],
        workflow_result: Dict[str, Any],
        hotspot_result: Dict[str, Any],
        repo_path: str
    ) -> str:
        """
        Generate comprehensive onboarding guide.
        
        Args:
            architecture_result: Architecture analysis results
            workflow_result: Workflow extraction results
            hotspot_result: Hotspot detection results
            repo_path: Path to repository
            
        Returns:
            str: Markdown-formatted onboarding guide
        """
        arch_parsed = architecture_result.get('parsed', {})
        workflow_parsed = workflow_result.get('parsed', {})
        hotspot_parsed = hotspot_result.get('parsed', {})
        arch_diagrams = arch_parsed.get('diagrams', {})
        workflow_diagrams = workflow_parsed.get('workflows', [])
        hotspot_diagrams = hotspot_parsed.get('diagrams', {})

        structure = architecture_result.get('structure', {})
        entry_points = architecture_result.get('entry_points', [])
        dependencies = architecture_result.get('dependencies', [])
        hotspots = hotspot_result.get('hotspots', [])
        
        # Prepare summary
        total_files = structure.get('totalFiles', 0)
        file_types = structure.get('filesByExtension', {})
        primary_lang = max(file_types.items(), key=lambda x: x[1])[0] if file_types else 'Unknown'
        
        critical_hotspots = [h for h in hotspots if h.get('risk_level') == 'CRITICAL']
        
        diagram_context = json.dumps(
            {
                "architecture_diagrams": arch_diagrams,
                "workflows": workflow_diagrams,
                "hotspot_diagrams": hotspot_diagrams,
            },
            indent=2,
        )

        prompt = self.format_prompt(
            """You are creating a comprehensive onboarding guide for new developers joining a project. Create a welcoming, informative guide.

## Project Overview
- Repository: {repo_path}
- Total Files: {total_files}
- Primary Language: {primary_lang}
- Entry Points: {entry_point_count}
- Dependencies: {dependency_count}
- Critical Hotspots: {hotspot_count}

## Key Entry Points
{entry_points}

## Top Dependencies
{dependencies}

## Areas Requiring Attention
{hotspots}

## Mermaid diagrams (embed verbatim in markdown fences)
{diagram_context}

Create a comprehensive onboarding guide in Markdown format with these sections:

1. **Welcome** - Friendly introduction to the project
2. **Project Overview** - What the project does and its purpose
3. **Getting Started** - Quick start guide
4. **Architecture Overview** - Embed c4_context and request_flow Mermaid diagrams exactly as provided
5. **Key Components** - Important parts of the codebase
6. **Common Workflows** - Embed workflow sequence Mermaid diagrams exactly as provided
7. **Code Hotspots** - Embed heatmap Mermaid exactly as provided; advice for new devs
8. **First Week Checklist** - Actionable checklist
9. **Getting Help** - Where to find help and resources
10. **Next Steps** - What to do after reading this guide

Preserve every ```mermaid code block from the diagram data. Link to ARCHITECTURE.md and WORKFLOWS.md.""",
            diagram_context=diagram_context,
            repo_path=repo_path,
            total_files=total_files,
            primary_lang=primary_lang,
            entry_point_count=len(entry_points),
            dependency_count=len(dependencies),
            hotspot_count=len(critical_hotspots),
            entry_points=self._format_entry_points(entry_points[:5]),
            dependencies=self._format_dependencies(dependencies[:10]),
            hotspots=self._format_hotspots_summary(critical_hotspots[:5])
        )
        
        guide = await self.generate(prompt, max_tokens=2500, temperature=0.4)
        
        header = f"""# 🚀 Onboarding Guide

**Welcome to the team!** This guide will help you get up to speed with the codebase.

**Generated by:** DevRamp Documentation Generator  
**Date:** {self._get_timestamp()}

---

"""
        
        footer = """

---

## 📚 Additional Resources

- [Architecture](ARCHITECTURE.md) - Detailed architecture analysis
- [Workflows](WORKFLOWS.md) - Development workflows and processes
- [API Reference](API_REFERENCE.md) - API documentation
- [FAQ](FAQ.md) - Frequently asked questions

## 🤝 Contributing

We're excited to have you contribute! Please read through this guide and the linked resources before making changes.

**Happy coding!** 🎉
"""
        
        return header + guide + footer

    def _ensure_diagrams_in_onboarding(
        self,
        guide: str,
        architecture_result: Dict[str, Any],
        workflow_result: Dict[str, Any],
        hotspot_result: Dict[str, Any],
    ) -> str:
        """Inject Mermaid blocks if the LLM omitted them."""
        if "```mermaid" in guide:
            return guide

        blocks: List[str] = []
        arch_diagrams = architecture_result.get("parsed", {}).get("diagrams", {})
        for title, key in [
            ("System Context", "c4_context"),
            ("Request Flow", "request_flow"),
        ]:
            if arch_diagrams.get(key):
                blocks.append(embed_mermaid_in_markdown(title, arch_diagrams[key]))

        for wf in workflow_result.get("parsed", {}).get("workflows", []):
            seq = wf.get("diagrams", {}).get("sequence")
            if seq:
                blocks.append(
                    embed_mermaid_in_markdown(
                        wf.get("name", "Workflow"), seq, heading_level=3
                    )
                )

        hotspot_diagrams = hotspot_result.get("parsed", {}).get("diagrams", {})
        if hotspot_diagrams.get("heatmap"):
            blocks.append(
                embed_mermaid_in_markdown("Hotspot Map", hotspot_diagrams["heatmap"])
            )

        if not blocks:
            return guide

        return guide + "\n\n## Diagrams\n\n" + "\n".join(blocks)

    async def _generate_api_reference(
        self,
        architecture_result: Dict[str, Any],
        repo_path: str
    ) -> str:
        """
        Generate API reference documentation.
        
        Args:
            architecture_result: Architecture analysis results
            repo_path: Path to repository
            
        Returns:
            str: Markdown-formatted API reference
        """
        entry_points = architecture_result.get('entry_points', [])
        structure = architecture_result.get('structure', {})
        dependencies = architecture_result.get('dependencies', [])
        
        prompt = self.format_prompt(
            """You are creating API reference documentation for a codebase. Generate comprehensive API documentation.

## Project Information
- Repository: {repo_path}
- Entry Points: {entry_point_count}
- Key Dependencies: {dependency_count}

## Entry Points
{entry_points}

## Dependencies
{dependencies}

Create API reference documentation in Markdown format with these sections:

1. **Overview** - What this API reference covers
2. **Entry Points** - Main entry points and how to use them
3. **Core Modules** - Key modules and their purposes
4. **Public APIs** - Public interfaces and functions
5. **Configuration** - Configuration options and environment variables
6. **Error Handling** - Common errors and how to handle them
7. **Examples** - Usage examples
8. **Best Practices** - Recommended patterns for using the API

Be technical and specific. Include code examples where appropriate.""",
            repo_path=repo_path,
            entry_point_count=len(entry_points),
            dependency_count=len(dependencies),
            entry_points=self._format_entry_points(entry_points),
            dependencies=self._format_dependencies(dependencies[:15])
        )
        
        reference = await self.generate(prompt, max_tokens=2000, temperature=0.3)
        
        header = f"""# API Reference

**Generated by:** DevRamp Documentation Generator  
**Date:** {self._get_timestamp()}

---

"""
        
        return header + reference
    
    async def _generate_faq(
        self,
        architecture_result: Dict[str, Any],
        workflow_result: Dict[str, Any],
        hotspot_result: Dict[str, Any]
    ) -> str:
        """
        Generate FAQ documentation.
        
        Args:
            architecture_result: Architecture analysis results
            workflow_result: Workflow extraction results
            hotspot_result: Hotspot detection results
            
        Returns:
            str: Markdown-formatted FAQ
        """
        structure = architecture_result.get('structure', {})
        hotspots = hotspot_result.get('hotspots', [])
        
        file_types = structure.get('filesByExtension', {})
        primary_lang = max(file_types.items(), key=lambda x: x[1])[0] if file_types else 'Unknown'
        
        prompt = self.format_prompt(
            """You are creating a FAQ (Frequently Asked Questions) document for developers working on a codebase.

## Project Context
- Primary Language: {primary_lang}
- Total Files: {total_files}
- High-Risk Files: {hotspot_count}

Generate a comprehensive FAQ in Markdown format covering:

1. **Getting Started**
   - How do I set up the development environment?
   - What are the prerequisites?
   - How do I run the project locally?

2. **Development**
   - What's the development workflow?
   - How do I run tests?
   - What coding standards should I follow?

3. **Architecture**
   - How is the code organized?
   - What are the main components?
   - What design patterns are used?

4. **Common Issues**
   - What are common setup problems?
   - How do I debug issues?
   - What should I do if tests fail?

5. **Contributing**
   - How do I contribute code?
   - What's the code review process?
   - How do I report bugs?

6. **Technical Debt**
   - What areas need improvement?
   - What should I avoid changing?
   - What's the refactoring strategy?

Make answers practical and actionable. Include specific examples.""",
            primary_lang=primary_lang,
            total_files=structure.get('totalFiles', 0),
            hotspot_count=len([h for h in hotspots if h.get('risk_level') in ['CRITICAL', 'HIGH']])
        )
        
        faq = await self.generate(prompt, max_tokens=2000, temperature=0.4)
        
        header = f"""# Frequently Asked Questions (FAQ)

**Generated by:** DevRamp Documentation Generator  
**Date:** {self._get_timestamp()}

---

"""
        
        footer = """

---

## 💡 Didn't Find Your Answer?

If your question isn't answered here:

1. Check the [Onboarding Guide](ONBOARDING_GUIDE.md)
2. Review the [Architecture Report](architecture_report.md)
3. Read the [Workflow Guide](workflow_guide.md)
4. Ask your team lead or mentor
5. Check the project's issue tracker

**We're here to help!** Don't hesitate to ask questions.
"""
        
        return header + faq + footer
    
    def _format_entry_points(self, entry_points: List[Dict]) -> str:
        """Format entry points for prompt."""
        if not entry_points:
            return "No entry points identified."
        
        lines = []
        for ep in entry_points:
            path = ep.get('path', '')
            ep_type = ep.get('type', '')
            reason = ep.get('reason', '')
            lines.append(f"- `{path}` ({ep_type}): {reason}")
        
        return '\n'.join(lines)
    
    def _format_dependencies(self, dependencies: List[Dict]) -> str:
        """Format dependencies for prompt."""
        if not dependencies:
            return "No dependencies found."
        
        lines = []
        for dep in dependencies:
            name = dep.get('name', '')
            count = dep.get('count', 0)
            lines.append(f"- `{name}`: used in {count} file(s)")
        
        return '\n'.join(lines)
    
    def _format_hotspots_summary(self, hotspots: List[Dict]) -> str:
        """Format hotspots summary for prompt."""
        if not hotspots:
            return "No critical hotspots identified."
        
        lines = []
        for h in hotspots:
            path = h.get('path', '')
            risk = h.get('risk_score', 0)
            lines.append(f"- `{path}`: Risk score {risk}/100")
        
        return '\n'.join(lines)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Made with Bob
