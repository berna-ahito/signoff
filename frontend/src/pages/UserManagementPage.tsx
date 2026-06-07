import { useEffect, useState } from 'react'
import { createUser, listUsers, updateUser } from '../api/users'
import type { Role, User, UserCreate } from '../types'

export function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createError, setCreateError] = useState<string | null>(null)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState<Role>('requester')
  const [departmentId, setDepartmentId] = useState('')

  function load() {
    setLoading(true)
    setError(null)
    listUsers()
      .then(setUsers)
      .catch(() => setError('Failed to load users.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function handleToggleActive(user: User) {
    try {
      await updateUser(user.id, { is_active: !user.is_active })
      load()
    } catch {
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
      setEmail('')
      setPassword('')
      setFullName('')
      setRole('requester')
      setDepartmentId('')
      load()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
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
        <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={load}>
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="workbench-shell">
      <div className="workbench-header">
        <div className="workbench-header-left">
          <div className="workbench-context">
            <span className="workbench-context-mark" aria-hidden="true" />
            <span className="workbench-context-label">Admin</span>
          </div>
          <h2 className="page-title">User Management</h2>
          <p className="page-subtitle">Manage user accounts and roles</p>
        </div>
      </div>

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

      <div className="section-label" style={{ marginTop: 24 }}>Create User</div>

      <div className="card" style={{ padding: 20 }}>
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 12, maxWidth: 480 }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
            Email
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="user@example.com"
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
            Password
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Min 8 characters"
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
            Full Name
            <input
              type="text"
              className="form-input"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              placeholder="Jane Smith"
            />
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
            Role
            <select
              className="form-input"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
            >
              <option value="requester">Requester</option>
              <option value="manager">Manager</option>
              <option value="finance">Finance</option>
              <option value="admin">Admin</option>
            </select>
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13 }}>
            Department ID (optional)
            <input
              type="number"
              className="form-input"
              value={departmentId}
              onChange={(e) => setDepartmentId(e.target.value)}
              placeholder="e.g. 1"
            />
          </label>
          {createError && (
            <div className="alert alert-error" role="alert">{createError}</div>
          )}
          <button type="submit" className="btn btn-primary" style={{ alignSelf: 'flex-start' }}>
            Create User
          </button>
        </form>
      </div>
    </div>
  )
}
