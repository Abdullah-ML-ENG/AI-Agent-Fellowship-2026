import 'dotenv/config';
import cors from 'cors';
import express from 'express';
import { z } from 'zod';
import { sendChat } from './providers';
import { ChatMessage, ChatRequest, Provider } from './types';

const app = express();
const port = Number(process.env.PORT || 8787);

app.use(
  cors({
    origin: process.env.CLIENT_ORIGIN || true,
  }),
);
app.use(express.json({ limit: '1mb' }));

const requestSchema = z.object({
  provider: z.enum(['groq', 'gemini']),
  model: z.string().trim().min(1),
  systemPrompt: z.string().max(8000).optional().default(''),
  messages: z
    .array(
      z.object({
        role: z.enum(['system', 'user', 'assistant']),
        content: z.string().trim().min(1),
      }),
    )
    .min(1),
});

const hasUserPrompt = (messages: ChatMessage[]): boolean =>
  messages.some((message) => message.role === 'user' && message.content.trim().length > 0);

const getProviderError = (provider: Provider, error: unknown): { status: number; code: string; message: string } => {
  const err = error as { status?: number; message?: string };
  const status = err?.status;
  const text = err?.message || '';

  if (status === 401 || status === 403 || /api key|unauthorized|invalid key|authentication/i.test(text)) {
    return {
      status: 401,
      code: 'INVALID_API_KEY',
      message: `The ${provider} API key appears to be invalid. Please check your server environment variables.`,
    };
  }

  if (status === 429) {
    return {
      status: 429,
      code: 'RATE_LIMITED',
      message: `${provider} is currently rate-limited. Please retry shortly.`,
    };
  }

  return {
    status: 502,
    code: 'PROVIDER_ERROR',
    message: `${provider} is currently unavailable. Please try another provider or retry in a moment.`,
  };
};

app.get('/api/health', (_req, res) => {
  res.json({
    ok: true,
    providers: {
      groq: Boolean(process.env.GROQ_API_KEY),
      gemini: Boolean(process.env.GEMINI_API_KEY),
    },
  });
});

app.post('/api/chat', async (req, res) => {
  const parsed = requestSchema.safeParse(req.body);

  if (!parsed.success) {
    return res.status(400).json({
      error: {
        code: 'INVALID_REQUEST',
        message: 'Request validation failed.',
        details: parsed.error.flatten(),
      },
    });
  }

  const payload = parsed.data as ChatRequest;

  if (!hasUserPrompt(payload.messages)) {
    return res.status(400).json({
      error: {
        code: 'EMPTY_PROMPT',
        message: 'Please enter a prompt before sending.',
      },
    });
  }

  const startedAt = Date.now();

  try {
    const response = await sendChat(payload);
    return res.json({
      ...response,
      responseTimeMs: Date.now() - startedAt,
    });
  } catch (error) {
    const providerError = getProviderError(payload.provider, error);
    return res.status(providerError.status).json({
      error: {
        code: providerError.code,
        message: providerError.message,
      },
    });
  }
});

app.use((_req, res) => {
  res.status(404).json({
    error: {
      code: 'NOT_FOUND',
      message: 'Endpoint not found.',
    },
  });
});

app.listen(port, () => {
  console.log(`AI Workspace server listening on http://localhost:${port}`);
});
