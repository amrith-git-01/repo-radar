"""
Hotspot Detector Agent

Identifies code hotspots (frequently changed files with high complexity) using
git history analysis and complexity metrics, then generates refactoring recommendations.
"""

import json
from typing import Dict, Any, List
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.agents.mcp_client import MCPClient


class HotspotDetector(BaseAgent):
    """
    Agent that detects code hotspots and generates refactoring recommendations.
    
    Combines git history analysis with complexity metrics to identify files
    that are frequently changed and have high complexity, indicating potential
    technical debt or areas needing refactoring.
    """
    
    def __init__(self, code_analyzer: MCPClient, git_analyzer: MCPClient):
        """
        Initialize the Hotspot Detector agent.
        
        Args:
            code_analyzer: Connected MCP client for code-analyzer server
            git_analyzer: Connected MCP client for git-analyzer server
        """
        super().__init__(name="HotspotDetector")
        self.code_analyzer = code_analyzer
        self.git_analyzer = git_analyzer
    
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect code hotspots and generate recommendations.
        
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
        
        self.log_info(f"Detecting hotspots in {repo_path}")
        
        # Step 1: Get git hotspot files (frequently changed)
        self.log_info("Analyzing git history for frequently changed files...")
        git_hotspots = await self.git_analyzer.call_tool('get_hotspot_files', {'limit': 30})
        
        # Step 2: Get complexity metrics
        self.log_info("Analyzing code complexity...")
        complexity_metrics = await self.code_analyzer.call_tool('get_complexity_metrics')
        
        # Step 3: Get contributor information
        self.log_info("Analyzing contributors...")
        contributors = await self.git_analyzer.call_tool('get_contributors')
        
        # Step 4: Combine metrics to identify true hotspots
        self.log_info("Identifying critical hotspots...")
        hotspots = self._identify_hotspots(git_hotspots, complexity_metrics)
        
        # Step 5: Generate hotspot report
        self.log_info("Generating hotspot report with watsonx.ai...")
        hotspot_report = await self._generate_hotspot_report(
            hotspots, git_hotspots, complexity_metrics, contributors
        )
        
        # Step 6: Generate refactoring priorities
        self.log_info("Creating refactoring priorities...")
        refactoring_priorities = self._create_refactoring_priorities(hotspots)
        
        # Step 7: Save outputs
        report_path = output_dir / 'hotspot_report.md'
        priorities_path = output_dir / 'refactoring_priorities.json'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(hotspot_report)
        
        with open(priorities_path, 'w', encoding='utf-8') as f:
            json.dump(refactoring_priorities, f, indent=2)
        
        self.log_info(f"Hotspot report saved to {report_path}")
        self.log_info(f"Refactoring priorities saved to {priorities_path}")
        
        return {
            'hotspot_report': str(report_path),
            'refactoring_priorities': str(priorities_path),
            'hotspots': hotspots,
            'git_hotspots': git_hotspots,
            'complexity_metrics': complexity_metrics
        }
    
    def _identify_hotspots(
        self,
        git_hotspots: List[Dict],
        complexity_metrics: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Identify critical hotspots by combining git and complexity data.
        
        Args:
            git_hotspots: Files with frequent changes
            complexity_metrics: Complexity metrics for files
            
        Returns:
            list: Combined hotspot data with risk scores
        """
        # Create complexity lookup
        complexity_map = {
            c['file']: c for c in complexity_metrics
        }
        
        hotspots = []
        
        for git_hot in git_hotspots:
            file_path = git_hot.get('path', '')
            commits = git_hot.get('commits', 0)
            authors = git_hot.get('authors', 0)
            change_freq = git_hot.get('changeFrequency', 0)
            
            # Get complexity data if available
            complexity_data = complexity_map.get(file_path, {})
            complexity = complexity_data.get('complexity', 0)
            lines = complexity_data.get('lines', 0)
            maintainability = complexity_data.get('maintainabilityIndex', 100)
            
            # Calculate risk score (0-100)
            # Higher score = higher risk
            risk_score = self._calculate_risk_score(
                commits, authors, complexity, maintainability, change_freq
            )
            
            hotspots.append({
                'path': file_path,
                'risk_score': risk_score,
                'commits': commits,
                'authors': authors,
                'change_frequency': round(change_freq, 4),
                'complexity': complexity,
                'lines': lines,
                'maintainability_index': maintainability,
                'risk_level': self._get_risk_level(risk_score)
            })
        
        # Sort by risk score
        hotspots.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return hotspots
    
    def _calculate_risk_score(
        self,
        commits: int,
        authors: int,
        complexity: int,
        maintainability: int,
        change_freq: float
    ) -> int:
        """
        Calculate risk score for a file.
        
        Args:
            commits: Number of commits
            authors: Number of authors
            complexity: Cyclomatic complexity
            maintainability: Maintainability index (0-100)
            change_freq: Change frequency
            
        Returns:
            int: Risk score (0-100)
        """
        # Normalize factors (0-1 scale)
        commit_factor = min(commits / 50, 1.0)  # 50+ commits = max
        author_factor = min(authors / 10, 1.0)  # 10+ authors = max
        complexity_factor = min(complexity / 50, 1.0)  # 50+ complexity = max
        maintainability_factor = (100 - maintainability) / 100  # Invert (lower is worse)
        frequency_factor = min(change_freq * 100, 1.0)  # Normalize frequency
        
        # Weighted combination
        risk = (
            commit_factor * 0.25 +
            author_factor * 0.15 +
            complexity_factor * 0.30 +
            maintainability_factor * 0.20 +
            frequency_factor * 0.10
        )
        
        return int(risk * 100)
    
    def _get_risk_level(self, risk_score: int) -> str:
        """Get risk level label from score."""
        if risk_score >= 75:
            return "CRITICAL"
        elif risk_score >= 50:
            return "HIGH"
        elif risk_score >= 25:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _generate_hotspot_report(
        self,
        hotspots: List[Dict],
        git_hotspots: List[Dict],
        complexity_metrics: List[Dict],
        contributors: List[Dict]
    ) -> str:
        """
        Generate hotspot report using watsonx.ai.
        
        Args:
            hotspots: Combined hotspot data
            git_hotspots: Git hotspot data
            complexity_metrics: Complexity metrics
            contributors: Contributor information
            
        Returns:
            str: Markdown-formatted hotspot report
        """
        # Get top hotspots
        critical_hotspots = [h for h in hotspots if h['risk_level'] in ['CRITICAL', 'HIGH']][:10]
        
        # Get top contributors
        top_contributors = contributors[:5] if contributors else []
        
        prompt = self.format_prompt(
            """You are a senior software engineer analyzing code quality and technical debt. Generate a comprehensive hotspot analysis report.

## Critical Hotspots (High Risk Files)
{critical_hotspots}

## Overall Statistics
- Total Files Analyzed: {total_files}
- Critical Risk Files: {critical_count}
- High Risk Files: {high_count}
- Top Contributors: {top_contributors}

## Analysis Context
These hotspots were identified by combining:
1. Git history (frequently changed files)
2. Code complexity metrics
3. Maintainability indices
4. Change frequency patterns

Generate a detailed hotspot report in Markdown format with these sections:

1. **Executive Summary** - Overview of technical debt and risk areas
2. **Critical Hotspots** - Detailed analysis of highest-risk files
3. **Risk Factors** - What makes these files problematic
4. **Impact Assessment** - Potential impact on development velocity and quality
5. **Refactoring Strategy** - Recommended approach for addressing hotspots
6. **Quick Wins** - Easy improvements that can be made immediately
7. **Long-term Recommendations** - Strategic improvements for technical debt reduction

Be specific about each file and provide actionable recommendations.""",
            critical_hotspots=self._format_hotspots(critical_hotspots),
            total_files=len(hotspots),
            critical_count=len([h for h in hotspots if h['risk_level'] == 'CRITICAL']),
            high_count=len([h for h in hotspots if h['risk_level'] == 'HIGH']),
            top_contributors=self._format_contributors(top_contributors)
        )
        
        report = await self.generate(prompt, max_tokens=2000, temperature=0.3)
        
        header = f"""# Code Hotspot Analysis Report

**Generated by:** DevRamp Hotspot Detector
**Date:** {self._get_timestamp()}
**Files Analyzed:** {len(hotspots)}

---

"""
        
        return header + report
    
    def _create_refactoring_priorities(self, hotspots: List[Dict]) -> Dict[str, Any]:
        """
        Create structured refactoring priorities.
        
        Args:
            hotspots: Hotspot data
            
        Returns:
            dict: Refactoring priorities in JSON format
        """
        priorities = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for hotspot in hotspots:
            risk_level = hotspot['risk_level'].lower()
            
            priority_item = {
                'file': hotspot['path'],
                'risk_score': hotspot['risk_score'],
                'metrics': {
                    'commits': hotspot['commits'],
                    'authors': hotspot['authors'],
                    'complexity': hotspot['complexity'],
                    'lines': hotspot['lines'],
                    'maintainability': hotspot['maintainability_index']
                },
                'recommendations': self._get_recommendations(hotspot)
            }
            
            priorities[risk_level].append(priority_item)
        
        return {
            'priorities': priorities,
            'summary': {
                'total_hotspots': len(hotspots),
                'critical': len(priorities['critical']),
                'high': len(priorities['high']),
                'medium': len(priorities['medium']),
                'low': len(priorities['low'])
            },
            'generated_at': self._get_timestamp()
        }
    
    def _get_recommendations(self, hotspot: Dict) -> List[str]:
        """Generate recommendations for a hotspot."""
        recommendations = []
        
        if hotspot['complexity'] > 30:
            recommendations.append("Reduce cyclomatic complexity through function extraction")
        
        if hotspot['lines'] > 500:
            recommendations.append("Consider splitting into smaller modules")
        
        if hotspot['maintainability_index'] < 40:
            recommendations.append("Improve code maintainability through refactoring")
        
        if hotspot['authors'] > 5:
            recommendations.append("High author count suggests unclear ownership - consider assigning a maintainer")
        
        if hotspot['commits'] > 30:
            recommendations.append("Frequent changes indicate instability - add comprehensive tests")
        
        if not recommendations:
            recommendations.append("Monitor for future changes and complexity growth")
        
        return recommendations
    
    def _format_hotspots(self, hotspots: List[Dict]) -> str:
        """Format hotspots for prompt."""
        if not hotspots:
            return "No critical hotspots identified."
        
        lines = []
        for i, h in enumerate(hotspots, 1):
            lines.append(
                f"{i}. **{h['path']}** (Risk: {h['risk_score']}/100, {h['risk_level']})\n"
                f"   - Commits: {h['commits']}, Authors: {h['authors']}\n"
                f"   - Complexity: {h['complexity']}, Lines: {h['lines']}\n"
                f"   - Maintainability: {h['maintainability_index']}/100"
            )
        
        return '\n\n'.join(lines)
    
    def _format_contributors(self, contributors: List[Dict]) -> str:
        """Format contributors for prompt."""
        if not contributors:
            return "No contributor data available."
        
        lines = []
        for c in contributors:
            name = c.get('name', 'Unknown')
            commits = c.get('commits', 0)
            lines.append(f"- {name}: {commits} commits")
        
        return '\n'.join(lines)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Made with Bob
