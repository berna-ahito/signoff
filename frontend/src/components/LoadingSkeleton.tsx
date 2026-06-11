import './LoadingSkeleton.css'

interface Props {
  rows?: number
  variant?: 'text' | 'card' | 'table'
}

export function LoadingSkeleton({ rows = 3, variant = 'text' }: Props) {
  if (variant === 'card') {
    return (
      <div className="skeleton-card" aria-busy="true" aria-label="Loading">
        <div className="skeleton skeleton--title" />
        <div className="skeleton skeleton--line" />
        <div className="skeleton skeleton--line skeleton--short" />
      </div>
    )
  }

  if (variant === 'table') {
    return (
      <div className="skeleton-table" aria-busy="true" aria-label="Loading table">
        {Array.from({ length: rows }).map((_item, i) => (
          <div key={i} className="skeleton-row">
            <div className="skeleton skeleton--cell" />
            <div className="skeleton skeleton--cell skeleton--cell-wide" />
            <div className="skeleton skeleton--cell" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="skeleton-lines" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_item, i) => (
        <div
          key={i}
          className={`skeleton skeleton--line${i === rows - 1 ? ' skeleton--short' : ''}`}
        />
      ))}
    </div>
  )
}
