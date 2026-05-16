# MCP Server Setup Guide

This guide explains how to set up and register MCP (Model Context Protocol) servers for use with Bob IDE and the DevRamp analysis system.

## Overview

DevRamp uses two MCP servers:
1. **code-analyzer** - Analyzes codebase structure, dependencies, and complexity
2. **git-analyzer** - Analyzes git history, hotspots, and contributors

## Prerequisites

- Node.js 18+ installed
- npm or pnpm package manager
- Bob IDE (for global MCP registration)

## Building MCP Servers

### 1. Install Dependencies

```bash
cd src/mcp-servers
npm install
```

### 2. Build Servers

```bash
npm run build
```

This will compile both servers:
- `code-analyzer/build/server.js`
- `git-analyzer/build/server.js`

### 3. Verify Build

Check that the build directories exist:
```bash
ls code-analyzer/build/server.js
ls git-analyzer/build/server.js
```

## Global MCP Registration for Bob IDE

**IMPORTANT**: MCP servers must be registered globally in Bob IDE to be accessible.

### Configuration File Location

The MCP configuration file location depends on your operating system:

- **Windows**: `%APPDATA%\.bob\mcp_servers.json`
  - Typically: `C:\Users\YourUsername\AppData\Roaming\.bob\mcp_servers.json`
  
- **macOS**: `~/.bob/mcp_servers.json`
  - Full path: `/Users/YourUsername/.bob/mcp_servers.json`
  
- **Linux**: `~/.bob/mcp_servers.json`
  - Full path: `/home/YourUsername/.bob/mcp_servers.json`

### Configuration Format

Create or edit the `mcp_servers.json` file with the following structure:

```json
{
  "mcpServers": {
    "code-analyzer": {
      "command": "node",
      "args": ["ABSOLUTE_PATH/src/mcp-servers/code-analyzer/build/server.js"],
      "env": {
        "REPO_PATH": "ABSOLUTE_PATH/target_repo"
      }
    },
    "git-analyzer": {
      "command": "node",
      "args": ["ABSOLUTE_PATH/src/mcp-servers/git-analyzer/build/server.js"],
      "env": {
        "REPO_PATH": "ABSOLUTE_PATH/target_repo"
      }
    }
  }
}
```

### Important Notes

1. **Use Absolute Paths**: Replace `ABSOLUTE_PATH` with the full path to your DevRamp installation
   - Windows example: `C:/Users/YourName/Desktop/Programs/ibm-bob/devramp`
   - macOS/Linux example: `/Users/YourName/projects/devramp`

2. **REPO_PATH Environment Variable**: Set this to the repository you want to analyze
   - Can be changed per analysis
   - Use forward slashes (/) even on Windows

3. **Path Separators**: Use forward slashes (/) in JSON, even on Windows

### Example Configuration (Windows)

```json
{
  "mcpServers": {
    "code-analyzer": {
      "command": "node",
      "args": ["C:/Users/vishn/Desktop/Programs/ibm-bob/devramp/src/mcp-servers/code-analyzer/build/server.js"],
      "env": {
        "REPO_PATH": "C:/Users/vishn/Desktop/Programs/ibm-bob/devramp/test_repo"
      }
    },
    "git-analyzer": {
      "command": "node",
      "args": ["C:/Users/vishn/Desktop/Programs/ibm-bob/devramp/src/mcp-servers/git-analyzer/build/server.js"],
      "env": {
        "REPO_PATH": "C:/Users/vishn/Desktop/Programs/ibm-bob/devramp/test_repo"
      }
    }
  }
}
```

### Example Configuration (macOS/Linux)

```json
{
  "mcpServers": {
    "code-analyzer": {
      "command": "node",
      "args": ["/Users/username/projects/devramp/src/mcp-servers/code-analyzer/build/server.js"],
      "env": {
        "REPO_PATH": "/Users/username/projects/devramp/test_repo"
      }
    },
    "git-analyzer": {
      "command": "node",
      "args": ["/Users/username/projects/devramp/src/mcp-servers/git-analyzer/build/server.js"],
      "env": {
        "REPO_PATH": "/Users/username/projects/devramp/test_repo"
      }
    }
  }
}
```

## Testing MCP Servers

### Manual Testing

You can test MCP servers manually using stdio:

```bash
# Test code-analyzer
cd src/mcp-servers
REPO_PATH=../../test_repo node code-analyzer/build/server.js

# Test git-analyzer
REPO_PATH=../../test_repo node git-analyzer/build/server.js
```

### Testing with Bob IDE

1. Restart Bob IDE after updating `mcp_servers.json`
2. Open Bob IDE and check the MCP servers panel
3. Verify both servers appear in the list
4. Try calling a tool to test connectivity

## Using MCP Servers with DevRamp

Once registered, the MCP servers will be automatically used by the DevRamp analysis pipeline:

```bash
python run_analysis.py --repo-path ./test_repo
```

The coordinator will:
1. Connect to registered MCP servers
2. Call tools as needed during analysis
3. Disconnect when complete

## Troubleshooting

### Server Not Found

**Problem**: Bob IDE can't find the MCP server

**Solutions**:
- Verify the path in `mcp_servers.json` is absolute and correct
- Check that the server.js file exists at the specified path
- Ensure you've run `npm run build` to compile the servers
- Restart Bob IDE after configuration changes

### Connection Errors

**Problem**: Can't connect to MCP server

**Solutions**:
- Check that Node.js is installed and in PATH
- Verify the REPO_PATH environment variable points to a valid directory
- Check server logs for error messages
- Ensure no other process is using the same stdio connection

### Tool Call Failures

**Problem**: MCP tool calls fail or timeout

**Solutions**:
- Verify REPO_PATH points to a valid git repository (for git-analyzer)
- Check that the repository has read permissions
- Ensure the repository isn't too large (may cause timeouts)
- Check for .git directory (required for git-analyzer)

### Build Errors

**Problem**: `npm run build` fails

**Solutions**:
- Delete `node_modules` and run `npm install` again
- Check Node.js version (requires 18+)
- Verify TypeScript is installed: `npm list typescript`
- Check for syntax errors in server.ts files

## Advanced Configuration

### Custom Environment Variables

You can add additional environment variables to the MCP server configuration:

```json
{
  "mcpServers": {
    "code-analyzer": {
      "command": "node",
      "args": ["..."],
      "env": {
        "REPO_PATH": "...",
        "DEBUG": "true",
        "MAX_FILES": "1000"
      }
    }
  }
}
```

### Multiple Repository Configurations

To analyze different repositories, update the REPO_PATH in the configuration:

```json
{
  "mcpServers": {
    "code-analyzer-project1": {
      "command": "node",
      "args": ["..."],
      "env": {
        "REPO_PATH": "/path/to/project1"
      }
    },
    "code-analyzer-project2": {
      "command": "node",
      "args": ["..."],
      "env": {
        "REPO_PATH": "/path/to/project2"
      }
    }
  }
}
```

## Security Considerations

1. **File Permissions**: Ensure MCP servers only have read access to repositories
2. **Path Validation**: Always use absolute paths to prevent path traversal
3. **Environment Variables**: Don't store sensitive data in environment variables
4. **Network Access**: MCP servers run locally and don't require network access

## Next Steps

After setting up MCP servers:

1. Test with the sample test_repo: `python run_analysis.py --repo-path ./test_repo`
2. Review generated documentation in `docs/onboarding/`
3. Try analyzing your own repositories
4. Customize agent behavior in `src/agents/`

## Support

For issues or questions:
- Check the main [README.md](../README.md)
- Review agent logs for detailed error messages
- Verify MCP server configuration is correct
- Ensure all prerequisites are installed