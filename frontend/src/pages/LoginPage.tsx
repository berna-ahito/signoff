import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BrandMark } from '../components/BrandMark'
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
      <div className="login-brand-panel" aria-hidden="true">
        <div className="login-brand-content">
          <div className="login-brand-identity">
            <BrandMark size={40} accentColor="#93c5fd" />
            <div>
              <div className="login-brand-wordmark">
                ProcureFlow<span className="login-brand-ai"> AI</span>
              </div>
              <div className="login-brand-subtitle">Executive Procurement OS</div>
            </div>
          </div>
          <p className="login-brand-tagline">
            Structured intake, AI-assisted review,<br />
            and auditable approval trails.
          </p>
          <ul className="login-brand-features">
            <li>Purchase request intake &amp; validation</li>
            <li>AI risk classification &amp; RFQ drafting</li>
            <li>Human-controlled approval workflow</li>
          </ul>
        </div>
        <div className="login-brand-footer">ProcureFlow AI · Portfolio Build</div>
      </div>

      <div className="login-form-panel">
        <div className="login-card">
          <div className="login-header">
            <div className="login-logo-row">
              <BrandMark size={20} variant="light" />
              <div className="login-logo">
                Procure<span className="logo-flow">Flow</span>
                <span className="login-ai-tag">AI</span>
              </div>
            </div>
            <p className="login-tagline">Sign in to your workspace</p>
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

          <div className="login-hint" aria-label="Demo credentials">
            <p style={{ marginBottom: 6 }}>Demo accounts:</p>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
              <tbody>
                <tr><td><code>alice@test.com</code></td><td style={{ color: 'var(--color-text-subtle)' }}>alice123</td><td style={{ color: 'var(--color-text-subtle)', textAlign: 'right' }}>Requester</td></tr>
                <tr><td><code>bob@test.com</code></td><td style={{ color: 'var(--color-text-subtle)' }}>bob123</td><td style={{ color: 'var(--color-text-subtle)', textAlign: 'right' }}>Manager</td></tr>
                <tr><td><code>carol@test.com</code></td><td style={{ color: 'var(--color-text-subtle)' }}>carol123</td><td style={{ color: 'var(--color-text-subtle)', textAlign: 'right' }}>Finance</td></tr>
                <tr><td><code>admin@test.com</code></td><td style={{ color: 'var(--color-text-subtle)' }}>admin123</td><td style={{ color: 'var(--color-text-subtle)', textAlign: 'right' }}>Admin</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
