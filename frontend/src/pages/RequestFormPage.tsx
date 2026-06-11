import { useState, useEffect, useRef } from 'react'
import { toast } from 'sonner'
import type { DragEvent, ChangeEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { motion } from 'motion/react'
import type { Variants } from 'motion/react'
import { createRequest, getRequest, updateRequest, submitRequest } from '../api/requests'
import { listAttachments, uploadAttachment } from '../api/attachments'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog'
import type { Attachment, Urgency } from '../types'

const CONTAINER: Variants = { hidden: {}, show: { transition: { staggerChildren: 0.08 } } }
const CARD: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.28, ease: 'easeOut' } },
}

const CATEGORIES = ['IT', 'Office Supplies', 'Facilities', 'Marketing', 'HR', 'Legal', 'Other']
const URGENCY_OPTIONS: { value: Urgency; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
]

type FileEntry = { id: number; name: string; status: 'uploading' | 'done' | 'error'; error?: string }

interface FormValues {
  title: string
  description: string
  category: string
  urgency: Urgency
  quantity: string
  estimated_cost: string
  justification: string
}

const DEFAULT_FORM: FormValues = {
  title: '',
  description: '',
  category: CATEGORIES[0],
  urgency: 'medium',
  quantity: '1',
  estimated_cost: '',
  justification: '',
}

export function RequestFormPage() {
  const { id } = useParams<{ id: string }>()
  const requestId = id ? parseInt(id, 10) : null
  const isEdit = requestId !== null
  const navigate = useNavigate()

  const [form, setForm] = useState<FormValues>(DEFAULT_FORM)
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [fileEntries, setFileEntries] = useState<FileEntry[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [isLoading, setIsLoading] = useState(isEdit)
  const [isSaving, setIsSaving] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const entryCounterRef = useRef(0)

  useEffect(() => {
    if (!requestId) return
    setIsLoading(true)
    Promise.all([getRequest(requestId), listAttachments(requestId)])
      .then(([req, atts]) => {
        setForm({
          title: req.title,
          description: req.description,
          category: req.category,
          urgency: req.urgency,
          quantity: String(req.quantity),
          estimated_cost: String(req.estimated_cost),
          justification: req.justification,
        })
        setAttachments(atts)
      })
      .catch(() => setError('Failed to load request.'))
      .finally(() => setIsLoading(false))
  }, [requestId])

  function setField<K extends keyof FormValues>(key: K, value: FormValues[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function buildPayload() {
    return {
      title: form.title.trim(),
      description: form.description.trim(),
      category: form.category,
      urgency: form.urgency,
      quantity: parseInt(form.quantity, 10),
      estimated_cost: parseFloat(form.estimated_cost),
      justification: form.justification.trim(),
    }
  }

  function validate(): string | null {
    const p = buildPayload()
    if (!p.title) return 'Title is required.'
    if (!p.description) return 'Description is required.'
    if (!p.justification) return 'Justification is required.'
    if (isNaN(p.quantity) || p.quantity < 1) return 'Quantity must be at least 1.'
    if (isNaN(p.estimated_cost) || p.estimated_cost <= 0) return 'Estimated cost must be positive.'
    return null
  }

  function validateDraft(): string | null {
    if (!form.title.trim()) return 'Title is required.'
    return null
  }

  async function handleSaveDraft() {
    const err = validateDraft()
    if (err) { setError(err); return }
    setIsSaving(true)
    setError(null)
    try {
      const payload = buildPayload()
      if (isEdit && requestId) {
        await updateRequest(requestId, payload)
        toast.success('Draft saved')
      } else {
        const created = await createRequest(payload)
        toast.success('Draft saved')
        navigate(`/requests/${created.id}/edit`, { replace: true })
      }
    } catch {
      toast.error('Failed to save draft.')
      setError('Failed to save draft.')
    } finally {
      setIsSaving(false)
    }
  }

  async function handleSubmit() {
    const err = validate()
    if (err) { setError(err); setConfirmOpen(false); return }
    setIsSubmitting(true)
    setError(null)
    try {
      const payload = buildPayload()
      let rid = requestId
      if (!rid) {
        const created = await createRequest(payload)
        rid = created.id
      } else {
        await updateRequest(rid, payload)
      }
      await submitRequest(rid)
      navigate(`/requests/${rid}`)
    } catch {
      toast.error('Failed to submit request.')
      setError('Failed to submit request.')
      setIsSubmitting(false)
    }
  }

  async function uploadFiles(files: File[]) {
    if (!requestId) return
    const MAX_SIZE = 5 * 1024 * 1024
    const MAX_FILES = 5
    const existing = attachments.length + fileEntries.filter((e) => e.status !== 'error').length
    if (existing + files.length > MAX_FILES) {
      setError('Maximum 5 files allowed.')
      return
    }
    const entries: FileEntry[] = files.map((f) => ({
      id: ++entryCounterRef.current,
      name: f.name,
      status: f.size > MAX_SIZE ? 'error' : 'uploading',
      error: f.size > MAX_SIZE ? 'Exceeds 5 MB limit.' : undefined,
    }))
    setFileEntries((prev) => [...prev, ...entries])

    for (let i = 0; i < entries.length; i++) {
      const entry = entries[i]
      if (entry.status === 'error') continue
      try {
        const att = await uploadAttachment(requestId, files[i])
        setAttachments((prev) => [...prev, att])
        setFileEntries((prev) =>
          prev.map((e) => (e.id === entry.id ? { ...e, status: 'done' } : e))
        )
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Upload failed.'
        setFileEntries((prev) =>
          prev.map((fe) => (fe.id === entry.id ? { ...fe, status: 'error', error: msg } : fe))
        )
      }
    }
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length) void uploadFiles(files)
  }

  function onFileInput(e: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    if (files.length) void uploadFiles(files)
    e.target.value = ''
  }

  if (isLoading) {
    return (
      <div className="loading-state">
        <div className="spinner" />
        <span>Loading request…</span>
      </div>
    )
  }

  return (
    <>
      <motion.div
        className="stack"
        style={{ gap: 24, maxWidth: 720, margin: '0 auto' }}
        variants={CONTAINER}
        initial="hidden"
        animate="show"
      >
        <motion.div variants={CARD}>
          <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 className="page-title">{isEdit ? 'Edit Request' : 'New Request'}</h1>
              <p className="page-subtitle">
                {isEdit
                  ? 'Update draft details and manage attachments.'
                  : 'Fill in the details to create a purchase request.'}
              </p>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate(-1)}>
              ← Back
            </button>
          </div>
        </motion.div>

        {error && (
          <motion.div variants={CARD} className="alert alert-error">
            {error}
          </motion.div>
        )}

        <motion.div variants={CARD} className="card">
          <div className="card-header">
            <h2 className="card-title">Request Details</h2>
          </div>
          <div className="card-body stack" style={{ gap: 20 }}>
            <div className="form-group">
              <label className="form-label">Title *</label>
              <input
                className="form-input"
                placeholder="e.g. 10 ergonomic chairs for dev team"
                value={form.title}
                onChange={(e) => setField('title', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Description *</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="Describe what you need and why"
                value={form.description}
                onChange={(e) => setField('description', e.target.value)}
              />
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Category</label>
                <select
                  className="form-select"
                  value={form.category}
                  onChange={(e) => setField('category', e.target.value)}
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Urgency</label>
                <select
                  className="form-select"
                  value={form.urgency}
                  onChange={(e) => setField('urgency', e.target.value as Urgency)}
                >
                  {URGENCY_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Quantity *</label>
                <input
                  className="form-input"
                  type="number"
                  min={1}
                  value={form.quantity}
                  onChange={(e) => setField('quantity', e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Estimated Cost (USD) *</label>
                <input
                  className="form-input"
                  type="number"
                  min={0}
                  step="0.01"
                  placeholder="0.00"
                  value={form.estimated_cost}
                  onChange={(e) => setField('estimated_cost', e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Justification *</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="Business justification for this purchase"
                value={form.justification}
                onChange={(e) => setField('justification', e.target.value)}
              />
            </div>
          </div>
        </motion.div>

        {isEdit && (
          <motion.div variants={CARD} className="card">
            <div className="card-header">
              <h2 className="card-title">Attachments</h2>
            </div>
            <div className="card-body stack" style={{ gap: 16 }}>
              <div
                className={`file-dropzone${isDragging ? ' file-dropzone--active' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={onDrop}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
                aria-label="Upload attachments"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  style={{ display: 'none' }}
                  onChange={onFileInput}
                />
                <span className="file-dropzone__icon">↑</span>
                <span className="file-dropzone__primary">
                  {isDragging ? 'Drop files here' : 'Drag & drop or click to browse'}
                </span>
                <span className="file-dropzone__hint">Max 5 MB per file · Max 5 files total</span>
              </div>

              {(attachments.length > 0 || fileEntries.length > 0) && (
                <ul className="attachment-list">
                  {attachments.map((att) => (
                    <li key={att.id} className="attachment-item attachment-item--done">
                      <span className="attachment-item__icon">📄</span>
                      <span className="attachment-item__name">{att.filename}</span>
                      <span className="attachment-item__size">
                        {(att.file_size / 1024).toFixed(1)} KB
                      </span>
                      <span className="attachment-item__status">✓</span>
                    </li>
                  ))}
                  {fileEntries.map((fe) => (
                    <li
                      key={fe.id}
                      className={`attachment-item attachment-item--${fe.status}`}
                    >
                      <span className="attachment-item__icon">📄</span>
                      <span className="attachment-item__name">{fe.name}</span>
                      {fe.status === 'uploading' && (
                        <span className="attachment-item__status">Uploading…</span>
                      )}
                      {fe.status === 'error' && (
                        <span className="attachment-item__status attachment-item__status--error">
                          {fe.error ?? 'Error'}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </motion.div>
        )}

        <motion.div variants={CARD}>
          <div className="row" style={{ gap: 12, justifyContent: 'flex-end' }}>
            <button
              className="btn btn-outline"
              onClick={handleSaveDraft}
              disabled={isSaving || isSubmitting}
            >
              {isSaving ? 'Saving…' : 'Save as Draft'}
            </button>
            <button
              className="btn btn-primary"
              onClick={() => {
                const err = validate()
                if (err) { setError(err); return }
                setConfirmOpen(true)
              }}
              disabled={isSaving || isSubmitting}
            >
              {isSubmitting ? 'Submitting…' : 'Submit for Review'}
            </button>
          </div>
        </motion.div>
      </motion.div>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Submit request?</AlertDialogTitle>
            <AlertDialogDescription>
              Once submitted, the request will be sent for review and can no longer be edited.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleSubmit}>
              {isSubmitting ? 'Submitting…' : 'Yes, Submit'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
