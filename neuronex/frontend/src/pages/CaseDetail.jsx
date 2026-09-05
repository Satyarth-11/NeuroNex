import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getCase,
  listDocuments,
  listEntities,
  getGraph,
  getCommunities,
  listInsights,
  getTimeline,
} from '../api/client'
import StatCard from '../components/StatCard'
import SourceTypeBadge from '../components/SourceTypeBadge'
import DocumentDetailModal from '../components/DocumentDetailModal'
import CommunityDetailModal from '../components/CommunityDetailModal'

export default function CaseDetail() {
  const { caseId } = useParams()
  const navigate = useNavigate()

  const [caseData, setCaseData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [error, setError] = useState(null)

  // Tab-specific data
  const [documents, setDocuments] = useState([])
  const [entities, setEntities] = useState([])
  const [relationships, setRelationships] = useState([])
  const [communities, setCommunities] = useState([])
  const [insights, setInsights] = useState([])
  const [timelineData, setTimelineData] = useState(null)

  // Modal states
  const [selectedDocId, setSelectedDocId] = useState(null)
  const [selectedCommId, setSelectedCommId] = useState(null)

  useEffect(() => {
    loadCase()
  }, [caseId])

  async function loadCase() {
    setLoading(true)
    setError(null)
    try {
      const res = await getCase(caseId)
      setCaseData(res.data)

      // Pre-populate documents from detail response
      if (res.data.documents) {
        setDocuments(res.data.documents)
      }

      // Load related tab data in background
      loadCaseRelatedData(res.data)
    } catch (err) {
      console.error('Failed to load case detail:', err)
      setError(err.response?.data?.detail || 'Case not found or unable to fetch detail.')
    } finally {
      setLoading(false)
    }
  }

  async function loadCaseRelatedData(caseDetail) {
    try {
      const caseCode = caseDetail.case_code
      const caseDocIds = new Set((caseDetail.documents || []).map(d => d.id))
      const caseCids = new Set(caseDetail.canonical_entity_ids || [])

      const [entRes, graphRes, commRes, insRes, timeRes] = await Promise.allSettled([
        listEntities({ case_id: caseDetail.id }),
        getGraph({ case_code: caseCode, limit: 100 }),
        getCommunities(),
        listInsights(),
        getTimeline({ case_code: caseCode }),
      ])

      if (entRes.status === 'fulfilled') {
        const allEnts = entRes.value.data || []
        const caseEnts = allEnts.filter(e => caseDocIds.has(e.document_id))
        setEntities(caseEnts.length > 0 ? caseEnts : allEnts.filter(e => caseCids.has(e.canonical_entity_id)))
      }
      if (graphRes.status === 'fulfilled') {
        const edges = graphRes.value.data.edges || []
        const caseEdges = edges.filter(e => e.related_case === caseCode || (caseCids.has(e.source) && caseCids.has(e.target)))
        setRelationships(caseEdges)
      }
      if (commRes.status === 'fulfilled') {
        const rawComms = Array.isArray(commRes.value.data)
          ? commRes.value.data
          : (commRes.value.data?.communities || [])
        const matchingComms = rawComms.filter(c => {
          const members = c.members || []
          return members.some(m => caseCids.has(typeof m === 'object' ? m.node_id : String(m)))
        })
        setCommunities(matchingComms)
      }
      if (insRes.status === 'fulfilled') {
        const allIns = insRes.value.data || []
        const caseIns = allIns.filter(i => {
          const refs = (i.source_refs || []).map(r => Number(String(r).replace('doc_', '')))
          return refs.some(r => caseDocIds.has(r))
        })
        setInsights(caseIns)
      }
      if (timeRes.status === 'fulfilled') {
        setTimelineData(timeRes.value.data)
      }
    } catch (e) {
      console.warn('Error loading secondary case data:', e)
    }
  }

  if (loading) {
    return (
      <div className="fade-in loading-container" style={{ minHeight: 300 }}>
        <div className="spinner" />
      </div>
    )
  }

  if (error || !caseData) {
    return (
      <div className="fade-in card" style={{ textAlign: 'center', padding: 40 }}>
        <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Case Workspace Unavailable</div>
        <div className="text-muted" style={{ marginBottom: 20 }}>{error}</div>
        <button className="btn btn-primary" onClick={() => navigate('/cases')}>
          ← Back to All Cases
        </button>
      </div>
    )
  }

  const tabs = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'documents', label: `📄 Documents (${caseData.document_count ?? documents.length})` },
    { id: 'entities', label: `👤 Entities (${caseData.entity_count ?? entities.length})` },
    { id: 'relationships', label: `🔗 Relationships (${caseData.relationship_count ?? relationships.length})` },
    { id: 'timeline', label: `⏱️ Timeline (${timelineData?.total_events ?? '…'})` },
    { id: 'communities', label: `🔵 Communities (${caseData.community_count ?? communities.length})` },
    { id: 'insights', label: `💡 Insights (${caseData.insight_count ?? insights.length})` },
    { id: 'review', label: '🛡️ Analyst Review' },
  ]

  return (
    <div className="fade-in">
      {/* Header with Back Button */}
      <div style={{ marginBottom: 20 }}>
        <button
          className="btn btn-outline"
          onClick={() => navigate('/cases')}
          style={{ marginBottom: 12, padding: '6px 12px', fontSize: 13 }}
        >
          ← Back to Cases
        </button>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h1 className="page-title" style={{ margin: 0 }}>{caseData.title}</h1>
              <span className="badge badge-primary monospace" style={{ fontSize: 13 }}>
                {caseData.case_code}
              </span>
            </div>
            <p className="page-subtitle" style={{ margin: 0 }}>
              {caseData.description || 'Dedicated multi-source investigative workspace.'}
            </p>
          </div>
          <div className="text-xs text-muted">
            Created: {new Date(caseData.created_at).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div style={{ display: 'flex', gap: 6, borderBottom: '1px solid var(--border-subtle)', marginBottom: 24, overflowX: 'auto' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '10px 16px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === tab.id ? '2px solid var(--accent-primary)' : '2px solid transparent',
              color: activeTab === tab.id ? 'var(--accent-primary)' : 'var(--text-muted)',
              fontWeight: activeTab === tab.id ? 700 : 500,
              fontSize: 13,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* TAB 1: Overview */}
      {activeTab === 'overview' && (
        <div className="fade-in">
          <div className="stat-grid" style={{ marginBottom: 24 }}>
            <StatCard icon="📄" value={caseData.document_count ?? 0} label="Ingested Documents" />
            <StatCard icon="👤" value={caseData.entity_count ?? 0} label="Extracted Entities" />
            <StatCard icon="🔗" value={caseData.relationship_count ?? 0} label="Case Relationships" />
            <StatCard icon="🔵" value={caseData.community_count ?? 0} label="Touching Clusters" />
            <StatCard icon="💡" value={caseData.insight_count ?? 0} label="Generated Leads" />
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="card-header">
                <div className="card-title">Case Metadata</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <div className="text-xs text-muted">Case Registration Identifier</div>
                  <div className="monospace text-sm text-accent" style={{ marginTop: 2 }}>{caseData.case_code}</div>
                </div>
                <div>
                  <div className="text-xs text-muted">Full Investigation Title</div>
                  <div className="text-sm text-primary" style={{ marginTop: 2, fontWeight: 600 }}>{caseData.title}</div>
                </div>
                <div>
                  <div className="text-xs text-muted">Case Scope & Description</div>
                  <div className="text-sm text-secondary" style={{ marginTop: 2, lineHeight: 1.5 }}>
                    {caseData.description || 'No detailed scope provided.'}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted">Status</div>
                  <div style={{ marginTop: 4 }}>
                    <span className="badge badge-proposed">Active Investigation</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <div className="card-title">Multi-Source Document Breakdown</div>
              </div>
              {documents.length === 0 ? (
                <div className="text-muted text-sm">No documents attached to this case.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {documents.map(d => (
                    <div
                      key={d.id}
                      onClick={() => setSelectedDocId(d.id)}
                      style={{
                        padding: '10px 12px',
                        borderRadius: 6,
                        background: 'var(--bg-elevated)',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <SourceTypeBadge type={d.source_type} />
                        <span style={{ fontSize: 13, fontWeight: 600 }}>{d.filename}</span>
                      </div>
                      <span className="badge badge-proposed" style={{ fontSize: 11 }}>{d.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Top Connected Entities (Case Subgraph) */}
          {caseData.top_connected_entities && caseData.top_connected_entities.length > 0 && (
            <div className="card" style={{ marginTop: 20 }}>
              <div className="card-header flex-between">
                <div className="card-title">🌟 Top Connected Entities (Case Subgraph)</div>
                <span className="badge badge-primary">{caseData.top_connected_entities.length} entities</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
                {caseData.top_connected_entities.map(ent => (
                  <div
                    key={ent.id}
                    style={{
                      padding: '12px 14px',
                      borderRadius: 'var(--r-md)',
                      background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{ent.name}</div>
                      <div className="text-xs text-muted">{ent.entity_type}</div>
                    </div>
                    <span className="badge badge-proposed" title="Degree within case subgraph">
                      {ent.degree} link{ent.degree !== 1 ? 's' : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Documents */}
      {activeTab === 'documents' && (
        <div className="fade-in card">
          <div className="card-header">
            <div className="card-title">Case Document Registry</div>
            <span className="badge badge-proposed">{documents.length} files</span>
          </div>
          {documents.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <div className="empty-title">No documents uploaded for this case</div>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Source Type</th>
                    <th>Filename</th>
                    <th>Records</th>
                    <th>Uploaded</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map(d => (
                    <tr
                      key={d.id}
                      onClick={() => setSelectedDocId(d.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td><SourceTypeBadge type={d.source_type} /></td>
                      <td style={{ fontWeight: 600 }}>{d.filename}</td>
                      <td>{d.record_count ?? 0}</td>
                      <td className="text-xs text-muted">{new Date(d.uploaded_at).toLocaleString()}</td>
                      <td>
                        <span className={`badge badge-${d.status === 'processed' ? 'approved' : d.status === 'failed' ? 'rejected' : 'proposed'}`}>
                          {d.status}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-outline"
                          style={{ padding: '4px 8px', fontSize: 11 }}
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedDocId(d.id)
                          }}
                        >
                          View Detail
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Entities */}
      {activeTab === 'entities' && (
        <div className="fade-in card">
          <div className="card-header">
            <div className="card-title">Extracted Entities associated with this case</div>
            <span className="badge badge-primary">{entities.length} shown</span>
          </div>
          {entities.length === 0 ? (
            <div className="empty-state"><div className="empty-title">No extracted entities</div></div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
              {entities.map((ent, idx) => (
                <div key={idx} style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: 13 }}>{ent.text || ent.normalized_text}</span>
                    <span className="badge badge-proposed" style={{ fontSize: 10 }}>{ent.entity_type}</span>
                  </div>
                  {ent.canonical_entity_id && (
                    <div className="monospace text-xs text-muted" style={{ fontSize: 10 }}>{ent.canonical_entity_id}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: Relationships */}
      {activeTab === 'relationships' && (
        <div className="fade-in card">
          <div className="card-header">
            <div className="card-title">Relationships in Knowledge Graph for this Case</div>
            <button className="btn btn-primary" onClick={() => navigate('/graph')}>
              Open Full Graph View →
            </button>
          </div>
          {relationships.length === 0 ? (
            <div className="empty-state"><div className="empty-title">No relationships linked directly to this case code</div></div>
          ) : (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Source Node</th>
                    <th>Relationship</th>
                    <th>Target Node</th>
                    <th>Source Type</th>
                    <th>Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {relationships.map((r, idx) => (
                    <tr key={idx}>
                      <td className="monospace text-xs">{r.src}</td>
                      <td><span className="badge badge-proposed" style={{ fontSize: 10 }}>{r.rel_type}</span></td>
                      <td className="monospace text-xs">{r.dst}</td>
                      <td><SourceTypeBadge type={r.source_types?.[0] || 'fir'} /></td>
                      <td>{r.confidence ?? '0.75'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB: Timeline & Temporal Correlations */}
      {activeTab === 'timeline' && (
        <div className="fade-in card">
          <div className="card-header flex-between">
            <div>
              <div className="card-title">⏱️ Investigative Timeline & Temporal Correlations</div>
              <div className="text-xs text-muted" style={{ marginTop: 2 }}>
                Chronological multi-source event stream linked by actual event timestamps · <strong style={{ color: 'var(--accent-rose)' }}>SYNTHETIC DATA ONLY</strong>
              </div>
            </div>
            {timelineData?.sources_represented && (
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {timelineData.sources_represented.map(st => (
                  <SourceTypeBadge key={st} type={st} />
                ))}
              </div>
            )}
          </div>

          {/* Temporal Correlations Section */}
          {timelineData?.correlations && timelineData.correlations.length > 0 && (
            <div style={{
              background: 'rgba(59, 130, 246, 0.08)',
              border: '1px solid rgba(59, 130, 246, 0.25)',
              borderRadius: 'var(--r-md)',
              padding: 16,
              marginBottom: 24,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>⚡</span> Detected Temporal Correlations ({timelineData.correlations.length})
                </div>
                <span className="badge badge-primary">{timelineData.window_hours}h Window</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {timelineData.correlations.map(corr => (
                  <div
                    key={corr.correlation_id}
                    style={{
                      padding: 12,
                      background: 'var(--bg-elevated)',
                      borderRadius: 'var(--r-sm)',
                      border: '1px solid var(--border-subtle)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <span className="badge badge-proposed" style={{ fontSize: 11 }}>{corr.correlation_label}</span>
                      <span className="text-xs text-muted">Δt = {corr.time_delta_hours} hours</span>
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.4, marginTop: 4 }}>
                      {corr.explanation}
                    </div>
                    <div className="text-xs text-muted" style={{ marginTop: 6, fontStyle: 'italic' }}>
                      ℹ️ {corr.neutral_disclaimer}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Chronological Event Stream */}
          {!timelineData || timelineData.events?.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">⏱️</div>
              <div className="empty-title">No timestamped events recorded for this case</div>
              <div className="empty-desc text-muted">All synthetic records for this case lack valid chronological timestamps.</div>
            </div>
          ) : (
            <div style={{ position: 'relative', paddingLeft: 24, borderLeft: '2px solid var(--border-subtle)', marginLeft: 8 }}>
              {timelineData.events.map((evt, idx) => (
                <div
                  key={evt.event_id || idx}
                  style={{
                    position: 'relative',
                    marginBottom: 20,
                    padding: '12px 16px',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--r-md)',
                  }}
                >
                  {/* Dot on the timeline line */}
                  <div style={{
                    position: 'absolute',
                    left: -31,
                    top: 16,
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    background: 'var(--accent-primary)',
                    border: '2px solid var(--bg-surface)',
                  }} />

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6, flexWrap: 'wrap', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <SourceTypeBadge type={evt.source_type} />
                      <span style={{ fontWeight: 600, fontSize: 13 }}>{evt.title}</span>
                    </div>
                    <span className="monospace text-xs text-muted">
                      {evt.timestamp ? new Date(evt.timestamp).toLocaleString() : 'No timestamp'}
                    </span>
                  </div>

                  <div className="text-sm text-secondary" style={{ lineHeight: 1.5, marginBottom: 8 }}>
                    {evt.description}
                  </div>

                  {evt.entities && evt.entities.length > 0 && (
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                      <span className="text-xs text-muted">Entities involved:</span>
                      {evt.entities.map(ent => (
                        <span
                          key={ent}
                          className="badge"
                          style={{ fontSize: 11, background: 'rgba(255,255,255,0.06)' }}
                        >
                          {ent}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 5: Communities */}
      {activeTab === 'communities' && (
        <div className="fade-in card">
          <div className="card-header">
            <div className="card-title">Network Clusters & Communities touching this Case</div>
          </div>
          {communities.length === 0 ? (
            <div className="empty-state"><div className="empty-title">No communities computed yet</div></div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
              {communities.map((c) => (
                <div
                  key={c.community_id}
                  onClick={() => setSelectedCommId(c.community_id)}
                  style={{
                    padding: 14,
                    borderRadius: 8,
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>Community #{c.community_id + 1}</span>
                    <span className="badge badge-primary">{c.member_count} members</span>
                  </div>
                  <div className="text-xs text-muted" style={{ lineHeight: 1.4, marginBottom: 8 }}>
                    {c.summary}
                  </div>
                  <div className="text-xs text-accent">Click to view community members & metrics →</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 6: Insights */}
      {activeTab === 'insights' && (
        <div className="fade-in card">
          <div className="card-header">
            <div className="card-title">Investigative Leads & Insights</div>
            <button className="btn btn-outline" onClick={() => navigate('/insights')}>
              Go to Insights Desk →
            </button>
          </div>
          {insights.length === 0 ? (
            <div className="empty-state"><div className="empty-title">No insights for this case</div></div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {insights.map((ins) => (
                <div key={ins.id} style={{ padding: 14, borderRadius: 8, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: 13 }}>{ins.title}</span>
                    <span className="badge badge-proposed">{ins.insight_type}</span>
                  </div>
                  <div className="text-sm text-secondary" style={{ lineHeight: 1.5, marginTop: 4 }}>
                    {ins.explanation}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 7: Analyst Review */}
      {activeTab === 'review' && (
        <div className="fade-in card">
          <div className="card-header">
            <div className="card-title">Analyst Verification & Decision Logging</div>
          </div>
          <div className="decision-notice" style={{ marginBottom: 16 }}>
            🛡️ <strong>Human In The Loop.</strong> Law enforcement analysts verify and record findings here.
            All AI-extracted entities, resolution links, and anomaly patterns remain in 'proposed' status until reviewed.
          </div>
          <button className="btn btn-primary" onClick={() => navigate('/review')}>
            Open Analyst Review Desk →
          </button>
        </div>
      )}

      {/* Document Detail Modal */}
      {selectedDocId && (
        <DocumentDetailModal
          docId={selectedDocId}
          onClose={() => setSelectedDocId(null)}
        />
      )}

      {/* Community Detail Modal */}
      {selectedCommId !== null && (
        <CommunityDetailModal
          communityId={selectedCommId}
          onClose={() => setSelectedCommId(null)}
        />
      )}
    </div>
  )
}
