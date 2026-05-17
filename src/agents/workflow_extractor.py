"""
Workflow Extractor Agent

Extracts development workflows, build processes, and setup instructions from
configuration files and generates workflow documentation.
"""

import json
import os
import re
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.agents.diagram_utils import (
    extract_json_from_llm_text,
    embed_mermaid_in_markdown,
    write_mermaid_file,
    build_fallback_workflow_diagram,
)


class WorkflowExtractor(BaseAgent):
    """
    Agent that extracts and documents development workflows.
    
    Analyzes build files, CI/CD configurations, and other workflow-related
    files to generate comprehensive workflow documentation.
    """
    
    def __init__(self):
        """Initialize the Workflow Extractor agent."""
        super().__init__(name="WorkflowExtractor")
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and document workflows.
        
        Args:
            context: Analysis context containing:
                - repo_path: Path to repository
                - output_dir: Directory for output files
                
        Returns:
            dict: Analysis results with paths to generated files
        """
        repo_path = Path(context.get('repo_path', '.'))
        output_dir = Path(context.get('output_dir', 'docs/onboarding'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_info(f"Extracting workflows from {repo_path}")
        
        # Step 1: Discover workflow files
        workflow_files = self._discover_workflow_files(repo_path)
        self.log_info(f"Found {len(workflow_files)} workflow-related files")
        
        # Step 2: Parse workflow files
        workflows = {}
        for file_type, file_path in workflow_files.items():
            self.log_info(f"Parsing {file_type}: {file_path}")
            content = self._read_file(file_path)
            workflows[file_type] = {
                'path': str(file_path.relative_to(repo_path)),
                'content': content
            }
        
        # Step 3: Generate workflow guide
        self.log_info("Generating workflow guide with watsonx.ai...")
        workflow_report = await self._generate_workflow_guide(workflows)
        workflow_data = self._parse_workflow_json(workflow_report)
        if workflow_data is None:
            workflow_report = await self._generate_workflow_guide(workflows, json_only=True)
            workflow_data = self._parse_workflow_json(workflow_report)
        if workflow_data is None:
            workflow_data = build_fallback_workflow_diagram("Standard development workflow")

        docs_root = output_dir.parent if output_dir.name == "onboarding" else output_dir
        lines = ["# Workflows\n\n"]
        for wf in workflow_data.get("workflows", []):
            lines.append(f"## {wf.get('name', 'Workflow')}\n\n")
            for step in wf.get("steps", []):
                lines.append(f"- {step}\n")
            seq = wf.get("diagrams", {}).get("sequence")
            if seq:
                slug = re.sub(r"[^a-z0-9]+", "-", wf.get("name", "workflow").lower()).strip("-")
                write_mermaid_file(docs_root, f"workflow-{slug}", seq)
                lines.append("\n")
                lines.append(embed_mermaid_in_markdown("Sequence", seq, heading_level=3))
            lines.append("\n")
        workflows_path = docs_root / "WORKFLOWS.md"
        workflows_path.write_text("".join(lines), encoding="utf-8")
        self.log_info(f"Workflows saved to {workflows_path}")

        return {
            "workflow_guide": str(workflows_path),
            "discovered_files": {k: v["path"] for k, v in workflows.items()},
            "parsed": workflow_data,
        }

    def _parse_workflow_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            return extract_json_from_llm_text(text)
        except (json.JSONDecodeError, ValueError) as e:
            self.log_error(f"Failed to parse workflow JSON: {e}")
            return None
    
    def _discover_workflow_files(self, repo_path: Path) -> Dict[str, Path]:
        """
        Discover workflow-related files in the repository.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            dict: Mapping of file type to file path
        """
        files = {}
        
        # Package managers
        if (repo_path / 'package.json').exists():
            files['package.json'] = repo_path / 'package.json'
        if (repo_path / 'requirements.txt').exists():
            files['requirements.txt'] = repo_path / 'requirements.txt'
        if (repo_path / 'Pipfile').exists():
            files['Pipfile'] = repo_path / 'Pipfile'
        if (repo_path / 'pom.xml').exists():
            files['pom.xml'] = repo_path / 'pom.xml'
        if (repo_path / 'build.gradle').exists():
            files['build.gradle'] = repo_path / 'build.gradle'
        if (repo_path / 'Cargo.toml').exists():
            files['Cargo.toml'] = repo_path / 'Cargo.toml'
        if (repo_path / 'go.mod').exists():
            files['go.mod'] = repo_path / 'go.mod'
        
        # Build tools
        if (repo_path / 'Makefile').exists():
            files['Makefile'] = repo_path / 'Makefile'
        if (repo_path / 'CMakeLists.txt').exists():
            files['CMakeLists.txt'] = repo_path / 'CMakeLists.txt'
        
        # CI/CD
        github_workflows = repo_path / '.github' / 'workflows'
        if github_workflows.exists():
            workflow_files = list(github_workflows.glob('*.yml')) + list(github_workflows.glob('*.yaml'))
            if workflow_files:
                files['github_workflow'] = workflow_files[0]
        
        if (repo_path / '.gitlab-ci.yml').exists():
            files['gitlab_ci'] = repo_path / '.gitlab-ci.yml'
        if (repo_path / 'Jenkinsfile').exists():
            files['jenkinsfile'] = repo_path / 'Jenkinsfile'
        if (repo_path / '.travis.yml').exists():
            files['travis_ci'] = repo_path / '.travis.yml'
        
        # Docker
        if (repo_path / 'Dockerfile').exists():
            files['dockerfile'] = repo_path / 'Dockerfile'
        if (repo_path / 'docker-compose.yml').exists():
            files['docker_compose'] = repo_path / 'docker-compose.yml'
        
        # Documentation
        if (repo_path / 'README.md').exists():
            files['readme'] = repo_path / 'README.md'
        if (repo_path / 'CONTRIBUTING.md').exists():
            files['contributing'] = repo_path / 'CONTRIBUTING.md'
        
        return files
    
    def _read_file(self, file_path: Path) -> str:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.log_warning(f"Failed to read {file_path}: {e}")
            return ""
    
    async def _generate_workflow_guide(
        self, workflows: Dict[str, Dict], json_only: bool = False
    ) -> str:
        """
        Generate workflow guide using watsonx.ai.
        
        Args:
            workflows: Dictionary of workflow files and their content
            
        Returns:
            str: Markdown-formatted workflow guide
        """
        # Prepare workflow summaries
        workflow_summary = self._summarize_workflows(workflows)
        
        json_suffix = (
            " Return ONLY raw JSON, no markdown fences or prose."
            if json_only
            else ""
        )
        prompt = self.format_prompt(
            """You are a technical writer creating MCP-grounded onboarding workflow docs. Return ONLY valid JSON (no prose).{json_suffix}

## Quality Rules
- Use only the workflow files and contents below.
- Include exact commands, scripts, config file names, and environment hints only when they appear in the provided data.
- If setup, tests, CI/CD, or deployment are not present, include a workflow step that says "Not found in MCP data" with the next file to inspect.
- Make steps specific enough for a new developer to follow during the first week.
- Use valid Mermaid sequenceDiagram syntax and keep participant names grounded in discovered files/processes.

## Available Workflow Files
{workflow_files}

## File Contents Summary
{workflow_summary}

Return ONLY JSON:
{{
  "workflows": [
    {{
      "name": "Workflow name",
      "steps": ["step 1", "step 2"],
      "diagrams": {{ "sequence": "sequenceDiagram\\n  Client->>API: request" }}
    }}
  ]
}}

Use valid Mermaid sequenceDiagram syntax. Escape newlines as \\n in JSON strings.""",
            json_suffix=json_suffix,
            workflow_files=', '.join(workflows.keys()),
            workflow_summary=workflow_summary,
        )

        return await self.generate(prompt, max_tokens=2000, temperature=0.3)
    
    async def _generate_setup_instructions(self, workflows: Dict[str, Dict]) -> str:
        """
        Generate setup instructions using watsonx.ai.
        
        Args:
            workflows: Dictionary of workflow files and their content
            
        Returns:
            str: Markdown-formatted setup instructions
        """
        # Extract setup-relevant information
        setup_info = self._extract_setup_info(workflows)
        
        prompt = self.format_prompt(
            """You are creating setup instructions for new developers. Use only the project evidence below and be explicit about missing data.

Quality rules:
- Include exact commands only when they appear in project files.
- Say "Not found in MCP data" for unknown prerequisites, env vars, IDE settings, or first-run commands.
- Organize the result as polished Markdown with checklists and code fences.

## Project Information
{setup_info}

Generate detailed setup instructions in Markdown format with these sections:

1. **Prerequisites** - Required software, tools, and versions
2. **Installation Steps** - Step-by-step installation process
3. **Configuration** - Environment variables and configuration files
4. **Verification** - How to verify the setup is correct
5. **First Run** - How to run the project for the first time
6. **IDE Setup** - Recommended IDE settings and extensions
7. **Next Steps** - What to do after setup

Be specific with commands and include platform-specific instructions (Windows/Mac/Linux) where relevant.""",
            setup_info=setup_info
        )
        
        instructions = await self.generate(prompt, max_tokens=2000, temperature=0.3)
        
        header = f"""# Setup Instructions

**Generated by:** DevRamp Workflow Extractor
**Date:** {self._get_timestamp()}

---

"""
        
        return header + instructions
    
    def _summarize_workflows(self, workflows: Dict[str, Dict]) -> str:
        """Create a summary of workflow files for the prompt."""
        lines = []
        
        for file_type, data in workflows.items():
            path = data['path']
            content = data['content']
            
            # Truncate long content
            if len(content) > 500:
                content = content[:500] + "\n... (truncated)"
            
            lines.append(f"\n### {file_type} ({path})")
            lines.append("```")
            lines.append(content)
            lines.append("```")
        
        return '\n'.join(lines)
    
    def _extract_setup_info(self, workflows: Dict[str, Dict]) -> str:
        """Extract setup-relevant information from workflows."""
        info_parts = []
        
        # Check for package.json
        if 'package.json' in workflows:
            try:
                pkg = json.loads(workflows['package.json']['content'])
                info_parts.append(f"**Node.js Project**")
                info_parts.append(f"- Package Manager: npm/yarn/pnpm")
                if 'engines' in pkg:
                    info_parts.append(f"- Node Version: {pkg['engines'].get('node', 'not specified')}")
                if 'scripts' in pkg:
                    info_parts.append(f"- Available Scripts: {', '.join(list(pkg['scripts'].keys())[:5])}")
            except:
                pass
        
        # Check for requirements.txt
        if 'requirements.txt' in workflows:
            info_parts.append(f"**Python Project**")
            info_parts.append(f"- Package Manager: pip")
            info_parts.append(f"- Dependencies file: requirements.txt")
        
        # Check for Docker
        if 'dockerfile' in workflows:
            info_parts.append(f"**Docker Support**")
            info_parts.append(f"- Dockerfile available for containerization")
        
        if 'docker_compose' in workflows:
            info_parts.append(f"- Docker Compose available for multi-container setup")
        
        # Check for CI/CD
        if 'github_workflow' in workflows:
            info_parts.append(f"**CI/CD: GitHub Actions**")
        elif 'gitlab_ci' in workflows:
            info_parts.append(f"**CI/CD: GitLab CI**")
        
        return '\n'.join(info_parts) if info_parts else "No specific setup information found in workflow files."
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Made with Bob
