import './RoleBadge.css'
import type { Role } from '../types'

interface Props {
  role: Role
}

export function RoleBadge({ role }: Props) {
  return (
    <span className={`role-badge role-badge--${role}`}>
      {role}
    </span>
  )
}
