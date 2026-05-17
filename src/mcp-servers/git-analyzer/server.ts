#!/usr/bin/env node

/**
 * Git Analyzer MCP Server
 *
 * Provides tools for analyzing git repository history, hotspots, and contributors.
 * Uses the Model Context Protocol (MCP) to expose git analysis capabilities to AI agents.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { execSync } from "child_process";
import * as path from "path";
import * as fs from "fs";

// Get repository path from environment variable
const REPO_PATH = process.env["REPO_PATH"] || process.cwd();

interface HotspotFile {
  path: string;
  commits: number;
  authors: number;
  lastModified: string;
  changeFrequency: number;
}

interface Contributor {
  name: string;
  email: string;
  commits: number;
  linesAdded: number;
  linesDeleted: number;
  firstCommit: string;
  lastCommit: string;
  files: string[];
}

interface FileHistory {
  path: string;
  commits: Array<{
    hash: string;
    author: string;
    date: string;
    message: string;
    changes: {
      additions: number;
      deletions: number;
    };
  }>;
  totalCommits: number;
  authors: string[];
}

/**
 * Executes a git command and returns the output
 */
function executeGitCommand(command: string): string {
  try {
    const fullCommand = `git -C "${REPO_PATH}" ${command}`;
    return execSync(fullCommand, {
      encoding: "utf-8",
      maxBuffer: 10 * 1024 * 1024,
    });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Git command failed: ${errorMessage}`);
  }
}

/**
 * Checks if the repository is a valid git repository
 */
function isGitRepository(): boolean {
  try {
    executeGitCommand("rev-parse --git-dir");
    return true;
  } catch {
    return false;
  }
}

/**
 * Gets hotspot files (files with most changes)
 */
function getHotspotFiles(limit: number = 20): HotspotFile[] {
  if (!isGitRepository()) {
    throw new Error("Not a git repository");
  }

  try {
    // Get all files with their commit counts
    const output = executeGitCommand(
      'log --name-only --pretty=format:"%H|%an|%ad" --date=iso',
    );
    const lines = output.split("\n").filter((line) => line.trim());

    const fileStats = new Map<
      string,
      {
        commits: Set<string>;
        authors: Set<string>;
        lastModified: string;
      }
    >();

    let currentCommit = "";
    let currentAuthor = "";
    let currentDate = "";

    for (const line of lines) {
      if (line.includes("|")) {
        // This is a commit header line
        const parts = line.split("|");
        const hash = parts[0] ?? "";
        const author = parts[1] ?? "";
        const date = parts[2] ?? "";
        currentCommit = hash;
        currentAuthor = author;
        currentDate = date;
      } else if (line.trim() && currentCommit) {
        // This is a file path
        const filePath = line.trim();

        // Skip non-code files
        if (
          filePath.includes("node_modules/") ||
          filePath.includes(".git/") ||
          filePath.includes("target/") ||
          filePath.includes("build/") ||
          filePath.includes("dist/")
        ) {
          continue;
        }

        if (!fileStats.has(filePath)) {
          fileStats.set(filePath, {
            commits: new Set(),
            authors: new Set(),
            lastModified: currentDate,
          });
        }

        const stats = fileStats.get(filePath)!;
        stats.commits.add(currentCommit);
        stats.authors.add(currentAuthor);

        // Update last modified if this commit is more recent
        if (new Date(currentDate) > new Date(stats.lastModified)) {
          stats.lastModified = currentDate;
        }
      }
    }

    // Convert to array and calculate change frequency
    const hotspots: HotspotFile[] = [];
    for (const [filePath, stats] of fileStats.entries()) {
      // Check if file still exists
      const fullPath = path.join(REPO_PATH, filePath);
      if (!fs.existsSync(fullPath)) {
        continue;
      }

      const commits = stats.commits.size;
      const authors = stats.authors.size;

      // Calculate change frequency (commits per day since first commit)
      const daysSinceLastModified = Math.max(
        1,
        (Date.now() - new Date(stats.lastModified).getTime()) /
          (1000 * 60 * 60 * 24),
      );
      const changeFrequency = commits / daysSinceLastModified;

      hotspots.push({
        path: filePath,
        commits,
        authors,
        lastModified: stats.lastModified,
        changeFrequency,
      });
    }

    // Sort by commit count and return top N
    return hotspots.sort((a, b) => b.commits - a.commits).slice(0, limit);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to get hotspot files: ${errorMessage}`);
  }
}

/**
 * Gets contributor statistics
 */
function getContributors(): Contributor[] {
  if (!isGitRepository()) {
    throw new Error("Not a git repository");
  }

  try {
    // Use shortlog for large repos (avoids huge --numstat payloads)
    const output = executeGitCommand("shortlog -sne --all");
    const contributors: Contributor[] = [];

    for (const line of output.split("\n")) {
      const match = line.trim().match(/^(\d+)\s+(.+?)\s+<([^>]+)>$/);
      if (!match) {
        continue;
      }
      const commits = parseInt(match[1] ?? "0", 10);
      const name = match[2] ?? "";
      const email = match[3] ?? "";
      contributors.push({
        name,
        email,
        commits,
        linesAdded: 0,
        linesDeleted: 0,
        firstCommit: "",
        lastCommit: "",
        files: [],
      });
    }

    return contributors.sort((a, b) => b.commits - a.commits);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to get contributors: ${errorMessage}`);
  }
}

/**
 * Gets history for a specific file
 */
function getFileHistory(filePath: string, limit: number = 50): FileHistory {
  if (!isGitRepository()) {
    throw new Error("Not a git repository");
  }

  try {
    // Get commits for the file
    const output = executeGitCommand(
      `log --follow --pretty=format:"%H|%an|%ad|%s" --date=iso --numstat -n ${limit} -- "${filePath}"`,
    );

    if (!output.trim()) {
      return {
        path: filePath,
        commits: [],
        totalCommits: 0,
        authors: [],
      };
    }

    const lines = output.split("\n");
    const commits: FileHistory["commits"] = [];
    const authors = new Set<string>();

    let currentCommit: FileHistory["commits"][0] | null = null;

    for (const line of lines) {
      if (line.includes("|")) {
        // Save previous commit if exists
        if (currentCommit) {
          commits.push(currentCommit);
        }

        // Parse new commit header
        const parts = line.split("|");
        const hash = parts[0] ?? "";
        const author = parts[1] ?? "";
        const date = parts[2] ?? "";
        const messageParts = parts.slice(3);
        const message = messageParts.join("|");

        if (author) {
          authors.add(author);
        }

        currentCommit = {
          hash,
          author,
          date,
          message,
          changes: {
            additions: 0,
            deletions: 0,
          },
        };
      } else if (line.trim() && currentCommit) {
        // Parse numstat line
        const match = line.match(/^(\d+|-)\s+(\d+|-)\s+/);
        if (match) {
          const added = match[1];
          const deleted = match[2];
          if (added && added !== "-") {
            currentCommit.changes.additions += parseInt(added, 10);
          }
          if (deleted && deleted !== "-") {
            currentCommit.changes.deletions += parseInt(deleted, 10);
          }
        }
      }
    }

    // Add last commit
    if (currentCommit) {
      commits.push(currentCommit);
    }

    return {
      path: filePath,
      commits,
      totalCommits: commits.length,
      authors: Array.from(authors),
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to get file history: ${errorMessage}`);
  }
}

/**
 * Main server setup
 */
async function main() {
  console.error("Starting Git Analyzer MCP Server...");
  console.error(`Repository path: ${REPO_PATH}`);

  const server = new Server(
    {
      name: "git-analyzer",
      version: "1.0.0",
    },
    {
      capabilities: {
        tools: {},
      },
    },
  );

  // Define available tools
  const tools: Tool[] = [
    {
      name: "get_hotspot_files",
      description:
        "Identifies files with the most changes (hotspots) that may need refactoring",
      inputSchema: {
        type: "object",
        properties: {
          limit: {
            type: "number",
            description:
              "Maximum number of hotspot files to return (default: 20)",
            default: 20,
          },
        },
      },
    },
    {
      name: "get_contributors",
      description: "Gets statistics about all contributors to the repository",
      inputSchema: {
        type: "object",
        properties: {},
      },
    },
    {
      name: "get_file_history",
      description: "Gets the commit history for a specific file",
      inputSchema: {
        type: "object",
        properties: {
          file_path: {
            type: "string",
            description: "Path to the file relative to repository root",
          },
          limit: {
            type: "number",
            description: "Maximum number of commits to return (default: 50)",
            default: 50,
          },
        },
        required: ["file_path"],
      },
    },
  ];

  // Handle tool list requests
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools,
  }));

  // Handle tool execution requests
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      let result: unknown;

      switch (name) {
        case "get_hotspot_files": {
          const limit = (args as { limit?: number })?.limit || 20;
          result = getHotspotFiles(limit);
          break;
        }

        case "get_contributors":
          result = getContributors();
          break;

        case "get_file_history": {
          const filePath = (args as { file_path: string }).file_path;
          const limit = (args as { limit?: number })?.limit || 50;

          if (!filePath) {
            throw new Error("file_path parameter is required");
          }

          result = getFileHistory(filePath, limit);
          break;
        }

        default:
          throw new Error(`Unknown tool: ${name}`);
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result, null, 2),
          },
        ],
      } as const;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      console.error(`Error executing tool ${name}:`, errorMessage);

      return {
        content: [
          {
            type: "text",
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

  console.error("Git Analyzer MCP Server running on stdio");
}

// Run the server
main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});

// Made with Bob
