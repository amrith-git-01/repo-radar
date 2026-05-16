#!/usr/bin/env python3
"""
Legacy Codebase Onboarding Accelerator - Main Entry Point

This is the main entry point for the DevRamp project, which uses IBM watsonx.ai
and watsonx Orchestrate to analyze legacy codebases and generate onboarding documentation.

Phase 1: Project setup and foundation
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Load environment variables
load_dotenv()

# Import configuration
from config.watsonx_config import config

# Initialize rich console for beautiful output
console = Console()


def print_banner():
    """Display the application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        Legacy Codebase Onboarding Accelerator            ║
    ║                      DevRamp v1.0                         ║
    ║                                                           ║
    ║        Powered by IBM watsonx.ai & Orchestrate            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def check_environment():
    """
    Check if the environment is properly configured.
    
    Returns:
        bool: True if environment is valid, False otherwise
    """
    console.print("\n[bold]Checking Environment Configuration...[/bold]\n")
    
    # Create status table
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Component", style="cyan", width=30)
    table.add_column("Status", width=15)
    table.add_column("Details", width=40)
    
    all_valid = True
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 9):
        table.add_row("Python Version", "✓ OK", f"v{python_version}")
    else:
        table.add_row("Python Version", "✗ FAIL", f"v{python_version} (requires 3.9+)")
        all_valid = False
    
    # Check watsonx.ai configuration
    is_valid, error_msg = config.validate()
    if is_valid:
        table.add_row("watsonx.ai Config", "✓ OK", "API key and project ID set")
    else:
        table.add_row("watsonx.ai Config", "✗ FAIL", error_msg)
        all_valid = False
    
    # Check directory structure
    required_dirs = [
        "src/agents",
        "src/dashboard",
        "src/mcp-servers",
        "bob_sessions",
        "docs/onboarding",
        "config",
        "orchestrate"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if not missing_dirs:
        table.add_row("Directory Structure", "✓ OK", "All directories present")
    else:
        table.add_row("Directory Structure", "✗ FAIL", f"{len(missing_dirs)} directories missing")
        all_valid = False
    
    # Check Node.js for MCP servers
    try:
        import subprocess
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            node_version = result.stdout.strip()
            table.add_row("Node.js", "✓ OK", node_version)
        else:
            table.add_row("Node.js", "⚠ WARNING", "Not found (needed for MCP servers)")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        table.add_row("Node.js", "⚠ WARNING", "Not found (needed for MCP servers)")
    
    # Check required files
    required_files = [
        "config/watsonx_config.py",
        "orchestrate/agents.yaml",
        "src/mcp-servers/package.json",
        "src/mcp-servers/tsconfig.json",
        ".env.example"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if not missing_files:
        table.add_row("Required Files", "✓ OK", "All files present")
    else:
        table.add_row("Required Files", "✗ FAIL", f"{len(missing_files)} files missing")
        all_valid = False
    
    console.print(table)
    console.print()
    
    return all_valid


def show_status():
    """Display current project status."""
    console.print("\n[bold]Project Status:[/bold]\n")
    
    status_panel = Panel(
        "[green]✓[/green] Phase 1: Project Setup - [bold green]COMPLETE[/bold green]\n\n"
        "Components Initialized:\n"
        "  • Directory structure created\n"
        "  • watsonx.ai configuration ready\n"
        "  • Orchestrate agents defined\n"
        "  • MCP server foundation prepared\n\n"
        "[yellow]Next Steps:[/yellow]\n"
        "  1. Configure your .env file with watsonx.ai credentials\n"
        "  2. Run: python test_watsonx.py (to test connection)\n"
        "  3. Install Node.js dependencies: cd src/mcp-servers && npm install\n"
        "  4. Proceed to Phase 2: MCP Server Implementation",
        title="[bold cyan]Phase 1 Status[/bold cyan]",
        border_style="cyan",
        box=box.DOUBLE
    )
    
    console.print(status_panel)


def show_help():
    """Display help information."""
    console.print("\n[bold]Available Commands:[/bold]\n")
    
    help_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    help_table.add_column("Command", style="cyan", width=30)
    help_table.add_column("Description", width=50)
    
    help_table.add_row("python main.py", "Show project status and environment check")
    help_table.add_row("python main.py --help", "Display this help message")
    help_table.add_row("python test_watsonx.py", "Test watsonx.ai connection")
    help_table.add_row("cd src/mcp-servers && npm install", "Install MCP server dependencies")
    
    console.print(help_table)
    console.print()


def main():
    """Main entry point."""
    # Parse simple command line arguments
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_banner()
        show_help()
        return 0
    
    # Display banner
    print_banner()
    
    # Check environment
    env_valid = check_environment()
    
    # Show status
    show_status()
    
    # Show next steps if environment is not fully configured
    if not env_valid:
        console.print("\n[bold yellow]⚠ Configuration Required[/bold yellow]\n")
        console.print("Please complete the setup steps:")
        console.print("  1. Copy .env.example to .env")
        console.print("  2. Add your watsonx.ai credentials to .env")
        console.print("  3. Run this script again to verify\n")
        return 1
    
    console.print("\n[bold green]✓ Environment is ready![/bold green]")
    console.print("Run [cyan]python test_watsonx.py[/cyan] to test your watsonx.ai connection.\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
