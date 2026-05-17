# Legacy Codebase Onboarding Accelerator (DevRamp)

> **Phase 1: Project Setup and Foundation** ✅
> **Phase 2: MCP Servers and AI Agents** ✅

An intelligent system that uses IBM watsonx.ai, watsonx Orchestrate, and Model Context Protocol (MCP) servers to analyze legacy codebases and generate comprehensive onboarding documentation for new developers.

## 🎯 Project Overview

DevRamp accelerates the onboarding process for legacy codebases by automatically:

- Mapping codebase architecture and dependencies
- Extracting development workflows and patterns
- Generating comprehensive documentation
- Identifying code hotspots and technical debt

### Key Technologies

- **IBM watsonx.ai**: AI-powered code analysis using Granite models
- **watsonx Orchestrate**: Multi-agent orchestration for complex analysis tasks
- **Model Context Protocol (MCP)**: Standardized context sharing between AI agents
- **Python & TypeScript**: Core implementation languages

## Bob onboarding demo (primary)

1. Build MCP servers: `cd src/mcp-servers && npm install && npm run build`
2. Copy `.bob/mcp_servers.example.json` → global Bob `mcp_servers.json` (see [docs/MCP_SETUP.md](docs/MCP_SETUP.md))
3. Set watsonx credentials in `.env`
4. Open **Onboarding Assistant** in Bob IDE
5. Run **`@onboard test_repo`** (required — plain "onboard me" alone may only chat until the skill runs)
6. Review `docs/ONBOARDING.md` (embedded Mermaid diagrams)
7. Export Bob session to `bob_sessions/02_onboarding/` for judges

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **npm 9+** - Comes with Node.js
- **IBM Cloud Account** - [Sign up for IBM Cloud](https://cloud.ibm.com/registration)
- **watsonx.ai Access** - [Get watsonx.ai access](https://www.ibm.com/products/watsonx-ai)

## 🚀 Phase 1 Setup Instructions

### 1. Clone or Navigate to Project Directory

```bash
cd devramp
```

### 2. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure watsonx.ai Credentials

#### Get Your Credentials

1. **API Key**:
   - Go to [IBM Cloud API Keys](https://cloud.ibm.com/iam/apikeys)
   - Click "Create an IBM Cloud API key"
   - Copy the generated API key

2. **Project ID**:
   - Go to your [watsonx.ai project](https://dataplatform.cloud.ibm.com/wx/home)
   - Open your project
   - Go to "Manage" tab → "General" → Copy the "Project ID"

#### Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your credentials
# On Windows, use: notepad .env
# On macOS/Linux, use: nano .env or vim .env
```

Add your credentials to `.env`:

```env
WATSONX_API_KEY=your_actual_api_key_here
WATSONX_PROJECT_ID=your_actual_project_id_here
```

### 4. Install MCP Server Dependencies

```bash
# Navigate to MCP servers directory
cd src/mcp-servers

# Install Node.js dependencies
npm install

# Build TypeScript code
npm run build

# Return to project root
cd ../..
```

### 5. Verify Installation

Run the main script to check your setup:

```bash
python main.py
```

This will display:

- Environment configuration status
- Component availability check
- Next steps

### 6. Test watsonx.ai Connection

```bash
python test_watsonx.py
```

This script will:

- Validate your credentials
- Test API connectivity
- Send a test prompt to watsonx.ai
- Display the response

## 📁 Project Structure

```
devramp/
├── src/
│   ├── agents/              # AI agent implementations (Phase 2)
│   ├── dashboard/           # Web dashboard (Phase 3)
│   └── mcp-servers/         # MCP server implementations
│       ├── package.json     # Node.js dependencies
│       ├── tsconfig.json    # TypeScript configuration
│       └── src/             # TypeScript source code (Phase 2)
├── bob_sessions/            # Bob AI session data
├── docs/
│   └── onboarding/          # Generated documentation output
├── config/
│   └── watsonx_config.py    # watsonx.ai configuration
├── orchestrate/
│   └── agents.yaml          # Agent definitions and orchestration
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── main.py                  # Main entry point
├── test_watsonx.py          # Connection test script
├── requirements.txt         # Python dependencies
├── plan.md                  # Project plan and phases
├── rules.md                 # Development rules and guidelines
└── README.md                # This file
```

## 🤖 Defined Agents (Phase 1)

The system uses four specialized AI agents defined in `orchestrate/agents.yaml`:

### 1. Architecture Analyzer

- Maps codebase structure and organization
- Identifies architectural patterns
- Analyzes dependencies and relationships
- Generates dependency graphs

### 2. Workflow Extractor

- Identifies development workflows
- Documents build and deployment processes
- Extracts testing strategies
- Maps CI/CD pipelines

### 3. Documentation Generator

- Creates comprehensive onboarding guides
- Generates API documentation
- Produces troubleshooting guides
- Documents code conventions

### 4. Hotspot Detector

- Analyzes git history for frequently changed files
- Detects code complexity metrics
- Identifies technical debt
- Prioritizes refactoring candidates

## 🔧 Configuration

### watsonx.ai Model Settings

Default configuration in `config/watsonx_config.py`:

- **Model**: `ibm/granite-13b-chat-v2`
- **Max Tokens**: 1000
- **Temperature**: 0.7
- **Top P**: 0.9

You can override these in your `.env` file:

```env
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2
WATSONX_MAX_TOKENS=1000
WATSONX_TEMPERATURE=0.7
WATSONX_TOP_P=0.9
```

## 🧪 Testing Your Setup

### Quick Test Checklist

- [ ] Python 3.9+ installed
- [ ] Node.js 18+ installed
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Node.js dependencies installed (`cd src/mcp-servers && npm install`)
- [ ] `.env` file created with credentials
- [ ] `python main.py` runs successfully
- [ ] `python test_watsonx.py` connects to watsonx.ai

### Troubleshooting

**Issue**: `WATSONX_API_KEY environment variable is not set`

- **Solution**: Ensure you've created `.env` file and added your API key

**Issue**: `Import "ibm_watsonx_ai" could not be resolved`

- **Solution**: Install Python dependencies: `pip install -r requirements.txt`

**Issue**: `node: command not found`

- **Solution**: Install Node.js from [nodejs.org](https://nodejs.org/)

**Issue**: API connection fails

- **Solution**: Verify your API key and project ID are correct
- Check your internet connection
- Ensure you have access to watsonx.ai

## 🚀 Phase 2: MCP Servers and AI Agents

Phase 2 is now complete! The system includes fully functional MCP servers and AI agents.

### MCP Servers

Two TypeScript-based MCP servers provide code analysis capabilities:

1. **code-analyzer** - Analyzes codebase structure, dependencies, and complexity
   - `analyze_structure` - Overall codebase structure
   - `find_entry_points` - Identifies main entry points
   - `analyze_dependencies` - External dependencies
   - `get_complexity_metrics` - Code complexity analysis

2. **git-analyzer** - Analyzes git history and contributors
   - `get_hotspot_files` - Frequently changed files
   - `get_contributors` - Contributor statistics
   - `get_file_history` - File change history

### AI Agents

Four specialized Python agents use watsonx.ai and MCP servers:

1. **Architecture Analyzer** - Generates architecture documentation
2. **Workflow Extractor** - Documents development workflows
3. **Hotspot Detector** - Identifies technical debt
4. **Documentation Generator** - Creates comprehensive onboarding guides

### Setup Instructions

#### 1. Build MCP Servers

```bash
cd src/mcp-servers
npm install
npm run build
```

#### 2. Register MCP Servers Globally

**IMPORTANT**: MCP servers must be registered globally in Bob IDE.

See [docs/MCP_SETUP.md](docs/MCP_SETUP.md) for detailed instructions.

Quick setup:

- **Windows**: Edit `%APPDATA%\.bob\mcp_servers.json`
- **macOS/Linux**: Edit `~/.bob/mcp_servers.json`

Example configuration:

```json
{
  "mcpServers": {
    "code-analyzer": {
      "command": "node",
      "args": ["ABSOLUTE_PATH/src/mcp-servers/code-analyzer/build/server.js"],
      "env": { "REPO_PATH": "ABSOLUTE_PATH/target_repo" }
    },
    "git-analyzer": {
      "command": "node",
      "args": ["ABSOLUTE_PATH/src/mcp-servers/git-analyzer/build/server.js"],
      "env": { "REPO_PATH": "ABSOLUTE_PATH/target_repo" }
    }
  }
}
```

Replace `ABSOLUTE_PATH` with your actual paths.

#### 3. Run Analysis

```bash
# Analyze the test repository
python run_analysis.py --repo-path ./test_repo

# Analyze your own repository
python run_analysis.py --repo-path /path/to/your/repo

# Run specific agents only
python run_analysis.py --repo-path ./test_repo --agents architecture workflow

# Use parallel execution
python run_analysis.py --repo-path ./test_repo --parallel

# Verbose output
python run_analysis.py --repo-path ./test_repo --verbose
```

### Generated Documentation

The analysis generates comprehensive documentation in `docs/onboarding/`:

- **ONBOARDING_GUIDE.md** - Main onboarding guide for new developers
- **architecture_report.md** - Detailed architecture analysis
- **dependency_graph.json** - Dependency visualization data
- **workflow_guide.md** - Development workflow documentation
- **setup_instructions.md** - Step-by-step setup guide
- **hotspot_report.md** - Code quality and technical debt analysis
- **refactoring_priorities.json** - Prioritized refactoring recommendations
- **API_REFERENCE.md** - API documentation
- **FAQ.md** - Frequently asked questions

### Command-Line Options

```bash
python run_analysis.py --help
```

Options:

- `--repo-path PATH` - Repository to analyze (default: current directory)
- `--output-dir DIR` - Output directory (default: docs/onboarding)
- `--agents AGENT [AGENT ...]` - Specific agents to run
- `--parallel` - Run independent agents in parallel
- `--verbose` - Enable verbose logging
- `--mcp-config FILE` - Custom MCP server configuration

### Testing with Sample Repository

A test repository is included for testing:

```bash
# Initialize test repo as git repository (if not already done)
cd test_repo
git init
git add .
git commit -m "Initial commit"
cd ..

# Run analysis
python run_analysis.py --repo-path ./test_repo
```

## 📚 Next Steps (Phase 3 Preview)

After completing Phase 2, the next phase will include:

1. **Web Dashboard**
   - Interactive visualization of analysis results
   - Real-time analysis progress
   - Documentation browser

2. **Advanced Features**
   - Custom agent configurations
   - Multi-repository analysis
   - Historical trend analysis

3. **Integration & Deployment**
   - CI/CD integration
   - Docker containerization
   - Cloud deployment options

## 🤝 Contributing

This project follows the guidelines in `rules.md`:

- Never use placeholder production code
- Prefer runnable implementations
- Keep modules independent
- Use environment variables for credentials
- Follow async patterns consistently

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review `plan.md` for project details
3. Review `rules.md` for development guidelines
4. Check IBM watsonx.ai documentation

## 🎉 Phase 2 Complete!

You now have a fully functional AI-powered codebase analysis system with:

- ✅ MCP servers for code and git analysis
- ✅ AI agents using watsonx.ai
- ✅ Automated documentation generation
- ✅ Comprehensive onboarding guides

**Current Status**: ✅ Phase 2 Complete
**Next Phase**: 🚧 Phase 3 - Web Dashboard & Advanced Features

---

**Built with ❤️ using IBM watsonx.ai**
