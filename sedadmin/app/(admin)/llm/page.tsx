'use client'

import { useEffect, useState } from 'react'
import { Bot, Save, RefreshCw, CheckCircle, AlertCircle, Loader2, ChevronDown } from 'lucide-react'

const PRESETS = [
  { label: 'DeepSeek Chat', provider: 'deepseek', baseUrl: 'https://api.deepseek.com/v1', model: 'deepseek-chat', isAnthropic: false },
  { label: 'DeepSeek Reasoner', provider: 'deepseek', baseUrl: 'https://api.deepseek.com/v1', model: 'deepseek-reasoner', isAnthropic: false },
  { label: 'OpenAI GPT-4o', provider: 'openai', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o', isAnthropic: false },
  { label: 'OpenAI GPT-4o Mini', provider: 'openai', baseUrl: 'https://api.openai.com/v1', model: 'gpt-4o-mini', isAnthropic: false },
  { label: 'Anthropic Claude 3.5 Sonnet', provider: 'anthropic', baseUrl: 'https://api.anthropic.com/v1', model: 'claude-3-5-sonnet-20241022', isAnthropic: true },
  { label: 'Anthropic Claude 3.5 Haiku', provider: 'anthropic', baseUrl: 'https://api.anthropic.com/v1', model: 'claude-3-5-haiku-20241022', isAnthropic: true },
  { label: 'Mistral Large', provider: 'mistral', baseUrl: 'https://api.mistral.ai/v1', model: 'mistral-large-latest', isAnthropic: false },
  { label: 'Mistral Small', provider: 'mistral', baseUrl: 'https://api.mistral.ai/v1', model: 'mistral-small-latest', isAnthropic: false },
  { label: 'OpenRouter (Claude)', provider: 'openrouter', baseUrl: 'https://openrouter.ai/api/v1', model: 'anthropic/claude-3.5-sonnet', isAnthropic: false },
  { label: 'Ollama (local)', provider: 'ollama', baseUrl: 'http://localhost:11434/v1', model: 'llama3.2', isAnthropic: false },
  { label: 'Personnalisé', provider: 'custom', baseUrl: '', model: '', isAnthropic: false },
]

interface LLMForm {
  provider: string
  baseUrl: string
  model: string
  apiKey: string
  isAnthropic: boolean
  temperature: number
  maxTokens: number
}

export default function LLMPage() {
  const [form, setForm] = useState<LLMForm>({
    provider: 'deepseek',
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    apiKey: '',
    isAnthropic: false,
    temperature: 0.3,
    maxTokens: 8192,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const [showPresets, setShowPresets] = useState(false)

  useEffect(() => {
    fetch('/api/llm')
      .then(r => r.json())
      .then(data => {
        setForm(f => ({
          ...f,
          provider: data.provider ?? f.provider,
          baseUrl: data.baseUrl ?? f.baseUrl,
          model: data.model ?? f.model,
          apiKey: data.apiKey ?? '',
          isAnthropic: data.isAnthropic ?? false,
          temperature: data.temperature ?? 0.3,
          maxTokens: data.maxTokens ?? 8192,
        }))
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setForm(f => ({
      ...f,
      provider: preset.provider,
      baseUrl: preset.baseUrl,
      model: preset.model,
      isAnthropic: preset.isAnthropic,
    }))
    setShowPresets(false)
  }

  const handleSave = async () => {
    setSaving(true)
    setStatus(null)
    try {
      const res = await fetch('/api/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      if (res.ok) {
        setStatus({ type: 'success', msg: 'Configuration sauvegardée et active immédiatement.' })
      } else {
        setStatus({ type: 'error', msg: data.error ?? 'Erreur lors de la sauvegarde.' })
      }
    } catch (e) {
      setStatus({ type: 'error', msg: 'Erreur réseau.' })
    }
    setSaving(false)
  }

  const handleReset = async () => {
    if (!confirm('Réinitialiser vers les variables d\'environnement ?')) return
    await fetch('/api/llm', { method: 'DELETE' })
    setStatus({ type: 'success', msg: 'Réinitialisé vers les valeurs des variables d\'environnement.' })
  }

  if (loading) {
    return <div className="p-8 flex items-center gap-2 text-white/40"><Loader2 className="w-4 h-4 animate-spin" /> Chargement…</div>
  }

  return (
    <div className="p-8 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Bot className="w-6 h-6 text-sala-primary-light" />
          Configuration LLM
        </h1>
        <p className="text-white/40 text-sm mt-1">Provider IA utilisé par SedAI dans le builder</p>
      </div>

      <div className="glass rounded-2xl p-6 space-y-5">
        {/* Preset selector */}
        <div>
          <label className="text-xs text-white/50 mb-2 block">Preset rapide</label>
          <div className="relative">
            <button
              onClick={() => setShowPresets(!showPresets)}
              className="w-full flex items-center justify-between px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:border-sala-primary/60 transition-colors"
            >
              <span>{PRESETS.find(p => p.baseUrl === form.baseUrl && p.model === form.model)?.label ?? 'Sélectionner un preset…'}</span>
              <ChevronDown className={`w-4 h-4 text-white/40 transition-transform ${showPresets ? 'rotate-180' : ''}`} />
            </button>
            {showPresets && (
              <div className="absolute top-full mt-1 w-full bg-[#1a1a24] border border-white/10 rounded-xl shadow-2xl z-10 overflow-hidden">
                {PRESETS.map(p => (
                  <button
                    key={p.label}
                    onClick={() => applyPreset(p)}
                    className="w-full text-left px-4 py-2.5 text-sm text-white/70 hover:bg-white/5 hover:text-white transition-colors border-b border-white/5 last:border-0"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Fields */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Provider</label>
            <input
              value={form.provider}
              onChange={e => setForm(f => ({ ...f, provider: e.target.value }))}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-sala-primary/60"
              placeholder="deepseek"
            />
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Modèle</label>
            <input
              value={form.model}
              onChange={e => setForm(f => ({ ...f, model: e.target.value }))}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-sala-primary/60"
              placeholder="deepseek-chat"
            />
          </div>
        </div>

        <div>
          <label className="text-xs text-white/50 mb-1.5 block">Base URL</label>
          <input
            value={form.baseUrl}
            onChange={e => setForm(f => ({ ...f, baseUrl: e.target.value }))}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-sala-primary/60"
            placeholder="https://api.deepseek.com/v1"
          />
        </div>

        <div>
          <label className="text-xs text-white/50 mb-1.5 block">Clé API</label>
          <input
            type="password"
            value={form.apiKey}
            onChange={e => setForm(f => ({ ...f, apiKey: e.target.value }))}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-sala-primary/60 font-mono"
            placeholder="sk-…"
          />
          <p className="text-xs text-white/25 mt-1">Laissez vide pour conserver la clé existante</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Température ({form.temperature})</label>
            <input
              type="range" min="0" max="2" step="0.05"
              value={form.temperature}
              onChange={e => setForm(f => ({ ...f, temperature: parseFloat(e.target.value) }))}
              className="w-full accent-sala-primary"
            />
          </div>
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Max tokens</label>
            <input
              type="number"
              value={form.maxTokens}
              onChange={e => setForm(f => ({ ...f, maxTokens: parseInt(e.target.value) || 8192 }))}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-white text-sm focus:outline-none focus:border-sala-primary/60"
            />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-white/60">Format Anthropic Messages API</label>
          <button
            onClick={() => setForm(f => ({ ...f, isAnthropic: !f.isAnthropic }))}
            className={`relative w-10 h-5 rounded-full transition-colors ${form.isAnthropic ? 'bg-sala-primary' : 'bg-white/10'}`}
          >
            <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${form.isAnthropic ? 'translate-x-5' : 'translate-x-0.5'}`} />
          </button>
        </div>

        {status && (
          <div className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm ${status.type === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
            {status.type === 'success' ? <CheckCircle className="w-4 h-4 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 flex-shrink-0" />}
            {status.msg}
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl bg-sala-primary hover:bg-sala-primary-light disabled:opacity-40 text-white font-semibold text-sm transition-colors"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Sauvegarder
          </button>
          <button
            onClick={handleReset}
            className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-sm transition-colors flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Reset
          </button>
        </div>
      </div>

      {/* Current config summary */}
      <div className="glass rounded-2xl p-4 mt-4 text-xs font-mono text-white/40 space-y-1">
        <p className="text-white/60 font-sans text-xs font-semibold mb-2">Config active</p>
        <p>Provider : <span className="text-sala-primary-light">{form.provider}</span></p>
        <p>URL : <span className="text-sala-sky">{form.baseUrl}</span></p>
        <p>Modèle : <span className="text-emerald-300">{form.model}</span></p>
        <p>Format : <span className="text-white/60">{form.isAnthropic ? 'Anthropic Messages API' : 'OpenAI-compatible'}</span></p>
      </div>
    </div>
  )
}
