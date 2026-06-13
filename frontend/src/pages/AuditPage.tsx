import { useEffect, useState } from 'react'
import { listAuditLogs } from '../api/audit'
import type { AuditLog } from '../types'

function formatStatus(s: string | null | undefined): string {
  if (!s) return '—'
  return s.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
}

function formatStatusChange(from: string | null | undefined, to: string | null | undefined): string {
  if (!from && !to) return '—'
  return `${formatStatus(from)} → ${formatStatus(to)}`
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function formatTime(ts: string): string {
  return new Date(ts).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

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

      <div className="audit-table-wrap">
        {logs.length === 0 ? (
          <div className="empty-state">
            <p>No audit entries found.</p>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="audit-table" aria-label="Audit log">
              <thead>
                <tr>
                  <th scope="col">Time</th>
                  <th scope="col">Action</th>
                  <th scope="col">By</th>
                  <th scope="col">Status Change</th>
                  <th scope="col">Note</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td className="audit-time">{formatTime(log.created_at)}</td>
                    <td>{capitalize(log.action)}</td>
                    <td className="text-muted">
                      {log.actor_id != null ? `User #${log.actor_id}` : 'System'}
                    </td>
                    <td>{formatStatusChange(log.old_status, log.new_status)}</td>
                    <td className="audit-note">{log.note ?? '—'}</td>
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
