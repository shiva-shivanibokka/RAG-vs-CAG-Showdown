export const PROVIDERS = [
  {
    id: 'openai',
    label: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    keyPlaceholder: 'sk-...',
    keyHint: 'platform.openai.com',
    models: [
      { id: 'gpt-4o-mini',  label: 'gpt-4o-mini (recommended)', tier: 'paid', cagSafe: true },
      { id: 'gpt-4.1-mini', label: 'gpt-4.1-mini',              tier: 'paid', cagSafe: true },
      { id: 'gpt-4o',       label: 'gpt-4o',                    tier: 'paid', cagSafe: true },
      { id: 'gpt-4.1',      label: 'gpt-4.1',                   tier: 'paid', cagSafe: true },
      { id: 'gpt-4.1-nano', label: 'gpt-4.1-nano (cheapest)',   tier: 'paid', cagSafe: true },
    ],
  },
  {
    id: 'gemini',
    label: 'Google Gemini',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai/',
    keyPlaceholder: 'AIza...',
    keyHint: 'aistudio.google.com',
    models: [
      { id: 'gemini-2.0-flash',      label: 'gemini-2.0-flash (recommended)', tier: 'free', cagSafe: true },
      { id: 'gemini-2.0-flash-lite', label: 'gemini-2.0-flash-lite',          tier: 'free', cagSafe: true },
      { id: 'gemini-1.5-flash',      label: 'gemini-1.5-flash',               tier: 'free', cagSafe: true },
      { id: 'gemini-1.5-pro',        label: 'gemini-1.5-pro',                 tier: 'paid', cagSafe: true },
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
        id: 'mixtral-8x7b-32768',
        label: 'mixtral-8x7b-32768 (32K context)',
        tier: 'free',
        cagSafe: false,
        warning: 'Free tier TPM cap — CAG will likely be rejected. RAG works fine with its larger context window.',
      },
      {
        id: 'llama-3.1-8b-instant',
        label: 'llama-3.1-8b-instant',
        tier: 'free',
        cagSafe: false,
        warning: '6,000 TPM hard cap — CAG will be rejected. RAG only will work.',
      },
      {
        id: 'gemma2-9b-it',
        label: 'gemma2-9b-it',
        tier: 'free',
        cagSafe: false,
        warning: '8,192 token context window — CAG needs 13,500+ tokens and will fail.',
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
      { id: 'anthropic/claude-3.5-haiku',         label: 'claude-3.5-haiku', tier: 'paid', cagSafe: true },
      { id: 'mistralai/mistral-7b-instruct',      label: 'mistral-7b',       tier: 'paid', cagSafe: true },
    ],
  },
  {
    id: 'cerebras',
    label: 'Cerebras',
    baseUrl: 'https://api.cerebras.ai/v1',
    keyPlaceholder: 'csk-...',
    keyHint: 'cloud.cerebras.ai',
    models: [
      { id: 'llama3.3-70b', label: 'llama3.3-70b (recommended)', tier: 'free', cagSafe: true },
      { id: 'llama3.1-70b', label: 'llama3.1-70b',               tier: 'free', cagSafe: true },
      { id: 'llama3.1-8b',  label: 'llama3.1-8b',                tier: 'free', cagSafe: true },
    ],
  },
]

export const DEFAULT_PROVIDER_ID = 'openai'
export const DEFAULT_MODEL_ID = 'gpt-4o-mini'
