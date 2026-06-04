import { useState } from 'react'
import { decide } from '../api/approvals'
import type { Decision, RequestDetail, Role } from '../types'

interface Props {
  request: RequestDetail
  role: Role | null
  onDecision: () => void
}

export function ApprovalActions({ request, role, onDecision }: Props) {
  const [decision, setDecision] = useState<Decision | null>(null)
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canDecide =
    request.status === 'pending_approval' &&
    (role === 'admin' || role === request.assigned_role)

  if (!canDecide) return null

  async function submit() {
    if (!decision) return
    setLoading(true)
    setError(null)
    try {
      await decide(request.id, { decision, note: note || undefined })
      onDecision()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to submit decision'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card" aria-labelledby="approval-actions-heading">
      <div className="card-header">
        <h2 className="card-title" id="approval-actions-heading">Approval Decision</h2>
      </div>
      <div className="card-body stack">
        {error && <div className="alert alert-error" role="alert">{error}</div>}

        <fieldset style={{ border: 'none' }}>
          <legend className="form-label" style={{ marginBottom: 8 }}>Decision</legend>
          <div className="row" role="group" aria-label="Decision options">
            {(['approved', 'rejected', 'needs_more_info'] as Decision[]).map((d) => (
              <label key={d} className={`decision-option ${decision === d ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="decision"
                  value={d}
                  checked={decision === d}
                  onChange={() => setDecision(d)}
                  className="sr-only"
                />
                {d === 'approved' ? 'Approve' : d === 'rejected' ? 'Reject' : 'Need More Info'}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="form-group">
          <label htmlFor="approval-note" className="form-label">
            Note <span className="text-muted">(optional)</span>
          </label>
          <textarea
            id="approval-note"
            className="form-textarea"
            rows={3}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Add a note for this decision…"
          />
        </div>

        <div className="row">
          <button
            className={`btn ${decision === 'approved' ? 'btn-primary' : decision === 'rejected' ? 'btn-danger' : 'btn-outline'}`}
            onClick={submit}
            disabled={!decision || loading}
            aria-busy={loading}
          >
            {loading ? <><span className="spinner" aria-hidden="true" /> Submitting…</> : 'Submit Decision'}
          </button>
        </div>
      </div>
    </section>
  )
}
