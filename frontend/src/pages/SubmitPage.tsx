import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createRequest, submitRequest } from '../api/requests'
import type { RequestCreate, Urgency } from '../types'

const CATEGORIES = ['IT Equipment', 'Software', 'Office Supplies', 'Marketing', 'Facilities', 'HR', 'Operations', 'Other']

export function SubmitPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<RequestCreate>({
    title: '',
    description: '',
    category: '',
    urgency: 'medium',
    quantity: 1,
    estimated_cost: 0,
    justification: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function update<K extends keyof RequestCreate>(key: K, value: RequestCreate[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent, andSubmit: boolean) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const created = await createRequest(form)
      if (andSubmit) {
        await submitRequest(created.id)
      }
      navigate('/dashboard')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr?.response?.data?.detail ?? 'Failed to create request.')
    } finally {
      setLoading(false)
    }
  }

  const isValid =
    form.title.length >= 3 &&
    form.description.length >= 10 &&
    form.category.length >= 2 &&
    form.quantity > 0 &&
    form.estimated_cost > 0 &&
    form.justification.length >= 10

  return (
    <div style={{ maxWidth: 680 }}>
      <div className="page-header">
        <div>
          <h2 className="page-title">New Purchase Request</h2>
          <p className="page-subtitle">Fill in the details below. All fields required unless noted.</p>
        </div>
      </div>

      <form noValidate aria-label="New purchase request form" onSubmit={(e) => handleSubmit(e, true)}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Request Details</span>
          </div>
          <div className="card-body stack">
            {error && <div className="alert alert-error" role="alert" aria-live="polite">{error}</div>}

            <div className="form-group">
              <label htmlFor="title" className="form-label">Title</label>
              <input
                id="title"
                type="text"
                className="form-input"
                value={form.title}
                onChange={(e) => update('title', e.target.value)}
                placeholder="e.g. 10 MacBook Pro 14&quot; for Engineering"
                minLength={3}
                maxLength={500}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="description" className="form-label">Description</label>
              <textarea
                id="description"
                className="form-textarea"
                rows={3}
                value={form.description}
                onChange={(e) => update('description', e.target.value)}
                placeholder="Describe what you need and why…"
                minLength={10}
                required
              />
              <span className="form-hint">{form.description.length} chars (min 10)</span>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label htmlFor="category" className="form-label">Category</label>
                <select
                  id="category"
                  className="form-select"
                  value={form.category}
                  onChange={(e) => update('category', e.target.value)}
                  required
                >
                  <option value="">Select category</option>
                  {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="urgency" className="form-label">Urgency</label>
                <select
                  id="urgency"
                  className="form-select"
                  value={form.urgency}
                  onChange={(e) => update('urgency', e.target.value as Urgency)}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="quantity" className="form-label">Quantity</label>
                <input
                  id="quantity"
                  type="number"
                  className="form-input"
                  value={form.quantity}
                  onChange={(e) => update('quantity', parseInt(e.target.value, 10) || 1)}
                  min={1}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="estimated_cost" className="form-label">Estimated Cost (USD)</label>
                <input
                  id="estimated_cost"
                  type="number"
                  className="form-input"
                  value={form.estimated_cost || ''}
                  onChange={(e) => update('estimated_cost', parseFloat(e.target.value) || 0)}
                  min={0.01}
                  step={0.01}
                  placeholder="0.00"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="justification" className="form-label">Business Justification</label>
              <textarea
                id="justification"
                className="form-textarea"
                rows={3}
                value={form.justification}
                onChange={(e) => update('justification', e.target.value)}
                placeholder="Explain the business need and expected impact…"
                minLength={10}
                required
              />
              <span className="form-hint">{form.justification.length} chars (min 10)</span>
            </div>
          </div>
        </div>

        <div className="row" style={{ marginTop: 16, gap: 10 }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => navigate('/dashboard')}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-outline"
            onClick={(e) => handleSubmit(e, false)}
            disabled={!isValid || loading}
            aria-busy={loading}
          >
            Save as Draft
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            onClick={(e) => handleSubmit(e, true)}
            disabled={!isValid || loading}
            aria-busy={loading}
          >
            {loading ? <><span className="spinner" aria-hidden="true" /> Submitting…</> : 'Submit for Review'}
          </button>
        </div>
      </form>
    </div>
  )
}
