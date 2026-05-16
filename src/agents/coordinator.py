"""
Agent Coordinator

Orchestrates the execution of multiple agents, manages their dependencies,
and aggregates results.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import time

from src.agents.mcp_client import MCPClientManager
from src.agents.architecture_analyzer import ArchitectureAnalyzer
from src.agents.workflow_extractor import WorkflowExtractor
from src.agents.hotspot_detector import HotspotDetector
from src.agents.documentation_generator import DocumentationGenerator


logger = logging.getLogger(__name__)


class AgentCoordinator:
    """
    Coordinates the execution of multiple agents.
    
    Manages agent lifecycle, execution order, context passing, and result
    aggregation. Supports both sequential and parallel execution modes.
    """
    
    def __init__(
        self,
        repo_path: str,
        output_dir: str = 'docs/onboarding',
        mcp_servers_config: Optional[Dict[str, Dict]] = None
    ):
        """
        Initialize the coordinator.
        
        Args:
            repo_path: Path to the repository to analyze
            output_dir: Directory for output files
            mcp_servers_config: Configuration for MCP servers
        """
        self.repo_path = Path(repo_path).resolve()
        self.output_dir = Path(output_dir)
        self.mcp_servers_config = mcp_servers_config or {}
        
        self.mcp_manager = MCPClientManager()
        self.agents: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        
        self.logger = logging.getLogger("coordinator")
    
    async def initialize(self):
        """
        Initialize MCP clients and agents.
        
        Raises:
            Exception: If initialization fails
        """
        self.logger.info("Initializing coordinator...")
        
        # Setup MCP clients
        await self._setup_mcp_clients()
        
        # Initialize agents
        await self._initialize_agents()
        
        self.logger.info("Coordinator initialized successfully")
    
    async def _setup_mcp_clients(self):
        """Setup and connect to MCP servers."""
        self.logger.info("Setting up MCP clients...")
        
        # Get absolute path to MCP servers
        mcp_base = Path(__file__).parent.parent / 'mcp-servers'
        
        # Add code-analyzer client
        code_analyzer_config = self.mcp_servers_config.get('code-analyzer', {
            'command': 'node',
            'args': [str(mcp_base / 'code-analyzer' / 'build' / 'server.js')],
            'env': {'REPO_PATH': str(self.repo_path)}
        })
        
        self.mcp_manager.add_client(
            'code-analyzer',
            code_analyzer_config['command'],
            code_analyzer_config['args'],
            code_analyzer_config.get('env', {})
        )
        
        # Add git-analyzer client
        git_analyzer_config = self.mcp_servers_config.get('git-analyzer', {
            'command': 'node',
            'args': [str(mcp_base / 'git-analyzer' / 'build' / 'server.js')],
            'env': {'REPO_PATH': str(self.repo_path)}
        })
        
        self.mcp_manager.add_client(
            'git-analyzer',
            git_analyzer_config['command'],
            git_analyzer_config['args'],
            git_analyzer_config.get('env', {})
        )
        
        # Connect to all servers
        await self.mcp_manager.connect_all()
        
        self.logger.info("MCP clients connected")
    
    async def _initialize_agents(self):
        """Initialize all agents."""
        self.logger.info("Initializing agents...")
        
        # Get MCP clients
        code_analyzer = self.mcp_manager.get_client('code-analyzer')
        git_analyzer = self.mcp_manager.get_client('git-analyzer')
        
        # Initialize agents
        self.agents['architecture'] = ArchitectureAnalyzer(code_analyzer)
        self.agents['workflow'] = WorkflowExtractor()
        self.agents['hotspot'] = HotspotDetector(code_analyzer, git_analyzer)
        self.agents['documentation'] = DocumentationGenerator()
        
        self.logger.info(f"Initialized {len(self.agents)} agents")
    
    async def run_sequential(
        self,
        agents: Optional[List[str]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Run agents sequentially.
        
        Args:
            agents: List of agent names to run (None = all agents)
            verbose: Enable verbose logging
            
        Returns:
            dict: Aggregated results from all agents
        """
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        agents_to_run = agents or list(self.agents.keys())
        self.logger.info(f"Running {len(agents_to_run)} agents sequentially")
        
        start_time = time.time()
        context = {
            'repo_path': str(self.repo_path),
            'output_dir': str(self.output_dir)
        }
        
        # Run agents in order
        for agent_name in agents_to_run:
            if agent_name not in self.agents:
                self.logger.warning(f"Agent '{agent_name}' not found, skipping")
                continue
            
            agent = self.agents[agent_name]
            self.logger.info(f"Running {agent_name} agent...")
            
            try:
                result = await agent.run(context)
                self.results[agent_name] = result
                
                # Add result to context for next agents
                context[f'{agent_name}_result'] = result.get('result', {})
                
                if result['status'] == 'success':
                    self.logger.info(
                        f"✓ {agent_name} completed in {result['elapsed_time']:.2f}s"
                    )
                else:
                    self.logger.error(
                        f"✗ {agent_name} failed: {result.get('error', 'Unknown error')}"
                    )
                    
            except Exception as e:
                self.logger.error(f"Error running {agent_name}: {e}", exc_info=True)
                self.results[agent_name] = {
                    'agent': agent_name,
                    'status': 'error',
                    'error': str(e)
                }
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"All agents completed in {elapsed_time:.2f}s")
        
        return self._aggregate_results(elapsed_time)
    
    async def run_parallel(
        self,
        agents: Optional[List[str]] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Run independent agents in parallel.
        
        Note: Some agents have dependencies and will run sequentially.
        
        Args:
            agents: List of agent names to run (None = all agents)
            verbose: Enable verbose logging
            
        Returns:
            dict: Aggregated results from all agents
        """
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        agents_to_run = agents or list(self.agents.keys())
        self.logger.info(f"Running agents with parallelization")
        
        start_time = time.time()
        context = {
            'repo_path': str(self.repo_path),
            'output_dir': str(self.output_dir)
        }
        
        # Phase 1: Run independent agents in parallel
        phase1_agents = ['architecture', 'workflow']
        phase1_tasks = []
        
        for agent_name in phase1_agents:
            if agent_name in agents_to_run and agent_name in self.agents:
                agent = self.agents[agent_name]
                phase1_tasks.append(self._run_agent_with_name(agent, agent_name, context))
        
        if phase1_tasks:
            self.logger.info(f"Phase 1: Running {len(phase1_tasks)} agents in parallel")
            phase1_results = await asyncio.gather(*phase1_tasks, return_exceptions=True)
            
            for result in phase1_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Phase 1 agent failed: {result}")
                elif isinstance(result, dict):
                    agent_name = result.get('agent')
                    self.results[agent_name] = result
                    context[f'{agent_name}_result'] = result.get('result', {})
        
        # Phase 2: Run hotspot detector (depends on phase 1)
        if 'hotspot' in agents_to_run and 'hotspot' in self.agents:
            self.logger.info("Phase 2: Running hotspot detector")
            agent = self.agents['hotspot']
            result = await agent.run(context)
            self.results['hotspot'] = result
            context['hotspot_result'] = result.get('result', {})
        
        # Phase 3: Run documentation generator (depends on all previous)
        if 'documentation' in agents_to_run and 'documentation' in self.agents:
            self.logger.info("Phase 3: Running documentation generator")
            agent = self.agents['documentation']
            result = await agent.run(context)
            self.results['documentation'] = result
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"All agents completed in {elapsed_time:.2f}s")
        
        return self._aggregate_results(elapsed_time)
    
    async def _run_agent_with_name(
        self,
        agent: Any,
        name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run an agent and return result with name."""
        result = await agent.run(context)
        result['agent'] = name
        return result
    
    def _aggregate_results(self, total_time: float) -> Dict[str, Any]:
        """
        Aggregate results from all agents.
        
        Args:
            total_time: Total execution time
            
        Returns:
            dict: Aggregated results
        """
        successful = sum(1 for r in self.results.values() if r.get('status') == 'success')
        failed = sum(1 for r in self.results.values() if r.get('status') == 'error')
        
        # Collect output files
        output_files = []
        for result in self.results.values():
            if result.get('status') == 'success':
                result_data = result.get('result', {})
                for key, value in result_data.items():
                    if isinstance(value, str) and (
                        value.endswith('.md') or value.endswith('.json')
                    ):
                        output_files.append(value)
        
        return {
            'status': 'success' if failed == 0 else 'partial',
            'total_time': total_time,
            'agents_run': len(self.results),
            'successful': successful,
            'failed': failed,
            'results': self.results,
            'output_files': output_files,
            'output_dir': str(self.output_dir)
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up coordinator...")
        
        try:
            await self.mcp_manager.disconnect_all()
            self.logger.info("Coordinator cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


async def run_analysis(
    repo_path: str,
    output_dir: str = 'docs/onboarding',
    agents: Optional[List[str]] = None,
    parallel: bool = False,
    verbose: bool = False,
    mcp_servers_config: Optional[Dict[str, Dict]] = None
) -> Dict[str, Any]:
    """
    Convenience function to run analysis.
    
    Args:
        repo_path: Path to repository
        output_dir: Output directory
        agents: List of agents to run (None = all)
        parallel: Use parallel execution
        verbose: Enable verbose logging
        mcp_servers_config: MCP server configuration
        
    Returns:
        dict: Analysis results
    """
    async with AgentCoordinator(repo_path, output_dir, mcp_servers_config) as coordinator:
        if parallel:
            return await coordinator.run_parallel(agents, verbose)
        else:
            return await coordinator.run_sequential(agents, verbose)

# Made with Bob
