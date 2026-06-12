import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(_error: Error, _info: ErrorInfo): void {}

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            background: 'var(--color-canvas, #f0f2f5)',
          }}
        >
          <div
            style={{
              background: 'var(--color-surface, #ffffff)',
              borderRadius: 'var(--radius, 0.625rem)',
              boxShadow: 'var(--shadow-md, 0 4px 16px rgba(0,0,0,.08))',
              padding: '2rem 2.5rem',
              maxWidth: 420,
              textAlign: 'center',
            }}
          >
            <h2
              style={{
                color: 'var(--color-text, #0c1a2e)',
                marginBottom: '0.5rem',
                fontSize: '1.25rem',
                fontWeight: 600,
              }}
            >
              Something went wrong
            </h2>
            <p
              style={{
                color: 'var(--color-text-muted, #64748b)',
                marginBottom: '1.5rem',
                fontSize: 14,
              }}
            >
              An unexpected error occurred. Please reload the page to continue.
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                background: 'var(--color-primary, #0f766e)',
                color: '#ffffff',
                border: 'none',
                borderRadius: 'var(--radius, 0.625rem)',
                padding: '0.5rem 1.25rem',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              Reload page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
