import { useEffect, useRef, useState } from 'react'
import CytoscapeComponent from 'react-cytoscapejs'
import NodeDetailPanel from './NodeDetailPanel'
import RelationshipDetailPanel from './RelationshipDetailPanel'
import { useNavigate } from 'react-router-dom'

const getCytoscapeStyle = (isFullNetwork = false) => [
  {
    selector: 'node',
    style: {
      'background-color': 'data(color)',
      'label': 'data(label)',
      'color': '#e2e8f0',
      'font-size': 10,
      'font-family': 'Inter, sans-serif',
      'text-valign': 'bottom',
      'text-halign': 'center',
      'text-margin-y': 4,
      'width': 'mapData(mention_count, 1, 20, 22, 52)',
      'height': 'mapData(mention_count, 1, 20, 22, 52)',
      'border-width': 2,
      'border-color': '#1e2d45',
      'text-outline-width': 2,
      'text-outline-color': '#0d1321',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 3,
      'border-color': '#4f8ef7',
      'box-shadow': '0 0 16px #4f8ef7',
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 'mapData(weight, 1, 300, 1.5, 5)',
      'line-color': '#334e68',
      'target-arrow-color': '#334e68',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'opacity': 0.75,
      'label': isFullNetwork ? '' : 'data(rel_type)',
      'font-size': 8,
      'color': '#94a3b8',
      'text-rotation': 'autorotate',
      'text-background-opacity': isFullNetwork ? 0 : 0.8,
      'text-background-color': '#0b1120',
      'text-background-padding': 2,
    },
  },
  {
    selector: 'edge:selected',
    style: {
      'line-color': '#4f8ef7',
      'target-arrow-color': '#4f8ef7',
      'opacity': 1,
      'label': 'data(rel_type)',
      'font-size': 9,
      'color': '#ffffff',
      'text-background-opacity': 0.9,
      'text-background-color': '#1e293b',
    },
  },
  {
    selector: 'edge:hover',
    style: {
      'label': 'data(rel_type)',
      'line-color': '#60a5fa',
      'target-arrow-color': '#60a5fa',
      'opacity': 1,
      'text-background-opacity': 0.9,
      'text-background-color': '#0b1120',
    }
  }
]

export default function GraphCanvas({
  elements,
  loading,
  isFullNetwork = false,
  onExpand,
  onCollapse,
  onCyReady,
  emptyReason = null,
  caseCode = '',
  activeFilters = null,
  errorMessage = null,
}) {
  const cyRef = useRef(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedEdge, setSelectedEdge] = useState(null)
  const navigate = useNavigate()

  const handleCy = (cy) => {
    cyRef.current = cy
    if (onCyReady) onCyReady(cy)
    cy.removeAllListeners()
    cy.on('tap', 'node', (evt) => {
      setSelectedNode(evt.target)
      setSelectedEdge(null)
    })
    cy.on('tap', 'edge', (evt) => {
      setSelectedEdge(evt.target)
      setSelectedNode(null)
    })
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null)
        setSelectedEdge(null)
      }
    })
    if (elements?.nodes?.length) {
      cy.layout({
        name: 'cose',
        animate: true,
        animationDuration: 800,
        nodeRepulsion: 8000,
        idealEdgeLength: 80,
        padding: 40,
      }).run()
    }
  }

  useEffect(() => {
    const cy = cyRef.current
    if (!cy || !elements?.nodes?.length) return
    cy.layout({
      name: 'cose',
      animate: true,
      animationDuration: 600,
      nodeRepulsion: 8000,
      idealEdgeLength: 80,
      padding: 40,
    }).run()
  }, [elements?.nodes?.length, elements?.edges?.length])

  const cyElements = [
    ...(elements?.nodes || []),
    ...(elements?.edges || []),
  ]

  if (loading) {
    return (
      <div className="loading-container" style={{ height: '100%' }}>
        <div className="spinner" />
        Loading knowledge graph…
      </div>
    )
  }

  if (errorMessage) {
    return (
      <div className="empty-state" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: 40 }}>
        <div style={{ fontSize: 44, marginBottom: 12 }}>⚠️</div>
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-rose)', marginBottom: 8 }}>
          Unable to load graph: {errorMessage}
        </div>
        <div className="text-muted text-sm">Verify backend status and ensure Neo4j service is accessible.</div>
      </div>
    )
  }

  if (!cyElements.length) {
    let title = 'No graph data'
    let desc = 'Upload and process documents to build the knowledge graph.'

    if (emptyReason === 'filter_empty' || activeFilters?.entity || activeFilters?.source || activeFilters?.rel) {
      const fLabel = activeFilters?.entity || activeFilters?.source || activeFilters?.rel || 'active filter'
      title = 'No matching relationships'
      desc = `No ${fLabel} relationships found for this case.`
    } else if (emptyReason === 'no_relationships') {
      title = 'No graph relationships exist for this case'
      desc = `Entities were extracted for ${caseCode || 'this case'}, but no cross-entity relationships have been established yet.`
    } else if (emptyReason === 'no_entities') {
      title = 'Documents processed but graph construction has not completed'
      desc = 'Documents are processed but graph construction has not completed.'
    } else if (emptyReason === 'no_documents') {
      title = 'No documents attached'
      desc = `No documents have been uploaded or processed for case ${caseCode || 'selected'}.`
    }

    return (
      <div className="empty-state" style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: 40 }}>
        <div className="empty-icon">🕸️</div>
        <div className="empty-title">{title}</div>
        <div className="empty-desc">{desc}</div>
      </div>
    )
  }

  return (
    <div style={{ position: 'relative', height: '100%' }}>
      <CytoscapeComponent
        elements={cyElements}
        style={{ width: '100%', height: '100%', background: 'var(--bg-base)' }}
        stylesheet={getCytoscapeStyle(isFullNetwork)}
        cy={handleCy}
        userZoomingEnabled
        userPanningEnabled
        boxSelectionEnabled={false}
      />

      <NodeDetailPanel
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
        onTrace={(nodeId) => navigate(`/entities?trace=${nodeId}`)}
        onExpand={onExpand}
        onCollapse={onCollapse}
      />

      <RelationshipDetailPanel
        edge={selectedEdge}
        onClose={() => setSelectedEdge(null)}
        onTrace={(nodeId) => navigate(`/entities?trace=${nodeId}`)}
      />

      {/* Legend */}
      <div style={{
        position: 'absolute', bottom: 16, left: 16,
        background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--r-md)',
        padding: '10px 14px',
        fontSize: 11,
      }}>
        {[
          ['#6366f1', 'Person'],
          ['#22d3ee', 'Phone'],
          ['#10b981', 'Location'],
          ['#f59e0b', 'Vehicle'],
          ['#ec4899', 'Organisation'],
          ['#f87171', 'Case'],
          ['#a78bfa', 'Account'],
        ].map(([color, label]) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
            <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
