import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FilePlus } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { listRequests } from '../api/requests'
import { getSpendByCategory } from '../api/analytics'
import { StatusBadge } from '../components/StatusBadge'
import type { RequestSummary, Role, SpendGroup } from '../types'
import '../components/StatusBadge.css'

interface Props {
  role: Role | null
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(amount)
}

function hasMetricValue(value: number | null | undefined) {
  return typeof value === 'number' && value > 0
}

function formatMetricValue(value: number | null | undefined, formatter: (value: number) => string = String) {
  return typeof value === 'number' && value > 0 ? formatter(value) : '—'
}

function metricValueClass(value: number | null | undefined) {
  return hasMetricValue(value) ? 'stat-value' : 'stat-value stat-value-empty'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const CHART_COLORS = ['#14B8A6', '#2F81F7', '#3FB950', '#D29922', '#F85149', '#8B949E']

const ROLE_LABEL: Record<Role, string> = {
  requester: 'Requester',
  manager: 'Manager',
  finance: 'Finance',
  admin: 'Admin',
}

function getGreetingPrefix() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour <= 17) return 'Good afternoon'
  return 'Good evening'
}

interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{ value: number }>
  label?: string
}

function SpendTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius)',
      padding: '8px 12px',
      fontSize: 12,
      boxShadow: 'var(--shadow)',
    }}>
      <div style={{ fontWeight: 600, color: 'var(--color-text)', marginBottom: 2 }}>{label}</div>
      <div style={{ color: 'var(--color-primary)' }}>{formatCurrency(payload[0].value)}</div>
    </div>
  )
}

export function DashboardPage({ role }: Props) {
  const navigate = useNavigate()
  const [requests, setRequests] = useState<RequestSummary[]>([])
  const [spendData, setSpendData] = useState<SpendGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    Promise.all([listRequests(), getSpendByCategory().catch(() => [])])
      .then(([reqs, spend]) => {
        setRequests(reqs)
        setSpendData(spend)
      })
      .catch(() => setError('Failed to load dashboard data.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="loading-state" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" /> Loading dashboard…
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

  const pendingCount = requests.filter((r) => r.status === 'pending_approval').length
  const approvedCount = requests.filter((r) => r.status === 'approved').length
  const totalValue = requests.reduce((sum, r) => sum + (r.estimated_cost ?? 0), 0)
  const draftCount = requests.filter((r) => r.status === 'draft').length
  const rejectedCount = requests.filter((r) => r.status === 'rejected').length
  const recentRequests = [...requests].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ).slice(0, 8)
  const displayName = role ? ROLE_LABEL[role] : 'Guest'
  const greeting = `${getGreetingPrefix()}, ${displayName}`

  return (
    <div className="workbench-shell">
      <div className="workbench-header">
        <div className="workbench-header-left">
          <div className="workbench-context">
            <span className="workbench-context-mark" aria-hidden="true" />
            <span className="workbench-context-label">Procurement Operations</span>
          </div>
          <h2 className="page-title">{greeting}</h2>
          <p className="page-subtitle">Overview of all procurement activity</p>
        </div>
        {role === 'requester' && (
          <button className="btn btn-primary" onClick={() => navigate('/requests/new')} aria-label="Create new purchase request">
            + New Request
          </button>
        )}
      </div>

      <div className="approval-flow-cue" aria-hidden="true" title="Standard Approval Workflow">
        <div className="flow-step">Submitted</div>
        <div className="flow-arrow">→</div>
        <div className="flow-step flow-ai">AI Reviewed</div>
        <div className="flow-arrow">→</div>
        <div className="flow-step">Manager</div>
        <div className="flow-arrow">→</div>
        <div className="flow-step">Finance</div>
        <div className="flow-arrow">→</div>
        <div className="flow-step flow-audit">Audit Logged</div>
      </div>

      <div className="stats-bar" aria-label="Summary statistics">
        <div className="stat-card">
          <div className="stat-label">Total Requests</div>
          <div className={metricValueClass(requests.length)}>{formatMetricValue(requests.length)}</div>
          <div className="stat-subtext">{draftCount > 0 ? `${draftCount} in draft` : 'all submitted'}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Awaiting Decision</div>
          <div className={metricValueClass(pendingCount)}>{formatMetricValue(pendingCount)}</div>
          <div className="stat-subtext">pending approval</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Approved</div>
          <div className={metricValueClass(approvedCount)}>{formatMetricValue(approvedCount)}</div>
          <div className="stat-subtext">{rejectedCount > 0 ? `${rejectedCount} rejected` : 'no rejections'}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pipeline Value</div>
          <div className={metricValueClass(totalValue)}>{formatMetricValue(totalValue, formatCurrency)}</div>
          <div className="stat-subtext">estimated spend</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: spendData.length > 0 ? '1fr 340px' : '1fr', gap: 16, marginBottom: 20 }}>
        <div className="card card-table">
          <div className="card-header">
            <span className="card-title">Recent Activity</span>
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => navigate('/requests')}
              style={{ fontSize: 12 }}
            >
              View all →
            </button>
          </div>
          {recentRequests.length === 0 ? (
            <div className="dashboard-empty-state">
              <FilePlus className="dashboard-empty-icon" size={34} strokeWidth={1.7} aria-hidden="true" />
              <h3 className="dashboard-empty-title">No requests yet</h3>
              <p className="dashboard-empty-description">
                Purchase requests submitted by your team will appear here.
              </p>
              <button className="btn btn-primary dashboard-empty-cta" onClick={() => navigate('/requests/new')}>
                + New Request
              </button>
            </div>
          ) : (
            <div className="table-wrap">
              <table aria-label="Recent purchase requests">
                <thead>
                  <tr>
                    <th scope="col">Title</th>
                    <th scope="col">Category</th>
                    <th scope="col">Amount</th>
                    <th scope="col">Status</th>
                    <th scope="col">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {recentRequests.map((req) => (
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
                        <span className="truncate" style={{ display: 'block', maxWidth: 220 }}>
                          {req.title}
                        </span>
                      </td>
                      <td className="text-muted">{req.category}</td>
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

        {spendData.length > 0 && (
          <div className="card">
            <div className="card-header">
              <span className="card-title">Approved Spend by Category</span>
            </div>
            <div className="card-body" style={{ paddingTop: 8 }}>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={spendData}
                  layout="vertical"
                  margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
                >
                  <XAxis
                    type="number"
                    tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                    tick={{ fontSize: 10, fill: 'var(--color-text-subtle)' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="group"
                    width={80}
                    tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<SpendTooltip />} cursor={{ fill: 'rgba(15,118,110,0.06)' }} />
                  <Bar dataKey="total_estimated_cost" radius={[0, 3, 3, 0]}>
                    {spendData.map((_, idx) => (
                      <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
