#!/usr/bin/env node

/**
 * Code Analyzer MCP Server
 * 
 * Provides tools for analyzing codebase structure, entry points, dependencies, and complexity metrics.
 * Uses the Model Context Protocol (MCP) to expose analysis capabilities to AI agents.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import * as fs from 'fs';
import * as path from 'path';

// Get repository path from environment variable
const REPO_PATH = process.env.REPO_PATH || process.cwd();

// Directories to exclude from analysis
const EXCLUDED_DIRS = new Set([
  '.git',
  'node_modules',
  'target',
  'build',
  'dist',
  '__pycache__',
  '.venv',
  'venv',
  '.idea',
  '.vscode',
  'coverage',
  '.pytest_cache',
]);

// File extensions to analyze
const CODE_EXTENSIONS = new Set([
  '.js', '.ts', '.jsx', '.tsx',
  '.py', '.java', '.cpp', '.c', '.h',
  '.cs', '.go', '.rs', '.rb', '.php',
  '.swift', '.kt', '.scala', '.sh',
]);

interface FileInfo {
  path: string;
  extension: string;
  size: number;
  lines: number;
}

interface StructureAnalysis {
  totalFiles: number;
  filesByExtension: Record<string, number>;
  directoryStructure: string[];
  largestFiles: Array<{ path: string; size: number; lines: number }>;
}

interface EntryPoint {
  path: string;
  type: string;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
}

interface Dependency {
  name: string;
  type: 'import' | 'require' | 'package';
  files: string[];
  count: number;
}

interface ComplexityMetrics {
  file: string;
  lines: number;
  functions: number;
  classes: number;
  complexity: number;
  maintainabilityIndex: number;
}

/**
 * Recursively walks directory tree and collects file information
 */
function walkDirectory(dir: string, baseDir: string = dir): FileInfo[] {
  const files: FileInfo[] = [];
  
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relativePath = path.relative(baseDir, fullPath);
      
      if (entry.isDirectory()) {
        if (!EXCLUDED_DIRS.has(entry.name)) {
          files.push(...walkDirectory(fullPath, baseDir));
        }
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name);
        if (CODE_EXTENSIONS.has(ext)) {
          try {
            const stats = fs.statSync(fullPath);
            const content = fs.readFileSync(fullPath, 'utf-8');
            const lines = content.split('\n').length;
            
            files.push({
              path: relativePath,
              extension: ext,
              size: stats.size,
              lines,
            });
          } catch (error) {
            console.error(`Error reading file ${fullPath}:`, error);
          }
        }
      }
    }
  } catch (error) {
    console.error(`Error reading directory ${dir}:`, error);
  }
  
  return files;
}

/**
 * Analyzes codebase structure
 */
function analyzeStructure(repoPath: string): StructureAnalysis {
  const files = walkDirectory(repoPath);
  
  const filesByExtension: Record<string, number> = {};
  for (const file of files) {
    filesByExtension[file.extension] = (filesByExtension[file.extension] || 0) + 1;
  }
  
  const directoryStructure = Array.from(
    new Set(files.map(f => path.dirname(f.path)))
  ).sort();
  
  const largestFiles = files
    .sort((a, b) => b.lines - a.lines)
    .slice(0, 10)
    .map(f => ({ path: f.path, size: f.size, lines: f.lines }));
  
  return {
    totalFiles: files.length,
    filesByExtension,
    directoryStructure,
    largestFiles,
  };
}

/**
 * Finds potential entry points in the codebase
 */
function findEntryPoints(repoPath: string): EntryPoint[] {
  const entryPoints: EntryPoint[] = [];
  const files = walkDirectory(repoPath);
  
  for (const file of files) {
    const fullPath = path.join(repoPath, file.path);
    const fileName = path.basename(file.path);
    const content = fs.readFileSync(fullPath, 'utf-8');
    
    // Check for common entry point patterns
    if (fileName === 'main.py' || fileName === 'app.py' || fileName === '__main__.py') {
      entryPoints.push({
        path: file.path,
        type: 'python_main',
        confidence: 'high',
        reason: 'Standard Python entry point filename',
      });
    } else if (fileName === 'index.js' || fileName === 'index.ts' || fileName === 'app.js' || fileName === 'app.ts') {
      entryPoints.push({
        path: file.path,
        type: 'javascript_main',
        confidence: 'high',
        reason: 'Standard JavaScript/TypeScript entry point',
      });
    } else if (fileName === 'Main.java') {
      entryPoints.push({
        path: file.path,
        type: 'java_main',
        confidence: 'high',
        reason: 'Java Main class',
      });
    } else if (content.includes('if __name__ == "__main__"')) {
      entryPoints.push({
        path: file.path,
        type: 'python_script',
        confidence: 'high',
        reason: 'Contains Python main guard',
      });
    } else if (content.includes('public static void main(')) {
      entryPoints.push({
        path: file.path,
        type: 'java_main_method',
        confidence: 'high',
        reason: 'Contains Java main method',
      });
    } else if (content.match(/app\.(listen|run)\(/)) {
      entryPoints.push({
        path: file.path,
        type: 'web_server',
        confidence: 'medium',
        reason: 'Contains server startup code',
      });
    }
  }
  
  return entryPoints;
}

/**
 * Analyzes dependencies in the codebase
 */
function analyzeDependencies(repoPath: string): Dependency[] {
  const dependencyMap = new Map<string, { type: string; files: Set<string> }>();
  const files = walkDirectory(repoPath);
  
  for (const file of files) {
    const fullPath = path.join(repoPath, file.path);
    const content = fs.readFileSync(fullPath, 'utf-8');
    
    // Python imports
    const pythonImports = content.matchAll(/^(?:from|import)\s+([a-zA-Z0-9_\.]+)/gm);
    for (const match of pythonImports) {
      const depName = match[1].split('.')[0];
      if (!depName.startsWith('.')) {
        if (!dependencyMap.has(depName)) {
          dependencyMap.set(depName, { type: 'import', files: new Set() });
        }
        dependencyMap.get(depName)!.files.add(file.path);
      }
    }
    
    // JavaScript/TypeScript imports
    const jsImports = content.matchAll(/(?:import|require)\s*\(?['"]([^'"]+)['"]\)?/g);
    for (const match of jsImports) {
      const depName = match[1];
      if (!depName.startsWith('.') && !depName.startsWith('/')) {
        const pkgName = depName.split('/')[0];
        if (!dependencyMap.has(pkgName)) {
          dependencyMap.set(pkgName, { type: 'import', files: new Set() });
        }
        dependencyMap.get(pkgName)!.files.add(file.path);
      }
    }
  }
  
  // Check package files
  const packageJsonPath = path.join(repoPath, 'package.json');
  if (fs.existsSync(packageJsonPath)) {
    try {
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
      const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
      for (const dep of Object.keys(deps)) {
        if (!dependencyMap.has(dep)) {
          dependencyMap.set(dep, { type: 'package', files: new Set() });
        }
      }
    } catch (error) {
      console.error('Error reading package.json:', error);
    }
  }
  
  const requirementsPath = path.join(repoPath, 'requirements.txt');
  if (fs.existsSync(requirementsPath)) {
    try {
      const content = fs.readFileSync(requirementsPath, 'utf-8');
      const lines = content.split('\n');
      for (const line of lines) {
        const match = line.match(/^([a-zA-Z0-9_-]+)/);
        if (match) {
          const dep = match[1];
          if (!dependencyMap.has(dep)) {
            dependencyMap.set(dep, { type: 'package', files: new Set() });
          }
        }
      }
    } catch (error) {
      console.error('Error reading requirements.txt:', error);
    }
  }
  
  return Array.from(dependencyMap.entries())
    .map(([name, data]) => ({
      name,
      type: data.type as 'import' | 'require' | 'package',
      files: Array.from(data.files),
      count: data.files.size,
    }))
    .sort((a, b) => b.count - a.count);
}

/**
 * Calculates complexity metrics for files
 */
function getComplexityMetrics(repoPath: string): ComplexityMetrics[] {
  const files = walkDirectory(repoPath);
  const metrics: ComplexityMetrics[] = [];
  
  for (const file of files) {
    const fullPath = path.join(repoPath, file.path);
    const content = fs.readFileSync(fullPath, 'utf-8');
    
    // Count functions
    const functionMatches = content.match(/(?:function|def|func|fn)\s+\w+/g) || [];
    const functions = functionMatches.length;
    
    // Count classes
    const classMatches = content.match(/(?:class|interface|struct)\s+\w+/g) || [];
    const classes = classMatches.length;
    
    // Simple cyclomatic complexity estimation
    const complexityKeywords = [
      'if', 'else', 'elif', 'for', 'while', 'case', 'catch',
      '&&', '||', '?', 'and', 'or',
    ];
    let complexity = 1; // Base complexity
    for (const keyword of complexityKeywords) {
      const regex = new RegExp(`\\b${keyword}\\b`, 'g');
      const matches = content.match(regex);
      if (matches) {
        complexity += matches.length;
      }
    }
    
    // Maintainability Index (simplified)
    // MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
    // Simplified version based on lines and complexity
    const loc = file.lines;
    const maintainabilityIndex = Math.max(
      0,
      Math.min(100, 171 - 5.2 * Math.log(loc + 1) - 0.23 * complexity - 16.2 * Math.log(loc + 1))
    );
    
    metrics.push({
      file: file.path,
      lines: file.lines,
      functions,
      classes,
      complexity,
      maintainabilityIndex: Math.round(maintainabilityIndex),
    });
  }
  
  return metrics.sort((a, b) => b.complexity - a.complexity);
}

/**
 * Main server setup
 */
async function main() {
  console.error('Starting Code Analyzer MCP Server...');
  console.error(`Repository path: ${REPO_PATH}`);
  
  const server = new Server(
    {
      name: 'code-analyzer',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );
  
  // Define available tools
  const tools: Tool[] = [
    {
      name: 'analyze_structure',
      description: 'Analyzes the overall structure of the codebase, including file counts, directory structure, and largest files',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    {
      name: 'find_entry_points',
      description: 'Identifies potential entry points in the codebase (main files, scripts, server startup files)',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    {
      name: 'analyze_dependencies',
      description: 'Analyzes external dependencies used in the codebase from imports and package files',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
    {
      name: 'get_complexity_metrics',
      description: 'Calculates complexity metrics for files including cyclomatic complexity and maintainability index',
      inputSchema: {
        type: 'object',
        properties: {},
      },
    },
  ];
  
  // Handle tool list requests
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools,
  }));
  
  // Handle tool execution requests
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name } = request.params;
    
    try {
      let result: unknown;
      
      switch (name) {
        case 'analyze_structure':
          result = analyzeStructure(REPO_PATH);
          break;
          
        case 'find_entry_points':
          result = findEntryPoints(REPO_PATH);
          break;
          
        case 'analyze_dependencies':
          result = analyzeDependencies(REPO_PATH);
          break;
          
        case 'get_complexity_metrics':
          result = getComplexityMetrics(REPO_PATH);
          break;
          
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      } as const;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error(`Error executing tool ${name}:`, errorMessage);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({ error: errorMessage }, null, 2),
          },
        ],
        isError: true,
      } as const;
    }
  });
  
  // Start server with stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('Code Analyzer MCP Server running on stdio');
}

// Run the server
main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

// Made with Bob
