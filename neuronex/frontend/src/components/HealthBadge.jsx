import { useState, useEffect } from 'react'
import { getHealth } from '../api/client'

export default function HealthBadge() {
  const [health, setHealth] = useState(null)
  const [showTooltip, setShowTooltip] = useState(false)

  const check = () => {
    getHealth()
      .then((res) => setHealth(res.data))
      .catch(() =>
        setHealth({
          status: 'unreachable',
          backend: 'unreachable',
          neo4j: 'unreachable',
          database: 'unreachable',
        })
      )
  }

  useEffect(() => {
    check()
    const timer = setInterval(check, 30000)
    return () => clearInterval(timer)
  }, [])

  const status = (health?.status || 'checking').toLowerCase()
  const isOk = status === 'ok' || status === 'healthy'
  const isDegraded = status === 'degraded'
  const isChecking = status === 'checking'

  const dotColor = isOk ? '#10b981' : isDegraded ? '#f59e0b' : isChecking ? '#6b7280' : '#ef4444'
  const label = isOk ? 'System Operational' : isDegraded ? 'Service Degraded' : isChecking ? 'Checking Health...' : 'Service Offline'

  return (
    <div
      style={{ position: 'relative', display: 'inline-block', width: '100%' }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 10px',
          borderRadius: 'var(--r-sm)',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
          cursor: 'pointer',
          fontSize: 11,
          color: 'var(--text-secondary)',
        }}
      >
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: dotColor,
            boxShadow: `0 0 6px ${dotColor}`,
            flexShrink: 0,
          }}
        />
        <span style={{ fontWeight: 500, flex: 1 }}>{label}</span>
      </div>

      {showTooltip && (
        <div
          style={{
            position: 'absolute',
            bottom: '100%',
            left: 0,
            marginBottom: 8,
            width: 200,
            background: 'var(--bg-card)',
            border: '1px solid var(--border-active)',
            borderRadius: 'var(--r-sm)',
            padding: 10,
            boxShadow: 'var(--shadow-deep)',
            zIndex: 100,
            fontSize: 11,
            color: 'var(--text-primary)',
            animation: 'fadeIn 0.15s ease',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 6, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 4 }}>
            System Infrastructure
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ color: 'var(--text-muted)' }}>Backend API:</span>
            <span style={{ color: (health?.backend === 'ok' || health?.components?.backend === 'Healthy') ? '#10b981' : '#ef4444', fontWeight: 600 }}>
              {health?.components?.backend || (health?.backend === 'ok' ? 'Healthy' : health?.backend) || '...'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <span style={{ color: 'var(--text-muted)' }}>Neo4j Graph DB:</span>
            <span style={{ color: (health?.neo4j === 'ok' || health?.components?.neo4j === 'Healthy') ? '#10b981' : '#ef4444', fontWeight: 600 }}>
              {health?.components?.neo4j || (health?.neo4j === 'ok' ? 'Healthy' : health?.neo4j) || '...'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>SQLite Storage:</span>
            <span style={{ color: (health?.database === 'ok' || health?.components?.sqlite === 'Healthy') ? '#10b981' : '#ef4444', fontWeight: 600 }}>
              {health?.components?.sqlite || (health?.database === 'ok' ? 'Healthy' : health?.database) || '...'}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
