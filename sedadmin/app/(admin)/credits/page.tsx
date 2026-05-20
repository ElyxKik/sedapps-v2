'use client'

import { useState, useEffect } from 'react'
import { Search, Plus, Loader2, AlertCircle, CheckCircle2, Zap } from 'lucide-react'

interface User {
  id: string
  email: string
  name: string
  createdAt: string
  balance: number
  totalPurchased: number
  totalConsumed: number
}

export default function CreditsAdminPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [search, setSearch] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Modal state
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [creditsToAdd, setCreditsToAdd] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Fetch users
  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/credits/users?search=${encodeURIComponent(search)}&limit=50`)
        if (!res.ok) throw new Error('Erreur lors de la récupération des utilisateurs')
        const data = await res.json()
        setUsers(data.users)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    const timer = setTimeout(fetchUsers, 300) // Debounce search
    return () => clearTimeout(timer)
  }, [search])

  const handleAddCredits = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedUser || !creditsToAdd) return

    setSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      const res = await fetch('/api/credits/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: selectedUser.id,
          credits: parseInt(creditsToAdd, 10),
          description: description || undefined,
        }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.error || 'Erreur lors de l\'ajout de crédits')
      }

      const data = await res.json()
      setSuccess(`✅ ${data.message}`)
      setCreditsToAdd('')
      setDescription('')
      setSelectedUser(null)

      // Refresh users
      const refreshRes = await fetch(`/api/credits/users?search=${encodeURIComponent(search)}&limit=50`)
      if (refreshRes.ok) {
        const refreshData = await refreshRes.json()
        setUsers(refreshData.users)
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Zap className="w-8 h-8 text-amber-400" />
          Gestion des Crédits
        </h1>
        <p className="text-white/50 mt-2">Ajouter manuellement des crédits aux utilisateurs</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-3 w-5 h-5 text-white/30" />
        <input
          type="text"
          placeholder="Rechercher par email ou nom..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:border-blue-500/50"
        />
      </div>

      {/* Error/Success messages */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-3 p-4 bg-green-500/10 border border-green-500/20 rounded-xl">
          <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
          <p className="text-green-300 text-sm">{success}</p>
        </div>
      )}

      {/* Users table */}
      <div className="glass rounded-2xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 text-white/40 animate-spin" />
          </div>
        ) : users.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-white/40">Aucun utilisateur trouvé</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-white/60 uppercase">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-white/60 uppercase">Nom</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-white/60 uppercase">Solde</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-white/60 uppercase">Acheté</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-white/60 uppercase">Consommé</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-white/60 uppercase">Action</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                    <td className="px-6 py-4 text-sm text-white">{user.email}</td>
                    <td className="px-6 py-4 text-sm text-white/70">{user.name}</td>
                    <td className="px-6 py-4 text-sm text-right font-semibold text-amber-400">
                      {user.balance.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-right text-green-400">
                      {user.totalPurchased.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-right text-red-400">
                      {user.totalConsumed.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => setSelectedUser(user)}
                        className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors"
                      >
                        <Plus className="w-4 h-4" />
                        Ajouter
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="glass rounded-2xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4">
              Ajouter des crédits
            </h2>
            <p className="text-white/60 text-sm mb-4">
              Utilisateur: <span className="text-white font-semibold">{selectedUser.email}</span>
            </p>

            <form onSubmit={handleAddCredits} className="space-y-4">
              {/* Credits input */}
              <div>
                <label className="block text-sm font-semibold text-white mb-2">
                  Nombre de crédits
                </label>
                <input
                  type="number"
                  min="1"
                  max="10000"
                  value={creditsToAdd}
                  onChange={(e) => setCreditsToAdd(e.target.value)}
                  placeholder="Ex: 50"
                  className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:border-blue-500/50"
                  required
                />
                <p className="text-xs text-white/40 mt-1">
                  Solde actuel: {selectedUser.balance} crédits
                </p>
              </div>

              {/* Description input */}
              <div>
                <label className="block text-sm font-semibold text-white mb-2">
                  Description (optionnel)
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Ex: Bonus de bienvenue"
                  className="w-full px-4 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder:text-white/30 focus:outline-none focus:border-blue-500/50"
                />
              </div>

              {/* Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedUser(null)
                    setCreditsToAdd('')
                    setDescription('')
                  }}
                  className="flex-1 px-4 py-2.5 bg-white/5 hover:bg-white/10 text-white font-semibold rounded-xl transition-colors"
                  disabled={submitting}
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  disabled={submitting || !creditsToAdd}
                >
                  {submitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Ajout...
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4" />
                      Ajouter
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
