# AI Workspace

AI Workspace is a full-stack chat application that provides a unified interface for Groq and Gemini models through a secure backend proxy.

## Features

### Required
- Chat interface with user/assistant timeline
- Custom system prompt per session
- Provider/model switching (Groq + Gemini)
- Built-in prompt templates:
  - Summarize Text
  - Explain Code
  - Generate Ideas
  - Rewrite Content
  - Translate
  - Create Email
  - Brainstorm
- Conversation history persisted in LocalStorage
- Markdown rendering for assistant responses
- Error handling for empty prompts, invalid keys, provider/network failures
- Responsive desktop/mobile UI

### Bonus Implemented
- Dark mode toggle
- Export chat as Markdown and JSON
- Save custom prompt templates
- Token usage display (when provider returns usage metadata)
- Response time display (ms)
- Multiple chat sessions (create/switch/delete)
- Voice input (browser speech recognition where supported)

## Architecture

- `client/`: React + Vite + TypeScript SPA
  - Stores sessions/templates/theme in LocalStorage
  - Calls backend endpoint only (`POST /api/chat`)
  - Renders assistant output with Markdown
- `server/`: Node.js + Express + TypeScript API proxy
  - Reads API keys from environment only
  - Routes requests to Groq or Gemini adapters
  - Normalizes response shape and returns usage/latency metadata

## Security

- API keys are **never** hardcoded in source or frontend.
- Backend environment variables only:
  - `GROQ_API_KEY`
  - `GEMINI_API_KEY`
- Use `.env.example` templates and keep `.env` out of git.

## Setup

### 1) Install dependencies

From repository root:

```bash
cd ai-workspace
npm install
npm run install:all
```

### 2) Configure environment

Server:

```bash
cp server/.env.example server/.env
```

Set values in `server/.env`:

```env
PORT=8787
CLIENT_ORIGIN=http://localhost:5173
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

Client (optional if using default backend URL):

```bash
cp client/.env.example client/.env
```

Optional `client/.env`:

```env
VITE_API_BASE_URL=http://localhost:8787
```

## Run locally

### Run both apps together

```bash
cd ai-workspace
npm run dev
```

### Run separately

Server:
```bash
cd ai-workspace/server
npm run dev
```

Client:
```bash
cd ai-workspace/client
npm run dev
```

## Build

```bash
cd ai-workspace
npm run build
```

## Troubleshooting

- **Invalid API key**
  - Verify `GROQ_API_KEY` and/or `GEMINI_API_KEY` in `server/.env`
  - Restart the server after editing env vars
- **CORS/network errors**
  - Ensure backend is running on the URL in `VITE_API_BASE_URL`
  - Confirm `CLIENT_ORIGIN` includes frontend origin
- **Provider unavailable**
  - Switch provider/model in UI and retry
  - Check provider dashboard/status for outages/rate limits

## API

### `POST /api/chat`
Request body:

```json
{
  "provider": "groq",
  "model": "llama-3.3-70b-versatile",
  "systemPrompt": "You are a professional software engineer.",
  "messages": [{ "role": "user", "content": "Explain async/await." }]
}
```

Response body:

```json
{
  "content": "...",
  "model": "llama-3.3-70b-versatile",
  "provider": "groq",
  "usage": { "promptTokens": 10, "completionTokens": 40, "totalTokens": 50 },
  "responseTimeMs": 412
}
```
