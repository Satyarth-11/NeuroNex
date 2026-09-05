import { useState, useEffect } from 'react'
import { getCommunities } from '../api/client'
import SourceTypeBadge from '../components/SourceTypeBadge'
import CommunityDetailModal from '../components/CommunityDetailModal'

const ENTITY_TYPE_COLORS = {
  Person: '#6366f1', Phone: '#22d3ee', Location: '#10b981',
  Vehicle: '#f59e0b', Organisation: '#ec4899', Case: '#f87171', Account: '#a78bfa',
}

export default function Communities() {
  const [communities, setCommunities] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedCommId, setSelectedCommId] = useState(null)

  const [expandedCommIds, setExpandedCommIds] = useState(new Set())

  const toggleExpand = (id, e) => {
    e.stopPropagation()
    setExpandedCommIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  useEffect(() => {
    getCommunities().then(r => setCommunities(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading-container" style={{ minHeight: 400 }}><div className="spinner" />Loading communities…</div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">🔵 Network Community Detection</h1>
        <p className="page-subtitle">
          Louvain modularity clustering applied to the multi-source knowledge graph — <strong style={{ color: 'var(--accent-rose)' }}>SYNTHETIC DATA</strong>.
          Detected clusters represent structural network patterns, not factual conclusions.
        </p>
      </div>

      <div className="decision-notice" style={{ marginBottom: 24 }}>
        ⚠️ Detected communities represent entities with frequent co-occurrence and communication in the data.
        <strong> This does NOT constitute a finding of an unlawful organisation.</strong> Each
        connected cluster requires human analyst review before any investigative action.
      </div>

      {communities.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🔵</div>
          <div className="empty-title">No communities detected</div>
          <div className="empty-desc">Process documents and build the knowledge graph first.</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 20 }}>
          {communities.map(comm => {
            const typeCounts = {}
            comm.members.forEach(m => {
              typeCounts[m.entity_type] = (typeCounts[m.entity_type] || 0) + 1
            })

            const isExpanded = expandedCommIds.has(comm.community_id)
            const maxMembers = 20
            const displayedMembers = isExpanded ? comm.members : comm.members.slice(0, maxMembers)
            const remainingCount = comm.members.length - maxMembers

            return (
              <div
                key={comm.community_id}
                id={`community-card-${comm.community_id}`}
                className="card"
                onClick={() => setSelectedCommId(comm.community_id)}
                style={{
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  border: '1px solid var(--border-subtle)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = 'var(--accent-primary)'
                  e.currentTarget.style.transform = 'translateY(-1px)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border-subtle)'
                  e.currentTarget.style.transform = 'none'
                }}
              >
                <div className="flex-between" style={{ marginBottom: 16 }}>
                  <div>
                    <div className="card-title" style={{ fontSize: 17, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span>Community Cluster #{comm.community_id + 1}</span>
                      <span className="text-xs text-muted" style={{ fontWeight: 400 }}>Click for detail view ↗</span>
                    </div>
                    <div className="card-subtitle">
                      {comm.member_count} entities · internal density {(comm.internal_edge_density * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="flex gap-2" style={{ alignItems: 'center' }}>
                    {comm.members.length > maxMembers && (
                      <button
                        className="btn btn-outline btn-sm"
                        onClick={(e) => toggleExpand(comm.community_id, e)}
                        style={{ fontSize: 11, padding: '4px 10px' }}
                      >
                        {isExpanded ? '▲ Collapse' : `+${remainingCount} more`}
                      </button>
                    )}
                    {comm.source_types.map(st => <SourceTypeBadge key={st} type={st} />)}
                  </div>
                </div>

                {/* Entity type breakdown */}
                <div className="flex gap-2" style={{ marginBottom: 16, flexWrap: 'wrap' }}>
                  {Object.entries(typeCounts).map(([type, count]) => (
                    <div key={type} style={{
                      background: `${ENTITY_TYPE_COLORS[type] || '#94a3b8'}20`,
                      border: `1px solid ${ENTITY_TYPE_COLORS[type] || '#94a3b8'}40`,
                      borderRadius: 'var(--r-sm)',
                      padding: '3px 10px',
                      fontSize: 12,
                      color: ENTITY_TYPE_COLORS[type] || '#94a3b8',
                      fontWeight: 600,
                    }}>
                      {type}: {count}
                    </div>
                  ))}
                </div>

                {/* Members with compact preview */}
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 8,
                  marginBottom: 16,
                }}>
                  {displayedMembers.map(m => (
                    <div key={m.node_id} style={{
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--r-sm)',
                      padding: '4px 10px',
                      fontSize: 12,
                      color: 'var(--text-secondary)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}>
                      <span style={{
                        width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
                        background: ENTITY_TYPE_COLORS[m.entity_type] || '#94a3b8',
                      }} />
                      {m.name || m.node_id.slice(0, 12) + '…'}
                    </div>
                  ))}
                  {!isExpanded && remainingCount > 0 && (
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={(e) => toggleExpand(comm.community_id, e)}
                      style={{ fontSize: 11, padding: '4px 10px' }}
                    >
                      + {remainingCount} more members (Expand)
                    </button>
                  )}
                  {isExpanded && comm.members.length > maxMembers && (
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={(e) => toggleExpand(comm.community_id, e)}
                      style={{ fontSize: 11, padding: '4px 10px' }}
                    >
                      ▲ Collapse
                    </button>
                  )}
                </div>

                {/* Density bar */}
                <div style={{ marginBottom: 12 }}>
                  <div className="flex-between text-xs text-muted" style={{ marginBottom: 4 }}>
                    <span>Internal Edge Density</span>
                    <span className="monospace">{(comm.internal_edge_density * 100).toFixed(1)}%</span>
                  </div>
                  <div style={{ background: 'var(--bg-elevated)', borderRadius: 4, height: 6 }}>
                    <div style={{
                      width: `${comm.internal_edge_density * 100}%`,
                      height: '100%',
                      background: 'var(--grad-primary)',
                      borderRadius: 4,
                      transition: 'width 0.8s ease',
                    }} />
                  </div>
                </div>

                <div className="decision-notice" style={{ fontSize: 12 }}>
                  {comm.summary}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {selectedCommId !== null && (
        <CommunityDetailModal
          communityId={selectedCommId}
          onClose={() => setSelectedCommId(null)}
        />
      )}
    </div>
  )
}
