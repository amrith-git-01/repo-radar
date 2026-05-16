"""
Architecture Analyzer Agent

Analyzes codebase structure and generates architecture documentation using
MCP code-analyzer tools and watsonx.ai.
"""

import json
import os
from typing import Dict, Any
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.agents.mcp_client import MCPClient


class ArchitectureAnalyzer(BaseAgent):
    """
    Agent that analyzes codebase architecture and generates documentation.
    
    Uses MCP code-analyzer tools to gather structural information and
    watsonx.ai to generate comprehensive architecture documentation.
    """
    
    def __init__(self, mcp_client: MCPClient):
        """
        Initialize the Architecture Analyzer agent.
        
        Args:
            mcp_client: Connected MCP client for code-analyzer server
        """
        super().__init__(name="ArchitectureAnalyzer")
        self.mcp_client = mcp_client
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze codebase architecture.
        
        Args:
            context: Analysis context containing:
                - repo_path: Path to repository
                - output_dir: Directory for output files
                
        Returns:
            dict: Analysis results with paths to generated files
        """
        repo_path = context.get('repo_path', '.')
        output_dir = Path(context.get('output_dir', 'docs/onboarding'))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_info(f"Analyzing architecture of {repo_path}")
        
        # Step 1: Gather structural information from MCP
        self.log_info("Gathering codebase structure...")
        structure = await self.mcp_client.call_tool('analyze_structure')
        
        self.log_info("Finding entry points...")
        entry_points = await self.mcp_client.call_tool('find_entry_points')
        
        self.log_info("Analyzing dependencies...")
        dependencies = await self.mcp_client.call_tool('analyze_dependencies')
        
        self.log_info("Getting complexity metrics...")
        complexity = await self.mcp_client.call_tool('get_complexity_metrics')
        
        # Step 2: Generate architecture report using watsonx.ai
        self.log_info("Generating architecture report with watsonx.ai...")
        architecture_report = await self._generate_architecture_report(
            structure, entry_points, dependencies, complexity
        )
        
        # Step 3: Generate dependency graph
        self.log_info("Creating dependency graph...")
        dependency_graph = self._create_dependency_graph(dependencies)
        
        # Step 4: Save outputs
        report_path = output_dir / 'architecture_report.md'
        graph_path = output_dir / 'dependency_graph.json'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(architecture_report)
        
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(dependency_graph, f, indent=2)
        
        self.log_info(f"Architecture report saved to {report_path}")
        self.log_info(f"Dependency graph saved to {graph_path}")
        
        return {
            'architecture_report': str(report_path),
            'dependency_graph': str(graph_path),
            'structure': structure,
            'entry_points': entry_points,
            'dependencies': dependencies,
            'complexity': complexity
        }
    
    async def _generate_architecture_report(
        self,
        structure: Dict[str, Any],
        entry_points: list,
        dependencies: list,
        complexity: list
    ) -> str:
        """
        Generate architecture report using watsonx.ai.
        
        Args:
            structure: Codebase structure information
            entry_points: List of entry points
            dependencies: List of dependencies
            complexity: Complexity metrics
            
        Returns:
            str: Markdown-formatted architecture report
        """
        # Prepare data summaries
        total_files = structure.get('totalFiles', 0)
        files_by_ext = structure.get('filesByExtension', {})
        largest_files = structure.get('largestFiles', [])[:5]
        
        top_deps = dependencies[:10] if dependencies else []
        high_complexity = [c for c in complexity if c.get('complexity', 0) > 20][:5]
        
        # Create prompt
        prompt = self.format_prompt(
            """You are a senior software architect analyzing a codebase. Generate a comprehensive architecture report.

## Codebase Overview
- Total Files: {total_files}
- File Types: {file_types}
- Primary Language: {primary_lang}

## Entry Points
{entry_points}

## Key Dependencies
{dependencies}

## Complexity Hotspots
{complexity}

## Largest Files
{largest_files}

Generate a detailed architecture report in Markdown format with the following sections:
1. **Executive Summary** - High-level overview of the architecture
2. **Technology Stack** - Languages, frameworks, and key dependencies
3. **System Architecture** - Overall structure and design patterns
4. **Entry Points** - Main entry points and their purposes
5. **Module Organization** - How code is organized into modules/packages
6. **Key Components** - Important components and their responsibilities
7. **Data Flow** - How data flows through the system
8. **Complexity Analysis** - Areas of high complexity that may need attention
9. **Architecture Recommendations** - Suggestions for improvements

Be specific and technical. Use the actual data provided.""",
            total_files=total_files,
            file_types=', '.join(f"{ext}: {count}" for ext, count in sorted(files_by_ext.items(), key=lambda x: -x[1])[:5]),
            primary_lang=max(files_by_ext.items(), key=lambda x: x[1])[0] if files_by_ext else 'Unknown',
            entry_points=self._format_entry_points(entry_points),
            dependencies=self._format_dependencies(top_deps),
            complexity=self._format_complexity(high_complexity),
            largest_files=self._format_largest_files(largest_files)
        )
        
        # Generate report
        report = await self.generate(prompt, max_tokens=2000, temperature=0.3)
        
        # Add metadata header
        header = f"""# Architecture Report

**Generated by:** DevRamp Architecture Analyzer
**Date:** {self._get_timestamp()}
**Total Files Analyzed:** {total_files}

---

"""
        
        return header + report
    
    def _create_dependency_graph(self, dependencies: list) -> Dict[str, Any]:
        """
        Create a dependency graph structure.
        
        Args:
            dependencies: List of dependencies
            
        Returns:
            dict: Dependency graph in JSON format
        """
        nodes = []
        edges = []
        
        for dep in dependencies:
            name = dep.get('name', '')
            count = dep.get('count', 0)
            dep_type = dep.get('type', 'unknown')
            files = dep.get('files', [])
            
            # Add node
            nodes.append({
                'id': name,
                'label': name,
                'type': dep_type,
                'usage_count': count,
                'files': files
            })
            
            # Add edges from files to dependency
            for file in files[:10]:  # Limit edges for readability
                edges.append({
                    'from': file,
                    'to': name,
                    'type': 'uses'
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'total_dependencies': len(dependencies),
                'generated_at': self._get_timestamp()
            }
        }
    
    def _format_entry_points(self, entry_points: list) -> str:
        """Format entry points for prompt."""
        if not entry_points:
            return "No clear entry points identified."
        
        lines = []
        for ep in entry_points[:10]:
            path = ep.get('path', '')
            ep_type = ep.get('type', '')
            confidence = ep.get('confidence', '')
            reason = ep.get('reason', '')
            lines.append(f"- `{path}` ({ep_type}, {confidence} confidence): {reason}")
        
        return '\n'.join(lines)
    
    def _format_dependencies(self, dependencies: list) -> str:
        """Format dependencies for prompt."""
        if not dependencies:
            return "No external dependencies found."
        
        lines = []
        for dep in dependencies:
            name = dep.get('name', '')
            count = dep.get('count', 0)
            dep_type = dep.get('type', '')
            lines.append(f"- `{name}` ({dep_type}): used in {count} file(s)")
        
        return '\n'.join(lines)
    
    def _format_complexity(self, complexity: list) -> str:
        """Format complexity metrics for prompt."""
        if not complexity:
            return "No high-complexity files identified."
        
        lines = []
        for c in complexity:
            file = c.get('file', '')
            comp = c.get('complexity', 0)
            lines_count = c.get('lines', 0)
            mi = c.get('maintainabilityIndex', 0)
            lines.append(f"- `{file}`: complexity={comp}, lines={lines_count}, maintainability={mi}")
        
        return '\n'.join(lines)
    
    def _format_largest_files(self, files: list) -> str:
        """Format largest files for prompt."""
        if not files:
            return "No file size data available."
        
        lines = []
        for f in files:
            path = f.get('path', '')
            lines_count = f.get('lines', 0)
            size = f.get('size', 0)
            lines.append(f"- `{path}`: {lines_count} lines, {size} bytes")
        
        return '\n'.join(lines)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Made with Bob
