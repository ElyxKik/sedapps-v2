'use client'

import { useEffect, useState } from 'react'
import { FolderKanban, Search, RefreshCw, ExternalLink, Trash2, Eye, Code2 } from 'lucide-react'

interface Project {
  id: string
  name: string
  slug: string
  domain?: string
  stack_type: string
  status: string
  visits: number
  user_id: string
  created_at: string
}

const MAIN_APP = process.env.NEXT_PUBLIC_MAIN_APP_URL || 'http://localhost:3000'

function getViewerUrl(p: Project) {
  const builderMode = p.stack_type === 'wordpress' ? 'wordpress' : 'code'
  return `${MAIN_APP}/projects/${p.id}/builder/${builderMode}`
}

function getPreviewUrl(p: Project) {
  return `${MAIN_APP}/api/projects/${p.id}/preview/index.html`
}

const STACK_COLORS: Record<string, string> = {
  wordpress: 'bg-emerald-500/15 text-emerald-400',
  code: 'bg-blue-500/15 text-blue-400',
}
const STATUS_COLORS: Record<string, string> = {
  live: 'bg-emerald-500/15 text-emerald-400',
  draft: 'bg-white/8 text-white/40',
  building: 'bg-yellow-500/15 text-yellow-400',
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const fetchProjects = async () => {
    setLoading(true)
    const res = await fetch('/api/projects')
    const data = await res.json()
    setProjects(data.projects ?? [])
    setLoading(false)
  }

  useEffect(() => { fetchProjects() }, [])

  const filtered = projects.filter(p =>
    p.name?.toLowerCase().includes(search.toLowerCase()) ||
    p.domain?.toLowerCase().includes(search.toLowerCase()) ||
    p.user_id?.includes(search) ||
    p.id?.includes(search)
  )

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Supprimer le projet "${name}" définitivement ?`)) return
    await fetch(`/api/projects?id=${id}`, { method: 'DELETE' })
    fetchProjects()
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <FolderKanban className="w-6 h-6 text-violet-400" />
            Projets
          </h1>
          <p className="text-white/40 text-sm mt-1">{projects.length} projets enregistrés</p>
        </div>
        <button onClick={fetchProjects} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-sm transition-all">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          type="text"
          placeholder="Rechercher par nom, domaine, user ID..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-white text-sm placeholder-white/25 focus:outline-none focus:border-violet-500/50"
        />
      </div>

      <div className="glass rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/8">
              <th className="text-left px-4 py-3 text-white/40 font-medium">Projet</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium">Stack</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium">Statut</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium hidden md:table-cell">Visites</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium hidden lg:table-cell">Domaine</th>
              <th className="text-left px-4 py-3 text-white/40 font-medium hidden lg:table-cell">Créé le</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={7} className="text-center py-8 text-white/30">Chargement…</td></tr>}
            {!loading && filtered.length === 0 && <tr><td colSpan={7} className="text-center py-8 text-white/30">Aucun projet</td></tr>}
            {filtered.map(p => (
              <tr key={p.id} className="border-b border-white/5 hover:bg-white/3 transition-colors">
                <td className="px-4 py-3">
                  <p className="text-white/80 font-medium">{p.name}</p>
                  <p className="text-white/30 text-xs font-mono">{p.id.slice(0, 8)}…</p>
                </td>
                <td className="px-4 py-3">
                  <span className={`badge ${STACK_COLORS[p.stack_type] ?? 'bg-white/8 text-white/40'}`}>
                    {p.stack_type}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`badge ${STATUS_COLORS[p.status] ?? 'bg-white/8 text-white/40'}`}>
                    {p.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-white/50 hidden md:table-cell">{p.visits ?? 0}</td>
                <td className="px-4 py-3 hidden lg:table-cell">
                  <div className="flex flex-col gap-1">
                    {p.domain && (
                      <a href={`https://${p.domain}`} target="_blank" rel="noopener noreferrer"
                        className="text-xs text-white/40 hover:text-white/70 flex items-center gap-1 truncate max-w-[160px]">
                        {p.domain} <ExternalLink className="w-3 h-3 flex-shrink-0" />
                      </a>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-white/30 text-xs hidden lg:table-cell">
                  {new Date(p.created_at).toLocaleDateString('fr')}
                </td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <a
                      href={getPreviewUrl(p)}
                      target="_blank" rel="noopener noreferrer"
                      className="p-1.5 rounded-lg text-white/20 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                      title="Prévisualiser (viewer)"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </a>
                    <a
                      href={getViewerUrl(p)}
                      target="_blank" rel="noopener noreferrer"
                      className="p-1.5 rounded-lg text-white/20 hover:text-blue-400 hover:bg-blue-500/10 transition-colors"
                      title="Ouvrir dans le builder"
                    >
                      <Code2 className="w-3.5 h-3.5" />
                    </a>
                    <button
                      onClick={() => handleDelete(p.id, p.name)}
                      className="p-1.5 rounded-lg text-white/20 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                      title="Supprimer"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
