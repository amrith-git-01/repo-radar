#!/usr/bin/env node

/**
 * Documentation Generator MCP Server
 * 
 * Provides tools for generating comprehensive documentation for legacy codebases.
 * Integrates with code-analyzer and git-analyzer MCP servers and uses watsonx.ai for content generation.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  GetPromptRequestSchema,
  ListPromptsRequestSchema,
  Prompt,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';

import { createWatsonXClient } from './src/ai/watsonx-client.js';
import { createMCPClient } from './src/orchestrator/mcp-client.js';
import { DataCollector, CollectedData } from './src/orchestrator/data-collector.js';
import { OnboardingGenerator } from './src/tools/onboarding.js';
import { APIReferenceGenerator } from './src/tools/api-reference.js';
import { FAQGenerator } from './src/tools/faq.js';
import { SectionUpdater } from './src/tools/section-updater.js';
import { DocumentValidator } from './src/tools/validator.js';
import { getAPIReferenceTemplate, getFAQTemplate } from './src/formatters/templates.js';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const currentFilePath = fileURLToPath(import.meta.url);
const currentDir = path.dirname(currentFilePath);

// Load .env file manually (no dotenv dependency needed)
function loadEnvFile(): void {
  const repoPath = process.env['REPO_PATH'] || process.cwd();
  const reservedKeys = new Set(['REPO_PATH', 'OUTPUT_DIR']);
  const searchPaths = [
    path.resolve(repoPath, '.env'),
    path.resolve(process.cwd(), '.env'),
    path.resolve(currentDir, '../../../.env'),
    path.resolve(currentDir, '../../../../.env'),
    path.join(path.dirname(repoPath), '.env'),
  ];
  console.error('[loadEnvFile] Searching for .env in paths:', searchPaths);
  for (const envPath of searchPaths) {
    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, 'utf-8');
      for (const line of content.split('\n')) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
          const eqIdx = trimmed.indexOf('=');
          if (eqIdx > 0) {
            const key = trimmed.slice(0, eqIdx).trim();
            const value = trimmed.slice(eqIdx + 1).trim();
            if (!process.env[key] && !reservedKeys.has(key)) {
              process.env[key] = value;
            }
          }
        }
      }
      console.error(`[loadEnvFile] Loaded environment from ${envPath}`);
      return;
    }
  }
  console.error('Warning: No .env file found');
}

loadEnvFile();

// Get repository path from environment variable
const REPO_PATH = process.env['REPO_PATH'] || process.cwd();
const OUTPUT_DIR = process.env['OUTPUT_DIR'] || 'docs/onboarding';

const prompts: Prompt[] = [
  {
    name: 'devramp_onboarding_mode',
    description: 'Bob onboarding mode prompt that forces an MCP-backed documentation flow',
    arguments: [
      {
        name: 'repo_path',
        description: 'Repository path to onboard, such as "." or "test_repo"',
        required: false,
      },
      {
        name: 'project_name',
        description: 'Optional project name to use in generated documentation',
        required: false,
      },
    ],
  },
  {
    name: 'devramp_architecture_review',
    description: 'Prompt for architecture-first onboarding using MCP evidence',
    arguments: [
      {
        name: 'repo_path',
        description: 'Repository path to analyze',
        required: false,
      },
    ],
  },
  {
    name: 'devramp_first_week_plan',
    description: 'Prompt for generating a detailed first-week developer onboarding plan from generated docs',
    arguments: [
      {
        name: 'repo_path',
        description: 'Repository path to onboard',
        required: false,
      },
    ],
  },
];

function getPromptText(name: string, args: Record<string, string> = {}): string {
  const repoPath = args['repo_path'] || REPO_PATH || '.';
  const projectName = args['project_name'] || 'the target repository';

  switch (name) {
    case 'devramp_onboarding_mode':
      return `You are Bob's DevRamp Onboarding Assistant for ${projectName}.

Use MCP tools first. Do not generate onboarding content from general model knowledge until the MCP-backed document flow has been attempted.

Repository path: ${repoPath}

Required tool flow:
1. Call documentation-generator.generate_onboarding_package with output_dir "docs/onboarding" and project_name "${projectName}" when known.
2. Confirm the package includes ONBOARDING_GUIDE.md, API_REFERENCE.md, FAQ.md, ARCHITECTURE.md, WORKFLOWS.md, HOTSPOTS.md, and diagrams/*.mmd.
3. Call documentation-generator.validate_documentation on the generated Markdown files.
4. Use code-analyzer and git-analyzer MCP evidence for architecture, entry points, dependencies, workflows, hotspots, contributors, and complexity.

Quality bar:
- The docs must be specific and detailed: real repo paths, concrete commands, important modules, dependencies, entry points, and high-risk files.
- Use polished Markdown: clear headings, tables where helpful, checklists, code fences, cross-links, and Mermaid diagrams when MCP or generated outputs provide them.
- Never invent setup commands, APIs, architecture patterns, deployment steps, owners, or team contacts. If MCP data does not show something, write "Not found in MCP data" and suggest how to verify it.
- After generation, summarize created files, validation findings, and the first three reading steps for a new developer.`;

    case 'devramp_architecture_review':
      return `Use DevRamp MCP tools to produce an architecture-first onboarding explanation for ${repoPath}.

Start from code-analyzer MCP data: structure, entry points, dependencies, and complexity. Add git-analyzer evidence only for hotspots or ownership context. Explain architecture claims with file paths and observable evidence. Include Mermaid diagrams only when they are valid and supported by the MCP data. Mark unknowns as "Not found in MCP data".`;

    case 'devramp_first_week_plan':
      return `Create a first-week onboarding plan for a developer joining ${repoPath}, but only after using the DevRamp MCP-generated docs and validation results.

Base the plan on ONBOARDING_GUIDE.md, API_REFERENCE.md, FAQ.md, architecture/workflow outputs, code hotspots, and validation findings. Organize the plan by Day 1, Days 2-3, Days 4-5, and first PR. Include exact files to read, commands to run, questions to ask, and risks to avoid. Do not include generic tasks unless they are grounded in MCP evidence.`;

    default:
      throw new Error(`Unknown prompt: ${name}`);
  }
}

type AnyRecord = Record<string, any>;

function asRecords(value: unknown): AnyRecord[] {
  return Array.isArray(value)
    ? value.filter((item): item is AnyRecord => Boolean(item) && typeof item === 'object')
    : [];
}

function stringifyValue(value: unknown): string {
  if (value === undefined || value === null || value === '') {
    return 'Not found in MCP data';
  }
  if (typeof value === 'string') {
    return value;
  }
  return JSON.stringify(value);
}

function escapeMermaidLabel(value: unknown): string {
  return stringifyValue(value)
    .replace(/["\\]/g, '')
    .replace(/\r?\n/g, ' ')
    .slice(0, 80);
}

function writeMarkdownFile(filePath: string, content: string): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, 'utf-8');
}

function writeDiagram(outputDir: string, name: string, mermaid: string): string {
  const diagramsDir = path.join(outputDir, 'diagrams');
  fs.mkdirSync(diagramsDir, { recursive: true });
  const filePath = path.join(diagramsDir, `${name}.mmd`);
  fs.writeFileSync(filePath, `${mermaid.trim()}\n`, 'utf-8');
  return filePath;
}

function markdownTable(headers: string[], rows: string[][]): string {
  if (rows.length === 0) {
    return 'Not found in MCP data.\n';
  }
  const header = `| ${headers.join(' |')} |`;
  const divider = `| ${headers.map(() => '---').join(' | ')} |`;
  const body = rows.map((row) => `| ${row.map((cell) => cell.replace(/\r?\n/g, ' ')).join(' | ')} |`);
  return [header, divider, ...body].join('\n') + '\n';
}

function topEntryPoints(data: CollectedData): AnyRecord[] {
  return asRecords(data.entryPoints).slice(0, 8);
}

function topDependencies(data: CollectedData): AnyRecord[] {
  return asRecords(data.dependencies).slice(0, 12);
}

function topHotspots(data: CollectedData): AnyRecord[] {
  return asRecords(data.hotspots).slice(0, 10);
}

function buildArchitectureDiagram(data: CollectedData): string {
  const lines = [
    'flowchart LR',
    '  Developer["New developer"] --> Repo["Repository"]',
  ];

  topEntryPoints(data).forEach((entry, index) => {
    const id = `Entry${index}`;
    lines.push(`  Repo --> ${id}["${escapeMermaidLabel(entry.path || entry.file || entry.name)}"]`);
  });

  topDependencies(data).slice(0, 6).forEach((dep, index) => {
    const id = `Dep${index}`;
    lines.push(`  Repo --> ${id}["${escapeMermaidLabel(dep.name || dep.path || dep)}"]`);
  });

  return lines.join('\n');
}

function buildDependencyDiagram(data: CollectedData): string {
  const lines = [
    'flowchart TD',
    '  Repo["Repository"]',
  ];

  topDependencies(data).forEach((dep, index) => {
    const id = `Dep${index}`;
    const label = dep.name || dep.path || dep.package || `dependency ${index + 1}`;
    const count = dep.count || dep.usage_count || dep.files?.length;
    lines.push(`  Repo --> ${id}["${escapeMermaidLabel(label)}${count ? ` (${count})` : ''}"]`);
  });

  if (lines.length === 2) {
    lines.push('  Repo --> Missing["Not found in MCP data"]');
  }

  return lines.join('\n');
}

function buildHotspotDiagram(data: CollectedData): string {
  const lines = [
    'flowchart TD',
    '  Hotspots["Code hotspots"]',
  ];

  topHotspots(data).forEach((hotspot, index) => {
    const id = `Hotspot${index}`;
    const label = hotspot.path || hotspot.file || hotspot.name || `hotspot ${index + 1}`;
    const risk = hotspot.risk_score || hotspot.risk || hotspot.commits || hotspot.changeFrequency;
    lines.push(`  Hotspots --> ${id}["${escapeMermaidLabel(label)}${risk ? ` - ${escapeMermaidLabel(risk)}` : ''}"]`);
  });

  if (lines.length === 2) {
    lines.push('  Hotspots --> Missing["Not found in MCP data"]');
  }

  return lines.join('\n');
}

function buildWorkflowDiagram(workflowFiles: string[]): string {
  const lines = [
    'flowchart LR',
    '  Start["Open repo"] --> Setup["Install dependencies"]',
    '  Setup --> Run["Run project"]',
    '  Run --> Test["Run tests"]',
    '  Test --> Change["Make first change"]',
  ];

  workflowFiles.slice(0, 5).forEach((file, index) => {
    lines.push(`  Setup --> WF${index}["${escapeMermaidLabel(file)}"]`);
  });

  return lines.join('\n');
}

function discoverWorkflowFiles(repoPath: string): string[] {
  const candidates = [
    'README.md',
    'CONTRIBUTING.md',
    'package.json',
    'requirements.txt',
    'pyproject.toml',
    'Pipfile',
    'Makefile',
    'Dockerfile',
    'docker-compose.yml',
    '.github/workflows',
    '.gitlab-ci.yml',
    'Jenkinsfile',
  ];

  return candidates.filter((candidate) => fs.existsSync(path.join(repoPath, candidate)));
}

function buildArchitectureMarkdown(projectName: string, data: CollectedData, diagrams: Record<string, string>): string {
  const structure = (data.structure || {}) as AnyRecord;
  const filesByExtension = (structure.filesByExtension || {}) as Record<string, number>;
  const languages = Object.entries(filesByExtension)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([ext, count]) => `${ext}: ${count}`)
    .join(', ') || 'Not found in MCP data';

  const entryRows = topEntryPoints(data).map((entry) => [
    `\`${stringifyValue(entry.path || entry.file || entry.name)}\``,
    stringifyValue(entry.type),
    stringifyValue(entry.reason || entry.confidence),
  ]);

  const dependencyRows = topDependencies(data).map((dep) => [
    `\`${stringifyValue(dep.name || dep.path || dep.package)}\``,
    stringifyValue(dep.type),
    stringifyValue(dep.count || dep.files?.length || dep.usage_count),
  ]);

  return `# Architecture

## Overview

Project: **${projectName}**

- Total files: ${stringifyValue(structure.totalFiles)}
- Main languages/extensions: ${languages}
- Architecture confidence: derived from MCP code-analyzer structure, entry points, and dependencies.

## System Map

\`\`\`mermaid
${diagrams.architecture}
\`\`\`

## Entry Points

${markdownTable(['Path', 'Type', 'Evidence'], entryRows)}

## Dependency Map

\`\`\`mermaid
${diagrams.dependencies}
\`\`\`

## Key Dependencies

${markdownTable(['Dependency', 'Type', 'Usage'], dependencyRows)}

## Notes For New Developers

- Start with the entry points above before reading low-level modules.
- Treat missing rows as "Not found in MCP data" rather than a claim that the repo has no such concept.
`;
}

function buildWorkflowsMarkdown(projectName: string, repoPath: string, diagrams: Record<string, string>): string {
  const workflowFiles = discoverWorkflowFiles(repoPath);
  const rows = workflowFiles.map((file) => [
    `\`${file}\``,
    file.includes('requirements') || file.includes('package') || file.includes('pyproject')
      ? 'Dependencies/setup'
      : file.includes('workflow') || file.includes('ci') || file.includes('Jenkins')
        ? 'Automation'
        : 'Project guidance',
  ]);

  return `# Workflows

## Overview

Project: **${projectName}**

This document is generated from repository workflow files discovered by the MCP-backed documentation generator.

## Workflow Map

\`\`\`mermaid
${diagrams.workflow}
\`\`\`

## Discovered Workflow Files

${markdownTable(['File', 'Likely purpose'], rows)}

## First Local Pass

- Read the discovered workflow files before running commands.
- Use package or requirements files as the source of truth for installation.
- If setup, test, or deployment commands are absent, mark them as "Not found in MCP data" and verify with the team.
`;
}

function buildHotspotsMarkdown(projectName: string, data: CollectedData, diagrams: Record<string, string>): string {
  const hotspotRows = topHotspots(data).map((hotspot) => [
    `\`${stringifyValue(hotspot.path || hotspot.file || hotspot.name)}\``,
    stringifyValue(hotspot.commits || hotspot.changeFrequency || hotspot.risk_score || hotspot.risk),
    stringifyValue(hotspot.authors || hotspot.contributors || hotspot.complexity),
  ]);

  return `# Hotspots

## Overview

Project: **${projectName}**

Hotspots are files that MCP git/code analysis indicates may deserve extra care during onboarding.

## Hotspot Map

\`\`\`mermaid
${diagrams.hotspots}
\`\`\`

## Files To Approach Carefully

${markdownTable(['File', 'Change/risk signal', 'Ownership/complexity signal'], hotspotRows)}

## How To Use This

- Review hotspot files before making broad changes.
- Add or run focused tests before editing frequently changed areas.
- If a metric is missing, treat it as "Not found in MCP data" rather than assuming the file is safe.
`;
}

async function generateOnboardingPackage(options: {
  outputDir: string;
  projectName: string;
  onboardingGen: OnboardingGenerator;
  apiRefGen: APIReferenceGenerator;
  faqGen: FAQGenerator;
  dataCollector: DataCollector;
}): Promise<Record<string, unknown>> {
  const { outputDir, projectName, onboardingGen, apiRefGen, faqGen, dataCollector } = options;
  fs.mkdirSync(outputDir, { recursive: true });

  const onboardingPath = path.join(outputDir, 'ONBOARDING_GUIDE.md');
  const apiPath = path.join(outputDir, 'API_REFERENCE.md');
  const faqPath = path.join(outputDir, 'FAQ.md');
  const architecturePath = path.join(outputDir, 'ARCHITECTURE.md');
  const workflowsPath = path.join(outputDir, 'WORKFLOWS.md');
  const hotspotsPath = path.join(outputDir, 'HOTSPOTS.md');

  const results = await Promise.allSettled([
    onboardingGen.generate({ outputPath: onboardingPath, projectName }),
    apiRefGen.generate({ outputPath: apiPath, projectName }),
    faqGen.generate({ outputPath: faqPath, projectName }),
    dataCollector.collectAll(),
  ]);

  const [onboardingResult, apiResult, faqResult, dataResult] = results;

  const onboardingContent = onboardingResult.status === 'fulfilled' ? onboardingResult.value : '# Onboarding Guide\n\n*Not generated: AI generation failed.*';
  const apiContent = apiResult.status === 'fulfilled' ? apiResult.value : getAPIReferenceTemplate(projectName);
  const faqContent = faqResult.status === 'fulfilled' ? faqResult.value : getFAQTemplate(projectName);
  const data = dataResult.status === 'fulfilled' && dataResult.value ? dataResult.value : {};

  const diagrams = {
    architecture: buildArchitectureDiagram(data),
    dependencies: buildDependencyDiagram(data),
    workflow: buildWorkflowDiagram(discoverWorkflowFiles(REPO_PATH)),
    hotspots: buildHotspotDiagram(data),
  };

  const diagramPaths = {
    architecture: writeDiagram(outputDir, 'architecture-system-map', diagrams.architecture),
    dependencies: writeDiagram(outputDir, 'architecture-dependency-map', diagrams.dependencies),
    workflow: writeDiagram(outputDir, 'workflow-map', diagrams.workflow),
    hotspots: writeDiagram(outputDir, 'hotspot-map', diagrams.hotspots),
  };

  writeMarkdownFile(architecturePath, buildArchitectureMarkdown(projectName, data, diagrams));
  writeMarkdownFile(workflowsPath, buildWorkflowsMarkdown(projectName, REPO_PATH, diagrams));
  writeMarkdownFile(hotspotsPath, buildHotspotsMarkdown(projectName, data, diagrams));

  return {
    success: true,
    message: `Onboarding package generated successfully at ${outputDir}`,
    outputDir,
    documents: {
      onboardingGuide: onboardingPath,
      apiReference: apiPath,
      faq: faqPath,
      architecture: architecturePath,
      workflows: workflowsPath,
      hotspots: hotspotsPath,
    },
    diagrams: diagramPaths,
    preview: onboardingContent.substring(0, 500) + '...',
    generatedLengths: {
      onboardingGuide: onboardingContent.length,
      apiReference: apiContent.length,
      faq: faqContent.length,
    },
  };
}

/**
 * Main server setup
 */
async function main() {
  console.error('Starting Documentation Generator MCP Server...');
  console.error(`Repository path: ${REPO_PATH}`);
  console.error(`Output directory: ${OUTPUT_DIR}`);

  // Initialize clients with better error handling
  let watsonxClient: ReturnType<typeof createWatsonXClient> | undefined;
  let mcpClient: Awaited<ReturnType<typeof createMCPClient>> | undefined;
  let dataCollector: DataCollector | undefined;
  let onboardingGen: OnboardingGenerator | undefined;
  let apiRefGen: APIReferenceGenerator | undefined;
  let faqGen: FAQGenerator | undefined;
  let sectionUpdater: SectionUpdater | undefined;
  let validator: DocumentValidator | undefined;

  // Track initialization errors
  const initErrors: string[] = [];

  // Initialize WatsonX client
  try {
    watsonxClient = createWatsonXClient();
    console.error('✓ WatsonX client initialized successfully');
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    initErrors.push(`WatsonX client: ${errorMsg}`);
    console.error('✗ Failed to initialize WatsonX client:', errorMsg);
    console.error('  Make sure WATSONX_API_KEY and WATSONX_PROJECT_ID are set in environment');
  }

  // Initialize MCP client
  try {
    mcpClient = await createMCPClient(REPO_PATH);
    dataCollector = new DataCollector(mcpClient);
    console.error('✓ MCP client and data collector initialized successfully');
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    initErrors.push(`MCP client: ${errorMsg}`);
    console.error('✗ Failed to initialize MCP client:', errorMsg);
    console.error('  Code and git analysis features may be limited');
  }

  // Initialize tool generators - require at minimum watsonxClient
  // dataCollector is optional for some tools
  if (watsonxClient) {
    try {
      if (dataCollector) {
        onboardingGen = new OnboardingGenerator(watsonxClient, dataCollector);
        apiRefGen = new APIReferenceGenerator(watsonxClient, dataCollector);
        faqGen = new FAQGenerator(watsonxClient, dataCollector);
        sectionUpdater = new SectionUpdater(watsonxClient, dataCollector);
        console.error('✓ All tool generators initialized successfully');
      } else {
        console.error('⚠ Tool generators initialized without data collector (limited functionality)');
        // Initialize with a mock data collector that returns empty data
        const mockDataCollector = new DataCollector(mcpClient!);
        onboardingGen = new OnboardingGenerator(watsonxClient, mockDataCollector);
        apiRefGen = new APIReferenceGenerator(watsonxClient, mockDataCollector);
        faqGen = new FAQGenerator(watsonxClient, mockDataCollector);
        sectionUpdater = new SectionUpdater(watsonxClient, mockDataCollector);
      }
      validator = new DocumentValidator(watsonxClient);
      console.error('✓ Document validator initialized successfully');
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      initErrors.push(`Tool generators: ${errorMsg}`);
      console.error('✗ Failed to initialize tool generators:', errorMsg);
    }
  } else {
    initErrors.push('Cannot initialize tools: WatsonX client is required');
    console.error('✗ Cannot initialize tools: WatsonX client is required');
  }

  // Log initialization summary
  if (initErrors.length === 0) {
    console.error('\n✓ All components initialized successfully');
  } else {
    console.error('\n⚠ Server started with initialization warnings:');
    initErrors.forEach(err => console.error(`  - ${err}`));
    console.error('\nSome tools may not be available. Check environment variables and dependencies.');
  }

  const server = new Server(
    {
      name: 'documentation-generator',
      version: '1.0.0',
    },
    {
      capabilities: {
        prompts: {},
        tools: {},
      },
    }
  );

  // Define available tools
  const tools: Tool[] = [
    {
      name: 'generate_onboarding_package',
      description: 'Generates the complete onboarding package: guide, API reference, FAQ, architecture, workflows, hotspots, and Mermaid diagrams',
      inputSchema: {
        type: 'object',
        properties: {
          output_dir: {
            type: 'string',
            description: 'Directory where the onboarding package should be saved',
          },
          project_name: {
            type: 'string',
            description: 'Name of the project',
          },
        },
      },
    },
    {
      name: 'generate_onboarding_guide',
      description: 'Generates a comprehensive onboarding guide (ONBOARDING_GUIDE.md) for the codebase',
      inputSchema: {
        type: 'object',
        properties: {
          output_path: {
            type: 'string',
            description: 'Path where the onboarding guide should be saved',
          },
          project_name: {
            type: 'string',
            description: 'Name of the project',
          },
          use_template: {
            type: 'boolean',
            description: 'Use template-based generation instead of AI (faster but less customized)',
            default: false,
          },
        },
      },
    },
    {
      name: 'generate_api_reference',
      description: 'Generates API reference documentation (API_REFERENCE.md) for the codebase',
      inputSchema: {
        type: 'object',
        properties: {
          output_path: {
            type: 'string',
            description: 'Path where the API reference should be saved',
          },
          project_name: {
            type: 'string',
            description: 'Name of the project',
          },
          use_template: {
            type: 'boolean',
            description: 'Use template-based generation instead of AI',
            default: false,
          },
        },
      },
    },
    {
      name: 'generate_faq',
      description: 'Generates FAQ documentation (FAQ.md) for the codebase',
      inputSchema: {
        type: 'object',
        properties: {
          output_path: {
            type: 'string',
            description: 'Path where the FAQ should be saved',
          },
          project_name: {
            type: 'string',
            description: 'Name of the project',
          },
          use_template: {
            type: 'boolean',
            description: 'Use template-based generation instead of AI',
            default: false,
          },
        },
      },
    },
    {
      name: 'regenerate_section',
      description: 'Updates a specific section in an existing documentation file',
      inputSchema: {
        type: 'object',
        properties: {
          document_path: {
            type: 'string',
            description: 'Path to the documentation file to update',
          },
          section_name: {
            type: 'string',
            description: 'Name of the section to update',
          },
          document_type: {
            type: 'string',
            description: 'Type of document (e.g., "Onboarding Guide", "API Reference")',
          },
          output_path: {
            type: 'string',
            description: 'Path where the updated document should be saved (defaults to original path)',
          },
        },
        required: ['document_path', 'section_name'],
      },
    },
    {
      name: 'validate_documentation',
      description: 'Validates documentation for quality, completeness, and correctness',
      inputSchema: {
        type: 'object',
        properties: {
          document_path: {
            type: 'string',
            description: 'Path to the documentation file to validate',
          },
          document_type: {
            type: 'string',
            description: 'Type of document being validated',
          },
          use_ai: {
            type: 'boolean',
            description: 'Use AI-powered validation (more thorough but slower)',
            default: true,
          },
        },
        required: ['document_path'],
      },
    },
  ];

  // Handle tool list requests
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools,
  }));

  server.setRequestHandler(ListPromptsRequestSchema, async () => ({
    prompts,
  }));

  server.setRequestHandler(GetPromptRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    return {
      description: prompts.find((prompt) => prompt.name === name)?.description,
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: getPromptText(name, args ?? {}),
          },
        },
      ],
    };
  });

  // Handle tool execution requests
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      let result: unknown;

      switch (name) {
        case 'generate_onboarding_package': {
          if (!onboardingGen || !apiRefGen || !faqGen || !dataCollector) {
            throw new Error('Onboarding package generators not initialized');
          }

          const outputDir = (args as { output_dir?: string })?.output_dir || OUTPUT_DIR;
          const projectName = (args as { project_name?: string })?.project_name || path.basename(REPO_PATH);

          result = await generateOnboardingPackage({
            outputDir,
            projectName,
            onboardingGen,
            apiRefGen,
            faqGen,
            dataCollector,
          });
          break;
        }

        case 'generate_onboarding_guide': {
          if (!onboardingGen) {
            throw new Error('Onboarding generator not initialized');
          }

          const outputPath = (args as { output_path?: string })?.output_path || `${OUTPUT_DIR}/ONBOARDING_GUIDE.md`;
          const projectName = (args as { project_name?: string })?.project_name;
          const useTemplate = (args as { use_template?: boolean })?.use_template || false;

          const content = await onboardingGen.generate({
            outputPath,
            projectName,
            useTemplate,
          });

          result = {
            success: true,
            message: `Onboarding guide generated successfully at ${outputPath}`,
            path: outputPath,
            preview: content.substring(0, 500) + '...',
          };
          break;
        }

        case 'generate_api_reference': {
          if (!apiRefGen) {
            throw new Error('API reference generator not initialized');
          }

          const outputPath = (args as { output_path?: string })?.output_path || `${OUTPUT_DIR}/API_REFERENCE.md`;
          const projectName = (args as { project_name?: string })?.project_name;
          const useTemplate = (args as { use_template?: boolean })?.use_template || false;

          const content = await apiRefGen.generate({
            outputPath,
            projectName,
            useTemplate,
          });

          result = {
            success: true,
            message: `API reference generated successfully at ${outputPath}`,
            path: outputPath,
            preview: content.substring(0, 500) + '...',
          };
          break;
        }

        case 'generate_faq': {
          if (!faqGen) {
            throw new Error('FAQ generator not initialized');
          }

          const outputPath = (args as { output_path?: string })?.output_path || `${OUTPUT_DIR}/FAQ.md`;
          const projectName = (args as { project_name?: string })?.project_name;
          const useTemplate = (args as { use_template?: boolean })?.use_template || false;

          const content = await faqGen.generate({
            outputPath,
            projectName,
            useTemplate,
          });

          result = {
            success: true,
            message: `FAQ generated successfully at ${outputPath}`,
            path: outputPath,
            preview: content.substring(0, 500) + '...',
          };
          break;
        }

        case 'regenerate_section': {
          if (!sectionUpdater) {
            throw new Error('Section updater not initialized');
          }

          const documentPath = (args as { document_path: string }).document_path;
          const sectionName = (args as { section_name: string }).section_name;
          const documentType = (args as { document_type?: string })?.document_type;
          const outputPath = (args as { output_path?: string })?.output_path;

          if (!documentPath || !sectionName) {
            throw new Error('document_path and section_name are required');
          }

          await sectionUpdater.updateSection({
            documentPath,
            sectionName,
            documentType,
            outputPath,
          });

          result = {
            success: true,
            message: `Section "${sectionName}" updated successfully`,
            path: outputPath || documentPath,
          };
          break;
        }

        case 'validate_documentation': {
          if (!validator) {
            throw new Error('Validator not initialized');
          }

          const documentPath = (args as { document_path: string }).document_path;
          const documentType = (args as { document_type?: string })?.document_type;
          const useAI = (args as { use_ai?: boolean })?.use_ai !== false;

          if (!documentPath) {
            throw new Error('document_path is required');
          }

          const validationResult = await validator.validate({
            documentPath,
            documentType,
            useAI,
          });

          const report = validator.generateReport(validationResult);

          result = {
            success: true,
            validation: validationResult,
            report,
          };
          break;
        }

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

  console.error('Documentation Generator MCP Server running on stdio');

  // Cleanup on exit
  process.on('SIGINT', async () => {
    console.error('Shutting down...');
    if (mcpClient) {
      await mcpClient.disconnectAll();
    }
    process.exit(0);
  });
}

// Run the server
main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

// Made with Bob
