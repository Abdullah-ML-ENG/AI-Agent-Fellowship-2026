import { useEffect, useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './App.css';

type Provider = 'groq' | 'gemini';
type Role = 'user' | 'assistant';

interface Usage {
  promptTokens?: number;
  completionTokens?: number;
  totalTokens?: number;
}

interface ChatMessage {
  id: string;
  role: Role;
  content: string;
  createdAt: string;
  provider?: Provider;
  model?: string;
  usage?: Usage;
  responseTimeMs?: number;
}

interface Session {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  provider: Provider;
  model: string;
  systemPrompt: string;
  messages: ChatMessage[];
}

interface PromptTemplate {
  id: string;
  name: string;
  prompt: string;
  builtIn?: boolean;
}

interface ChatApiResponse {
  content: string;
  model: string;
  provider: Provider;
  usage?: Usage;
  responseTimeMs: number;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8787';
const THEME_KEY = 'ai_workspace_theme';
const SESSIONS_KEY = 'ai_workspace_sessions';
const ACTIVE_SESSION_KEY = 'ai_workspace_active_session';
const TEMPLATES_KEY = 'ai_workspace_templates';

const MODELS: Record<Provider, string[]> = {
  groq: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant'],
  gemini: ['gemini-2.0-flash', 'gemini-1.5-pro'],
};

const BUILTIN_TEMPLATES: PromptTemplate[] = [
  { id: 'tpl-summary', name: 'Summarize Text', prompt: 'Summarize the following text in bullet points:\n\n' , builtIn: true},
  { id: 'tpl-code', name: 'Explain Code', prompt: 'Explain what this code does, line by line:\n\n```\n\n```', builtIn: true },
  { id: 'tpl-ideas', name: 'Generate Ideas', prompt: 'Generate 10 practical ideas for:\n\n', builtIn: true },
  { id: 'tpl-rewrite', name: 'Rewrite Content', prompt: 'Rewrite the following content in a professional tone:\n\n', builtIn: true },
  { id: 'tpl-translate', name: 'Translate', prompt: 'Translate this text to [target language]:\n\n', builtIn: true },
  { id: 'tpl-email', name: 'Create Email', prompt: 'Write a concise and polite email for this situation:\n\n', builtIn: true },
  { id: 'tpl-brainstorm', name: 'Brainstorm', prompt: 'Brainstorm creative approaches for:\n\n', builtIn: true },
];

const createSession = (): Session => {
  const now = new Date().toISOString();
  return {
    id: crypto.randomUUID(),
    title: 'New Session',
    createdAt: now,
    updatedAt: now,
    provider: 'groq',
    model: MODELS.groq[0],
    systemPrompt: 'You are a helpful AI assistant.',
    messages: [],
  };
};

const exportMarkdown = (session: Session) => {
  const lines = [`# ${session.title}`, '', `Provider: ${session.provider}`, `Model: ${session.model}`, ''];
  session.messages.forEach((message) => {
    lines.push(`## ${message.role === 'user' ? 'User' : 'Assistant'}`);
    lines.push(message.content);
    lines.push('');
  });

  const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${session.title.replace(/\s+/g, '-').toLowerCase() || 'session'}.md`;
  link.click();
  URL.revokeObjectURL(link.href);
};

const exportJson = (session: Session) => {
  const blob = new Blob([JSON.stringify(session, null, 2)], { type: 'application/json;charset=utf-8' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${session.title.replace(/\s+/g, '-').toLowerCase() || 'session'}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
};

function App() {
  const [sessions, setSessions] = useState<Session[]>(() => {
    const saved = localStorage.getItem(SESSIONS_KEY);
    if (!saved) return [createSession()];

    try {
      const parsed = JSON.parse(saved) as Session[];
      return parsed.length ? parsed : [createSession()];
    } catch {
      return [createSession()];
    }
  });
  const [activeSessionId, setActiveSessionId] = useState(() => localStorage.getItem(ACTIVE_SESSION_KEY) || '');
  const [templates, setTemplates] = useState<PromptTemplate[]>(() => {
    const saved = localStorage.getItem(TEMPLATES_KEY);
    if (!saved) return BUILTIN_TEMPLATES;

    try {
      const parsed = JSON.parse(saved) as PromptTemplate[];
      return [...BUILTIN_TEMPLATES, ...parsed.filter((template) => !template.builtIn)];
    } catch {
      return BUILTIN_TEMPLATES;
    }
  });
  const [input, setInput] = useState('');
  const [customTemplateName, setCustomTemplateName] = useState('');
  const [customTemplatePrompt, setCustomTemplatePrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (localStorage.getItem(THEME_KEY) === 'dark' ? 'dark' : 'light'));

  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) ?? sessions[0],
    [sessions, activeSessionId],
  );

  useEffect(() => {
    if (!activeSessionId && sessions[0]) {
      setActiveSessionId(sessions[0].id);
    }
  }, [sessions, activeSessionId]);

  useEffect(() => {
    if (!activeSession) return;
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
    localStorage.setItem(ACTIVE_SESSION_KEY, activeSession.id);
  }, [sessions, activeSession]);

  useEffect(() => {
    localStorage.setItem(TEMPLATES_KEY, JSON.stringify(templates.filter((template) => !template.builtIn)));
  }, [templates]);

  useEffect(() => {
    localStorage.setItem(THEME_KEY, theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  const updateSession = (sessionId: string, updater: (session: Session) => Session) => {
    setSessions((prev) => prev.map((session) => (session.id === sessionId ? updater(session) : session)));
  };

  const handleCreateSession = () => {
    const newSession = createSession();
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
    setError('');
  };

  const handleDeleteSession = (sessionId: string) => {
    const remaining = sessions.filter((session) => session.id !== sessionId);
    if (!remaining.length) {
      const fallback = createSession();
      setSessions([fallback]);
      setActiveSessionId(fallback.id);
      return;
    }

    setSessions(remaining);
    if (activeSessionId === sessionId) {
      setActiveSessionId(remaining[0].id);
    }
  };

  const handleAddTemplate = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!customTemplateName.trim() || !customTemplatePrompt.trim()) return;

    const newTemplate: PromptTemplate = {
      id: crypto.randomUUID(),
      name: customTemplateName.trim(),
      prompt: customTemplatePrompt,
    };

    setTemplates((prev) => [...prev, newTemplate]);
    setCustomTemplateName('');
    setCustomTemplatePrompt('');
  };

  const recognitionSupported =
    typeof window !== 'undefined' &&
    ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window);

  const handleVoiceInput = () => {
    if (!recognitionSupported) return;

    const RecognitionCtor =
      (window as Window & { webkitSpeechRecognition?: new () => SpeechRecognition }).webkitSpeechRecognition ||
      (window as Window & { SpeechRecognition?: new () => SpeechRecognition }).SpeechRecognition;

    if (!RecognitionCtor) return;

    const recognition = new RecognitionCtor();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript || '';
      setInput((prev) => `${prev}${prev ? ' ' : ''}${transcript}`.trim());
    };
    recognition.start();
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!activeSession) return;

    const trimmedInput = input.trim();
    if (!trimmedInput) {
      setError('Please enter a prompt before sending.');
      return;
    }

    setIsLoading(true);
    setError('');

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmedInput,
      createdAt: new Date().toISOString(),
    };

    const pendingMessages = [...activeSession.messages, userMessage];

    updateSession(activeSession.id, (session) => ({
      ...session,
      title: session.messages.length ? session.title : trimmedInput.slice(0, 40),
      updatedAt: new Date().toISOString(),
      messages: pendingMessages,
    }));
    setInput('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: activeSession.provider,
          model: activeSession.model,
          systemPrompt: activeSession.systemPrompt,
          messages: pendingMessages.map((message) => ({
            role: message.role,
            content: message.content,
          })),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.error?.message || 'Request failed. Please retry.');
      }

      const apiData = data as ChatApiResponse;
      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: apiData.content,
        createdAt: new Date().toISOString(),
        provider: apiData.provider,
        model: apiData.model,
        usage: apiData.usage,
        responseTimeMs: apiData.responseTimeMs,
      };

      updateSession(activeSession.id, (session) => ({
        ...session,
        updatedAt: new Date().toISOString(),
        messages: [...session.messages, assistantMessage],
      }));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Connection failure. Please try again.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!activeSession) return null;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1>AI Workspace</h1>
          <button onClick={handleCreateSession}>New Session</button>
        </div>

        <section>
          <h2>Sessions</h2>
          <ul className="session-list">
            {sessions.map((session) => (
              <li key={session.id} className={session.id === activeSession.id ? 'active' : ''}>
                <button onClick={() => setActiveSessionId(session.id)}>{session.title || 'Untitled Session'}</button>
                <button className="danger" onClick={() => handleDeleteSession(session.id)} aria-label="Delete session">
                  ×
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h2>Templates</h2>
          <div className="template-list">
            {templates.map((template) => (
              <button key={template.id} onClick={() => setInput(template.prompt)}>
                {template.name}
              </button>
            ))}
          </div>
          <form className="template-form" onSubmit={handleAddTemplate}>
            <input
              placeholder="Template name"
              value={customTemplateName}
              onChange={(event) => setCustomTemplateName(event.target.value)}
            />
            <textarea
              placeholder="Custom template prompt"
              value={customTemplatePrompt}
              onChange={(event) => setCustomTemplatePrompt(event.target.value)}
              rows={3}
            />
            <button type="submit">Save Template</button>
          </form>
        </section>

        <section>
          <h2>Settings</h2>
          <button onClick={() => setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))}>
            {theme === 'light' ? 'Enable Dark Mode' : 'Enable Light Mode'}
          </button>
          <p className="hint">Voice input: {recognitionSupported ? 'Supported' : 'Not supported in this browser'}</p>
        </section>
      </aside>

      <main className="chat-layout">
        <header className="top-controls">
          <label>
            Provider
            <select
              value={activeSession.provider}
              onChange={(event) => {
                const provider = event.target.value as Provider;
                updateSession(activeSession.id, (session) => ({
                  ...session,
                  provider,
                  model: MODELS[provider][0],
                }));
              }}
            >
              <option value="groq">Groq</option>
              <option value="gemini">Gemini</option>
            </select>
          </label>

          <label>
            Model
            <select
              value={activeSession.model}
              onChange={(event) => updateSession(activeSession.id, (session) => ({ ...session, model: event.target.value }))}
            >
              {MODELS[activeSession.provider].map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </label>

          <label className="system-prompt">
            System Prompt
            <textarea
              rows={2}
              value={activeSession.systemPrompt}
              onChange={(event) =>
                updateSession(activeSession.id, (session) => ({
                  ...session,
                  systemPrompt: event.target.value,
                }))
              }
            />
          </label>

          <div className="export-actions">
            <button onClick={() => exportMarkdown(activeSession)}>Export .md</button>
            <button onClick={() => exportJson(activeSession)}>Export .json</button>
          </div>
        </header>

        <section className="messages" aria-live="polite">
          {activeSession.messages.length === 0 ? (
            <div className="empty-state">Start a conversation by sending a prompt or applying a template.</div>
          ) : (
            activeSession.messages.map((message) => (
              <article key={message.id} className={`message ${message.role}`}>
                <div className="message-header">{message.role === 'user' ? 'You' : 'Assistant'}</div>
                {message.role === 'assistant' ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                ) : (
                  <p>{message.content}</p>
                )}
                {message.role === 'assistant' && (
                  <div className="meta">
                    {message.provider}/{message.model}
                    {typeof message.responseTimeMs === 'number' ? ` • ${message.responseTimeMs}ms` : ''}
                    {typeof message.usage?.totalTokens === 'number' ? ` • ${message.usage.totalTokens} tokens` : ''}
                  </div>
                )}
              </article>
            ))
          )}
          {isLoading && <div className="loading">Thinking…</div>}
        </section>

        <form className="composer" onSubmit={handleSubmit}>
          <textarea
            placeholder="Ask anything..."
            rows={4}
            value={input}
            onChange={(event) => setInput(event.target.value)}
          />
          <div className="composer-actions">
            <button type="button" onClick={handleVoiceInput} disabled={!recognitionSupported || isLoading}>
              Voice Input
            </button>
            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </form>

        {error && <p className="error">{error}</p>}
      </main>
    </div>
  );
}

export default App;
