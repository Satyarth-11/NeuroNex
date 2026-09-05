/** SourceTypeBadge — coloured pill for each of the 7 source types */
const SOURCE_TYPE_META = {
  fir:                  { label: 'FIR / Police',       icon: '🚔' },
  cdr:                  { label: 'CDR',                icon: '📞' },
  financial:            { label: 'Financial',          icon: '💳' },
  surveillance:         { label: 'Surveillance',       icon: '👁️' },
  social_media:         { label: 'Social Media',       icon: '📲' },
  criminal_history:     { label: 'Criminal History',   icon: '🗂️' },
  intelligence_report:  { label: 'Intel Report',       icon: '🔒' },
}

export default function SourceTypeBadge({ type, showIcon = true }) {
  const meta = SOURCE_TYPE_META[type] || { label: type, icon: '📄' }
  return (
    <span className={`badge badge-${type}`} title={meta.label}>
      {showIcon && meta.icon} {meta.label}
    </span>
  )
}

export { SOURCE_TYPE_META }
