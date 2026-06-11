import type { RequestStatus } from '../types'

interface Props {
  status: RequestStatus
}

const labelMap: Record<RequestStatus, string> = {
  draft: 'Draft',
  pending_review: 'In Review',
  pending_approval: 'Pending Approval',
  needs_rule: 'Needs Routing',
  approved: 'Approved',
  rejected: 'Rejected',
  needs_more_info: 'Needs Info',
}

const classMap: Record<RequestStatus, string> = {
  draft: 'badge-draft',
  pending_review: 'badge-pending',
  pending_approval: 'badge-approval',
  needs_rule: 'badge-rule',
  approved: 'badge-approved',
  rejected: 'badge-rejected',
  needs_more_info: 'badge-info',
}

export function StatusBadge({ status }: Props) {
  const label = (labelMap as Record<string, string | undefined>)[status] ?? status
  const cls = (classMap as Record<string, string | undefined>)[status] ?? 'badge-unknown'
  return (
    <span className={`badge ${cls}`} aria-label={`Status: ${label}`}>
      {label}
    </span>
  )
}
