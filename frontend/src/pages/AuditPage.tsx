import { useEffect, useState } from 'react'
import { listAuditLogs } from '../api/audit'
import type { AuditLog } from '../types'

export function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    listAuditLogs()
      .then(setLogs)
      .catch(() => setError('Failed to load audit log.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="loading-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> Loading audit log…
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
          <h2 className="page-title">Audit Log</h2>
          <p className="page-subtitle">Last 100 system-wide status change events</p>
        </div>
      </div>

      <div className="section-label">Events</div>

      <div className="card card-table">
        {logs.length === 0 ? (
          <div className="empty-state">
            <p>No audit entries found.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table aria-label="Audit log">
              <thead>
                <tr>
                  <th scope="col">Time</th>
                  <th scope="col">Action</th>
                  <th scope="col">Actor ID</th>
                  <th scope="col">Status Change</th>
                  <th scope="col">Note</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="text-muted text-sm">{new Date(log.created_at).toLocaleString()}</td>
                    <td>{log.action}</td>
                    <td className="text-muted">{log.actor_id ?? '—'}</td>
                    <td className="text-sm">{log.old_status ?? '—'} → {log.new_status ?? '—'}</td>
                    <td className="text-muted text-sm">{log.note ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
