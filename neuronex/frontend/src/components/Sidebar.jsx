import { NavLink } from 'react-router-dom'
import HealthBadge from './HealthBadge'

const NAV_ITEMS = [
  { to: '/',               icon: '📊', label: 'Overview' },
  { to: '/cases',          icon: '📁', label: 'Cases' },
  { to: '/upload',         icon: '⬆️', label: 'Upload Data' },
  { section: 'Analysis' },
  { to: '/graph',          icon: '🕸️', label: 'Knowledge Graph' },
  { to: '/entities',       icon: '👤', label: 'Entity Explorer' },
  { to: '/communities',    icon: '🔵', label: 'Communities' },
  { section: 'Intelligence' },
  { to: '/insights',       icon: '💡', label: 'Insights' },
  { to: '/review',         icon: '🔍', label: 'Analyst Review' },
  { section: 'Quality' },
  { to: '/validation',     icon: '✅', label: 'Validation' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-logo">
          <div className="brand-icon">🧠</div>
          <div>
            <div className="brand-name">NeuroNex</div>
            <div className="brand-sub">Decision Support Platform</div>
          </div>
        </div>
      </div>

      <div className="synthetic-badge">⚠ Synthetic Data Only</div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item, idx) => {
          if (item.section) {
            return (
              <div key={idx} className="nav-section-label" style={{ marginTop: 16 }}>
                {item.section}
              </div>
            )
          }
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              id={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          )
        })}
      </nav>

      <div style={{ padding: '16px', borderTop: '1px solid var(--border-subtle)' }}>
        <div style={{ marginBottom: 12 }}>
          <HealthBadge />
        </div>
        <div className="text-xs text-muted" style={{ lineHeight: 1.6 }}>
          <strong style={{ color: 'var(--accent-primary)' }}>SIH26189</strong><br />
          Decision support tool only.<br />
          No real investigative data.
        </div>
      </div>
    </aside>
  )
}
