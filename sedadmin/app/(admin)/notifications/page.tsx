'use client'

import { useState } from 'react'
import { Bell, Send, Loader2, CheckCircle } from 'lucide-react'

export default function NotificationsPage() {
  const [form, setForm] = useState({ title: '', message: '', target: 'all' })
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    setSending(true)
    await fetch('/api/notifications', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    setSending(false)
    setSent(true)
    setForm({ title: '', message: '', target: 'all' })
    setTimeout(() => setSent(false), 3000)
  }

  return (
    <div className="p-8 max-w-xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Bell className="w-6 h-6 text-yellow-400" />
          Notifications
        </h1>
        <p className="text-white/40 text-sm mt-1">Envoyer un message à vos utilisateurs</p>
      </div>

      <form onSubmit={handleSend} className="glass rounded-2xl p-6 space-y-4">
        <div>
          <label className="text-xs text-white/50 mb-1.5 block">Destinataires</label>
          <select
            value={form.target}
            onChange={e => setForm(f => ({ ...f, target: e.target.value }))}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm focus:outline-none focus:border-sala-primary/60"
          >
            <option value="all">Tous les utilisateurs</option>
            <option value="active">Abonnés actifs</option>
            <option value="free">Utilisateurs gratuits</option>
          </select>
        </div>

        <div>
          <label className="text-xs text-white/50 mb-1.5 block">Titre</label>
          <input
            type="text"
            value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            placeholder="Titre de la notification"
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm placeholder-white/20 focus:outline-none focus:border-sala-primary/60"
            required
          />
        </div>

        <div>
          <label className="text-xs text-white/50 mb-1.5 block">Message</label>
          <textarea
            value={form.message}
            onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
            placeholder="Contenu du message…"
            rows={4}
            className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-white text-sm placeholder-white/20 focus:outline-none focus:border-sala-primary/60 resize-none"
            required
          />
        </div>

        {sent && (
          <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-500/10 text-emerald-400 text-sm">
            <CheckCircle className="w-4 h-4" /> Notification enregistrée.
          </div>
        )}

        <button
          type="submit"
          disabled={sending}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-sala-primary hover:bg-sala-primary-light disabled:opacity-40 text-white font-semibold text-sm transition-colors"
        >
          {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Envoyer
        </button>
      </form>
    </div>
  )
}
