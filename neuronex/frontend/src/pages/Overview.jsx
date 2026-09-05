import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import StatCard from '../components/StatCard'
import SourceTypeBadge, { SOURCE_TYPE_META } from '../components/SourceTypeBadge'
import {
  sourcesSummary,
  getCentrality,
  getCommunities,
  listInsights,
  listCases,
  getKeyInfluencers,
  getPatterns,
  getHealth,
  seedDemoData,
  seedExpandedData,
  resetDemoData,
} from '../api/client'

// NOTE: A larger 500-case tier is possible in the future only after further profiling
// with the Fix 0 blocking strategy in place, and is out of scope for this pass.

export default function Overview() {
  const navigate = useNavigate()

  // 3-state metric containers: { loading: boolean, value/data: any, error: boolean }
  const [sourcesState, setSourcesState] = useState({ loading: true, data: [], error: false })
  const [statsState, setStatsState] = useState({ loading: true, data: null, error: false })
  const [casesState, setCasesState] = useState({ loading: true, items: [], count: null, error: false })
  const [communityState, setCommunityState] = useState({ loading: true, count: null, error: false })
  const [insightsState, setInsightsState] = useState({ loading: true, items: [], count: null, error: false })
  const [patternsState, setPatternsState] = useState({ loading: true, items: [], error: false })
  const [influencersState, setInfluencersState] = useState({ loading: true, items: [], error: false })
  const [healthState, setHealthState] = useState({ loading: true, data: null, error: false })

  // Demo data seeding & reset states
  const [seeding, setSeeding] = useState(null) // null | 'demo' | 'expanded'
  const [resetting, setResetting] = useState(false)
  const [statusMessage, setStatusMessage] = useState(null)
  const [statusType, setStatusType] = useState('info') // 'info' | 'success' | 'error'

  useEffect(() => {
    load()
  }, [])

  async function load() {
    // Set all to loading state
    setSourcesState(prev => ({ ...prev, loading: true }))
    setStatsState(prev => ({ ...prev, loading: true }))
    setCasesState(prev => ({ ...prev, loading: true }))
    setCommunityState(prev => ({ ...prev, loading: true }))
    setInsightsState(prev => ({ ...prev, loading: true }))
    setPatternsState(prev => ({ ...prev, loading: true }))
    setInfluencersState(prev => ({ ...prev, loading: true }))
    setHealthState(prev => ({ ...prev, loading: true }))

    const [srcRes, centRes, commRes, insRes, caseRes, infRes, patRes, healthRes] = await Promise.allSettled([
      sourcesSummary(),
      getCentrality(),
      getCommunities(),
      listInsights(),
      listCases(),
      getKeyInfluencers(3),
      getPatterns(),
      getHealth(),
    ])

    // Multi-source Ingestion
    if (srcRes.status === 'fulfilled') {
      setSourcesState({ loading: false, data: srcRes.value.data || [], error: false })
    } else {
      setSourcesState({ loading: false, data: [], error: true })
    }

    // Graph Centrality & Metrics
    if (centRes.status === 'fulfilled') {
      setStatsState({ loading: false, data: centRes.value.data?.stats || null, error: false })
    } else {
      setStatsState({ loading: false, data: null, error: true })
    }

    // Communities
    if (commRes.status === 'fulfilled') {
      setCommunityState({ loading: false, count: Array.isArray(commRes.value.data) ? commRes.value.data.length : null, error: false })
    } else {
      setCommunityState({ loading: false, count: null, error: true })
    }

    // Insights
    if (insRes.status === 'fulfilled') {
      const insList = insRes.value.data || []
      setInsightsState({
        loading: false,
        items: insList.slice(0, 3),
        count: insList.length,
        error: false,
      })
    } else {
      setInsightsState({ loading: false, items: [], count: null, error: true })
    }

    // Cases
    if (caseRes.status === 'fulfilled') {
      const caseList = caseRes.value.data || []
      setCasesState({
        loading: false,
        items: caseList.slice(0, 3),
        count: caseList.length,
        error: false,
      })
    } else {
      setCasesState({ loading: false, items: [], count: null, error: true })
    }

    // Key Influencers
    if (infRes.status === 'fulfilled') {
      setInfluencersState({ loading: false, items: (infRes.value.data || []).slice(0, 3), error: false })
    } else {
      setInfluencersState({ loading: false, items: [], error: true })
    }

    // Suspicious Patterns
    if (patRes.status === 'fulfilled') {
      setPatternsState({ loading: false, items: (patRes.value.data || []).slice(0, 3), error: false })
    } else {
      setPatternsState({ loading: false, items: [], error: true })
    }

    // Infrastructure Health
    if (healthRes.status === 'fulfilled') {
      setHealthState({ loading: false, data: healthRes.value.data || null, error: false })
    } else {
      setHealthState({ loading: false, data: null, error: true })
    }
  }

  // 10 Demo Cases Seeder
  async function handleSeedDemo() {
    setSeeding('demo')
    setStatusMessage('⚡ Seeding 10 demo cases with multi-source records and building graph...')
    setStatusType('info')
    try {
      const res = await seedDemoData()
      const data = res.data
      const rels = data.relationships_created ?? data.graph_edges
      const txs = data.transactions_created ?? '—'
      const comms = data.communications_created ?? '—'
      setStatusMessage(
        `✅ ${data.message || '10 demo cases seeded successfully!'} · Cases: ${data.cases_created} · Docs: ${data.documents_processed} · Entities: ${data.entities_extracted} · Relationships: ${rels} · Transactions: ${txs} · Communications: ${comms}`
      )
      setStatusType('success')
      await load()
    } catch (err) {
      console.error('Seed demo error:', err)
      const rawDetail = err.response?.data?.detail || err.message
      const detail = typeof rawDetail === 'object' ? JSON.stringify(rawDetail) : String(rawDetail)
      setStatusMessage(`❌ Seeding failed: ${detail}`)
      setStatusType('error')
    } finally {
      setSeeding(null)
    }
  }

  // 50 Expanded Cases Seeder (Additive)
  async function handleSeedExpanded() {
    setSeeding('expanded')
    setStatusMessage('🚀 Seeding 50 expanded investigative cases additively and processing documents...')
    setStatusType('info')
    try {
      const res = await seedExpandedData()
      const data = res.data
      const rels = data.relationships_created ?? data.graph_edges
      const txs = data.transactions_created ?? '—'
      const comms = data.communications_created ?? '—'
      setStatusMessage(
        `✅ ${data.message || '50 expanded cases seeded successfully!'} · Cases: ${data.cases_created} · Docs: ${data.documents_processed} · Entities: ${data.entities_extracted} · Relationships: ${rels} · Transactions: ${txs} · Communications: ${comms}`
      )
      setStatusType('success')
      await load()
    } catch (err) {
      console.error('Seed expanded error:', err)
      const rawDetail = err.response?.data?.detail || err.message
      const detail = typeof rawDetail === 'object' ? JSON.stringify(rawDetail) : String(rawDetail)
      setStatusMessage(`❌ Expanded seeding failed: ${detail}`)
      setStatusType('error')
    } finally {
      setSeeding(null)
    }
  }

  async function handleReset() {
    if (!window.confirm('⚠️ Are you sure you want to wipe all demo data? This will clear all cases, documents, entities, candidates, and empty the Neo4j graph.')) {
      return
    }
    setResetting(true)
    setStatusMessage('🧹 Resetting all demo data from SQLite and Neo4j...')
    setStatusType('info')
    try {
      await resetDemoData()
      setStatusMessage('✅ All demo data wiped clean. SQLite tables cleared and Neo4j graph emptied.')
      setStatusType('success')
      await load()
    } catch (err) {
      console.error('Reset error:', err)
      setStatusMessage(`❌ Reset failed: ${err.response?.data?.detail || err.message}`)
      setStatusType('error')
    } finally {
      setResetting(false)
    }
  }

  // Safe stat value renderer: loading -> "…", error -> "— Unable to load", value -> number
  const renderStat = (state, key = 'count', formatFn = null) => {
    if (state.loading) return '…'
    if (state.error || state[key] === null || state[key] === undefined) return '— Unable to load'
    if (formatFn) return formatFn(state[key])
    return Number(state[key]).toLocaleString()
  }

  const totalDocs = sourcesState.data.reduce((a, s) => a + (s.document_count || 0), 0)
  const totalRecords = sourcesState.data.reduce((a, s) => a + (s.record_count || 0), 0)

  // System Health Helpers
  const healthComponents = [
    { key: 'sqlite', label: 'Relational Database (SQLite)', status: healthState.data?.components?.sqlite || (healthState.data?.database === 'ok' ? 'Healthy' : (healthState.error ? 'Unavailable' : 'Healthy')) },
    { key: 'neo4j', label: 'Knowledge Graph (Neo4j)', status: healthState.data?.components?.neo4j || (healthState.data?.neo4j === 'ok' ? 'Healthy' : (healthState.error ? 'Unavailable' : 'Healthy')) },
    { key: 'nlp', label: 'NLP Pipeline (spaCy + Rules)', status: healthState.data?.components?.nlp || (healthState.error ? 'Unavailable' : 'Healthy') },
    { key: 'graph_analytics', label: 'Knowledge Graph Engine', status: healthState.data?.components?.graph_analytics || (healthState.error ? 'Unavailable' : 'Healthy') },
    { key: 'entity_resolution', label: 'Entity Resolution (rapidfuzz)', status: healthState.data?.components?.entity_resolution || (healthState.error ? 'Unavailable' : 'Healthy') },
    { key: 'backend', label: 'Analytics & Reasoning API', status: healthState.data?.components?.backend || (healthState.data?.backend === 'ok' ? 'Healthy' : (healthState.error ? 'Unavailable' : 'Healthy')) },
  ]

  const getStatusColor = (status) => {
    if (status === 'Healthy') return { text: '#10b981', bg: 'rgba(16, 185, 129, 0.15)', dot: '●' }
    if (status === 'Degraded') return { text: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', dot: '◐' }
    return { text: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', dot: '○' }
  }

  return (
    <div className="fade-in">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 className="page-title">🧠 NeuroNex Overview</h1>
          <p className="page-subtitle">
            Pre-Trained NLP & Graph Analytics · <strong style={{ color: 'var(--accent-rose)' }}>SYNTHETIC DATA ONLY</strong> · SIH26189
          </p>
        </div>

        {/* Multi-Tier Seeding & Reset Controls */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            id="seed-demo-btn"
            className="btn btn-primary"
            onClick={handleSeedDemo}
            disabled={Boolean(seeding) || resetting}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 16px', fontWeight: 600 }}
            title="Seed the default 10 investigative cases"
          >
            {seeding === 'demo' ? (
              <>
                <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                <span>Seeding 10 Cases…</span>
              </>
            ) : (
              <>
                <span>⚡</span>
                <span>Load Demo Data (10 cases)</span>
              </>
            )}
          </button>

          <button
            id="seed-expanded-btn"
            className="btn btn-outline"
            onClick={handleSeedExpanded}
            disabled={Boolean(seeding) || resetting}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '9px 16px',
              fontWeight: 600,
              borderColor: 'var(--accent-primary)',
              color: 'var(--accent-primary)',
            }}
            title="Seed the 50 expanded investigative cases additively"
          >
            {seeding === 'expanded' ? (
              <>
                <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                <span>Seeding 50 Cases…</span>
              </>
            ) : (
              <>
                <span>🚀</span>
                <span>+ 50 Expanded Cases</span>
              </>
            )}
          </button>

          <button
            id="reset-demo-btn"
            className="btn btn-outline"
            onClick={handleReset}
            disabled={Boolean(seeding) || resetting}
            style={{
              borderColor: 'var(--border-subtle)',
              color: 'var(--text-muted)',
              fontSize: 13,
              padding: '9px 14px',
            }}
            title="Wipe all cases, documents, entities, and clear the Neo4j graph"
          >
            {resetting ? 'Resetting…' : '🗑️ Reset Demo Data'}
          </button>
        </div>
      </div>

      {/* Status banner */}
      {statusMessage && (
        <div
          className="fade-in"
          style={{
            padding: '12px 16px',
            borderRadius: 'var(--r-md)',
            marginBottom: 20,
            fontSize: 13,
            lineHeight: 1.5,
            border: '1px solid',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor:
              statusType === 'success'
                ? 'rgba(16, 185, 129, 0.12)'
                : statusType === 'error'
                ? 'rgba(239, 68, 68, 0.12)'
                : 'rgba(79, 142, 247, 0.12)',
            borderColor:
              statusType === 'success'
                ? 'var(--accent-emerald)'
                : statusType === 'error'
                ? 'var(--accent-rose)'
                : 'var(--accent-primary)',
            color:
              statusType === 'success'
                ? 'var(--accent-emerald)'
                : statusType === 'error'
                ? 'var(--accent-rose)'
                : 'var(--accent-primary)',
          }}
        >
          <div>{statusMessage}</div>
          <button
            onClick={() => setStatusMessage(null)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              fontSize: 16,
              marginLeft: 12,
            }}
          >
            ✕
          </button>
        </div>
      )}

      <div className="decision-notice" style={{ marginBottom: 24 }}>
        ⚠️ <strong>Decision Support Tool Only.</strong> NeuroNex surfaces investigative leads from
        synthetic data. All insights require human analyst review. No output constitutes a legal finding.
      </div>

      {/* SECTION 1: Primary Stat Cards (3-state display: loading / real count / error) */}
      <div className="stat-grid" style={{ marginBottom: 28 }}>
        <StatCard
          icon="📁"
          value={renderStat(casesState, 'count')}
          label="Active Cases"
          accent
          onClick={() => navigate('/cases')}
        />
        <StatCard
          icon="📄"
          value={sourcesState.loading ? '…' : (sourcesState.error ? '— Unable to load' : totalDocs.toLocaleString())}
          label="Documents Ingested"
          onClick={() => navigate('/upload')}
        />
        <StatCard
          icon="📝"
          value={sourcesState.loading ? '…' : (sourcesState.error ? '— Unable to load' : totalRecords.toLocaleString())}
          label="Source Records"
          onClick={() => navigate('/upload')}
        />
        <StatCard
          icon="👤"
          value={statsState.loading ? '…' : (statsState.error || statsState.data?.node_count == null ? '— Unable to load' : statsState.data.node_count.toLocaleString())}
          label="Graph Nodes"
          onClick={() => navigate('/entities')}
        />
        <StatCard
          icon="🔗"
          value={statsState.loading ? '…' : (statsState.error || statsState.data?.edge_count == null ? '— Unable to load' : statsState.data.edge_count.toLocaleString())}
          label="Relationships"
          onClick={() => navigate('/graph')}
        />
        <StatCard
          icon="🔵"
          value={renderStat(communityState, 'count')}
          label="Communities"
          onClick={() => navigate('/communities')}
        />
        <StatCard
          icon="💡"
          value={renderStat(insightsState, 'count')}
          label="Insights Generated"
          onClick={() => navigate('/analyst-review')}
        />
        <StatCard
          icon="📈"
          value={statsState.loading ? '…' : (statsState.error || statsState.data?.density == null ? '— Unable to load' : statsState.data.density.toFixed(3))}
          label="Graph Density"
          sub="Network connectivity measure"
          onClick={() => navigate('/graph')}
        />
      </div>

      {/* SECTION 2: 4 Real Mini-Widgets (Recent Cases, Top Influential Entities, Recent Insights, Suspicious Patterns) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20, marginBottom: 28 }}>
        {/* 1. Recent Cases Mini-Widget */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="card-title" style={{ fontSize: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>📁</span> Recent Cases
            </div>
            <Link to="/cases" className="text-sm" style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}>
              View all →
            </Link>
          </div>
          {casesState.loading ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>Loading cases…</div>
          ) : casesState.error ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0', color: 'var(--accent-rose)' }}>— Unable to load recent cases.</div>
          ) : casesState.items.length === 0 ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>No active cases. Seed demo data to begin.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
              {casesState.items.map((c) => (
                <div
                  key={c.id}
                  onClick={() => navigate(`/cases/${c.id}`)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 6,
                    background: 'var(--bg-elevated)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    border: '1px solid var(--border-subtle)',
                    transition: 'border-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-primary)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  <div style={{ overflow: 'hidden', paddingRight: 8 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>{c.case_code}</div>
                    <div className="text-xs text-muted" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {c.title}
                    </div>
                  </div>
                  <span className="badge badge-proposed" style={{ fontSize: 11, flexShrink: 0 }}>
                    {c.document_count ?? 0} docs
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 2. Top Influential Entities Mini-Widget */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="card-title" style={{ fontSize: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>⭐</span> Top Influential Entities
            </div>
            <Link to="/analyst-review" className="text-sm" style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}>
              View all →
            </Link>
          </div>
          {influencersState.loading ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>Loading key influencers…</div>
          ) : influencersState.error ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0', color: 'var(--accent-rose)' }}>— Unable to load key influencers.</div>
          ) : influencersState.items.length === 0 ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>No network centralities computed yet.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
              {influencersState.items.map((inf) => (
                <div
                  key={inf.node_id || inf.name}
                  onClick={() => navigate('/analyst-review')}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 6,
                    background: 'var(--bg-elevated)',
                    cursor: 'pointer',
                    border: '1px solid var(--border-subtle)',
                    transition: 'border-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-primary)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>{inf.name}</span>
                    <span className="badge badge-primary" style={{ fontSize: 10 }}>PageRank: {inf.pagerank?.toFixed(3)}</span>
                  </div>
                  <div className="text-xs text-muted" style={{ display: 'flex', gap: 12 }}>
                    <span>Betweenness: {inf.betweenness_centrality?.toFixed(3)}</span>
                    {inf.related_cases?.length > 0 && <span>Cases: {inf.related_cases.length}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 3. Recent Investigative Insights Mini-Widget */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="card-title" style={{ fontSize: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>💡</span> Recent Insights
            </div>
            <Link to="/analyst-review" className="text-sm" style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}>
              View all →
            </Link>
          </div>
          {insightsState.loading ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>Loading insights…</div>
          ) : insightsState.error ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0', color: 'var(--accent-rose)' }}>— Unable to load insights.</div>
          ) : insightsState.items.length === 0 ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>No insights generated. Seed demo data to begin.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
              {insightsState.items.map((ins) => (
                <div
                  key={ins.id}
                  onClick={() => navigate('/analyst-review')}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 6,
                    background: 'var(--bg-elevated)',
                    cursor: 'pointer',
                    border: '1px solid var(--border-subtle)',
                    transition: 'border-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-primary)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  <div style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-primary)', marginBottom: 2 }}>
                    {ins.title}
                  </div>
                  <div className="text-xs text-muted" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {ins.explanation}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 4. Suspicious Patterns Mini-Widget */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div className="card-title" style={{ fontSize: 15, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>⚠️</span> Suspicious Patterns
            </div>
            <Link to="/analyst-review" className="text-sm" style={{ color: 'var(--accent-primary)', textDecoration: 'none', fontWeight: 600 }}>
              View all →
            </Link>
          </div>
          {patternsState.loading ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>Loading detected patterns…</div>
          ) : patternsState.error ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0', color: 'var(--accent-rose)' }}>— Unable to load patterns.</div>
          ) : patternsState.items.length === 0 ? (
            <div className="text-muted text-sm" style={{ padding: '16px 0' }}>No anomaly patterns currently flagged.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
              {patternsState.items.map((pat, pIdx) => (
                <div
                  key={pat.title || pIdx}
                  onClick={() => navigate('/analyst-review')}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 6,
                    background: 'var(--bg-elevated)',
                    cursor: 'pointer',
                    border: '1px solid var(--border-subtle)',
                    transition: 'border-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-primary)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <div style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-primary)' }}>{pat.title}</div>
                    <span className="badge badge-flagged" style={{ fontSize: 9 }}>{pat.pattern_type}</span>
                  </div>
                  <div className="text-xs text-muted" style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {pat.description}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* SECTION 3: Data Sources Ingestion Breakdown */}
      <div className="card mb-6" style={{ marginBottom: 28 }}>
        <div className="card-header">
          <div>
            <div className="card-title">📡 Multi-Source Ingestion Breakdown</div>
            <div className="card-subtitle">Ingestion counts across all 7 supported data modalities</div>
          </div>
          <span className="badge badge-rejected" style={{ fontSize: 10 }}>SYNTHETIC BENCHMARK</span>
        </div>

        {sourcesState.loading ? (
          <div className="loading-container"><div className="spinner" /></div>
        ) : sourcesState.error ? (
          <div className="text-muted text-sm" style={{ padding: '16px 0', color: 'var(--accent-rose)' }}>
            — Unable to load multi-source ingestion counts from backend.
          </div>
        ) : sourcesState.data.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <div className="empty-title">No data ingested yet</div>
            <div className="empty-desc">
              Click <strong>"Load Demo Data (10 cases)"</strong> above to seed the multi-case network, or upload files manually.
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 12 }}>
            {Object.keys(SOURCE_TYPE_META).map((st) => {
              const found = sourcesState.data.find(s => s.source_type === st)
              const docCount = found?.document_count ?? 0
              const recCount = found?.record_count ?? 0
              const pct = totalRecords > 0 ? (recCount / totalRecords) * 100 : 0

              return (
                <div key={st} style={{ display: 'grid', gridTemplateColumns: '180px 60px 1fr 70px', alignItems: 'center', gap: 16 }}>
                  <SourceTypeBadge type={st} />
                  <span className="text-sm" style={{ color: 'var(--text-muted)' }}>{docCount} docs</span>
                  <div style={{ background: 'var(--bg-elevated)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
                    <div style={{
                      width: `${pct}%`, height: '100%',
                      background: 'var(--grad-primary)',
                      transition: 'width 0.5s ease',
                      borderRadius: 4,
                    }} />
                  </div>
                  <span className="text-sm monospace" style={{ color: 'var(--text-secondary)', textAlign: 'right' }}>
                    {recCount} rec
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* SECTION 4: Independent System Infrastructure Health (Phase 4 & 11) */}
      <div className="card" style={{ marginBottom: 28 }}>
        <div className="card-header">
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>🛡️</span> System Infrastructure Health
          </div>
          <span
            className="badge"
            style={{
              backgroundColor: healthState.data?.overall_status === 'Healthy' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              color: healthState.data?.overall_status === 'Healthy' ? '#10b981' : '#f59e0b',
              fontSize: 11,
            }}
          >
            {healthState.loading ? 'Checking Health…' : (healthState.error ? 'Status Unavailable' : (healthState.data?.overall_status || 'Healthy'))}
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
          {healthComponents.map(comp => {
            const conf = getStatusColor(healthState.error ? 'Unavailable' : comp.status)
            return (
              <div key={comp.key} style={{ padding: '12px 14px', borderRadius: 8, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
                <div className="text-xs text-muted">{comp.label}</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: conf.text, marginTop: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>{conf.dot}</span>
                  <span>{healthState.error ? 'Unavailable' : comp.status}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* SECTION 5: Collapsed Technical Processing Pipeline */}
      <details style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--r-md)', padding: '14px 18px' }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: 14, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>🔄</span> Technical Processing Pipeline (Architecture View) ▾
        </summary>
        <div style={{ marginTop: 16, display: 'flex', gap: 0, overflowX: 'auto', paddingBottom: 8 }}>
          {[
            ['⬆️', 'Ingest', '7 source types'],
            ['🧹', 'Clean', 'Normalise'],
            ['🧠', 'NER', 'spaCy + regex'],
            ['🔀', 'Resolve', 'rapidfuzz'],
            ['🕸️', 'Graph', 'Neo4j'],
            ['📊', 'Analytics', 'NetworkX'],
            ['🔵', 'Cluster', 'Louvain'],
            ['💡', 'Explain', 'Rule-based'],
            ['🔍', 'Review', 'Analyst (HITL)'],
          ].map(([icon, label, sub], i) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
              <div style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--r-md)',
                padding: '10px 14px',
                textAlign: 'center',
                minWidth: 100,
              }}>
                <div style={{ fontSize: 20 }}>{icon}</div>
                <div style={{ fontWeight: 600, fontSize: 12, marginTop: 4, color: 'var(--text-primary)' }}>{label}</div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{sub}</div>
              </div>
              {i < 8 && (
                <div style={{ color: 'var(--text-muted)', padding: '0 6px', fontSize: 14 }}>→</div>
              )}
            </div>
          ))}
        </div>
      </details>
    </div>
  )
}
