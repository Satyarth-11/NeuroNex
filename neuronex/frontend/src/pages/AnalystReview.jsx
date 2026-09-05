import { useState, useEffect } from 'react'
import {
  listInsights,
  listCandidates,
  reviewInsight,
  decideCandidate,
  getLowConfidenceEdges,
  reviewEdge,
  getKeyInfluencers,
  regenerateInsights,
} from '../api/client'
import InsightCard from '../components/InsightCard'
import SourceTypeBadge from '../components/SourceTypeBadge'

function SectionError({ title, endpoint, error }) {
  return (
    <div className="card" style={{ border: '1px solid var(--accent-danger)', background: 'rgba(239, 68, 68, 0.08)', padding: '16px 20px', marginBottom: 16 }}>
      <div style={{ color: 'var(--accent-danger)', fontWeight: 700, fontSize: 15, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span>⚠️</span>
        <span>Unable to load {title}</span>
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-primary)', marginBottom: 4 }}>
        <strong>Endpoint:</strong> <code style={{ background: 'var(--bg-elevated)', padding: '2px 6px', borderRadius: 4, fontSize: 12 }}>{endpoint}</code>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
        <strong>Reason:</strong> {error || 'Service returned an error'}
      </div>
    </div>
  )
}

export default function AnalystReview() {
  const [dataState, setDataState] = useState({
    insights: { status: 'loading', data: [], error: null, endpoint: 'GET /api/insights?status=proposed' },
    candidates: { status: 'loading', data: [], error: null, endpoint: 'GET /api/resolution/candidates?decision=pending' },
    edges: { status: 'loading', data: [], error: null, endpoint: 'GET /api/graph/edges/low-confidence' },
    influencers: { status: 'loading', data: [], error: null, endpoint: 'GET /api/analytics/key-influencers?limit=10' },
  })
  const [loading, setLoading] = useState(true)
  const [regenerating, setRegenerating] = useState(false)
  const [tab, setTab] = useState('investigative')
  const [notes, setNotes] = useState({})
  const [edgeNotes, setEdgeNotes] = useState({})

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const [ins, cand, edges, infs] = await Promise.allSettled([
        listInsights({ status: 'proposed' }),
        listCandidates({ decision: 'pending' }),
        getLowConfidenceEdges(),
        getKeyInfluencers(10),
      ])

      const formatErr = (res) => {
        if (!res || !res.reason) return 'Unknown error'
        const r = res.reason
        const status = r.response?.status ? `HTTP ${r.response.status}: ` : ''
        const detail = r.response?.data?.detail || r.response?.data?.message || r.message || 'Request failed'
        return `${status}${detail}`
      }

      setDataState({
        insights: ins.status === 'fulfilled'
          ? { status: 'success', data: ins.value.data || [], error: null, endpoint: 'GET /api/insights?status=proposed' }
          : { status: 'error', data: [], error: formatErr(ins), endpoint: 'GET /api/insights?status=proposed' },
        candidates: cand.status === 'fulfilled'
          ? { status: 'success', data: cand.value.data || [], error: null, endpoint: 'GET /api/resolution/candidates?decision=pending' }
          : { status: 'error', data: [], error: formatErr(cand), endpoint: 'GET /api/resolution/candidates?decision=pending' },
        edges: edges.status === 'fulfilled'
          ? { status: 'success', data: edges.value.data || [], error: null, endpoint: 'GET /api/graph/edges/low-confidence' }
          : { status: 'error', data: [], error: formatErr(edges), endpoint: 'GET /api/graph/edges/low-confidence' },
        influencers: infs.status === 'fulfilled'
          ? { status: 'success', data: infs.value.data || [], error: null, endpoint: 'GET /api/analytics/key-influencers?limit=10' }
          : { status: 'error', data: [], error: formatErr(infs), endpoint: 'GET /api/analytics/key-influencers?limit=10' },
      })
    } finally {
      setLoading(false)
    }
  }

  async function handleRegenerate() {
    setRegenerating(true)
    try {
      await regenerateInsights()
      await load()
    } catch (err) {
      console.error("Failed to regenerate insights:", err)
    } finally {
      setRegenerating(false)
    }
  }

  async function handleInsightReview(insightId, decision) {
    await reviewInsight(insightId, {
      decision,
      analyst_id: 'analyst_01',
      notes: notes[insightId] || '',
    })
    load()
  }

  async function handleCandidateDecide(candidateId, decision) {
    await decideCandidate(candidateId, {
      decision,
      analyst_id: 'analyst_01',
    })
    load()
  }

  async function handleEdgeReview(edge, decision) {
    await reviewEdge({
      src: edge.src,
      dst: edge.dst,
      rel_type: edge.rel_type,
      decision,
    })
    // Remove edge from local list
    setDataState(prev => ({
      ...prev,
      edges: {
        ...prev.edges,
        data: prev.edges.data.filter(e => e.id !== edge.id)
      }
    }))
  }

  const insights = dataState.insights.data
  const candidates = dataState.candidates.data
  const lowConfidenceEdges = dataState.edges.data
  const rawInfluencers = dataState.influencers.data

  // 1. Investigative Insights: central_entity and community
  const investigativeList = insights.filter(i =>
    ['central_entity', 'community'].includes(i.insight_type)
  )

  // 2. Suspicious Patterns: suspicious_pattern
  const patternsList = insights.filter(i =>
    i.insight_type === 'suspicious_pattern'
  )

  // 3. Duplicate Resolution: candidates
  const duplicatesList = candidates

  // 4. Key Influential Entities: insight_type === 'key_influencer' or fallback
  const influencersList = insights.filter(i => i.insight_type === 'key_influencer')
  const displayInfluencers = influencersList.length > 0 ? influencersList : rawInfluencers

  // 5. Relationships Requiring Review: edges where confidence < 0.75
  const relationshipsList = lowConfidenceEdges

  const tabs = [
    {
      id: 'investigative',
      label: dataState.insights.status === 'error'
        ? 'Investigative Insights (Error)'
        : `Investigative Insights (${investigativeList.length})`,
      isError: dataState.insights.status === 'error',
    },
    {
      id: 'patterns',
      label: dataState.insights.status === 'error'
        ? 'Suspicious Patterns (Error)'
        : `Suspicious Patterns (${patternsList.length})`,
      isError: dataState.insights.status === 'error',
    },
    {
      id: 'duplicates',
      label: dataState.candidates.status === 'error'
        ? 'Duplicate / Entity Resolution (Error)'
        : `Duplicate / Entity Resolution (${duplicatesList.length})`,
      isError: dataState.candidates.status === 'error',
    },
    {
      id: 'influencers',
      label: (dataState.influencers.status === 'error' && dataState.insights.status === 'error')
        ? 'Key Influential Entities (Error)'
        : `Key Influential Entities (${displayInfluencers.length})`,
      isError: dataState.influencers.status === 'error' && dataState.insights.status === 'error',
    },
    {
      id: 'relationships',
      label: dataState.edges.status === 'error'
        ? 'Relationships Requiring Review (Error)'
        : `Relationships Requiring Review (${relationshipsList.length})`,
      isError: dataState.edges.status === 'error',
    },
  ]

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 className="page-title">🔍 Analyst Review Workflow</h1>
          <p className="page-subtitle">
            5-Tier Decision Support Console · All decisions logged with analyst ID · Reversible & non-prejudicial
          </p>
        </div>
        <button
          id="regenerate-insights-btn"
          className="btn btn-outline"
          onClick={handleRegenerate}
          disabled={loading || regenerating}
          style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, padding: '8px 14px' }}
          title="Re-compute all insights and pattern detections against the latest graph state"
        >
          {regenerating ? 'Regenerating…' : '🔄 Regenerate All Insights'}
        </button>
      </div>

      <div className="decision-notice" style={{ marginBottom: 24 }}>
        ⚠️ <strong>Analyst Notice:</strong> NeuroNex operates strictly as an investigative decision-support system.
        Approving an insight, merging duplicate entities, or validating low-confidence edges updates the knowledge
        graph but does not constitute judicial findings or charges.
      </div>

      {/* 5 Real Tabs */}
      <div style={{
        display: 'flex',
        gap: 6,
        marginBottom: 24,
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: 0,
        overflowX: 'auto',
      }}>
        {tabs.map(t => (
          <button
            key={t.id}
            id={`tab-${t.id}`}
            onClick={() => setTab(t.id)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '10px 16px',
              fontSize: 13,
              fontWeight: 600,
              whiteSpace: 'nowrap',
              color: tab === t.id ? 'var(--accent-primary)' : 'var(--text-muted)',
              borderBottom: `2px solid ${tab === t.id ? 'var(--accent-primary)' : 'transparent'}`,
              marginBottom: -1,
              transition: 'all 0.15s',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-container"><div className="spinner" /></div>
      ) : (
        <div>
          {/* TAB 1: Investigative Insights */}
          {tab === 'investigative' && (
            dataState.insights.status === 'error' ? (
              <SectionError
                title="Investigative Insights"
                endpoint={dataState.insights.endpoint}
                error={dataState.insights.error}
              />
            ) : investigativeList.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🌐</div>
                <div className="empty-title">No investigative insights currently available</div>
                <div className="empty-desc">All graph central entity and community detection insights have been reviewed or none are currently proposed.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {investigativeList.map(insight => (
                  <div key={insight.id}>
                    <InsightCard insight={insight} onReview={handleInsightReview} />
                    <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                      <input
                        id={`notes-${insight.id}`}
                        placeholder="Add analyst rationale / reference notes…"
                        value={notes[insight.id] || ''}
                        onChange={e => setNotes(n => ({ ...n, [insight.id]: e.target.value }))}
                        style={{ flex: 1, padding: '6px 12px', fontSize: 13 }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )
          )}

          {/* TAB 2: Suspicious Patterns */}
          {tab === 'patterns' && (
            dataState.insights.status === 'error' ? (
              <SectionError
                title="Suspicious Patterns"
                endpoint={dataState.insights.endpoint}
                error={dataState.insights.error}
              />
            ) : patternsList.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">⚠️</div>
                <div className="empty-title">No suspicious patterns currently available</div>
                <div className="empty-desc">Zero cross-case, high-frequency, financial, or convergence anomalies pending approval.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {patternsList.map(insight => (
                  <div key={insight.id}>
                    <InsightCard insight={insight} onReview={handleInsightReview} />
                    <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                      <input
                        id={`notes-pat-${insight.id}`}
                        placeholder="Add analyst rationale / investigation notes…"
                        value={notes[insight.id] || ''}
                        onChange={e => setNotes(n => ({ ...n, [insight.id]: e.target.value }))}
                        style={{ flex: 1, padding: '6px 12px', fontSize: 13 }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )
          )}

          {/* TAB 3: Duplicate / Entity Resolution */}
          {tab === 'duplicates' && (
            dataState.candidates.status === 'error' ? (
              <SectionError
                title="Duplicate / Entity Resolution"
                endpoint={dataState.candidates.endpoint}
                error={dataState.candidates.error}
              />
            ) : duplicatesList.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🔀</div>
                <div className="empty-title">No duplicate resolution candidates currently available</div>
                <div className="empty-desc">All pairwise candidates above the 0.72 similarity threshold have been evaluated.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {duplicatesList.map(cand => (
                  <div key={cand.id} className="card">
                    <div className="flex-between" style={{ marginBottom: 12 }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)', marginBottom: 4 }}>
                          Possible Duplicate — {cand.entity_type}
                        </div>
                        <div className="text-sm text-muted">
                          Similarity: <strong className="text-accent monospace">{(cand.similarity_score * 100).toFixed(1)}%</strong>
                          {' '}· Reason: <span style={{ fontFamily: 'monospace' }}>{cand.match_reason}</span>
                        </div>
                      </div>
                      <span className="badge badge-pending">{cand.decision}</span>
                    </div>

                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr auto 1fr',
                      gap: 12,
                      alignItems: 'center',
                      marginBottom: 16,
                    }}>
                      <div style={{
                        background: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--r-md)',
                        padding: '12px 14px',
                        fontSize: 13,
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                          <span className="text-xs text-muted">Entity A (ID: {cand.entity_a_id})</span>
                          {cand.entity_a_case && (
                            <span className="badge badge-approved" style={{ fontSize: 10 }}>{cand.entity_a_case}</span>
                          )}
                        </div>
                        <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
                          {cand.entity_a_text || `Entity ${cand.entity_a_id}`}
                        </div>
                        {cand.entity_a_doc && (
                          <div className="text-xs text-muted" style={{ marginTop: 4 }}>
                            📄 {cand.entity_a_doc}
                          </div>
                        )}
                      </div>

                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 22, color: 'var(--accent-primary)' }}>↔</div>
                        {cand.entity_a_case && cand.entity_b_case && cand.entity_a_case !== cand.entity_b_case && (
                          <div className="badge badge-flagged" style={{ fontSize: 9, marginTop: 4, whiteSpace: 'nowrap' }}>
                            ⚡ Cross-Case
                          </div>
                        )}
                      </div>

                      <div style={{
                        background: 'var(--bg-elevated)',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: 'var(--r-md)',
                        padding: '12px 14px',
                        fontSize: 13,
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                          <span className="text-xs text-muted">Entity B (ID: {cand.entity_b_id})</span>
                          {cand.entity_b_case && (
                            <span className="badge badge-pending" style={{ fontSize: 10 }}>{cand.entity_b_case}</span>
                          )}
                        </div>
                        <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
                          {cand.entity_b_text || `Entity ${cand.entity_b_id}`}
                        </div>
                        {cand.entity_b_doc && (
                          <div className="text-xs text-muted" style={{ marginTop: 4 }}>
                            📄 {cand.entity_b_doc}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="decision-notice" style={{ marginBottom: 12, fontSize: 12 }}>
                      Merging transfers all Neo4j edges to Canonical Entity A and marks Entity B as merged. This action is logged and fully reversible.
                    </div>

                    <div className="flex gap-2">
                      <button
                        id={`approve-cand-${cand.id}`}
                        className="btn btn-success btn-sm"
                        onClick={() => handleCandidateDecide(cand.id, 'approved')}
                      >
                        ✓ Merge Entities
                      </button>
                      <button
                        id={`reject-cand-${cand.id}`}
                        className="btn btn-danger btn-sm"
                        onClick={() => handleCandidateDecide(cand.id, 'rejected')}
                      >
                        ✗ Keep Separate
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}

          {/* TAB 4: Key Influential Entities */}
          {tab === 'influencers' && (
            (dataState.influencers.status === 'error' && dataState.insights.status === 'error') ? (
              <SectionError
                title="Key Influential Entities"
                endpoint={dataState.influencers.endpoint}
                error={dataState.influencers.error || dataState.insights.error}
              />
            ) : displayInfluencers.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">👑</div>
                <div className="empty-title">No key influential entities currently available</div>
                <div className="empty-desc">Run graph analytics to detect top network bridge actors in the PERSON domain.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {displayInfluencers.map((item, idx) => {
                  // If materialised as Insight row
                  if (item.insight_type === 'key_influencer') {
                    return (
                      <div key={item.id}>
                        <InsightCard insight={item} onReview={handleInsightReview} />
                        <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                          <input
                            id={`notes-inf-${item.id}`}
                            placeholder="Add analyst notes for influencer…"
                            value={notes[item.id] || ''}
                            onChange={e => setNotes(n => ({ ...n, [item.id]: e.target.value }))}
                            style={{ flex: 1, padding: '6px 12px', fontSize: 13 }}
                          />
                        </div>
                      </div>
                    )
                  }
                  // Raw analytics object format fallback
                  return (
                    <div key={item.node_id || idx} className="card">
                      <div className="flex-between" style={{ marginBottom: 10 }}>
                        <div>
                          <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>
                            Key Influential Entity: {item.name}
                          </div>
                          <div className="text-xs text-muted" style={{ marginTop: 2 }}>
                            Betweenness: <strong>{item.betweenness_centrality?.toFixed(4)}</strong> · PageRank: <strong>{item.pagerank?.toFixed(4)}</strong>
                          </div>
                        </div>
                        <span className="badge badge-approved" style={{ fontSize: 10 }}>PERSON Centrality Lead</span>
                      </div>

                      <div style={{
                        background: 'var(--bg-elevated)',
                        padding: '12px 14px',
                        borderRadius: 'var(--r-sm)',
                        fontSize: 13,
                        lineHeight: 1.5,
                        marginBottom: 12,
                      }}>
                        {item.explanation || `Entity '${item.name}' displays prominent topological centrality across the network.`}
                      </div>

                      {item.related_cases && item.related_cases.length > 0 && (
                        <div style={{ marginBottom: 12 }}>
                          <span className="text-xs text-muted" style={{ marginRight: 6 }}>Related Cases:</span>
                          {item.related_cases.map(c => (
                            <span key={c} className="badge badge-proposed" style={{ fontSize: 10, marginRight: 4 }}>
                              {c}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="flex-between" style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: 10 }}>
                        <span className="text-xs text-muted font-italic">
                          Informational ranking derived from PageRank & betweenness centrality.
                        </span>
                        <div className="flex gap-2">
                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => alert(`Marked ${item.name} for prioritized case follow-up.`)}
                          >
                            ⭐ Prioritize Entity
                          </button>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )
          )}

          {/* TAB 5: Relationships Requiring Review */}
          {tab === 'relationships' && (
            dataState.edges.status === 'error' ? (
              <SectionError
                title="Relationships Requiring Review"
                endpoint={dataState.edges.endpoint}
                error={dataState.edges.error}
              />
            ) : relationshipsList.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🔗</div>
                <div className="empty-title">No relationships currently requiring review</div>
                <div className="empty-desc">All graph edges meet or exceed the 0.75 confidence threshold.</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {relationshipsList.map((edge) => (
                  <div key={edge.id} className="card">
                    <div className="flex-between" style={{ marginBottom: 12 }}>
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>
                          Low-Confidence Relationship: {edge.src_name} → {edge.dst_name}
                        </div>
                        <div className="text-xs text-muted" style={{ marginTop: 2 }}>
                          Type: <strong style={{ color: 'var(--accent-primary)', fontFamily: 'monospace' }}>{edge.rel_type}</strong>
                          {' '}· Case: <strong className="text-accent">{edge.related_case || 'Unassociated'}</strong>
                        </div>
                      </div>
                      <span className="badge badge-flagged" style={{ fontSize: 11 }}>
                        Confidence: {(edge.confidence * 100).toFixed(1)}% (&lt; 75%)
                      </span>
                    </div>

                    <div style={{
                      background: 'var(--bg-elevated)',
                      padding: '12px 14px',
                      borderRadius: 'var(--r-sm)',
                      marginBottom: 12,
                      fontSize: 13,
                    }}>
                      <div className="text-xs text-muted" style={{ marginBottom: 4, fontWeight: 600 }}>
                        Evidence & Provenance
                      </div>
                      {edge.evidence_snippets && edge.evidence_snippets.length > 0 ? (
                        edge.evidence_snippets.map((snip, sIdx) => (
                          <div key={sIdx} style={{ fontStyle: 'italic', color: 'var(--text-secondary)', marginBottom: 4 }}>
                            "{snip}"
                          </div>
                        ))
                      ) : (
                        <div className="text-muted" style={{ fontStyle: 'italic' }}>
                          Edge surfaced through single-mention co-occurrence or weak indirect interaction without multi-source confirmation.
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
                      {edge.source_types && edge.source_types.map(st => (
                        <SourceTypeBadge key={st} type={st} />
                      ))}
                    </div>

                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <input
                        id={`edge-notes-${edge.id}`}
                        placeholder="Add analyst rationale for edge decision…"
                        value={edgeNotes[edge.id] || ''}
                        onChange={e => setEdgeNotes(n => ({ ...n, [edge.id]: e.target.value }))}
                        style={{ flex: 1, padding: '6px 12px', fontSize: 13 }}
                      />
                      <button
                        id={`approve-edge-${edge.id}`}
                        className="btn btn-success btn-sm"
                        onClick={() => handleEdgeReview(edge, 'approved')}
                      >
                        ✓ Validate Edge
                      </button>
                      <button
                        id={`flag-edge-${edge.id}`}
                        className="btn btn-outline btn-sm"
                        onClick={() => handleEdgeReview(edge, 'flagged')}
                      >
                        ⚡ Flag
                      </button>
                      <button
                        id={`reject-edge-${edge.id}`}
                        className="btn btn-danger btn-sm"
                        onClick={() => handleEdgeReview(edge, 'rejected')}
                      >
                        ✗ Suppress Edge
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      )}
    </div>
  )
}
