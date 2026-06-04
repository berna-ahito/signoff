interface Props {
  size?: number
  accentColor?: string
  variant?: 'dark' | 'light'
}

export function BrandMark({ size = 24, accentColor, variant = 'dark' }: Props) {
  const isLight = variant === 'light'
  const docPrimary = isLight ? '#1b2a3d' : 'rgba(255,255,255,0.85)'
  const docSecondary = isLight ? 'rgba(27,42,61,0.5)' : 'rgba(255,255,255,0.6)'
  const arrow = accentColor ?? (isLight ? '#1a56db' : '#93c5fd')

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 28 28"
      fill="none"
      aria-hidden="true"
      style={{ display: 'block', flexShrink: 0 }}
    >
      <rect x="2" y="1" width="16" height="22" rx="2.5"
        stroke={docPrimary} strokeWidth="1.5" />
      <rect x="5.5" y="7.5" width="9" height="1.5" rx="0.75"
        fill={docPrimary} />
      <rect x="5.5" y="11.5" width="6.5" height="1.5" rx="0.75"
        fill={docSecondary} />
      <path
        d="M19 11.5H26M23.5 9L26 11.5L23.5 14"
        stroke={arrow}
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
