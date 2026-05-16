#!/usr/bin/env python3
"""
DevRamp Analysis Runner

Main script to run the complete codebase analysis pipeline using AI agents
and MCP servers.
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
import json

from src.agents.coordinator import run_analysis


def setup_logging(verbose: bool = False):
    """
    Setup logging configuration.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='DevRamp - AI-Powered Legacy Codebase Onboarding Accelerator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current directory
  python run_analysis.py
  
  # Analyze specific repository
  python run_analysis.py --repo-path /path/to/repo
  
  # Run specific agents only
  python run_analysis.py --agents architecture workflow
  
  # Use parallel execution
  python run_analysis.py --parallel
  
  # Verbose output
  python run_analysis.py --verbose
        """
    )
    
    parser.add_argument(
        '--repo-path',
        type=str,
        default='.',
        help='Path to the repository to analyze (default: current directory)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='docs/onboarding',
        help='Directory for output files (default: docs/onboarding)'
    )
    
    parser.add_argument(
        '--agents',
        nargs='+',
        choices=['architecture', 'workflow', 'hotspot', 'documentation'],
        help='Specific agents to run (default: all agents)'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run independent agents in parallel for faster execution'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--mcp-config',
        type=str,
        help='Path to MCP servers configuration JSON file'
    )
    
    return parser.parse_args()


def load_mcp_config(config_path: str) -> dict:
    """
    Load MCP server configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        dict: MCP server configuration
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load MCP config from {config_path}: {e}")
        return {}


def print_banner():
    """Print application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗ ███████╗██╗   ██╗██████╗  █████╗ ███╗   ███╗██████╗║
║   ██╔══██╗██╔════╝██║   ██║██╔══██╗██╔══██╗████╗ ████║██╔══██╗
║   ██║  ██║█████╗  ██║   ██║██████╔╝███████║██╔████╔██║██████╔╝
║   ██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══██╗██╔══██║██║╚██╔╝██║██╔═══╝║
║   ██████╔╝███████╗ ╚████╔╝ ██║  ██║██║  ██║██║ ╚═╝ ██║██║    ║
║   ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝    ║
║                                                               ║
║   AI-Powered Legacy Codebase Onboarding Accelerator          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_summary(results: dict):
    """
    Print analysis summary.
    
    Args:
        results: Analysis results
    """
    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)
    
    status = results.get('status', 'unknown')
    total_time = results.get('total_time', 0)
    agents_run = results.get('agents_run', 0)
    successful = results.get('successful', 0)
    failed = results.get('failed', 0)
    
    # Status emoji
    status_emoji = "✓" if status == "success" else "⚠" if status == "partial" else "✗"
    
    print(f"\n{status_emoji} Status: {status.upper()}")
    print(f"⏱  Total Time: {total_time:.2f}s")
    print(f"🤖 Agents Run: {agents_run}")
    print(f"✓  Successful: {successful}")
    if failed > 0:
        print(f"✗  Failed: {failed}")
    
    # Output files
    output_files = results.get('output_files', [])
    if output_files:
        print(f"\n📄 Generated Files ({len(output_files)}):")
        for file in output_files:
            print(f"   - {file}")
    
    # Output directory
    output_dir = results.get('output_dir', '')
    if output_dir:
        print(f"\n📁 Output Directory: {output_dir}")
    
    print("\n" + "="*70)
    
    # Agent details
    agent_results = results.get('results', {})
    if agent_results:
        print("\nAGENT DETAILS:")
        print("-"*70)
        for agent_name, agent_result in agent_results.items():
            agent_status = agent_result.get('status', 'unknown')
            elapsed = agent_result.get('elapsed_time', 0)
            
            status_icon = "✓" if agent_status == "success" else "✗"
            print(f"{status_icon} {agent_name.capitalize()}: {agent_status} ({elapsed:.2f}s)")
            
            if agent_status == "error":
                error = agent_result.get('error', 'Unknown error')
                print(f"   Error: {error}")
        print("-"*70)
    
    # Next steps
    if status in ['success', 'partial']:
        print("\n🎉 NEXT STEPS:")
        print("   1. Review the generated documentation in the output directory")
        print("   2. Read the ONBOARDING_GUIDE.md for an overview")
        print("   3. Check the architecture_report.md for technical details")
        print("   4. Review hotspot_report.md for areas needing attention")
        print("   5. Follow setup_instructions.md to get started")
    
    print()


async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Print banner
    if not args.verbose:
        print_banner()
    
    # Validate repository path
    repo_path = Path(args.repo_path).resolve()
    if not repo_path.exists():
        logging.error(f"Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    if not repo_path.is_dir():
        logging.error(f"Repository path is not a directory: {repo_path}")
        sys.exit(1)
    
    # Load MCP configuration if provided
    mcp_config = None
    if args.mcp_config:
        mcp_config = load_mcp_config(args.mcp_config)
    
    # Print configuration
    logging.info(f"Repository: {repo_path}")
    logging.info(f"Output Directory: {args.output_dir}")
    if args.agents:
        logging.info(f"Agents: {', '.join(args.agents)}")
    else:
        logging.info("Agents: all")
    logging.info(f"Execution Mode: {'parallel' if args.parallel else 'sequential'}")
    
    print()
    
    try:
        # Run analysis
        results = await run_analysis(
            repo_path=str(repo_path),
            output_dir=args.output_dir,
            agents=args.agents,
            parallel=args.parallel,
            verbose=args.verbose,
            mcp_servers_config=mcp_config
        )
        
        # Print summary
        print_summary(results)
        
        # Exit with appropriate code
        if results.get('status') == 'success':
            sys.exit(0)
        elif results.get('status') == 'partial':
            sys.exit(1)
        else:
            sys.exit(2)
            
    except KeyboardInterrupt:
        logging.warning("\nAnalysis interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        logging.error(f"Analysis failed: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    # Run async main
    asyncio.run(main())

# Made with Bob
