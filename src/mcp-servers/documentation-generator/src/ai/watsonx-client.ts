/**
 * WatsonX AI Client
 *
 * Handles communication with IBM watsonx.ai for content generation.
 * Uses the official @ibm-cloud/watsonx-ai SDK which handles IAM token
 * exchange and refresh internally.
 *
 * The SDK expects one of these env var setups:
 *   WATSONX_AI_AUTH_TYPE=iam
 *   WATSONX_AI_APIKEY=<your-api-key>
 *
 * We set them programmatically before creating the service instance.
 */

import { WatsonXAI } from '@ibm-cloud/watsonx-ai';

interface WatsonXConfig {
  apiKey: string;
  projectId: string;
  modelId?: string;
  maxTokens?: number;
  temperature?: number;
  topP?: number;
}

interface GenerationParams {
  prompt: string;
  maxTokens?: number;
  temperature?: number;
  topP?: number;
}

export class WatsonXClient {
  private service: WatsonXAI;
  private config: Required<WatsonXConfig>;

  constructor(config: WatsonXConfig) {
    this.config = {
      apiKey: config.apiKey,
      projectId: config.projectId,
      modelId: config.modelId || 'openai/gpt-oss-120b',
      maxTokens: config.maxTokens || 2000,
      temperature: config.temperature || 0.7,
      topP: config.topP || 0.9,
    };

    // Set SDK authentication env vars the SDK expects
    process.env['WATSONX_AI_AUTH_TYPE'] = 'iam';
    process.env['WATSONX_AI_APIKEY'] = this.config.apiKey;

    this.service = new WatsonXAI({
      version: '2024-05-31',
      serviceUrl: 'https://us-south.ml.cloud.ibm.com',
    });
  }

  /**
   * Generate text using watsonx.ai chat completions API via the official SDK
   */
  async generate(params: GenerationParams): Promise<string> {
    const result = await this.service.textChat({
      messages: [
        {
          role: 'user',
          content: params.prompt,
        },
      ],
      modelId: this.config.modelId,
      projectId: this.config.projectId,
      maxTokens: params.maxTokens || this.config.maxTokens,
      temperature: params.temperature ?? this.config.temperature,
      topP: params.topP || this.config.topP,
    });

    const content = result.result.choices?.[0]?.message?.content;
    if (content) {
      return content.trim();
    }

    throw new Error('No content in chat response');
  }

  /**
   * Test connection to watsonx.ai
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.generate({
        prompt: 'Reply with the word ok',
        maxTokens: 10,
      });
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * Create WatsonX client from environment variables
 */
export function createWatsonXClient(): WatsonXClient {
  const apiKey = process.env['WATSONX_API_KEY'];
  const projectId = process.env['WATSONX_PROJECT_ID'];

  if (!apiKey || !projectId) {
    throw new Error('WATSONX_API_KEY and WATSONX_PROJECT_ID environment variables are required');
  }

  return new WatsonXClient({
    apiKey,
    projectId,
    modelId: process.env['WATSONX_MODEL_ID'],
    maxTokens: process.env['WATSONX_MAX_TOKENS'] ? parseInt(process.env['WATSONX_MAX_TOKENS'], 10) : undefined,
    temperature: process.env['WATSONX_TEMPERATURE'] ? parseFloat(process.env['WATSONX_TEMPERATURE']) : undefined,
    topP: process.env['WATSONX_TOP_P'] ? parseFloat(process.env['WATSONX_TOP_P']) : undefined,
  });
}

// Made with Bob
