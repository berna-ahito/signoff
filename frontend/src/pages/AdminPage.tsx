import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend,
} from 'recharts'
import { createUser, listUsers, updateUser } from '../api/users'
import { listRules, createRule } from '../api/rules'
import { getSpendByCategory, getCategorySummaries } from '../api/analytics'
import type {
  ApprovalRule, ApprovalRuleCreate,
  CategorySummary, Role, SpendGroup, User, UserCreate,
} from '../types'

type Tab = 'users' | 'rules' | 'analytics'

const SPEND_COLORS = ['#0f766e', '#0891b2', '#7c3aed', '#d97706', '#dc2626', '#059669']

// ── Users panel ───────────────────────────────────────────────────────────────

function UsersPanel() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createError, setCreateError] = useState<string | null>(null)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState<Role>('requester')
  const [departmentId, setDepartmentId] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    listUsers()
      .then(setUsers)
      .catch(() => setError('Failed to load users.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  async function handleToggleActive(user: User) {
    try {
      await updateUser(user.id, { is_active: !user.is_active })
      toast.success(user.is_active ? 'User deactivated' : 'User activated')
      load()
    } catch {
      toast.error('Failed to update user.')
      setError('Failed to update user.')
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreateError(null)
    const body: UserCreate = {
      email,
      password,
      full_name: fullName,
      role,
      ...(departmentId ? { department_id: Number(departmentId) } : {}),
    }
    try {
      await createUser(body)
      toast.success('User created')
      setEmail('')
      setPassword('')
      setFullName('')
      setRole('requester')
      setDepartmentId('')
      load()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg ?? 'Failed to create user.')
      setCreateError(msg ?? 'Failed to create user.')
    }
  }

  if (loading) {
    return (
      <div className="loading-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> Loading users…
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="alert alert-error" role="alert">{error}</div>
        <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={load}>Retry</button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <div className="section-label">Users</div>
        <div className="card card-table">
          <div className="table-wrap">
            <table aria-label="User list">
              <thead>
                <tr>
                  <th scope="col">Email</th>
                  <th scope="col">Full Name</th>
                  <th scope="col">Role</th>
                  <th scope="col">Dept ID</th>
                  <th scope="col">Active</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.email}</td>
                    <td>{u.full_name}</td>
                    <td>{u.role}</td>
                    <td className="text-muted">{u.department_id ?? '—'}</td>
                    <td>
                      <span style={{ color: u.is_active ? 'var(--color-success)' : 'var(--color-error)' }}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-outline"
                        style={{ fontSize: 12, padding: '2px 10px' }}
                        onClick={() => handleToggleActive(u)}
                      >
                        {u.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div>
        <div className="section-label">Create User</div>
        <div className="card" style={{ padding: 20 }}>
          <form
            onSubmit={handleCreate}
            style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 480 }}
          >
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
              Email
              <input
                type="email" className="form-input" value={email}
                onChange={(e) => setEmail(e.target.value)} required placeholder="user@example.com"
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
              Password
              <input
                type="password" className="form-input" value={password}
                onChange={(e) => setPassword(e.target.value)} required placeholder="Min 8 characters"
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
              Full Name
              <input
                type="text" className="form-input" value={fullName}
                onChange={(e) => setFullName(e.target.value)} required placeholder="Jane Smith"
              />
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
              Role
              <select className="form-input" value={role} onChange={(e) => setRole(e.target.value as Role)}>
                <option value="requester">Requester</option>
                <option value="manager">Manager</option>
                <option value="finance">Finance</option>
                <option value="admin">Admin</option>
              </select>
            </label>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
              Department ID (optional)
              <input
                type="number" className="form-input" value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)} placeholder="e.g. 1"
              />
            </label>
            {createError && <div className="alert alert-error" role="alert">{createError}</div>}
            <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
              Create User
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

// ── Rules panel ───────────────────────────────────────────────────────────────

function RulesPanel() {
  const [rules, setRules] = useState<ApprovalRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createError, setCreateError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const [name, setName] = useState('')
  const [minAmount, setMinAmount] = useState('')
  const [maxAmount, setMaxAmount] = useState('')
  const [category, setCategory] = useState('')
  const [requiredRole, setRequiredRole] = useState<ApprovalRuleCreate['required_role']>('manager')
  const [priority, setPriority] = useState('1')

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    listRules()
      .then(setRules)
      .catch(() => setError('Failed to load approval rules.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreateError(null)
    setSubmitting(true)
    const body: ApprovalRuleCreate = {
      name,
      min_amount: Number(minAmount),
      ...(maxAmount ? { max_amount: Number(maxAmount) } : {}),
      ...(category ? { category } : {}),
      required_role: requiredRole,
      priority: Number(priority),
    }
    try {
      await createRule(body)
      toast.success('Approval rule created')
      setName('')
      setMinAmount('')
      setMaxAmount('')
      setCategory('')
      setRequiredRole('manager')
      setPriority('1')
      load()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      toast.error(msg ?? 'Failed to create rule.')
      setCreateError(msg ?? 'Failed to create rule.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> Loading rules…
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <div className="alert alert-error" role="alert">{error}</div>
        <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={load}>Retry</button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <div className="section-label">Approval Rules</div>
        {rules.length === 0 ? (
          <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginTop: 8 }}>No rules configured yet.</p>
        ) : (
          <div className="card card-table">
            <div className="table-wrap">
              <table aria-label="Approval rules">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Min ($)</th>
                    <th scope="col">Max ($)</th>
                    <th scope="col">Category</th>
                    <th scope="col">Required Role</th>
                    <th scope="col">Priority</th>
                    <th scope="col">Active</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((r) => (
                    <tr key={r.id}>
                      <td>{r.name}</td>
                      <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                        {r.min_amount.toLocaleString()}
                      </td>
                      <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                        {r.max_amount != null ? r.max_amount.toLocaleString() : '—'}
                      </td>
                      <td className="text-muted">{r.category ?? '—'}</td>
                      <td>{r.required_role}</td>
                      <td>{r.priority}</td>
                      <td>
                        <span style={{ color: r.is_active ? 'var(--color-success)' : 'var(--color-error)' }}>
                          {r.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <div>
        <div className="section-label">New Rule</div>
        <div className="card" style={{ padding: 20 }}>
          <form
            onSubmit={handleCreate}
            style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 520 }}
          >
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
              Rule Name
              <input
                type="text" className="form-input" value={name}
                onChange={(e) => setName(e.target.value)} required
                placeholder="e.g. High-value IT purchases"
              />
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                Min Amount ($)
                <input
                  type="number" className="form-input" value={minAmount}
                  onChange={(e) => setMinAmount(e.target.value)} required min="0" step="0.01" placeholder="0"
                />
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                Max Amount (optional)
                <input
                  type="number" className="form-input" value={maxAmount}
                  onChange={(e) => setMaxAmount(e.target.value)} min="0" step="0.01" placeholder="No limit"
                />
              </label>
            </div>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
              Category (optional)
              <input
                type="text" className="form-input" value={category}
                onChange={(e) => setCategory(e.target.value)} placeholder="e.g. IT, Marketing"
              />
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                Required Role
                <select
                  className="form-input" value={requiredRole}
                  onChange={(e) => setRequiredRole(e.target.value as typeof requiredRole)}
                >
                  <option value="manager">Manager</option>
                  <option value="finance">Finance</option>
                  <option value="admin">Admin</option>
                </select>
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
                Priority
                <input
                  type="number" className="form-input" value={priority}
                  onChange={(e) => setPriority(e.target.value)} required min="1" step="1" placeholder="1"
                />
              </label>
            </div>
            {createError && <div className="alert alert-error" role="alert">{createError}</div>}
            <button
              type="submit" className="btn btn-primary"
              style={{ alignSelf: 'flex-start' }}
              disabled={submitting} aria-busy={submitting}
            >
              {submitting ? 'Creating…' : 'Create Rule'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

// ── Analytics panel ───────────────────────────────────────────────────────────

function AnalyticsPanel() {
  const [spend, setSpend] = useState<SpendGroup[]>([])
  const [categories, setCategories] = useState<CategorySummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([getSpendByCategory(), getCategorySummaries()])
      .then(([s, c]) => { setSpend(s); setCategories(c) })
      .catch(() => setError('Failed to load analytics data.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="loading-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> Loading analytics…
      </div>
    )
  }

  if (error) {
    return <div className="alert alert-error" role="alert">{error}</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="card">
        <div className="card-header">
          <span className="card-title">Total Spend by Category</span>
        </div>
        <div className="card-body">
          {spend.length === 0 ? (
            <p style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>No spend data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={spend} layout="vertical" margin={{ left: 16, right: 24, top: 4, bottom: 4 }}>
                <XAxis
                  type="number" tick={{ fontSize: 11 }}
                  tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                />
                <YAxis dataKey="category" type="category" tick={{ fontSize: 12 }} width={84} />
                <Tooltip
                  formatter={(v) => [`$${Number(v).toLocaleString()}`, 'Total Spend']}
                  contentStyle={{ fontSize: 12 }}
                />
                <Bar dataKey="total_spend" radius={[0, 4, 4, 0]}>
                  {spend.map((_item, i) => (
                    <Cell key={i} fill={SPEND_COLORS[i % SPEND_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">Request Volume by Category</span>
        </div>
        <div className="card-body">
          {categories.length === 0 ? (
            <p style={{ fontSize: 13, color: 'var(--color-text-muted)' }}>No data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={categories} layout="vertical" margin={{ left: 16, right: 24, top: 4, bottom: 4 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                <YAxis dataKey="category" type="category" tick={{ fontSize: 12 }} width={84} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="approved_count" name="Approved" fill="#0f766e" stackId="a" />
                <Bar dataKey="rejected_count" name="Rejected" fill="#dc2626" stackId="a" />
                <Bar
                  dataKey="pending_count" name="Pending" fill="#d97706"
                  stackId="a" radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}

// ── AdminPage ─────────────────────────────────────────────────────────────────

const TAB_LABELS: Record<Tab, string> = {
  users: 'Users',
  rules: 'Approval Rules',
  analytics: 'Analytics',
}

export function AdminPage() {
  const [tab, setTab] = useState<Tab>('users')

  return (
    <div className="workbench-shell">
      <div className="workbench-header">
        <div className="workbench-header-left">
          <div className="workbench-context">
            <span className="workbench-context-mark" aria-hidden="true" />
            <span className="workbench-context-label">Admin</span>
          </div>
          <h2 className="page-title">Administration</h2>
          <p className="page-subtitle">Manage users, approval rules, and analytics</p>
        </div>
      </div>

      <div
        role="tablist"
        aria-label="Admin sections"
        style={{
          display: 'flex',
          gap: 0,
          marginBottom: 20,
          borderBottom: '1px solid var(--color-border)',
        }}
      >
        {(Object.keys(TAB_LABELS) as Tab[]).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            aria-controls={`admin-panel-${t}`}
            id={`admin-tab-${t}`}
            onClick={() => setTab(t)}
            style={{
              background: 'transparent',
              border: 'none',
              borderBottom: tab === t ? '2px solid var(--color-primary)' : '2px solid transparent',
              padding: '8px 18px',
              fontSize: 13,
              fontWeight: tab === t ? 600 : 400,
              color: tab === t ? 'var(--color-primary)' : 'var(--color-text-muted)',
              cursor: 'pointer',
              transition: 'color 0.15s, border-color 0.15s',
              marginBottom: -1,
            }}
          >
            {TAB_LABELS[t]}
          </button>
        ))}
      </div>

      <div role="tabpanel" id={`admin-panel-${tab}`} aria-labelledby={`admin-tab-${tab}`}>
        {tab === 'users' && <UsersPanel />}
        {tab === 'rules' && <RulesPanel />}
        {tab === 'analytics' && <AnalyticsPanel />}
      </div>
    </div>
  )
}
