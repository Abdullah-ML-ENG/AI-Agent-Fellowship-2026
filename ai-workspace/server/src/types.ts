export type ChatRole = 'system' | 'user' | 'assistant';

export interface ChatMessage {
  role: ChatRole;
  content: string;
}

export type Provider = 'groq' | 'gemini';

export interface ChatRequest {
  provider: Provider;
  model: string;
  systemPrompt?: string;
  messages: ChatMessage[];
}

export interface UsageMetadata {
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
}

export interface ChatResponse {
  content: string;
  model: string;
  provider: Provider;
  usage?: UsageMetadata;
  responseTimeMs: number;
}
