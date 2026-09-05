/** StatCard — a single metric card for the overview dashboard */
export default function StatCard({ icon, value, label, accent, sub, onClick }) {
  const isClickable = typeof onClick === 'function'

  return (
    <div
      className="stat-card fade-in"
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => (e.key === 'Enter' || e.key === ' ') && onClick() : undefined}
      style={{
        cursor: isClickable ? 'pointer' : 'default',
        transition: 'transform 0.15s ease, background 0.15s ease, border-color 0.15s ease',
      }}
      onMouseEnter={(e) => {
        if (isClickable) {
          e.currentTarget.style.transform = 'translateY(-2px)'
          e.currentTarget.style.borderColor = 'var(--color-primary, #6366f1)'
        }
      }}
      onMouseLeave={(e) => {
        if (isClickable) {
          e.currentTarget.style.transform = 'translateY(0)'
          e.currentTarget.style.borderColor = ''
        }
      }}
    >
      <div className="stat-icon">{icon}</div>
      <div className={`stat-value ${accent ? 'stat-accent' : ''}`}>
        {value ?? '—'}
      </div>
      <div className="stat-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>{label}</span>
        {isClickable && <span style={{ opacity: 0.5, fontSize: '0.85em' }}>→</span>}
      </div>
      {sub && <div className="text-xs text-muted mt-4" style={{ marginTop: 6 }}>{sub}</div>}
    </div>
  )
}
