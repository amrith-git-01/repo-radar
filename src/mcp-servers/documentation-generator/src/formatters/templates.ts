/**
 * Documentation Templates
 * 
 * Provides base templates for different documentation types
 */

import * as md from './markdown.js';

/**
 * Get onboarding guide template (fallback when AI generation fails)
 */
export function getOnboardingTemplate(projectName: string = 'Project'): string {
  const today = new Date().toISOString().split('T')[0];
  return `# ${projectName} - Onboarding Guide

> **Note:** This document was generated using a fallback template because AI-powered generation was unavailable or failed. The content below is a structural outline only. Sections marked with an asterisk (*) could not be populated from MCP data. Run the documentation-generator with valid watsonx.ai credentials to regenerate with repo-specific content.

## Table of Contents

- [Project Overview](#project-overview)
- [Getting Started](#getting-started)
- [Codebase Structure](#codebase-structure)
- [Development Workflow](#development-workflow)
- [Key Concepts](#key-concepts)
- [Common Tasks](#common-tasks)
- [Resources](#resources)

## Project Overview

### Description *

_Not generated: AI generation failed or MCP data was unavailable. Verify WatsonX credentials and MCP server builds, then regenerate._

### Key Technologies *

_Not found in MCP data. Inspect \`package.json\`, \`requirements.txt\`, \`pom.xml\`, or similar dependency files in the repository root._

### Architecture Overview *

_Not found in MCP data. Run the code-analyzer MCP server with a valid \`REPO_PATH\` to generate architecture insights._

## Getting Started

### Prerequisites *

_Not found in MCP data. Check the repository's \`README.md\`, \`CONTRIBUTING.md\`, or existing \`docs/\` files for requirements._

### Installation *

\`\`\`bash
# Clone the repository
git clone <repository-url>

# Install dependencies
# Not found in MCP data - check package.json, requirements.txt, or Makefile for commands
\`\`\`

### Configuration *

_Not found in MCP data. Look for \`.env.example\`, \`config/\` directory, or environment variable documentation in the repo._

### Running the Project *

\`\`\`bash
# Run command
# Not found in MCP data - inspect README.md, package.json scripts, or Procfile for commands
\`\`\`

## Codebase Structure

### Directory Organization *

_Not found in MCP data. Run the code-analyzer MCP server with \`analyze_structure\` to generate an accurate directory tree._

### Key Modules *

_Not found in MCP data. Use code-analyzer to scan the repository structure and identify key modules._

### Entry Points *

_Not found in MCP data. Run code-analyzer's \`find_entry_points\` tool to discover main entry points._

## Development Workflow *

_Not found in MCP data. Check the repository for \`CONTRIBUTING.md\`, \`WORKFLOWS.md\`, \`.github/workflows/\`, or similar files describing development processes._

## Key Concepts *

_Not found in MCP data. Review the codebase structure and architecture diagrams (once generated) to identify design patterns, core business logic locations, and data flow._

## Common Tasks *

_Not found in MCP data. After generating repo-specific analysis with valid MCP servers, this section will include concrete commands and file paths._

## Resources

### Important Files *

_Not found in MCP data. Run code-analyzer's \`analyze_structure\` and \`find_entry_points\` to identify critical files._

### External Documentation *

_Not found in MCP data. Check the repository's \`README.md\` and existing \`docs/\` directory for linked resources._

---

*Last updated: ${today}*  \\
*Generated via fallback template (AI generation was unavailable)*
`;
}

/**
 * Get API reference template (fallback when AI generation fails)
 */
export function getAPIReferenceTemplate(projectName: string = 'Project'): string {
  const today = new Date().toISOString().split('T')[0];
  return `# ${projectName} - API Reference

> **Note:** This document was generated using a fallback template because AI-powered generation was unavailable or failed. Sections marked with an asterisk (*) could not be populated from MCP data. Regenerate with valid watsonx.ai credentials to produce repo-specific content.

## Table of Contents

- [Overview](#overview)
- [Core APIs](#core-apis)
- [Module Documentation](#module-documentation)
- [Data Structures](#data-structures)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Overview *

_Not generated: AI generation failed or MCP data was unavailable. Verify WatsonX credentials and MCP server builds, then regenerate._

## Core APIs *

_Not found in MCP data. Run code-analyzer's \`analyze_structure\` and \`find_entry_points\` tools to discover the repository's public APIs and functions._

## Module Documentation *

_Not found in MCP data. Use the code-analyzer MCP server to scan the repository structure and identify major modules._

## Data Structures *

_Not found in MCP data. Review key source files in the repository to identify important data types, interfaces, and models._

## Configuration *

_Not found in MCP data. Look for \`.env.example\`, \`config/\` files, or environment variable documentation in the repository._

## Error Handling *

_Not found in MCP data. Inspect the source code for error classes, exception handlers, or error code enums._

## Examples *

_Not found in MCP data. After generating repo-specific analysis with valid MCP servers and WatsonX credentials, this section will include code examples._

---

*Last updated: ${today}*  \\
*Generated via fallback template (AI generation was unavailable)*
`;
}

/**
 * Get FAQ template (fallback when AI generation fails)
 */
export function getFAQTemplate(projectName: string = 'Project'): string {
  const today = new Date().toISOString().split('T')[0];
  return `# ${projectName} - Frequently Asked Questions

> **Note:** This document was generated using a fallback template because AI-powered generation was unavailable or failed. Sections marked with an asterisk (*) could not be populated from MCP data. Regenerate with valid watsonx.ai credentials to produce repo-specific content.

## Table of Contents

- [General Questions](#general-questions)
- [Setup and Installation](#setup-and-installation)
- [Development Questions](#development-questions)
- [Architecture Questions](#architecture-questions)
- [Common Issues](#common-issues)
- [Contributing](#contributing)
- [Deployment and Operations](#deployment-and-operations)

## General Questions

### What is this project? *

_Not generated: AI generation failed or MCP data was unavailable. Verify WatsonX credentials and MCP server builds, then regenerate._

### What problem does it solve? *

_Not found in MCP data. Review the repository's \`README.md\` and existing documentation for project context._

### Who maintains it? *

_Not found in MCP data. Run the git-analyzer MCP server's \`get_contributors\` tool to identify active maintainers, or check the repository's \`CODEOWNERS\` file._

### What's the project history? *

_Not found in MCP data. Use \`git log\` or the git-analyzer MCP server to examine commit history._

## Setup and Installation

### How do I set up the development environment? *

_Not found in MCP data. Check \`README.md\`, \`CONTRIBUTING.md\`, \`SETUP.md\`, or existing \`docs/\` files in the repository._

### What are the system requirements? *

_Not found in MCP data. Inspect \`package.json\` (engines field), \`requirements.txt\`, \`.nvmrc\`, \`Dockerfile\`, or similar files for version requirements._

### What are common installation issues? *

_Not found in MCP data. After successfully setting up the environment, consider documenting issues in a \`TROUBLESHOOTING.md\` file._

### How do I configure the application? *

_Not found in MCP data. Look for \`.env.example\`, \`config/\` directory, or environment variable documentation._

## Development Questions

### Where do I start reading the code? *

_Not found in MCP data. Run code-analyzer's \`find_entry_points\` and \`analyze_structure\` tools to identify main entry points and directory organization._

### How is the code organized? *

_Not found in MCP data. Use the code-analyzer MCP server to scan the directory structure and identify module boundaries._

### What are the main entry points? *

_Not found in MCP data. Run code-analyzer's \`find_entry_points\` tool to discover main entry points._

### How do I run tests? *

_Not found in MCP data. Check \`package.json\` (scripts.test), \`Makefile\`, \`pytest.ini\`, \`.github/workflows/\`, or similar files for test commands._

### How do I debug issues? *

_Not found in MCP data. Look for debugging configuration files (\`.vscode/launch.json\`, debugger setup) or developer documentation in the repository._

## Architecture Questions

### What's the overall architecture? *

_Not found in MCP data. Run code-analyzer's \`analyze_structure\` and \`analyze_dependencies\` tools, then review generated ARCHITECTURE.md once available._

### What design patterns are used? *

_Not found in MCP data. Review the source code structure and module organization to identify patterns (MVC, layered, microservices, etc.)._

### How does data flow through the system? *

_Not found in MCP data. Trace entry points through dependency calls using code-analyzer results once MCP servers are running with a valid repo path._

### What are the key dependencies? *

_Not found in MCP data. Run code-analyzer's \`analyze_dependencies\` tool to extract dependency information from \`package.json\`, \`requirements.txt\`, \`pom.xml\`, etc._

## Common Issues *

_Not found in MCP data. Install and configure the repository locally first, then document common issues as they are encountered. Check existing \`docs/\` files or \`TROUBLESHOOTING.md\` for any pre-existing issue documentation._

## Contributing *

_Not found in MCP data. Check the repository for \`CONTRIBUTING.md\`, \`CODE_OF_CONDUCT.md\`, \`PULL_REQUEST_TEMPLATE.md\`, or \`.github/\` directory for contribution guidelines._

## Deployment and Operations *

_Not found in MCP data. Check for \`Dockerfile\`, \`docker-compose.yml\`, \`.github/workflows/deploy.yml\`, \`Jenkinsfile\`, \`helm/\` directory, or cloud platform configuration files for deployment information._

---

*Last updated: ${today}*  \\
*Generated via fallback template (AI generation was unavailable)*
`;
}

/**
 * Create a section template
 */
export function createSection(title: string, level: number = 2, content: string = ''): string {
  return md.heading(level, title) + (content ? md.paragraph(content) : '');
}

/**
 * Create a code example section
 */
export function createCodeExample(title: string, code: string, language: string = '', description: string = ''): string {
  let result = md.heading(3, title);
  
  if (description) {
    result += md.paragraph(description);
  }
  
  result += md.codeBlock(code, language);
  
  return result;
}

/**
 * Create a list section
 */
export function createListSection(title: string, items: string[], ordered: boolean = false): string {
  return md.heading(3, title) + md.list(items, ordered);
}

/**
 * Create a table section
 */
export function createTableSection(title: string, headers: string[], rows: string[][]): string {
  return md.heading(3, title) + md.table(headers, rows);
}

// Made with Bob
