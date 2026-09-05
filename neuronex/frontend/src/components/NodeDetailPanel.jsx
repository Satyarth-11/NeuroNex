import SourceTypeBadge from './SourceTypeBadge'

/** NodeDetailPanel — slide-in panel showing details for a selected graph node */
export default function NodeDetailPanel({ node, onClose, onTrace, onExpand, onCollapse }) {
  if (!node) return null
  const data = node.data()

  return (
    <div
      style={{
        position: 'absolute',
        top: 16, right: 16,
        width: 300,
        background: 'var(--bg-card)',
        border: '1px solid var(--border-active)',
        borderRadius: 'var(--r-lg)',
        padding: 20,
        boxShadow: 'var(--shadow-deep)',
        zIndex: 10,
        animation: 'fadeIn 0.2s ease',
      }}
    >
      <div className="flex-between mb-4" style={{ marginBottom: 16 }}>
        <div>
          <div className="text-xs text-muted" style={{ marginBottom: 4 }}>{data.entity_type}</div>
          <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-primary)' }}>
            {data.label || data.id}
          </div>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 18 }}
        >
          ✕
        </button>
      </div>

      <div style={{ marginBottom: 12 }}>
        <div className="text-xs text-muted" style={{ marginBottom: 6 }}>Source Types</div>
        <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
          {(data.source_types || []).map(st => (
            <SourceTypeBadge key={st} type={st} />
          ))}
          {(!data.source_types || data.source_types.length === 0) && (
            <span className="text-xs text-muted">Unknown</span>
          )}
        </div>
      </div>

      <div style={{
        background: 'var(--bg-elevated)',
        borderRadius: 'var(--r-sm)',
        padding: '10px 12px',
        marginBottom: 12,
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
      }}>
        <div style={{ color: 'var(--text-muted)', marginBottom: 2 }}>Node ID</div>
        <div style={{ color: 'var(--text-secondary)', wordBreak: 'break-all', fontSize: 11 }}>{data.id}</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: 10 }}>Mentions</div>
            <div style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>{data.mention_count || 1}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: 10 }}>Relationships</div>
            <div style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>
              {typeof node.connectedEdges === 'function' ? node.connectedEdges().length : '—'}
            </div>
          </div>
        </div>
      </div>

      {data.criminal_history_flag && (
        <div style={{
          background: 'rgba(245,158,11,0.1)',
          border: '1px solid rgba(245,158,11,0.3)',
          borderRadius: 'var(--r-sm)',
          padding: '8px 12px',
          fontSize: 12,
          color: '#f59e0b',
          marginBottom: 12,
        }}>
          ℹ️ <strong>Criminal history flag</strong> — informational context only.
          This is NOT an indication of current guilt.
        </div>
      )}

      <button
        id={`profile-node-${data.id?.slice(0, 8)}`}
        className="btn btn-secondary btn-sm"
        style={{ width: '100%', justifyContent: 'center', marginBottom: 8 }}
        onClick={() => onTrace(data.id)}
      >
        👤 Open Entity Profile
      </button>

      <div style={{ display: 'flex', gap: 8 }}>
        {onExpand && (
          <button
            className="btn btn-primary btn-sm"
            style={{ flex: 1, justifyContent: 'center', fontSize: 11 }}
            onClick={() => onExpand(data.id)}
            title="Fetch and display immediate neighbors of this node"
          >
            ➕ Expand 1 Hop
          </button>
        )}
        {onCollapse && (
          <button
            className="btn btn-outline btn-sm"
            style={{ flex: 1, justifyContent: 'center', fontSize: 11 }}
            onClick={() => onCollapse(data.id)}
            title="Collapse expanded neighbors"
          >
            ➖ Collapse
          </button>
        )}
      </div>
    </div>
  )
}
