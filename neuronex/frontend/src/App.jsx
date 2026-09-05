import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Overview from './pages/Overview'
import Upload from './pages/Upload'
import Cases from './pages/Cases'
import CaseDetail from './pages/CaseDetail'
import KnowledgeGraph from './pages/KnowledgeGraph'
import EntityExplorer from './pages/EntityExplorer'
import Communities from './pages/Communities'
import Insights from './pages/Insights'
import AnalystReview from './pages/AnalystReview'
import Validation from './pages/Validation'

export default function App() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/"            element={<Overview />} />
          <Route path="/upload"      element={<Upload />} />
          <Route path="/cases"       element={<Cases />} />
          <Route path="/cases/:caseId" element={<CaseDetail />} />
          <Route path="/graph"       element={<KnowledgeGraph />} />
          <Route path="/entities"    element={<EntityExplorer />} />
          <Route path="/communities" element={<Communities />} />
          <Route path="/insights"    element={<Insights />} />
          <Route path="/review"      element={<AnalystReview />} />
          <Route path="/validation"  element={<Validation />} />
        </Routes>
      </main>
    </div>
  )
}
