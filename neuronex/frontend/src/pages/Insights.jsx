import { useState, useEffect } from 'react'
import { listInsights, reviewInsight, regenerateInsights } from '../api/client'
import InsightCard from '../components/InsightCard'

const STATUS_FILTERS = ['all', 'proposed', 'approved', 'rejected', 'flagged']
const TYPE_FILTERS = ['all', 'central_entity', 'community', 'possible_duplicate', 'relationship_path', 'suspicious_pattern']

export default function Insights() {
  const [insights, setInsights] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [regenerating, setRegenerating] = useState(false)

  useEffect(() => { load() }, [statusFilter, typeFilter])

  async function load() {
    setLoading(true)
    try {
      const params = {}
      if (statusFilter !== 'all') params.status = statusFilter
      if (typeFilter !== 'all') params.insight_type = typeFilter
      const r = await listInsights(params)
      setInsights(r.data)
    } finally { setLoading(false) }
  }

  async function handleReview(insightId, decision) {
    try {
      await reviewInsight(insightId, { decision, analyst_id: 'analyst_01', notes: '' })
      load()
    } catch (e) {
      console.error('Review failed', e)
    }
  }

  async function handleRegenerate() {
    setRegenerating(true)
    try { await regenerateInsights(); load() }
    finally { setRegenerating(false) }
  }

  const proposed = insights.filter(i => i.status === 'proposed').length
  const approved = insights.filter(i => i.status === 'approved').length

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">💡 AI-Generated Insights</h1>
        <p className="page-subtitle">
          Explainable leads from <strong style={{ color: 'var(--accent-rose)' }}>SYNTHETIC</strong> data analysis.
          Each insight names its source evidence. Human review required for all.
        </p>
      </div>

      {/* Stats row */}
      <div className="stat-grid" style={{ marginBottom: 24 }}>
        {[
          { label: 'Total', value: insights.length, icon: '💡' },
          { label: 'Pending Review', value: proposed, icon: '⏳' },
          { label: 'Approved', value: approved, icon: '✅' },
          { label: 'Rejected/Flagged', value: insights.length - proposed - approved, icon: '❌' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-icon">{s.icon}</div>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="card" style={{ marginBottom: 20, padding: '12px 20px' }}>
        <div className="flex-between" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div className="flex gap-3" style={{ flexWrap: 'wrap' }}>
            <div>
              <label style={{ fontSize: 11, marginBottom: 4, display: 'block' }}>Status</label>
              <select
                id="insight-status-filter"
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                style={{ padding: '6px 10px', fontSize: 13 }}
              >
                {STATUS_FILTERS.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize: 11, marginBottom: 4, display: 'block' }}>Type</label>
              <select
                id="insight-type-filter"
                value={typeFilter}
                onChange={e => setTypeFilter(e.target.value)}
                style={{ padding: '6px 10px', fontSize: 13 }}
              >
                {TYPE_FILTERS.map(t => <option key={t}>{t.replace('_', ' ')}</option>)}
              </select>
            </div>
          </div>
          <button
            id="regenerate-insights-btn"
            className="btn btn-secondary btn-sm"
            onClick={handleRegenerate}
            disabled={regenerating}
          >
            {regenerating ? '⏳ Regenerating…' : '🔄 Regenerate Insights'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading-container"><div className="spinner" />Loading insights…</div>
      ) : insights.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">💡</div>
          <div className="empty-title">No insights yet</div>
          <div className="empty-desc">Process documents to generate AI insights. Then click Regenerate.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {insights.map(insight => (
            <InsightCard
              key={insight.id}
              insight={insight}
              onReview={handleReview}
            />
          ))}
        </div>
      )}
    </div>
  )
}
