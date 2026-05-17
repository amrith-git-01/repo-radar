/**
 * Data Collector
 * 
 * Orchestrates data collection from multiple MCP servers
 */

import { MCPClient } from './mcp-client.js';

export interface CollectedData {
  structure?: unknown;
  entryPoints?: unknown;
  dependencies?: unknown;
  complexity?: unknown;
  hotspots?: unknown;
  contributors?: unknown;
  fileHistory?: Record<string, unknown>;
}

export class DataCollector {
  constructor(private mcpClient: MCPClient) {}

  /**
   * Collect all data needed for documentation generation
   */
  async collectAll(): Promise<CollectedData> {
    const data: CollectedData = {};

    // Collect from code-analyzer
    if (this.mcpClient.isConnected('code-analyzer')) {
      try {
        data.structure = await this.mcpClient.callTool('code-analyzer', 'analyze_structure');
        data.entryPoints = await this.mcpClient.callTool('code-analyzer', 'find_entry_points');
        data.dependencies = await this.mcpClient.callTool('code-analyzer', 'analyze_dependencies');
        data.complexity = await this.mcpClient.callTool('code-analyzer', 'get_complexity_metrics');
      } catch (error) {
        console.error('Error collecting code analysis data:', error);
      }
    }

    // Collect from git-analyzer
    if (this.mcpClient.isConnected('git-analyzer')) {
      try {
        data.hotspots = await this.mcpClient.callTool('git-analyzer', 'get_hotspot_files', { limit: 20 });
        data.contributors = await this.mcpClient.callTool('git-analyzer', 'get_contributors');
      } catch (error) {
        console.error('Error collecting git analysis data:', error);
      }
    }

    return data;
  }

  /**
   * Collect data for onboarding guide
   */
  async collectForOnboarding(): Promise<CollectedData> {
    const data: CollectedData = {};

    if (this.mcpClient.isConnected('code-analyzer')) {
      try {
        data.structure = await this.mcpClient.callTool('code-analyzer', 'analyze_structure');
        data.entryPoints = await this.mcpClient.callTool('code-analyzer', 'find_entry_points');
        data.dependencies = await this.mcpClient.callTool('code-analyzer', 'analyze_dependencies');
      } catch (error) {
        console.error('Error collecting onboarding data:', error);
      }
    }

    if (this.mcpClient.isConnected('git-analyzer')) {
      try {
        data.hotspots = await this.mcpClient.callTool('git-analyzer', 'get_hotspot_files', { limit: 10 });
        data.contributors = await this.mcpClient.callTool('git-analyzer', 'get_contributors');
      } catch (error) {
        console.error('Error collecting git data for onboarding:', error);
      }
    }

    return data;
  }

  /**
   * Collect data for API reference
   * Complexity data is summarized to avoid oversized prompts.
   */
  async collectForAPIReference(): Promise<CollectedData> {
    const data: CollectedData = {};

    if (this.mcpClient.isConnected('code-analyzer')) {
      try {
        data.structure = await this.mcpClient.callTool('code-analyzer', 'analyze_structure');
        data.entryPoints = await this.mcpClient.callTool('code-analyzer', 'find_entry_points');
        data.dependencies = await this.mcpClient.callTool('code-analyzer', 'analyze_dependencies');
        // Summarize complexity to prevent oversized prompts
        data.complexity = await this.getSummaryStats();
      } catch (error) {
        console.error('Error collecting API reference data:', error);
      }
    }

    return data;
  }

  /**
   * Collect data for FAQ
   */
  async collectForFAQ(): Promise<CollectedData> {
    return await this.collectAll();
  }

  /**
   * Get file history for specific files
   */
  async getFileHistory(filePaths: string[]): Promise<Record<string, unknown>> {
    const history: Record<string, unknown> = {};

    if (!this.mcpClient.isConnected('git-analyzer')) {
      return history;
    }

    for (const filePath of filePaths) {
      try {
        history[filePath] = await this.mcpClient.callTool('git-analyzer', 'get_file_history', {
          file_path: filePath,
          limit: 20,
        });
      } catch (error) {
        console.error(`Error getting history for ${filePath}:`, error);
      }
    }

    return history;
  }

  /**
   * Get hotspot files with detailed history
   */
  async getHotspotsWithHistory(limit: number = 10): Promise<CollectedData> {
    const data: CollectedData = {};

    if (!this.mcpClient.isConnected('git-analyzer')) {
      return data;
    }

    try {
      const hotspots = await this.mcpClient.callTool('git-analyzer', 'get_hotspot_files', { limit }) as Array<{ path: string }>;
      data.hotspots = hotspots;

      // Get history for top hotspot files
      if (hotspots && Array.isArray(hotspots)) {
        const topFiles = hotspots.slice(0, 5).map(h => h.path);
        data.fileHistory = await this.getFileHistory(topFiles);
      }
    } catch (error) {
      console.error('Error getting hotspots with history:', error);
    }

    return data;
  }

  /**
   * Get summary statistics
   */
  async getSummaryStats(): Promise<{
    totalFiles: number;
    totalCommits: number;
    totalContributors: number;
    mainLanguages: string[];
    topDependencies: string[];
  }> {
    const stats = {
      totalFiles: 0,
      totalCommits: 0,
      totalContributors: 0,
      mainLanguages: [] as string[],
      topDependencies: [] as string[],
    };

    try {
      if (this.mcpClient.isConnected('code-analyzer')) {
        const structure = await this.mcpClient.callTool('code-analyzer', 'analyze_structure') as {
          totalFiles?: number;
          filesByExtension?: Record<string, number>;
        };
        
        if (structure) {
          stats.totalFiles = structure.totalFiles || 0;
          
          if (structure.filesByExtension) {
            stats.mainLanguages = Object.keys(structure.filesByExtension)
              .sort((a, b) => (structure.filesByExtension![b] || 0) - (structure.filesByExtension![a] || 0))
              .slice(0, 5);
          }
        }

        const dependencies = await this.mcpClient.callTool('code-analyzer', 'analyze_dependencies') as Array<{
          name: string;
          count: number;
        }>;
        
        if (dependencies && Array.isArray(dependencies)) {
          stats.topDependencies = dependencies.slice(0, 10).map(d => d.name);
        }
      }

      if (this.mcpClient.isConnected('git-analyzer')) {
        const contributors = await this.mcpClient.callTool('git-analyzer', 'get_contributors') as Array<{
          commits: number;
        }>;
        
        if (contributors && Array.isArray(contributors)) {
          stats.totalContributors = contributors.length;
          stats.totalCommits = contributors.reduce((sum, c) => sum + (c.commits || 0), 0);
        }
      }
    } catch (error) {
      console.error('Error getting summary stats:', error);
    }

    return stats;
  }
}

// Made with Bob
