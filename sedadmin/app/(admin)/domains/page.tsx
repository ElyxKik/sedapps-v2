'use client'

import { useEffect, useState } from 'react'
import { Globe, Search, RefreshCw, ExternalLink, CheckCircle, XCircle } from 'lucide-react'

interface Domain {
  id: string
  domain: string
  project_id: string
  user_id?: string
  status?: string
  verified?: boolean
  created_at: string
}

export default function DomainsPage() {
  const [domains, setDomains] = useState<Domain[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const fetchDomains = async () => {
    setLoading(true)
    const res = await fetch('/api/domains')
    const data = await res.json()
    setDomains(data.domains ?? [])
    setLoading(false)
  }

  useEffect(() => { fetchDomains() }, [])

  const filtered = domains.filter(d =>
    d.domain?.toLowerCase().includes(search.toLowerCase()) ||
    d.project_id?.includes(search)
  )

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Globe className="w-6 h-6 text-emerald-400" />
            Domaines
          </h1>
          <p className="text-white/40 text-sm mt-1">{domains.length} domaines enregistrés</p>
        </div>
        <button onClick={fetchDomains} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-sm transition-all">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          type="text"
          placeholder="Rechercher un domaine ou project ID..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-white text-sm placeholder-white/25 focus:outline-none focus:border-sala-primary/60"
        />
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/8">
              <th className="text-left px-4 py-3 text-white/40 font-medium">Domaine</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium">Projet</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium">Vérifié</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium hidden md:table-cell">Ajouté le</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={5} className="text-center py-8 text-white/30">Chargement…</td></tr>}
            {!loading && filtered.length === 0 && <tr><td colSpan={5} className="text-center py-8 text-white/30">Aucun domaine</td></tr>}
            {filtered.map(d => (
              <tr key={d.id} className="border-b border-white/5 hover:bg-white/3 transition-colors">
                <td className="px-4 py-3 font-medium text-white/80">{d.domain}</td>
                <td className="px-4 py-3 font-mono text-white/40 text-xs">{d.project_id?.slice(0, 12)}…</td>
                <td className="px-4 py-3">
                  {d.verified
                    ? <CheckCircle className="w-4 h-4 text-emerald-400" />
                    : <XCircle className="w-4 h-4 text-white/20" />}
                </td>
                <td className="px-4 py-3 text-white/30 text-xs hidden md:table-cell">
                  {new Date(d.created_at).toLocaleDateString('fr')}
                </td>
                <td className="px-4 py-3">
                  <a href={`https://${d.domain}`} target="_blank" rel="noopener noreferrer"
                    className="p-1.5 rounded-lg text-white/20 hover:text-sala-sky hover:bg-sala-sky/10 transition-colors inline-flex">
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
