'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Eye, EyeOff, Loader2 } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [secret, setSecret] = useState('')
  const [show, setShow] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ secret }),
    })
    setLoading(false)
    if (res.ok) {
      router.push('/')
    } else {
      setError('Clé incorrecte.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-sala-bg relative overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[480px] h-[480px] bg-sala-primary/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="w-full max-w-sm relative z-10">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-sala-primary/15 border border-sala-primary/20 flex items-center justify-center mx-auto mb-4 sala-glow overflow-hidden">
            <img
              src="/logo-sala-ai.png"
              alt="Sala AI Logo"
              width={64}
              height={64}
              className="w-full h-full object-contain"
            />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Sala AI</h1>
          <p className="text-sala-primary/70 text-sm mt-1 font-medium">Console Admin</p>
        </div>

        <form onSubmit={handleSubmit} className="glass rounded-2xl p-6 space-y-4 bg-sala-surface/80 border border-white/10">
          <div>
            <label className="text-xs text-white/50 mb-1.5 block">Clé d'accès</label>
            <div className="relative">
              <input
                type={show ? 'text' : 'password'}
                value={secret}
                onChange={e => setSecret(e.target.value)}
                placeholder="••••••••••••••••"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm placeholder-white/20 focus:outline-none focus:border-sala-primary/60 pr-10"
                autoFocus
              />
              <button type="button" onClick={() => setShow(!show)} className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60">
                {show ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {error && <p className="text-red-400 text-xs">{error}</p>}

          <button
            type="submit"
            disabled={loading || !secret}
            className="w-full py-2.5 rounded-xl bg-sala-primary hover:bg-sala-primary-light disabled:opacity-40 text-white font-semibold text-sm transition-colors flex items-center justify-center gap-2 sala-glow"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Accéder'}
          </button>
        </form>
      </div>
    </div>
  )
}
