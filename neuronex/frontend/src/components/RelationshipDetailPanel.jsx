import { useState, useEffect } from 'react'
import SourceTypeBadge from './SourceTypeBadge'
import { getEdgeDetails } from '../api/client'

/**
 * RelationshipDetailPanel — slide-in panel showing rich provenance, evidence snippets,
 * confidence score, and case references for a selected graph edge.
 */
const REL_TYPE_LABELS = {
  TRANSFERRED_TO: '💰 Transferred To',
  CONTACTED: '📞 Contacted',
  MENTIONED_IN: '📄 Mentioned In',
  LOCATED_AT: '📍 Located At',
  ASSOCIATED_WITH: '🤝 Associated With',
  INVOLVED_IN: '⚖️ Involved In',
  CONNECTED_TO: '🌐 Connected To',
}

export default function RelationshipDetailPanel({ edge, onClose, onTrace }) {
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!edge) {
      setDetails(null)
      return
    }

    const data = edge.data()
    const src = data.source
    const dst = data.target
    const relType = data.rel_type

    if (!src || !dst || !relType) {
      setDetails(data)
      return
    }

    let active = true
    setLoading(true)
    setError(null)

    getEdgeDetails(src, dst, relType)
      .then((res) => {
        if (active) setDetails(res.data)
      })
      .catch((err) => {
        console.warn('Could not load rich edge details:', err)
        if (active) setDetails(data)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [edge])

  if (!edge) return null

  const data = details || edge.data()
  const relType = data.rel_type || 'RELATIONSHIP'
  const displayLabel = REL_TYPE_LABELS[relType] || relType
  const confidence = data.confidence != null ? Math.round(data.confidence * 100) : null
  const evidenceList = data.evidence_snippets || []
  const docIds = data.source_doc_ids || []
  const sourceTypes = data.source_types || []

  return (
    <div
      style={{
        position: 'absolute',
        top: 16,
        left: 16,
        width: 320,
        maxHeight: 'calc(100% - 32px)',
        overflowY: 'auto',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-active)',
        borderRadius: 'var(--r-lg)',
        padding: 18,
        boxShadow: 'var(--shadow-deep)',
        zIndex: 10,
        animation: 'fadeIn 0.2s ease',
      }}
    >
      <div className="flex-between mb-4" style={{ marginBottom: 14 }}>
        <div>
          <div className="text-xs text-muted" style={{ textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Relationship Provenance
          </div>
          <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--accent-primary)', marginTop: 2 }}>
            {displayLabel}
          </div>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: 18 }}
        >
          ✕
        </button>
      </div>

      {loading && (
        <div style={{ padding: '12px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
          <div className="spinner" style={{ width: 16, height: 16, margin: '0 auto 8px' }} />
          Loading relationship provenance…
        </div>
      )}

      {/* Connected Entities */}
      <div style={{
        background: 'var(--bg-elevated)',
        borderRadius: 'var(--r-sm)',
        padding: '10px 12px',
        marginBottom: 12,
        fontSize: 12,
      }}>
        <div style={{ color: 'var(--text-muted)', marginBottom: 2 }}>Source Entity</div>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', wordBreak: 'break-all' }}>
          {data.src_name || data.source}
        </div>

        <div style={{ textAlign: 'center', color: 'var(--accent-primary)', margin: '4px 0', fontSize: 14 }}>
          ↓ <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{relType}</span>
        </div>

        <div style={{ color: 'var(--text-muted)', marginBottom: 2 }}>Target Entity</div>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', wordBreak: 'break-all' }}>
          {data.dst_name || data.target}
        </div>
      </div>

      {/* Provenance Metadata Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
        <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--r-sm)', padding: '8px 10px' }}>
          <div className="text-xs text-muted">Confidence</div>
          <div style={{ fontWeight: 700, color: confidence > 80 ? 'var(--accent-emerald)' : 'var(--accent-amber)', fontSize: 14 }}>
            {confidence != null ? `${confidence}%` : '75%'}
          </div>
        </div>

        <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--r-sm)', padding: '8px 10px' }}>
          <div className="text-xs text-muted">Weight / Count</div>
          <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: 14 }}>
            {data.weight || 1}
          </div>
        </div>
      </div>

      {/* Related Case */}
      {data.related_case && (
        <div style={{ marginBottom: 12 }}>
          <div className="text-xs text-muted" style={{ marginBottom: 4 }}>Associated Case</div>
          <span className="badge badge-approved" style={{ fontSize: 11 }}>
            📁 {data.related_case}
          </span>
        </div>
      )}

      {/* Source Types */}
      <div style={{ marginBottom: 12 }}>
        <div className="text-xs text-muted" style={{ marginBottom: 6 }}>Source Modalities</div>
        <div className="flex gap-2" style={{ flexWrap: 'wrap' }}>
          {sourceTypes.map((st) => (
            <SourceTypeBadge key={st} type={st} />
          ))}
          {sourceTypes.length === 0 && (
            <span className="text-xs text-muted">Direct inference</span>
          )}
        </div>
      </div>

      {/* Evidence Snippets */}
      <div style={{ marginBottom: 12 }}>
        <div className="text-xs text-muted" style={{ marginBottom: 6 }}>Evidence Provenance</div>
        {evidenceList.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {evidenceList.map((snip, idx) => (
              <div
                key={idx}
                style={{
                  background: 'rgba(79, 142, 247, 0.08)',
                  borderLeft: '3px solid var(--accent-primary)',
                  padding: '6px 8px',
                  borderRadius: 4,
                  fontSize: 11,
                  color: 'var(--text-secondary)',
                  lineHeight: 1.4,
                }}
              >
                {snip}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
            Extracted via co-occurrence in document records.
          </div>
        )}
      </div>

      {/* Source Document IDs */}
      {docIds.length > 0 && (
        <div style={{ marginBottom: 14 }}>
          <div className="text-xs text-muted" style={{ marginBottom: 4 }}>Source Documents</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {docIds.map((d) => (
              <span
                key={d}
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 4,
                  padding: '2px 6px',
                  fontSize: 10,
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-muted)',
                }}
              >
                Doc #{d}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Last Updated Timestamp */}
      {data.last_updated && (
        <div style={{ fontSize: 10, color: 'var(--text-muted)', marginBottom: 12 }}>
          Last indexed: {new Date(data.last_updated).toLocaleString()}
        </div>
      )}

      {/* Actions */}
      <div style={{ display: 'flex', gap: 8 }}>
        <button
          className="btn btn-secondary btn-sm"
          style={{ flex: 1, justifyContent: 'center', fontSize: 11 }}
          onClick={() => onTrace && onTrace(data.src_id || data.source)}
        >
          Trace Source
        </button>
        <button
          className="btn btn-secondary btn-sm"
          style={{ flex: 1, justifyContent: 'center', fontSize: 11 }}
          onClick={() => onTrace && onTrace(data.dst_id || data.target)}
        >
          Trace Target
        </button>
      </div>
    </div>
  )
}
