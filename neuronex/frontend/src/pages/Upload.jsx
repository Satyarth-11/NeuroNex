import { useState, useEffect, useRef } from 'react'
import { uploadDocument, processDocument, listCases, listDocuments } from '../api/client'
import SourceTypeBadge from '../components/SourceTypeBadge'
import DocumentDetailModal from '../components/DocumentDetailModal'

const SOURCE_TYPES = [
  { value: 'fir',                 label: 'FIR / Police Reports',      accept: '.csv' },
  { value: 'cdr',                 label: 'Call Detail Records (CDR)', accept: '.csv' },
  { value: 'financial',           label: 'Financial Transactions',    accept: '.csv' },
  { value: 'surveillance',        label: 'Surveillance Reports',      accept: '.txt' },
  { value: 'social_media',        label: 'Social Media Intelligence', accept: '.csv' },
  { value: 'criminal_history',    label: 'Criminal History Database', accept: '.csv' },
  { value: 'intelligence_report', label: 'Intelligence Agency Reports', accept: '.txt' },
]

export default function Upload() {
  const [cases, setCases] = useState([])
  const [documents, setDocuments] = useState([])
  const [sourceType, setSourceType] = useState('fir')
  const [caseId, setCaseId] = useState('')
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState({})
  const [message, setMessage] = useState(null)
  const [selectedDocId, setSelectedDocId] = useState(null)
  const fileRef = useRef()

  useEffect(() => {
    listCases().then(r => setCases(r.data)).catch(() => {})
    listDocuments().then(r => setDocuments(r.data)).catch(() => {})
  }, [])

  function refreshDocs() {
    listDocuments().then(r => setDocuments(r.data)).catch(() => {})
  }

  async function handleUpload() {
    if (!file) { setMessage({ type: 'error', text: 'Please select a file.' }); return }
    setUploading(true)
    setMessage(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('source_type', sourceType)
      if (caseId) fd.append('case_id', caseId)
      const res = await uploadDocument(fd)
      setMessage({ type: 'success', text: `✓ Uploaded "${file.name}" (${res.data.record_count} records parsed).` })
      setFile(null)
      refreshDocs()
    } catch (e) {
      setMessage({ type: 'error', text: `Upload failed: ${e.response?.data?.detail || e.message}` })
    } finally {
      setUploading(false)
    }
  }

  async function handleProcess(docId) {
    setProcessing(p => ({ ...p, [docId]: true }))
    try {
      const res = await processDocument(docId)
      const r = res.data
      setMessage({
        type: 'success',
        text: `✓ Processed doc #${docId}: ${r.entities_extracted} entities, ${r.graph_nodes_upserted} graph nodes, ${r.resolution_candidates} resolution candidates.`
      })
      refreshDocs()
    } catch (e) {
      setMessage({ type: 'error', text: `Processing failed: ${e.response?.data?.detail || e.message}` })
    } finally {
      setProcessing(p => ({ ...p, [docId]: false }))
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">⬆️ Upload Investigative Data</h1>
        <p className="page-subtitle">All data must be <strong style={{ color: 'var(--accent-rose)' }}>SYNTHETIC</strong> — no real investigative records.</p>
      </div>

      <div className="grid-2">
        {/* Upload panel */}
        <div className="card">
          <div className="card-header"><div className="card-title">Upload New Document</div></div>

          <div className="form-group">
            <label htmlFor="source-type-select">Source Type</label>
            <select
              id="source-type-select"
              value={sourceType}
              onChange={e => setSourceType(e.target.value)}
            >
              {SOURCE_TYPES.map(st => (
                <option key={st.value} value={st.value}>{st.label}</option>
              ))}
            </select>
            <div style={{ marginTop: 6 }}>
              <SourceTypeBadge type={sourceType} />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="case-select">Associate with Case (optional)</label>
            <select id="case-select" value={caseId} onChange={e => setCaseId(e.target.value)}>
              <option value="">— No case —</option>
              {cases.map(c => (
                <option key={c.id} value={c.id}>{c.case_code} — {c.title}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>File</label>
            <div
              className={`upload-zone ${dragging ? 'drag-over' : ''}`}
              onClick={() => fileRef.current?.click()}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
            >
              <div className="upload-icon">{file ? '📄' : '📂'}</div>
              <div className="upload-text">{file ? file.name : 'Drop file here or click to browse'}</div>
              <div className="upload-hint">
                {SOURCE_TYPES.find(s => s.value === sourceType)?.accept || '.csv / .txt'}
              </div>
            </div>
            <input
              ref={fileRef}
              type="file"
              id="file-input"
              style={{ display: 'none' }}
              accept={SOURCE_TYPES.find(s => s.value === sourceType)?.accept}
              onChange={e => setFile(e.target.files[0])}
            />
          </div>

          {message && (
            <div style={{
              padding: '10px 14px',
              borderRadius: 'var(--r-md)',
              marginBottom: 16,
              fontSize: 13,
              background: message.type === 'error' ? 'rgba(244,63,94,0.1)' : 'rgba(16,185,129,0.1)',
              border: `1px solid ${message.type === 'error' ? 'rgba(244,63,94,0.3)' : 'rgba(16,185,129,0.3)'}`,
              color: message.type === 'error' ? 'var(--accent-rose)' : 'var(--accent-emerald)',
            }}>
              {message.text}
            </div>
          )}

          <button
            id="upload-btn"
            className="btn btn-primary btn-lg"
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={handleUpload}
            disabled={uploading || !file}
          >
            {uploading ? '⏳ Uploading…' : '⬆️ Upload Document'}
          </button>
        </div>

        {/* Documents list */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Uploaded Documents</div>
            <button className="btn btn-secondary btn-sm" onClick={refreshDocs}>↻ Refresh</button>
          </div>

          {documents.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <div className="empty-title">No documents yet</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {documents.map(doc => (
                <div
                  key={doc.id}
                  id={`doc-card-${doc.id}`}
                  onClick={() => setSelectedDocId(doc.id)}
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--r-md)',
                    padding: '12px 14px',
                    cursor: 'pointer',
                    transition: 'border-color 0.15s ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--accent-primary)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
                >
                  <div className="flex-between" style={{ marginBottom: 6 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>
                      {doc.filename}
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <span className={`badge badge-${doc.status === 'processed' ? 'approved' : doc.status === 'failed' ? 'rejected' : 'pending'}`}>
                        {doc.status}
                      </span>
                      <span className="text-xs text-muted">View ↗</span>
                    </div>
                  </div>
                  <div className="flex gap-2" style={{ marginBottom: 8, alignItems: 'center' }}>
                    <SourceTypeBadge type={doc.source_type} />
                    <span className="text-xs text-muted">{doc.record_count} records</span>
                  </div>
                  {doc.status === 'uploaded' && (
                    <button
                      id={`process-doc-${doc.id}`}
                      className="btn btn-primary btn-sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleProcess(doc.id)
                      }}
                      disabled={!!processing[doc.id]}
                    >
                      {processing[doc.id] ? '⏳ Processing…' : '▶ Process → KG'}
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {selectedDocId && (
        <DocumentDetailModal
          docId={selectedDocId}
          onClose={() => setSelectedDocId(null)}
        />
      )}
    </div>
  )
}
