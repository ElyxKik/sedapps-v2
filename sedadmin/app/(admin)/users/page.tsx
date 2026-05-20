'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Users, Search, Ban, CheckCircle, RefreshCw, ChevronRight } from 'lucide-react'

interface User {
  id: string
  email: string
  created_at: string
  last_sign_in_at?: string
  banned_until?: string
  email_confirmed_at?: string
  user_metadata?: { full_name?: string; avatar_url?: string }
}



export default function UsersPage() {
  const router = useRouter()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [actionLoading, setActionLoading] = useState('')

  const fetchUsers = async () => {
    setLoading(true)
    const res = await fetch('/api/users')
    const data = await res.json()
    setUsers(data.users ?? [])
    setLoading(false)
  }

  useEffect(() => { fetchUsers() }, [])

  const filtered = users.filter(u =>
    u.email?.toLowerCase().includes(search.toLowerCase()) ||
    u.id.includes(search)
  )

  const handleBan = async (userId: string, ban: boolean) => {
    setActionLoading(userId)
    await fetch('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: ban ? 'ban' : 'unban', userId }),
    })
    await fetchUsers()
    setActionLoading('')
  }

  const isBanned = (u: User) => !!u.banned_until && new Date(u.banned_until) > new Date()

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-blue-400" />
            Utilisateurs
          </h1>
          <p className="text-white/40 text-sm mt-1">{users.length} comptes enregistrés</p>
        </div>
        <button onClick={fetchUsers} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/60 hover:text-white text-sm transition-all">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-5">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          type="text"
          placeholder="Rechercher par email ou ID..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-white text-sm placeholder-white/25 focus:outline-none focus:border-violet-500/50"
        />
      </div>

      <div className="glass rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/8">
                <th className="text-left px-4 py-3 text-white/40 font-medium">Utilisateur</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium hidden md:table-cell">Inscription</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium">Statut</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium hidden md:table-cell">Dernière connexion</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={4} className="text-center py-8 text-white/30">Chargement…</td></tr>
              )}
              {!loading && filtered.length === 0 && (
                <tr><td colSpan={4} className="text-center py-8 text-white/30">Aucun utilisateur trouvé</td></tr>
              )}
              {filtered.map(u => (
                <tr
                  key={u.id}
                  onClick={() => router.push(`/users/${u.id}`)}
                  className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-600/40 to-blue-600/40 flex items-center justify-center text-xs font-bold text-white/70 flex-shrink-0">
                        {u.email?.[0]?.toUpperCase() ?? '?'}
                      </div>
                      <div>
                        <p className="text-white/80 font-medium truncate max-w-[180px]">{u.email}</p>
                        <p className="text-white/30 text-xs font-mono">{u.id.slice(0, 8)}…</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-white/40 text-xs hidden md:table-cell">
                    {new Date(u.created_at).toLocaleDateString('fr')}
                  </td>
                  <td className="px-4 py-3 text-white/30 text-xs hidden md:table-cell">
                    {u.last_sign_in_at ? new Date(u.last_sign_in_at).toLocaleDateString('fr') : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {isBanned(u)
                      ? <span className="badge bg-red-500/15 text-red-400">Banni</span>
                      : u.email_confirmed_at
                        ? <span className="badge bg-emerald-500/15 text-emerald-400">Actif</span>
                        : <span className="badge bg-yellow-500/15 text-yellow-400">Non vérifié</span>
                    }
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={e => { e.stopPropagation(); handleBan(u.id, !isBanned(u)) }}
                        disabled={actionLoading === u.id}
                        className={`p-1.5 rounded-lg transition-colors ${isBanned(u) ? 'text-emerald-400 hover:bg-emerald-500/10' : 'text-white/30 hover:text-red-400 hover:bg-red-500/10'}`}
                        title={isBanned(u) ? 'Débannir' : 'Bannir'}
                      >
                        {isBanned(u) ? <CheckCircle className="w-4 h-4" /> : <Ban className="w-4 h-4" />}
                      </button>
                      <ChevronRight className="w-4 h-4 text-white/20" />
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
