import SourceTypeBadge from './SourceTypeBadge'

/** InsightCard — renders a single AI-generated insight with all traceability info */
export default function InsightCard({ insight, onReview }) {
  const statusColors = {
    proposed: 'badge-proposed',
    approved: 'badge-approved',
    rejected: 'badge-rejected',
    flagged:  'badge-flagged',
  }

  const typeIcon = {
    central_entity:    '🎯',
    community:         '🕸️',
    possible_duplicate:'🔀',
    relationship_path: '🛤️',
    suspicious_pattern:'⚡',
  }

  return (
    <div className="insight-card fade-in">
      <div className="insight-header">
        <div>
          <div className="flex gap-2 mb-4" style={{ marginBottom: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 18 }}>{typeIcon[insight.insight_type] || '💡'}</span>
            <span className={`badge ${statusColors[insight.status] || 'badge-proposed'}`}>
              {insight.status}
            </span>
            <span className="badge" style={{ background: 'rgba(79,142,247,0.1)', color: '#4f8ef7' }}>
              {insight.insight_type.replace('_', ' ')}
            </span>
          </div>
          <div className="insight-title">{insight.title}</div>
        </div>
        <div className="insight-confidence text-accent" style={{ whiteSpace: 'nowrap', fontSize: 12, fontFamily: 'monospace' }}>
          conf: {(insight.confidence * 100).toFixed(0)}%
        </div>
      </div>

      <div className="insight-explanation">{insight.explanation}</div>

      <div className="insight-meta">
        {insight.contributing_source_types?.map(st => (
          <SourceTypeBadge key={st} type={st} />
        ))}
      </div>

      {(insight.sample_size != null || insight.comparison_basis) && (
        <div style={{
          marginTop: 8,
          marginBottom: 8,
          padding: '6px 10px',
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--r-sm)',
          fontSize: 11,
          display: 'flex',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 6,
        }}>
          <span className="text-muted">📊 Statistical Basis:</span>
          <span style={{ fontWeight: 600 }}>{insight.comparison_basis || `n=${insight.sample_size}`}</span>
          {insight.sample_size != null && insight.sample_size < 10 && (
            <span className="badge badge-flagged" style={{ fontSize: 10 }}>
              Small-Sample Caveat (n &lt; 10)
            </span>
          )}
        </div>
      )}

      <div className="decision-notice">
        ⚠️ <strong>Decision Support Only.</strong> This AI-generated lead requires human analyst
        review before any investigative action. It does not constitute a finding of guilt or an
        official conclusion.
      </div>

      {onReview && insight.status === 'proposed' && (
        <div className="flex gap-2 mt-4" style={{ marginTop: 16 }}>
          <button
            id={`approve-insight-${insight.id}`}
            className="btn btn-success btn-sm"
            onClick={() => onReview(insight.id, 'approved')}
          >
            ✓ Approve
          </button>
          <button
            id={`reject-insight-${insight.id}`}
            className="btn btn-danger btn-sm"
            onClick={() => onReview(insight.id, 'rejected')}
          >
            ✗ Reject
          </button>
          <button
            id={`flag-insight-${insight.id}`}
            className="btn btn-secondary btn-sm"
            onClick={() => onReview(insight.id, 'flagged')}
          >
            🚩 Flag
          </button>
        </div>
      )}
    </div>
  )
}
