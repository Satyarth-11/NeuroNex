import { useState, useEffect, useRef } from 'react'
import { useLocation, useSearchParams } from 'react-router-dom'
import GraphCanvas from '../components/GraphCanvas'
import SourceTypeBadge from '../components/SourceTypeBadge'
import {
  getGraph,
  getNeighbors,
  searchGraphEntities,
  listCases,
} from '../api/client'

const ENTITY_TYPES = ['Person', 'Phone', 'Location', 'Vehicle', 'Organisation', 'Case', 'Account']
const SOURCE_TYPES = ['fir', 'cdr', 'financial', 'surveillance', 'social_media', 'criminal_history', 'intelligence_report']
const RELATIONSHIP_TYPES = ['MENTIONED_IN', 'ASSOCIATED_WITH', 'CALLED', 'TRANSFERRED_TO', 'RESOLVED_TO']

export default function KnowledgeGraph() {
  const [searchParams] = useSearchParams()
  const location = useLocation()

  const [elements, setElements] = useState({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(false)
  const [hasSelection, setHasSelection] = useState(false)
  const [cases, setCases] = useState([])
  const [selectedCase, setSelectedCase] = useState('')

  // Search autocomplete states
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [showResults, setShowResults] = useState(false)

  // Filters
  const [entityFilter, setEntityFilter] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [relFilter, setRelFilter] = useState('')

  // Cytoscape ref for controls (Fit)
  const cyInstanceRef = useRef(null)

  // Track expanded node IDs for collapse functionality
  const expandedHistoryRef = useRef(new Map())

  useEffect(() => {
    listCases().then(r => setCases(r.data || [])).catch(() => {})
  }, [])

  // Refetch when filters change if graph is currently populated
  useEffect(() => {
    if (hasSelection && (selectedCase || isFullNetwork)) {
      fetchTargetedGraph()
    }
  }, [entityFilter, sourceFilter, relFilter])

  // Auto-select entity if passed via query param or route state
  useEffect(() => {
    const eid = searchParams.get('entityId') || location.state?.entityId
    const ename = searchParams.get('entityName') || location.state?.entityName
    if (eid) {
      handleSelectNode(eid, ename || eid)
    }
  }, [searchParams, location.state])

  // Live search autocomplete
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([])
      return
    }
    const timer = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await searchGraphEntities(searchQuery.trim())
        setSearchResults(res.data || [])
        setShowResults(true)
      } catch (e) {
        console.warn('Search graph error:', e)
      } finally {
        setSearching(false)
      }
    }, 250)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Select node from search or case selection
  async function handleSelectNode(nodeId, nodeName) {
    setShowResults(false)
    setSearchQuery(nodeName || nodeId)
    setLoading(true)
    try {
      const res = await getNeighbors(nodeId, 1)
      setElements(res.data)
      setHasSelection(true)
      expandedHistoryRef.current.clear()
    } catch (err) {
      console.error('Failed to get neighbors for node:', err)
    } finally {
      setLoading(false)
    }
  }

  const [isFullNetwork, setIsFullNetwork] = useState(false)
  const [graphMeta, setGraphMeta] = useState({ case_code: '', depth: 1, limit: 40 })

  const [graphError, setGraphError] = useState(null)
  const [emptyReason, setEmptyReason] = useState(null)

  // Trigger graph load whenever case, filters, or view mode changes
  async function fetchTargetedGraph(params = {}) {
    setLoading(true)
    setGraphError(null)
    try {
      const qParams = {
        limit: params.limit || (isFullNetwork ? 150 : 40),
        depth: params.depth || 1,
      }
      if (selectedCase) qParams.case_code = selectedCase
      if (params.case_code !== undefined) qParams.case_code = params.case_code
      if (entityFilter) qParams.entity_type = entityFilter
      if (sourceFilter) qParams.source_type = sourceFilter
      if (relFilter) qParams.relationship_type = relFilter

      const res = await getGraph(qParams)
      setElements(res.data)
      setEmptyReason(res.data.empty_reason || null)
      setHasSelection(true)
      setGraphMeta({
        case_code: res.data.case_code || qParams.case_code || '',
        depth: qParams.depth,
        limit: qParams.limit,
      })
      expandedHistoryRef.current.clear()
    } catch (err) {
      console.error('Failed to get graph:', err)
      setGraphError(err.response?.data?.detail || err.message || 'Neo4j service error')
      setHasSelection(true)
    } finally {
      setLoading(false)
    }
  }

  // Case dropdown change
  async function handleCaseSelect(caseCode) {
    setSelectedCase(caseCode)
    setIsFullNetwork(false)
    if (!caseCode) {
      setElements({ nodes: [], edges: [] })
      setHasSelection(false)
      return
    }
    await fetchTargetedGraph({ case_code: caseCode, limit: 40 })
  }

  // Load entire graph on user request (Full Network View)
  async function handleLoadFullGraph() {
    setIsFullNetwork(true)
    setSelectedCase('')
    await fetchTargetedGraph({ case_code: '', limit: 200 })
  }

  // Expand neighbors of a node
  async function handleExpand(nodeId) {
    try {
      const res = await getNeighbors(nodeId, 1)
      const newNodes = res.data.nodes || []
      const newEdges = res.data.edges || []

      setElements(prev => {
        const existingNodeIds = new Set(prev.nodes.map(n => n.data.id))
        const existingEdgeIds = new Set(prev.edges.map(e => e.data.id))

        const addedNodes = newNodes.filter(n => !existingNodeIds.has(n.data.id))
        const addedEdges = newEdges.filter(e => !existingEdgeIds.has(e.data.id))

        // Record history for collapse
        expandedHistoryRef.current.set(nodeId, addedNodes.map(n => n.data.id))

        return {
          nodes: [...prev.nodes, ...addedNodes],
          edges: [...prev.edges, ...addedEdges],
        }
      })
    } catch (err) {
      console.error('Failed to expand node:', err)
    }
  }

  // Collapse neighbors of a node
  function handleCollapse(nodeId) {
    const addedNodeIds = expandedHistoryRef.current.get(nodeId)
    if (!addedNodeIds || addedNodeIds.length === 0) return

    const toRemove = new Set(addedNodeIds)
    setElements(prev => ({
      nodes: prev.nodes.filter(n => !toRemove.has(n.data.id)),
      edges: prev.edges.filter(e => !toRemove.has(e.data.source) && !toRemove.has(e.data.target)),
    }))
    expandedHistoryRef.current.delete(nodeId)
  }

  // Reset graph to empty state prompt
  function handleReset() {
    setElements({ nodes: [], edges: [] })
    setHasSelection(false)
    setSearchQuery('')
    setSelectedCase('')
    expandedHistoryRef.current.clear()
  }

  // Fit graph in Cytoscape viewport
  function handleFit() {
    if (cyInstanceRef.current) {
      cyInstanceRef.current.fit(undefined, 30)
    }
  }

  const nodeCount = elements.nodes?.length || 0
  const edgeCount = elements.edges?.length || 0

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
      <div className="page-header" style={{ marginBottom: 12 }}>
        <h1 className="page-title">🕸️ Targeted Knowledge Graph Explorer</h1>
        <p className="page-subtitle">
          Query-first interactive subgraphs · <strong style={{ color: 'var(--accent-rose)' }}>SYNTHETIC DATA ONLY</strong> · SIH26189
        </p>
      </div>

      {/* Control Bar: Search + Case Filter + Type Filters + Actions */}
      <div className="card" style={{ marginBottom: 14, padding: '12px 18px', zIndex: 20 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Autocomplete Search */}
          <div style={{ position: 'relative', minWidth: 240, flex: 1 }}>
            <label style={{ marginBottom: 4, display: 'block', fontSize: 11, fontWeight: 600 }}>
              🔍 Search Entity (Person, Phone, Vehicle, Org)
            </label>
            <input
              id="graph-search-input"
              type="text"
              placeholder="e.g. Vikram Singh, MH02AB1234, +9198..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onFocus={() => searchResults.length > 0 && setShowResults(true)}
              style={{ width: '100%', padding: '7px 10px', fontSize: 13 }}
            />
            {searching && (
              <span style={{ position: 'absolute', right: 10, top: 28, fontSize: 11, color: 'var(--text-muted)' }}>
                Searching…
              </span>
            )}

            {/* Dropdown Menu for Autocomplete */}
            {showResults && searchResults.length > 0 && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  background: 'var(--bg-card, #1e293b)',
                  border: '1px solid var(--border-active)',
                  borderRadius: 'var(--r-md)',
                  boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)',
                  maxHeight: 250,
                  overflowY: 'auto',
                  marginTop: 4,
                  zIndex: 999,
                }}
              >
                {searchResults.map((item, i) => (
                  <div
                    key={i}
                    onClick={() => handleSelectNode(item.id, item.name)}
                    style={{
                      padding: '8px 12px',
                      cursor: 'pointer',
                      borderBottom: '1px solid var(--border-subtle)',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      transition: 'background 0.1s ease',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-elevated)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--text-primary)' }}>{item.name}</div>
                      <div className="text-xs text-muted monospace">{item.id}</div>
                    </div>
                    <span className="badge badge-proposed" style={{ fontSize: 10 }}>{item.entity_type}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Case Filter Dropdown */}
          <div style={{ minWidth: 170 }}>
            <label style={{ marginBottom: 4, display: 'block', fontSize: 11, fontWeight: 600 }}>
              📁 Filter by Case
            </label>
            <select
              id="graph-case-filter"
              value={selectedCase}
              onChange={e => handleCaseSelect(e.target.value)}
              style={{ padding: '7px 10px', fontSize: 13, width: '100%' }}
            >
              <option value="">— Select Case —</option>
              {cases.map(c => (
                <option key={c.id} value={c.case_code}>
                  {c.case_code} ({c.title})
                </option>
              ))}
            </select>
          </div>

          {/* Entity Type Filter */}
          <div style={{ minWidth: 130 }}>
            <label style={{ marginBottom: 4, display: 'block', fontSize: 11, fontWeight: 600 }}>
              🏷️ Entity Type
            </label>
            <select
              id="graph-entity-filter"
              value={entityFilter}
              onChange={e => setEntityFilter(e.target.value)}
              style={{ padding: '7px 10px', fontSize: 13, width: '100%' }}
            >
              <option value="">All Entities</option>
              {ENTITY_TYPES.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          {/* Source Type Filter */}
          <div style={{ minWidth: 130 }}>
            <label style={{ marginBottom: 4, display: 'block', fontSize: 11, fontWeight: 600 }}>
              📄 Source Type
            </label>
            <select
              id="graph-source-filter"
              value={sourceFilter}
              onChange={e => setSourceFilter(e.target.value)}
              style={{ padding: '7px 10px', fontSize: 13, width: '100%' }}
            >
              <option value="">All Sources</option>
              {SOURCE_TYPES.map(st => (
                <option key={st} value={st}>{st.replace('_', ' ')}</option>
              ))}
            </select>
          </div>

          {/* Relationship Type Filter */}
          <div style={{ minWidth: 140 }}>
            <label style={{ marginBottom: 4, display: 'block', fontSize: 11, fontWeight: 600 }}>
              🔗 Edge Type
            </label>
            <select
              id="graph-rel-filter"
              value={relFilter}
              onChange={e => setRelFilter(e.target.value)}
              style={{ padding: '7px 10px', fontSize: 13, width: '100%' }}
            >
              <option value="">All Relationships</option>
              {RELATIONSHIP_TYPES.map(rt => (
                <option key={rt} value={rt}>{rt}</option>
              ))}
            </select>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginLeft: 'auto', marginTop: 12 }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {hasSelection && (
                <>
                  <button
                    id="fit-graph-btn"
                    className="btn btn-outline btn-sm"
                    onClick={handleFit}
                    title="Fit graph into viewport"
                    style={{ padding: '7px 12px' }}
                  >
                    🎯 Fit Graph
                  </button>
                  <button
                    id="reset-graph-btn"
                    className="btn btn-outline btn-sm"
                    onClick={handleReset}
                    title="Clear graph back to targeted search"
                    style={{ padding: '7px 12px' }}
                  >
                    ↺ Reset View
                  </button>
                </>
              )}

              {!hasSelection && (
                <button
                  id="load-full-graph-btn"
                  className="btn btn-secondary btn-sm"
                  onClick={handleLoadFullGraph}
                  style={{ padding: '7px 14px' }}
                >
                  🌐 Full Network View
                </button>
              )}

              {hasSelection && (
                <div className="text-sm" style={{ paddingLeft: 8 }}>
                  <span className="text-muted">Nodes: </span>
                  <strong className="text-accent">{nodeCount}</strong>
                  <span className="text-muted" style={{ marginLeft: 8 }}>Edges: </span>
                  <strong className="text-accent">{edgeCount}</strong>
                </div>
              )}
            </div>

            {!hasSelection && (
              <span className="text-xs text-muted" style={{ fontSize: 10, fontStyle: 'italic' }}>
                ⚠️ Large networks may render as a dense, harder-to-read graph.
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Graph Statistics Banner */}
      {hasSelection && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '6px 14px',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--r-sm)',
          fontSize: 12,
          marginBottom: 8,
        }}>
          <div>
            <span className="text-muted">Scope: </span>
            <strong>{graphMeta.case_code ? `Case ${graphMeta.case_code}` : isFullNetwork ? 'Full Network View' : 'Targeted Ego-Network'}</strong>
            <span className="text-muted" style={{ margin: '0 8px' }}>·</span>
            <span className="text-muted">Nodes: </span><strong>{nodeCount}</strong>
            <span className="text-muted" style={{ margin: '0 8px' }}>·</span>
            <span className="text-muted">Relationships: </span><strong>{edgeCount}</strong>
            <span className="text-muted" style={{ margin: '0 8px' }}>·</span>
            <span className="text-muted">Depth: </span><strong>{graphMeta.depth || 1}</strong>
          </div>
          <span className="text-muted text-xs">
            {isFullNetwork ? 'Hover over edges to view relationship types' : 'Showing targeted relationships with active labels'}
          </span>
        </div>
      )}

      {/* Graph Display Area / Empty State Prompt */}
      <div
        style={{
          flex: 1,
          borderRadius: 'var(--r-lg)',
          overflow: 'hidden',
          border: '1px solid var(--border-subtle)',
          position: 'relative',
          background: 'var(--bg-base, #0b1120)',
        }}
      >
        {!hasSelection && !loading ? (
          <div
            className="empty-state fade-in"
            style={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              padding: 40,
            }}
          >
            <div style={{ fontSize: 48, marginBottom: 16 }}>🕸️</div>
            <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>
              Select an Entity or Case to Explore its Targeted Network
            </div>
            <div className="text-muted" style={{ maxWidth: 540, lineHeight: 1.5, textAlign: 'center', marginBottom: 16 }}>
              To prevent unreadable dense network "hairballs", NeuroNex loads focused subgraphs on demand.
              Search for a person, vehicle, phone number above, choose a case, or load the entire graph.
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <button className="btn btn-primary" onClick={handleLoadFullGraph}>
                Full Network View
              </button>
              <span className="text-xs text-muted" style={{ fontSize: 11 }}>
                ⚠️ Large networks may render as a dense, harder-to-read graph.
              </span>
            </div>
          </div>
        ) : (
          <GraphCanvas
            elements={elements}
            loading={loading}
            isFullNetwork={isFullNetwork}
            emptyReason={emptyReason}
            caseCode={selectedCase || graphMeta.case_code}
            activeFilters={{ entity: entityFilter, source: sourceFilter, rel: relFilter }}
            errorMessage={graphError}
            onExpand={handleExpand}
            onCollapse={handleCollapse}
            onCyReady={(cy) => {
              cyInstanceRef.current = cy
            }}
          />
        )}
      </div>
    </div>
  )
}
