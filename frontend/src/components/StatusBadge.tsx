import type { RequestStatus } from '../types'

interface Props {
  status: RequestStatus
}

const labelMap: Record<RequestStatus, string> = {
  draft: 'Draft',
  pending_review: 'AI Review',
  pending_approval: 'Pending Approval',
  needs_rule: 'No Rule',
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
  return (
    <span className={`badge ${classMap[status]}`} aria-label={`Status: ${labelMap[status]}`}>
      {labelMap[status]}
    </span>
  )
}
