export const PROVIDERS = [
  {
    id: 'openai',
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    keyPlaceholder: 'sk-...',
    keyHint: 'platform.openai.com',
    models: [
      { id: 'gpt-4o-mini', label: 'gpt-4o-mini', tier: 'paid', cagSafe: true },
      { id: 'gpt-4o',      label: 'gpt-4o',      tier: 'paid', cagSafe: true },
    ],
  },
  {
    id: 'gemini',
    label: 'Google Gemini',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/',
    keyPlaceholder: 'AIza...',
    keyHint: 'aistudio.google.com',
    models: [
      { id: 'gemini-2.0-flash', label: 'gemini-2.0-flash', tier: 'free', cagSafe: true },
      { id: 'gemini-1.5-flash', label: 'gemini-1.5-flash', tier: 'free', cagSafe: true },
    ],
  },
  {
    id: 'groq',
    label: 'Groq',
    baseUrl: 'https://api.groq.com/openai/v1',
    keyPlaceholder: 'gsk_...',
    keyHint: 'console.groq.com',
    models: [
      {
        id: 'llama-3.3-70b-versatile',
        label: 'llama-3.3-70b-versatile',
        tier: 'free',
        cagSafe: false,
        warning: '12,000 TPM hard cap — CAG needs 13,500+ tokens and will be rejected. RAG only will work.',
      },
      {
        id: 'llama-3.1-8b-instant',
        label: 'llama-3.1-8b-instant',
        tier: 'free',
        cagSafe: false,
        warning: '6,000 TPM hard cap — CAG will be rejected. RAG only will work.',
      },
    ],
  },
  {
    id: 'openrouter',
    label: 'OpenRouter',
    baseUrl: 'https://openrouter.ai/api/v1',
    keyPlaceholder: 'sk-or-...',
    keyHint: 'openrouter.ai',
    models: [
      { id: 'openai/gpt-4o-mini',                label: 'gpt-4o-mini',       tier: 'paid', cagSafe: true },
      { id: 'meta-llama/llama-3.3-70b-instruct', label: 'llama-3.3-70b',    tier: 'paid', cagSafe: true },
      { id: 'google/gemini-2.0-flash-001',        label: 'gemini-2.0-flash', tier: 'paid', cagSafe: true },
    ],
  },
  {
    id: 'cerebras',
    label: 'Cerebras',
    baseUrl: 'https://api.cerebras.ai/v1',
    keyPlaceholder: 'csk-...',
    keyHint: 'cloud.cerebras.ai',
    models: [
      { id: 'llama3.3-70b', label: 'llama3.3-70b', tier: 'free', cagSafe: true },
      { id: 'llama3.1-8b',  label: 'llama3.1-8b',  tier: 'free', cagSafe: true },
    ],
  },
]

export const DEFAULT_PROVIDER_ID = 'openai'
export const DEFAULT_MODEL_ID = 'gpt-4o-mini'
