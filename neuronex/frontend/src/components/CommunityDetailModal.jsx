import { useState, useEffect } from 'react'
import { getCommunityDetail } from '../api/client'
import SourceTypeBadge from './SourceTypeBadge'

export default function CommunityDetailModal({ communityId, onClose }) {
  const [comm, setComm] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (communityId === null || communityId === undefined) return
    setLoading(true)
    setError(null)
    getCommunityDetail(communityId)
      .then((res) => setComm(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load community details'))
      .finally(() => setLoading(false))
  }, [communityId])

  if (communityId === null || communityId === undefined) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: 20,
      }}
      onClick={onClose}
    >
      <div
        className="card fade-in"
        style={{
          width: '100%',
          maxWidth: 820,
          maxHeight: '85vh',
          overflowY: 'auto',
          margin: 0,
          background: 'var(--bg-surface, #1e293b)',
          border: '1px solid var(--border-subtle)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid var(--border-subtle)',
            paddingBottom: 12,
            marginBottom: 16,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 22 }}>🔵</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>Network Community #{communityId + 1}</div>
              <div className="text-xs text-muted">Detected via Louvain modularity algorithm</div>
            </div>
          </div>
          <button
            className="btn btn-outline"
            onClick={onClose}
            style={{ padding: '4px 10px', fontSize: 14 }}
          >
            ✕ Close
          </button>
        </div>

        {loading ? (
          <div className="loading-container" style={{ padding: 40 }}><div className="spinner" /></div>
        ) : error ? (
          <div className="text-danger" style={{ padding: 20 }}>{error}</div>
        ) : comm ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            {/* Summary Metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10 }}>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6, textAlign: 'center' }}>
                <div className="text-xs text-muted">Total Members</div>
                <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4 }}>{comm.member_count}</div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6, textAlign: 'center' }}>
                <div className="text-xs text-muted">Persons</div>
                <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4, color: '#818cf8' }}>{comm.person_count}</div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6, textAlign: 'center' }}>
                <div className="text-xs text-muted">Phones</div>
                <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4, color: '#34d399' }}>{comm.phone_count}</div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6, textAlign: 'center' }}>
                <div className="text-xs text-muted">Vehicles</div>
                <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4, color: '#f59e0b' }}>{comm.vehicle_count}</div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6, textAlign: 'center' }}>
                <div className="text-xs text-muted">Accounts</div>
                <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4, color: '#ec4899' }}>{comm.account_count}</div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6, textAlign: 'center' }}>
                <div className="text-xs text-muted">Cluster Density</div>
                <div style={{ fontSize: 18, fontWeight: 700, marginTop: 4 }}>{comm.internal_edge_density?.toFixed(2)}</div>
              </div>
            </div>

            {/* Explainability Explanation */}
            <div style={{ padding: 14, background: 'var(--bg-elevated)', borderRadius: 8, border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>💡</span> Cluster Explanation & Analyst Context
              </div>
              <div className="text-sm text-secondary" style={{ lineHeight: 1.5 }}>
                {comm.explanation}
              </div>
            </div>

            {/* Related Cases & Sources */}
            <div className="grid-2" style={{ gap: 12 }}>
              <div style={{ padding: 12, background: 'var(--bg-elevated)', borderRadius: 8 }}>
                <div className="text-xs text-muted" style={{ marginBottom: 6 }}>Touching Investigation Cases</div>
                {comm.related_cases && comm.related_cases.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {comm.related_cases.map(c => (
                      <span key={c} className="badge badge-proposed monospace" style={{ fontSize: 11 }}>{c}</span>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-muted">No specific case reference attached.</div>
                )}
              </div>

              <div style={{ padding: 12, background: 'var(--bg-elevated)', borderRadius: 8 }}>
                <div className="text-xs text-muted" style={{ marginBottom: 6 }}>Involved Data Sources</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {comm.source_types?.map(st => (
                    <SourceTypeBadge key={st} type={st} />
                  ))}
                </div>
              </div>
            </div>

            {/* Most Central Members */}
            {comm.key_members && comm.key_members.length > 0 && (
              <div>
                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                  Most Connected Community Members
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
                  {comm.key_members.map((m, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '8px 12px',
                        background: 'var(--bg-elevated)',
                        borderRadius: 6,
                        border: '1px solid var(--border-subtle)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <span style={{ fontWeight: 600, fontSize: 12 }}>{m.name || m.node_id}</span>
                      <span className="badge badge-proposed" style={{ fontSize: 10 }}>{m.entity_type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Full Member List */}
            <div>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                All Cluster Member Entities ({comm.members?.length || 0})
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                  gap: 8,
                  maxHeight: 180,
                  overflowY: 'auto',
                }}
              >
                {comm.members?.map((m, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '6px 10px',
                      background: 'var(--bg-base)',
                      borderRadius: 4,
                      fontSize: 11,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {m.name || m.node_id}
                    </span>
                    <span className="text-muted" style={{ fontSize: 9, marginLeft: 6 }}>{m.entity_type}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
