import { useState, useEffect } from 'react'
import { getDocumentDetail } from '../api/client'
import SourceTypeBadge from './SourceTypeBadge'

export default function DocumentDetailModal({ docId, onClose }) {
  const [doc, setDoc] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!docId) return
    setLoading(true)
    setError(null)
    getDocumentDetail(docId)
      .then((res) => setDoc(res.data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load document details'))
      .finally(() => setLoading(false))
  }, [docId])

  if (!docId) return null

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
          maxWidth: 800,
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
            <span style={{ fontSize: 20 }}>📄</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{doc?.filename || 'Document Details'}</div>
              <div className="text-xs text-muted">ID #{docId}</div>
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
        ) : doc ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Metadata Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6 }}>
                <div className="text-xs text-muted">Source Modality</div>
                <div style={{ marginTop: 4 }}><SourceTypeBadge type={doc.source_type} /></div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6 }}>
                <div className="text-xs text-muted">Associated Case</div>
                <div style={{ marginTop: 4, fontWeight: 600, fontSize: 13 }}>
                  {doc.case_code ? `${doc.case_code}` : 'Unassigned'}
                </div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6 }}>
                <div className="text-xs text-muted">Processing Status</div>
                <div style={{ marginTop: 4 }}>
                  <span className={`badge badge-${doc.status === 'processed' ? 'approved' : doc.status === 'failed' ? 'rejected' : 'proposed'}`}>
                    {doc.status}
                  </span>
                </div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6 }}>
                <div className="text-xs text-muted">Ingested Timestamp</div>
                <div style={{ marginTop: 4, fontSize: 12 }} className="text-muted">
                  {new Date(doc.uploaded_at).toLocaleString()}
                </div>
              </div>
            </div>

            {/* Error Message banner if failed */}
            {doc.status === 'failed' && (
              <div
                style={{
                  padding: 12,
                  borderRadius: 6,
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid var(--accent-rose)',
                  color: 'var(--accent-rose)',
                  fontSize: 13,
                }}
              >
                <strong>Processing Error:</strong> {doc.error_message || 'An unhandled exception occurred during parsing/NER.'}
              </div>
            )}

            {/* Raw Text Excerpt */}
            <div>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>Source Text Content (Excerpt)</div>
              <div
                style={{
                  background: 'var(--bg-base, #0f172a)',
                  padding: 12,
                  borderRadius: 6,
                  fontFamily: 'monospace',
                  fontSize: 12,
                  maxHeight: 180,
                  overflowY: 'auto',
                  whiteSpace: 'pre-wrap',
                  color: 'var(--text-secondary)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                {doc.raw_text || '(No text content)'}
              </div>
            </div>

            {/* Extracted Entities List */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>
                  Extracted Entities ({doc.extracted_entities?.length || 0})
                </div>
                <span className="text-xs text-muted">via pre-trained spaCy NER & rule-based extractors</span>
              </div>
              {!doc.extracted_entities || doc.extracted_entities.length === 0 ? (
                <div className="text-muted text-xs" style={{ padding: 8 }}>
                  No entities extracted from this document.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8, maxHeight: 220, overflowY: 'auto' }}>
                  {doc.extracted_entities.map((ent, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '8px 10px',
                        background: 'var(--bg-elevated)',
                        borderRadius: 6,
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontWeight: 600, fontSize: 12 }}>{ent.text}</span>
                        <span className="badge badge-proposed" style={{ fontSize: 9 }}>{ent.entity_type}</span>
                      </div>
                      {ent.canonical_entity_id && (
                        <div className="text-xs text-muted monospace" style={{ fontSize: 10, marginTop: 2 }}>
                          {ent.canonical_entity_id}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
