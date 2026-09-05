import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { listCases, createCase } from '../api/client'

export default function Cases() {
  const navigate = useNavigate()
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ case_code: '', title: '', description: '' })
  const [creating, setCreating] = useState(false)
  const [showAll, setShowAll] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const r = await listCases()
      setCases(r.data || [])
    } finally {
      setLoading(false)
    }
  }

  const displayedCases = showAll ? cases : cases.slice(0, 10)

  async function handleCreate(e) {
    e.preventDefault()
    if (!form.case_code || !form.title) {
      setError('Case code and title are required.')
      return
    }
    setCreating(true)
    setError(null)
    try {
      await createCase(form)
      setForm({ case_code: '', title: '', description: '' })
      load()
    } catch (ex) {
      setError(ex.response?.data?.detail || ex.message)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">📁 Investigation Cases</h1>
        <p className="page-subtitle">Create, monitor, and explore multi-source investigative cases. Click any case to open its dedicated workspace.</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header"><div className="card-title">Create New Case</div></div>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label htmlFor="case-code">Case Code</label>
              <input
                id="case-code"
                placeholder="e.g. CASE-2024-015"
                value={form.case_code}
                onChange={e => setForm(f => ({ ...f, case_code: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label htmlFor="case-title">Title</label>
              <input
                id="case-title"
                placeholder="Brief case title"
                value={form.title}
                onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label htmlFor="case-desc">Description</label>
              <textarea
                id="case-desc"
                rows={3}
                placeholder="Brief description of the investigation"
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              />
            </div>
            {error && <div className="text-danger text-sm mb-4" style={{ marginBottom: 12 }}>{error}</div>}
            <button id="create-case-btn" className="btn btn-primary" type="submit" disabled={creating}>
              {creating ? '⏳ Creating…' : '+ Create Case'}
            </button>
          </form>
        </div>

        <div className="card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div className="card-title">Active Investigation Cases</div>
              <div className="text-xs text-muted" style={{ marginTop: 2 }}>
                {cases.length} Total Cases · Showing {displayedCases.length} of {cases.length}
              </div>
            </div>
            {cases.length > 10 && (
              <button
                id="toggle-cases-top-btn"
                className="btn btn-secondary btn-sm"
                onClick={() => setShowAll(s => !s)}
                style={{ fontSize: 12, padding: '5px 12px' }}
              >
                {showAll ? 'Show Less' : 'Show All Cases'}
              </button>
            )}
          </div>
          {loading ? (
            <div className="loading-container"><div className="spinner" /></div>
          ) : cases.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <div className="empty-title">No cases yet</div>
              <div className="empty-desc">Create your first investigation case or click "Load Demo Data" on Overview.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {displayedCases.map(c => (
                <div
                  key={c.id}
                  id={`case-card-${c.id}`}
                  onClick={() => navigate(`/cases/${c.id}`)}
                  style={{
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--r-md)',
                    padding: '14px 16px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--accent-primary)'
                    e.currentTarget.style.transform = 'translateY(-1px)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'var(--border-subtle)'
                    e.currentTarget.style.transform = 'none'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                    <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
                      {c.title}
                    </div>
                    <span style={{ color: 'var(--accent-primary)', fontSize: 14 }}>→</span>
                  </div>

                  <div className="monospace text-xs text-accent" style={{ marginBottom: 6 }}>
                    {c.case_code}
                  </div>

                  {c.description && (
                    <div className="text-sm text-muted" style={{ marginBottom: 10, lineHeight: 1.4 }}>
                      {c.description}
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <span className="badge badge-proposed" style={{ fontSize: 11 }}>
                      📄 {c.document_count ?? 0} Documents
                    </span>
                    <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', fontSize: 11 }}>
                      👤 {c.entity_count ?? 0} Entities
                    </span>
                    <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', fontSize: 11 }}>
                      🔗 {c.relationship_count ?? 0} Relationships
                    </span>
                    <span className="text-xs text-muted" style={{ marginLeft: 'auto' }}>
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}

              {cases.length > 10 && (
                <div style={{ textAlign: 'center', marginTop: 8 }}>
                  <button
                    id="toggle-cases-bottom-btn"
                    className="btn btn-outline btn-sm"
                    onClick={() => setShowAll(s => !s)}
                    style={{ minWidth: 160 }}
                  >
                    {showAll ? '▲ Show Less (First 10 Cases)' : `▼ Show All ${cases.length} Cases`}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
