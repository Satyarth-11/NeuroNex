import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listEntities, traceEntity, getEntitiesSummary, listCases } from '../api/client'
import SourceTypeBadge from '../components/SourceTypeBadge'

const ENTITY_TYPES = ['PERSON', 'PHONE', 'LOCATION', 'VEHICLE', 'ORGANISATION', 'CASE_REF', 'ACCOUNT']
const SOURCE_TYPES = ['fir', 'cdr', 'financial', 'surveillance', 'social_media', 'criminal_history', 'intelligence_report']

export default function EntityExplorer() {
  const navigate = useNavigate()
  const [entities, setEntities] = useState([])
  const [summary, setSummary] = useState(null)
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [caseFilter, setCaseFilter] = useState('')
  const [traceData, setTraceData] = useState(null)
  const [tracing, setTracing] = useState(null)

  const [page, setPage] = useState(0)
  const pageSize = 50

  useEffect(() => {
    getEntitiesSummary().then(r => setSummary(r.data)).catch(() => {})
    listCases().then(r => setCases(r.data || [])).catch(() => {})
  }, [])

  useEffect(() => {
    setPage(0)
  }, [search, typeFilter, sourceFilter, caseFilter])

  useEffect(() => {
    const t = setTimeout(() => load(), 300)
    return () => clearTimeout(t)
  }, [search, typeFilter, sourceFilter, caseFilter, page])

  async function load() {
    setLoading(true)
    try {
      const r = await listEntities({
        search,
        entity_type: typeFilter || undefined,
        source_type: sourceFilter || undefined,
        case_id: caseFilter || undefined,
        offset: page * pageSize,
        limit: pageSize,
      })
      setEntities(r.data)
    } finally {
      setLoading(false)
    }
  }

  async function handleTrace(canonicalId) {
    setTracing(canonicalId)
    try {
      const r = await traceEntity(canonicalId)
      setTraceData(r.data)
    } catch {
      setTraceData(null)
    } finally {
      setTracing(null)
    }
  }

  function handleExploreInGraph(canonicalId, name) {
    navigate(`/graph?entityId=${canonicalId}&entityName=${encodeURIComponent(name || '')}`, {
      state: { entityId: canonicalId, entityName: name },
    })
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">👤 Entity Explorer</h1>
        <p className="page-subtitle">
          Cross-source entity index, multi-case mentions, and trace provenance · <strong style={{ color: 'var(--accent-rose)' }}>SYNTHETIC DATA ONLY</strong>
        </p>
      </div>

      {/* Summary Cards Row */}
      {summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: 12,
          marginBottom: 20,
        }}>
          {[
            { label: 'Total Entities', value: summary.total, color: 'var(--accent-primary)' },
            { label: 'Persons', value: summary.by_type?.PERSON ?? 0, color: '#6366f1' },
            { label: 'Phones', value: summary.by_type?.PHONE ?? 0, color: '#22d3ee' },
            { label: 'Locations', value: summary.by_type?.LOCATION ?? 0, color: '#10b981' },
            { label: 'Vehicles', value: summary.by_type?.VEHICLE ?? 0, color: '#f59e0b' },
            { label: 'Organisations', value: summary.by_type?.ORGANISATION ?? 0, color: '#ec4899' },
            { label: 'Accounts', value: summary.by_type?.ACCOUNT ?? 0, color: '#a78bfa' },
            { label: 'Cases with Entities', value: summary.by_case ?? summary.cases_count ?? 0, color: '#f87171' },
          ].map(card => (
            <div key={card.label} style={{
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--r-md)',
              padding: '12px 14px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: card.color, fontVariantNumeric: 'tabular-nums' }}>
                {card.value}
              </div>
              <div className="text-xs text-muted" style={{ marginTop: 2 }}>{card.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div>
          {/* Filters */}
          <div className="card mb-6" style={{ marginBottom: 20 }}>
            <div className="form-group" style={{ marginBottom: 12 }}>
              <label htmlFor="entity-search">Search</label>
              <input
                id="entity-search"
                placeholder="Search by name or normalised text…"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <div className="grid-3" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Entity Type</label>
                <select id="entity-type-filter" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
                  <option value="">All Types</option>
                  {ENTITY_TYPES.map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Source Type</label>
                <select id="entity-source-filter" value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}>
                  <option value="">All Sources</option>
                  {SOURCE_TYPES.map(st => <option key={st} value={st}>{st.replace('_', ' ')}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label>Filter by Case</label>
                <select id="entity-case-filter" value={caseFilter} onChange={e => setCaseFilter(e.target.value)}>
                  <option value="">All Cases</option>
                  {cases.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.case_code}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Table */}
          <div className="card">
            <div className="card-header flex-between">
              <div className="card-title">Entities Index</div>
              <span className="text-sm text-muted">{entities.length} results</span>
            </div>
            {loading ? (
              <div className="loading-container"><div className="spinner" /></div>
            ) : entities.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🔍</div>
                <div className="empty-title">No entities found</div>
                <div className="empty-desc">Process documents to extract entities or adjust active filters.</div>
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Entity</th>
                      <th>Type</th>
                      <th>Mentions</th>
                      <th>Sources</th>
                      <th>Cases</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {entities.map(ent => (
                      <tr key={ent.id}>
                        <td>
                          <div style={{ fontWeight: 600, fontSize: 13 }}>{ent.normalized_text}</div>
                          {ent.text !== ent.normalized_text && (
                            <div className="text-xs text-muted">Raw: {ent.text}</div>
                          )}
                        </td>
                        <td>
                          <span className="badge" style={{ background: 'rgba(79,142,247,0.1)', color: 'var(--accent-primary)', fontSize: 10 }}>
                            {ent.entity_type}
                          </span>
                        </td>
                        <td>
                          <span className="badge badge-proposed" style={{ fontSize: 11 }}>
                            {ent.mention_count}
                          </span>
                        </td>
                        <td>
                          <div className="text-xs">
                            <span style={{ fontWeight: 600 }}>{ent.source_document_count}</span> doc(s) · <span className="text-muted">{ent.source_type_count} type(s)</span>
                          </div>
                        </td>
                        <td>
                          <span className={`badge ${ent.related_case_count > 1 ? 'badge-approved' : 'badge-pending'}`} style={{ fontSize: 10 }}>
                            {ent.related_case_count} case(s)
                          </span>
                        </td>
                        <td>
                          <span className={`badge badge-${ent.resolution_status === 'approved' ? 'approved' : ent.resolution_status === 'auto_merged' ? 'approved' : 'flagged'}`} style={{ fontSize: 10 }}>
                            {ent.resolution_status}
                          </span>
                        </td>
                        <td>
                          {ent.canonical_entity_id && (
                            <button
                              id={`trace-ent-${ent.id}`}
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleTrace(ent.canonical_entity_id)}
                              disabled={tracing === ent.canonical_entity_id}
                              title="Trace Provenance"
                            >
                              {tracing === ent.canonical_entity_id ? '…' : '🔍'}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination Controls */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px 16px',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: 12,
            }}>
              <span className="text-muted">
                Showing page {page + 1} ({entities.length} items on page)
              </span>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  className="btn btn-outline btn-sm"
                  disabled={page === 0 || loading}
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                >
                  ← Previous
                </button>
                <button
                  className="btn btn-outline btn-sm"
                  disabled={entities.length < pageSize || loading}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next →
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Trace panel */}
        {traceData && (
          <div className="card fade-in">
            <div className="card-header flex-between">
              <div>
                <div className="card-title">🔍 Entity Trace</div>
                <div className="card-subtitle">{traceData.entity_type} · {traceData.name}</div>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => setTraceData(null)}>✕</button>
            </div>

            {/* Explore in Knowledge Graph Button */}
            <div style={{ marginBottom: 16 }}>
              <button
                id="explore-kg-btn"
                className="btn btn-primary btn-sm"
                style={{ width: '100%', justifyContent: 'center' }}
                onClick={() => handleExploreInGraph(traceData.canonical_entity_id, traceData.name)}
              >
                🕸️ Explore in Knowledge Graph →
              </button>
            </div>

            {/* Related Cases Section */}
            <div style={{ marginBottom: 16 }}>
              <div className="text-xs text-muted" style={{ marginBottom: 6, fontWeight: 600 }}>
                Related Cases ({traceData.related_cases?.length || 0})
              </div>
              {traceData.related_cases && traceData.related_cases.length > 0 ? (
                <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                  {traceData.related_cases.map(c => (
                    <span
                      key={c.id}
                      className="badge badge-approved"
                      style={{ fontSize: 11, cursor: 'pointer' }}
                      title={c.title}
                      onClick={() => navigate(`/cases/${c.id}`)}
                    >
                      📁 {c.case_code}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-muted" style={{ fontStyle: 'italic' }}>
                  No data available for this entity.
                </div>
              )}
            </div>

            {/* Related Entities from Graph */}
            <div style={{ marginBottom: 16 }}>
              <div className="text-xs text-muted" style={{ marginBottom: 6, fontWeight: 600 }}>
                Related Entities (Co-occurring in Graph)
              </div>
              {traceData.related_entities && traceData.related_entities.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 160, overflowY: 'auto' }}>
                  {traceData.related_entities.map((re, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: 'var(--bg-elevated)',
                        borderRadius: 'var(--r-sm)',
                        padding: '6px 10px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: 12,
                      }}
                    >
                      <div>
                        <strong>{re.name}</strong> <span className="text-xs text-muted">({re.entity_type})</span>
                      </div>
                      <span className="badge badge-pending" style={{ fontSize: 9 }}>{re.rel_type}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-muted" style={{ fontStyle: 'italic' }}>
                  No data available for this entity.
                </div>
              )}
            </div>

            {/* Source Types */}
            <div style={{ marginBottom: 16 }}>
              <div className="text-xs text-muted" style={{ marginBottom: 6, fontWeight: 600 }}>Source Types</div>
              <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
                {traceData.source_types && traceData.source_types.length > 0 ? (
                  traceData.source_types.map(st => <SourceTypeBadge key={st} type={st} />)
                ) : (
                  <span className="text-xs text-muted">No data available for this entity.</span>
                )}
              </div>
            </div>

            {/* Source Documents */}
            <div style={{ marginBottom: 16 }}>
              <div className="text-xs text-muted" style={{ marginBottom: 8, fontWeight: 600 }}>
                Source Documents ({traceData.source_documents.length})
              </div>
              {traceData.source_documents.map(d => (
                <div key={d.id} style={{
                  background: 'var(--bg-elevated)',
                  borderRadius: 'var(--r-sm)',
                  padding: '8px 12px',
                  marginBottom: 6,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                }}>
                  <SourceTypeBadge type={d.source_type} showIcon={false} />
                  <span className="text-sm">{d.filename}</span>
                </div>
              ))}
            </div>

            {/* Mentions */}
            <div>
              <div className="text-xs text-muted" style={{ marginBottom: 8, fontWeight: 600 }}>
                Mentions ({traceData.mentions.length})
              </div>
              {traceData.mentions.slice(0, 5).map(m => (
                <div key={m.id} style={{
                  background: 'var(--bg-elevated)',
                  borderRadius: 'var(--r-sm)',
                  padding: '8px 12px',
                  marginBottom: 6,
                  fontSize: 12,
                  color: 'var(--text-secondary)',
                  borderLeft: '2px solid var(--accent-primary)',
                }}>
                  {m.context_snippet}
                </div>
              ))}
            </div>

            <div className="monospace text-xs text-muted" style={{ marginTop: 12, wordBreak: 'break-all' }}>
              Canonical ID: {traceData.canonical_entity_id}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
