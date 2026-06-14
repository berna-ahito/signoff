import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
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
  const [showDemoAccounts, setShowDemoAccounts] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await onLogin(email, password)
      navigate('/dashboard')
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        if (!err.response) {
          setError('Network error. Cannot reach the server.')
        } else if (err.response.status === 404) {
          setError('Auth endpoint not found. Please check API URL.')
        } else if (err.response.status === 401) {
          setError('Invalid email or password.')
        } else {
          setError(`Server error (${err.response.status}). Please try again.`)
        }
      } else {
        setError('Invalid email or password.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-root">
      <div className="login-brand-panel" aria-hidden="true">
        <div className="login-brand-content">
          <div className="login-brand-identity">
            <BrandMark size={40} accentColor="#1769E0" />
            <div>
              <div className="login-brand-wordmark">
                Signoff
              </div>
              <div className="login-brand-subtitle">AI-assisted approval workflow with RBAC, audit logs, and human review.</div>
            </div>
          </div>
          <h1 className="login-brand-headline">
            Purchase requests that actually get approved <span className="login-brand-headline-accent">correctly.</span>
          </h1>
          <p className="login-brand-tagline">
            Structured intake, AI-assisted review,<br />
            and auditable approval trails.
          </p>
          <ul className="login-brand-features">
            <li><strong>Structured intake</strong> &amp; validation</li>
            <li><strong>AI classification</strong> &amp; RFQ drafting</li>
            <li><strong>Human approval</strong> workflow</li>
          </ul>
        </div>
        <div className="login-brand-footer">Signoff · 2026</div>
      </div>

      <div className="login-form-panel">
        <div className="login-card">
          <div className="login-header">
            <div className="login-logo-row">
              <BrandMark size={20} variant="light" accentColor="#1769E0" />
              <div className="login-logo">
                Signoff
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

          {(import.meta.env.MODE === 'development' || import.meta.env.VITE_SHOW_DEMO_ACCOUNTS === 'true') && (
            <div className="login-demo">
              <button
                type="button"
                className="login-demo-toggle"
                onClick={() => setShowDemoAccounts((value) => !value)}
                aria-expanded={showDemoAccounts}
                aria-controls="demo-accounts"
              >
                {showDemoAccounts ? 'Hide demo accounts ↑' : 'View demo accounts ↓'}
              </button>
              {showDemoAccounts && (
                <div id="demo-accounts" className="login-hint" aria-label="Demo credentials">
                  <p>Demo accounts:</p>
                  <table>
                    <tbody>
                      <tr><td><code>alice@test.com</code></td><td>alice123</td><td>Requester</td></tr>
                      <tr><td><code>bob@test.com</code></td><td>bob123</td><td>Manager</td></tr>
                      <tr><td><code>carol@test.com</code></td><td>carol123</td><td>Finance</td></tr>
                      <tr><td><code>admin@test.com</code></td><td>admin123</td><td>Admin</td></tr>
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
