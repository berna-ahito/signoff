import './PageHeader.css'

interface Props {
  context?: string
  title: string
  subtitle?: string
  actions?: React.ReactNode
}

export function PageHeader({ context, title, subtitle, actions }: Props) {
  return (
    <div className="page-header-bar">
      <div className="page-header-bar__left">
        {context && (
          <div className="workbench-context">
            <span className="workbench-context-mark" aria-hidden="true" />
            <span className="workbench-context-label">{context}</span>
          </div>
        )}
        <h2 className="page-title">{title}</h2>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-header-bar__actions">{actions}</div>}
    </div>
  )
}
