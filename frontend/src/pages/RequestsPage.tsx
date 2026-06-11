import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { listRequests } from '../api/requests'
import { StatusBadge } from '../components/StatusBadge'
import type { RequestStatus, RequestSummary, Urgency } from '../types'
import '../components/StatusBadge.css'

const PAGE_SIZE = 20

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const STATUS_OPTIONS: Array<{ value: RequestStatus | ''; label: string }> = [
  { value: '', label: 'All statuses' },
  { value: 'draft', label: 'Draft' },
  { value: 'pending_review', label: 'Pending Review' },
  { value: 'pending_approval', label: 'Pending Approval' },
  { value: 'needs_rule', label: 'Needs Rule' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'needs_more_info', label: 'Needs Info' },
]

const URGENCY_OPTIONS: Array<{ value: Urgency | ''; label: string }> = [
  { value: '', label: 'All urgencies' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
]

function deriveCategories(requests: RequestSummary[]): string[] {
  const seen = new Set<string>()
  for (const r of requests) {
    if (r.category) seen.add(r.category)
  }
  return Array.from(seen).sort()
}

export function RequestsPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [all, setAll] = useState<RequestSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const statusFilter = searchParams.get('status') ?? ''
  const urgencyFilter = searchParams.get('urgency') ?? ''
  const categoryFilter = searchParams.get('category') ?? ''
  const searchFilter = searchParams.get('q') ?? ''
  const page = Math.max(1, parseInt(searchParams.get('page') ?? '1', 10))

  function setParam(key: string, value: string) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (value) {
        next.set(key, value)
      } else {
        next.delete(key)
      }
      next.delete('page')
      return next
    })
  }

  function setPage(p: number) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (p === 1) {
        next.delete('page')
      } else {
        next.set('page', String(p))
      }
      return next
    })
  }

  function load() {
    setLoading(true)
    setError(null)
    listRequests()
      .then(setAll)
      .catch(() => setError('Failed to load requests.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const categories = deriveCategories(all)

  const filtered = all.filter((r) => {
    if (statusFilter && r.status !== statusFilter) return false
    if (urgencyFilter && r.urgency !== urgencyFilter) return false
    if (categoryFilter && r.category !== categoryFilter) return false
    if (searchFilter) {
      const q = searchFilter.toLowerCase()
      if (!r.title.toLowerCase().includes(q) && !r.category.toLowerCase().includes(q)) return false
    }
    return true
  })

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages)
  const pageStart = (currentPage - 1) * PAGE_SIZE
  const pageItems = filtered.slice(pageStart, pageStart + PAGE_SIZE)

  if (loading) {
    return (
      <div className="loading-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> Loading requests…
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
    <div className="workbench-shell">
      <div className="workbench-header">
        <div className="workbench-header-left">
          <div className="workbench-context">
            <span className="workbench-context-mark" aria-hidden="true" />
            <span className="workbench-context-label">Procurement</span>
          </div>
          <h2 className="page-title">Purchase Requests</h2>
          <p className="page-subtitle">
            {filtered.length} request{filtered.length !== 1 ? 's' : ''}{all.length !== filtered.length ? ` of ${all.length}` : ''}
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/requests/new')}>
          + New Request
        </button>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="search"
          className="form-input"
          placeholder="Search by title or category…"
          value={searchFilter}
          onChange={(e) => setParam('q', e.target.value)}
          style={{ maxWidth: 220 }}
          aria-label="Search requests"
        />
        <select
          className="form-select"
          value={statusFilter}
          onChange={(e) => setParam('status', e.target.value)}
          style={{ maxWidth: 160 }}
          aria-label="Filter by status"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select
          className="form-select"
          value={urgencyFilter}
          onChange={(e) => setParam('urgency', e.target.value)}
          style={{ maxWidth: 148 }}
          aria-label="Filter by urgency"
        >
          {URGENCY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        {categories.length > 0 && (
          <select
            className="form-select"
            value={categoryFilter}
            onChange={(e) => setParam('category', e.target.value)}
            style={{ maxWidth: 160 }}
            aria-label="Filter by category"
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        )}
        {(statusFilter || urgencyFilter || categoryFilter || searchFilter) && (
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => setSearchParams({})}
          >
            Clear filters
          </button>
        )}
      </div>

      <div className="card card-table">
        {pageItems.length === 0 ? (
          <div className="empty-state">
            <p>{all.length === 0 ? 'No requests yet.' : 'No requests match the current filters.'}</p>
            {all.length === 0 && (
              <button className="btn btn-primary" onClick={() => navigate('/requests/new')}>
                Create your first request
              </button>
            )}
          </div>
        ) : (
          <div className="table-wrap">
            <table aria-label="Purchase requests">
              <thead>
                <tr>
                  <th scope="col">Title</th>
                  <th scope="col">Category</th>
                  <th scope="col">Urgency</th>
                  <th scope="col">Amount</th>
                  <th scope="col">Status</th>
                  <th scope="col">Submitted</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((req) => (
                  <tr
                    key={req.id}
                    onClick={() => navigate(`/requests/${req.id}`)}
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        navigate(`/requests/${req.id}`)
                      }
                    }}
                    aria-label={`View request: ${req.title}`}
                  >
                    <td>
                      <span className="truncate" style={{ display: 'block', maxWidth: 280 }}>
                        {req.title}
                      </span>
                    </td>
                    <td className="text-muted">{req.category}</td>
                    <td>
                      <span className={`urgency-pill urgency-${req.urgency}`}>
                        {req.urgency}
                      </span>
                    </td>
                    <td style={{ fontVariantNumeric: 'tabular-nums' }}>
                      {formatCurrency(req.estimated_cost)}
                    </td>
                    <td><StatusBadge status={req.status} /></td>
                    <td className="text-muted text-sm">{formatDate(req.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {totalPages > 1 && (
        <div
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12, fontSize: 13 }}
          role="navigation"
          aria-label="Pagination"
        >
          <span style={{ color: 'var(--color-text-muted)' }}>
            {pageStart + 1}–{Math.min(pageStart + PAGE_SIZE, filtered.length)} of {filtered.length}
          </span>
          <div style={{ display: 'flex', gap: 4 }}>
            <button
              className="btn btn-outline btn-sm"
              disabled={currentPage === 1}
              onClick={() => setPage(currentPage - 1)}
              aria-label="Previous page"
            >
              ←
            </button>
            {Array.from({ length: totalPages }, (_, i) => i + 1)
              .filter((p) => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1)
              .reduce<Array<number | '…'>>((acc, p, idx, arr) => {
                if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push('…')
                acc.push(p)
                return acc
              }, [])
              .map((p, idx) =>
                p === '…' ? (
                  <span key={`ellipsis-${idx}`} style={{ padding: '5px 6px', color: 'var(--color-text-muted)' }}>…</span>
                ) : (
                  <button
                    key={p}
                    className={`btn btn-sm ${currentPage === p ? 'btn-primary' : 'btn-outline'}`}
                    onClick={() => setPage(p as number)}
                    aria-label={`Page ${p}`}
                    aria-current={currentPage === p ? 'page' : undefined}
                  >
                    {p}
                  </button>
                )
              )}
            <button
              className="btn btn-outline btn-sm"
              disabled={currentPage === totalPages}
              onClick={() => setPage(currentPage + 1)}
              aria-label="Next page"
            >
              →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
