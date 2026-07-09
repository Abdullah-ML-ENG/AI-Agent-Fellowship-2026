import Groq from 'groq-sdk';
import { GoogleGenAI } from '@google/genai';
import { ChatRequest, ChatResponse, Provider, UsageMetadata } from './types';

const PROVIDER_KEYS: Record<Provider, string | undefined> = {
  groq: process.env.GROQ_API_KEY,
  gemini: process.env.GEMINI_API_KEY,
};

const toGeminiRole = (role: 'assistant' | 'user' | 'system'): 'model' | 'user' =>
  role === 'assistant' ? 'model' : 'user';

const extractGeminiUsage = (usageMetadata: unknown): UsageMetadata | undefined => {
  if (!usageMetadata || typeof usageMetadata !== 'object') {
    return undefined;
  }

  const usage = usageMetadata as Record<string, number | undefined>;
  return {
    promptTokens: usage.promptTokenCount,
    completionTokens: usage.candidatesTokenCount,
    totalTokens: usage.totalTokenCount,
  };
};

export const ensureProviderApiKey = (provider: Provider): string => {
  const key = PROVIDER_KEYS[provider];
  if (!key) {
    throw new Error(`Missing API key for ${provider}. Set ${provider === 'groq' ? 'GROQ_API_KEY' : 'GEMINI_API_KEY'}.`);
  }

  return key;
};

export const sendChat = async (request: ChatRequest): Promise<Omit<ChatResponse, 'responseTimeMs'>> => {
  if (request.provider === 'groq') {
    const groq = new Groq({ apiKey: ensureProviderApiKey('groq') });

    const completion = await groq.chat.completions.create({
      model: request.model,
      messages: [
        ...(request.systemPrompt?.trim() ? [{ role: 'system' as const, content: request.systemPrompt.trim() }] : []),
        ...request.messages.map((message) => ({
          role: message.role,
          content: message.content,
        })),
      ],
    });

    const content = completion.choices[0]?.message?.content?.trim();

    return {
      content: content || 'No response was returned by Groq.',
      model: completion.model || request.model,
      provider: 'groq',
      usage: completion.usage
        ? {
            promptTokens: completion.usage.prompt_tokens,
            completionTokens: completion.usage.completion_tokens,
            totalTokens: completion.usage.total_tokens,
          }
        : undefined,
    };
  }

  const gemini = new GoogleGenAI({ apiKey: ensureProviderApiKey('gemini') });

  const response = await gemini.models.generateContent({
    model: request.model,
    contents: request.messages.map((message) => ({
      role: toGeminiRole(message.role),
      parts: [{ text: message.content }],
    })),
    config: request.systemPrompt?.trim()
      ? {
          systemInstruction: request.systemPrompt.trim(),
        }
      : undefined,
  });

  const text = response.text?.trim();

  return {
    content: text || 'No response was returned by Gemini.',
    model: request.model,
    provider: 'gemini',
    usage: extractGeminiUsage(response.usageMetadata),
  };
};
