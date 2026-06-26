'use client'

import { useEffect, useState } from 'react'
import { Activity, RefreshCw, Search } from 'lucide-react'

interface LogEntry {
  id: string
  user_id?: string
  action: string
  resource?: string
  meta?: Record<string, unknown>
  created_at: string
}

const ACTION_COLORS: Record<string, string> = {
  create: 'bg-emerald-500/15 text-emerald-400',
  update: 'bg-blue-500/15 text-sala-sky',
  delete: 'bg-red-500/15 text-red-400',
  deploy: 'bg-sala-primary/15 text-sala-primary-light',
  login: 'bg-yellow-500/15 text-yellow-400',
}

export default function ActivityPage() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const fetchLogs = async () => {
    setLoading(true)
    const res = await fetch('/api/activity')
    const data = await res.json()
    setLogs(data.logs ?? [])
    setLoading(false)
  }

  useEffect(() => { fetchLogs() }, [])

  const filtered = logs.filter(l =>
    l.action?.toLowerCase().includes(search.toLowerCase()) ||
    l.user_id?.includes(search) ||
    l.resource?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-6 h-6 text-sala-sky" />
            Journal d'activité
          </h1>
          <p className="text-white/40 text-sm mt-1">Dernières actions sur la plateforme</p>
        </div>
        <button onClick={fetchLogs} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-sm transition-all">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          type="text"
          placeholder="Filtrer par action, user, ressource…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-white text-sm placeholder-white/25 focus:outline-none focus:border-sala-primary/60"
        />
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        {loading && <p className="text-center py-8 text-white/30">Chargement…</p>}
        {!loading && filtered.length === 0 && (
          <p className="text-center py-8 text-white/30">Aucune activité enregistrée</p>
        )}
        <div className="divide-y divide-white/5">
          {filtered.map(log => (
            <div key={log.id} className="flex items-start gap-4 px-5 py-3 hover:bg-white/3 transition-colors">
              <span className={`badge mt-0.5 flex-shrink-0 ${ACTION_COLORS[log.action?.split('_')[0]] ?? 'bg-white/8 text-white/40'}`}>
                {log.action}
              </span>
              <div className="flex-1 min-w-0">
                {log.resource && <p className="text-white/60 text-xs truncate">{log.resource}</p>}
                {log.user_id && <p className="text-white/30 text-xs font-mono">user: {log.user_id.slice(0, 12)}…</p>}
                {log.meta && Object.keys(log.meta).length > 0 && (
                  <p className="text-white/20 text-xs font-mono truncate">{JSON.stringify(log.meta)}</p>
                )}
              </div>
              <time className="text-white/25 text-xs flex-shrink-0">
                {new Date(log.created_at).toLocaleString('fr', { dateStyle: 'short', timeStyle: 'short' })}
              </time>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
