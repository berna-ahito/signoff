import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { Role } from '../types'
import './LoginPage.css'

interface Props {
  onLogin: (email: string, password: string) => Promise<Role | null>
}

export function LoginPage({ onLogin }: Props) {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await onLogin(email, password)
      navigate('/dashboard')
    } catch {
      setError('Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-root">
      <div className="login-card" role="main">
        <div className="login-header">
          <div className="login-logo">
            Procure<span>Flow</span>
            <span className="login-ai-tag">AI</span>
          </div>
          <p className="login-tagline">Procurement intake & approval workflow</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form" noValidate aria-label="Sign in form">
          {error && (
            <div className="alert alert-error" role="alert" aria-live="polite">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email" className="form-label">Email</label>
            <input
              id="email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <input
              id="password"
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', padding: '9px 14px' }}
            disabled={loading || !email || !password}
            aria-busy={loading}
          >
            {loading ? <><span className="spinner" aria-hidden="true" /> Signing in…</> : 'Sign in'}
          </button>
        </form>

        <p className="login-hint" aria-label="Demo credentials hint">
          Demo: use seeded users from <code>scripts/seed.py</code>
        </p>
      </div>
    </div>
  )
}
