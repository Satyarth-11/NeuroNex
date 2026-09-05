/**
 * NeuroNex API Client
 * Centralised axios instance with base URL and error handling.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api`
    : '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('[NeuroNex API Error]', err.response?.status, err.response?.data || err.message)
    return Promise.reject(err)
  }
)

// ── Documents / Cases ──────────────────────────────────────────
export const createCase = (data) => api.post('/documents/cases', data)
export const listCases = () => api.get('/documents/cases/all')
export const getCase = (caseId) => api.get(`/documents/cases/${caseId}`)
export const listDocuments = (params) => api.get('/documents', { params })
export const getDocumentDetail = (docId) => api.get(`/documents/${docId}/detail`)
export const uploadDocument = (formData) =>
  api.post('/documents/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const processDocument = (id) => api.post(`/documents/${id}/process`)
export const sourcesSummary = () => api.get('/documents/sources/summary')

// ── Entities ────────────────────────────────────────────────────
export const listEntities = (params) => api.get('/entities', { params })
export const getEntitiesSummary = () => api.get('/entities/summary')
export const traceEntity = (canonicalId) => api.get(`/entities/${canonicalId}/trace`)
export const searchGraphEntities = (q) => api.get('/entities/search/graph', { params: { q } })

// ── Resolution ─────────────────────────────────────────────────
export const listCandidates = (params) => api.get('/resolution/candidates', { params })
export const decideCandidate = (id, data) => api.post(`/resolution/${id}/decide`, data)

// ── Graph ───────────────────────────────────────────────────────
export const getGraph = (params) => api.get('/graph', { params })
export const getNeighbors = (nodeId, depth) => api.get(`/graph/neighbors/${nodeId}`, { params: { depth } })
export const getPath = (src, dst) => api.get('/graph/path', { params: { src, dst } })
export const getEdgeDetails = (src, dst, relType) => api.get(`/graph/edge/${src}/${dst}/${relType}`)
export const getLowConfidenceEdges = (params) => api.get('/graph/edges/low-confidence', { params })
export const reviewEdge = (data) => api.post('/graph/edge/review', data)

// ── Analytics ───────────────────────────────────────────────────
export const getCentrality = () => api.get('/analytics/centrality')
export const getTopEntities = (n = 10) => api.get('/analytics/top-entities', { params: { n } })
export const getKeyInfluencers = (limit = 10) => api.get('/analytics/key-influencers', { params: { limit } })
export const getCommunities = () => api.get('/analytics/communities')
export const getCommunityDetail = (communityId) => api.get(`/analytics/communities/${communityId}`)
export const getPatterns = () => api.get('/analytics/patterns')
export const getTimeline = (params) => api.get('/analytics/timeline', { params })
export const getMLModelEvaluation = () => api.get('/analytics/ml-model')

// ── Insights ────────────────────────────────────────────────────
export const listInsights = (params) => api.get('/insights', { params })
export const getInsight = (id) => api.get(`/insights/${id}`)
export const regenerateInsights = () => api.post('/insights/regenerate')

// ── Review ──────────────────────────────────────────────────────
export const reviewInsight = (insightId, data) => api.post(`/review/${insightId}`, data)

// ── Validation ──────────────────────────────────────────────────
export const runValidation = () => api.post('/validation/run')
export const validationHistory = () => api.get('/validation/history')

// ── Admin / Demo Seeding ────────────────────────────────────────
export const seedDemoData = () => api.post('/admin/seed-demo-data')
export const seedExpandedData = () => api.post('/admin/seed-expanded-data')
export const resetDemoData = () => api.delete('/admin/reset-demo-data')
export const getHealth = () => api.get('/health')

export default api
