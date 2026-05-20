'use client'

import { useState } from 'react'
import { Settings, Save, Loader2, CheckCircle, AlertTriangle } from 'lucide-react'

export default function SettingsPage() {
  const [adminSecret, setAdminSecret] = useState('')
  const [mainAppUrl, setMainAppUrl] = useState(process.env.NEXT_PUBLIC_MAIN_APP_URL ?? '')
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setStatus(null)
    await new Promise(r => setTimeout(r, 600))
    setSaving(false)
    setStatus({ type: 'success', msg: 'Modifiez ces valeurs directement dans le fichier .env.local de sedadmin et redémarrez le serveur.' })
  }

  return (
    <div className="p-8 max-w-xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-white/60" />
          Paramètres
        </h1>
        <p className="text-white/40 text-sm mt-1">Configuration de l'instance admin</p>
      </div>

      {/* Info box */}
      <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-yellow-500/8 border border-yellow-500/20 text-yellow-300 text-xs mb-6">
        <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold mb-0.5">Configuration via fichier .env.local</p>
          <p className="text-yellow-300/70">Les paramètres sensibles (clés API, secrets) doivent être définis dans <code className="font-mono bg-white/10 px-1 rounded">sedadmin/.env.local</code> et ne sont pas modifiables en ligne pour des raisons de sécurité.</p>
        </div>
      </div>

      <form onSubmit={handleSave} className="glass rounded-2xl p-6 space-y-5">
        <div>
          <label className="text-xs text-white/50 mb-1.5 block">URL de l'application principale</label>
          <input
            type="url"
            value={mainAppUrl}
            onChange={e => setMainAppUrl(e.target.value)}
            placeholder="http://localhost:3000"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-violet-500/50"
          />
          <p className="text-white/25 text-xs mt-1">Variable : NEXT_PUBLIC_MAIN_APP_URL</p>
        </div>

        <div>
          <label className="text-xs text-white/50 mb-1.5 block">Clé d'accès admin</label>
          <input
            type="password"
            value={adminSecret}
            onChange={e => setAdminSecret(e.target.value)}
            placeholder="••••••••"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-violet-500/50"
          />
          <p className="text-white/25 text-xs mt-1">Variable : ADMIN_SECRET</p>
        </div>

        {status && (
          <div className={`flex items-start gap-2 px-4 py-3 rounded-xl text-sm ${status.type === 'success' ? 'bg-blue-500/10 text-blue-300' : 'bg-red-500/10 text-red-400'}`}>
            <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            {status.msg}
          </div>
        )}

        <button
          type="submit"
          disabled={saving}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white font-semibold text-sm transition-colors"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Enregistrer
        </button>
      </form>

      {/* Env reference */}
      <div className="glass rounded-2xl p-5 mt-4">
        <p className="text-xs font-semibold text-white/60 mb-3">Variables d'environnement requises</p>
        <div className="space-y-2 text-xs font-mono">
          {[
            ['NEXT_PUBLIC_SUPABASE_URL', 'URL Supabase'],
            ['NEXT_PUBLIC_SUPABASE_ANON_KEY', 'Clé anonyme Supabase'],
            ['SUPABASE_SERVICE_ROLE_KEY', 'Clé service Supabase (admin)'],
            ['ADMIN_SECRET', 'Mot de passe d\'accès au dashboard'],
            ['NEXT_PUBLIC_MAIN_APP_URL', 'URL de l\'app principale'],
          ].map(([key, desc]) => (
            <div key={key} className="flex items-center justify-between gap-4">
              <code className="text-violet-300">{key}</code>
              <span className="text-white/30">{desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
