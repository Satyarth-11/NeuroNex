import { useState, useEffect } from 'react'
import { runValidation, validationHistory } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function Validation() {
  const [history, setHistory] = useState([])
  const [latest, setLatest] = useState(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try {
      const r = await validationHistory()
      setHistory(r.data)
      if (r.data.length) setLatest(r.data[0])
    } finally { setLoading(false) }
  }

  async function handleRun() {
    setRunning(true)
    try {
      const r = await runValidation()
      setLatest(r.data)
      await load()
    } finally { setRunning(false) }
  }

  const er = latest?.entity_resolution || latest
  const ner = latest?.ner_extraction
  const pat = latest?.pattern_detection
  const ml = latest?.ml_priority_model

  const erAlgo = er?.algorithmic || er
  const erAuto = er?.auto_merge_only
  const erAnalyst = er?.analyst_approved

  const chartData = erAlgo?.precision != null
    ? [
        { name: 'Algorithmic P', value: erAlgo.precision ?? 0, color: '#4f8ef7' },
        { name: 'Algorithmic R', value: erAlgo.recall ?? 0, color: '#10b981' },
        { name: 'Algorithmic F1', value: erAlgo.f1_score ?? 0, color: '#8b5cf6' },
        ...(erAuto?.precision != null ? [
          { name: 'Auto-Merge P', value: erAuto.precision ?? 0, color: '#38bdf8' },
          { name: 'Auto-Merge R', value: erAuto.recall ?? 0, color: '#34d399' },
          { name: 'Auto-Merge F1', value: erAuto.f1_score ?? 0, color: '#a78bfa' },
        ] : []),
      ]
    : []

  return (
    <div className="fade-in">
      <div className="page-header">
        <h1 className="page-title">✅ Algorithmic Validation Suite</h1>
        <p className="page-subtitle">
          Task-separated precision / recall / F1 evaluation against synthetic ground-truth benchmarks.
        </p>
      </div>

      {/* Dataset disclaimer banner */}
      <div style={{
        background: 'rgba(239, 68, 68, 0.08)',
        border: '1px solid rgba(239, 68, 68, 0.25)',
        borderRadius: 'var(--r-md)',
        padding: '12px 18px',
        marginBottom: 24,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
      }}>
        <div style={{ fontSize: 20 }}>⚠️</div>
        <div style={{ fontSize: 13, color: '#fca5a5', lineHeight: 1.5 }}>
          <strong>Synthetic Benchmark Notice:</strong>{' '}
          {latest?.dataset_note || 'Prototype validation on synthetic ground-truth dataset. Not representative of real-world law-enforcement accuracy.'}
        </div>
      </div>

      {/* Action Bar */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="flex-between">
          <div>
            <div style={{ fontWeight: 700, fontSize: 16 }}>Run Multi-Task Validation</div>
            <div className="text-xs text-muted" style={{ marginTop: 2 }}>
              Executes validation across Entity Resolution, Named Entity Recognition, and Pattern Detection pipelines.
            </div>
          </div>
          <button
            id="run-validation-btn"
            className="btn btn-primary"
            onClick={handleRun}
            disabled={running}
            style={{ minWidth: 160, justifyContent: 'center' }}
          >
            {running ? '⏳ Running Suite…' : '▶ Run All Tests'}
          </button>
        </div>
      </div>

      {/* Task 1: Entity Resolution - 3 Distinct Blocks */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header flex-between">
          <div className="card-title">
            <span style={{ marginRight: 8 }}>1️⃣</span> Task 1: Cross-Document Entity Resolution
          </div>
          <span className="badge badge-approved" style={{ fontSize: 11 }}>
            3-Tier Evaluation Architecture
          </span>
        </div>

        <p className="text-sm text-muted" style={{ marginBottom: 16, lineHeight: 1.6 }}>
          Evaluates deduplication and cross-modal alias linking against{' '}
          <code style={{ fontFamily: 'monospace', color: 'var(--accent-primary)' }}>ground_truth_pairs.csv</code>{' '}
          ({er?.total_evaluated ?? 20} annotated pairs). Evaluates raw algorithmic predictions independently from human review clicks.
        </p>

        {erAlgo?.precision != null ? (
          <div>
            {chartData.length > 0 && (
              <div style={{ height: 160, marginBottom: 20 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} barSize={28}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                    <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                    <YAxis domain={[0, 1]} tickFormatter={v => `${(v*100).toFixed(0)}%`} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-active)', borderRadius: 8 }}
                      labelStyle={{ color: 'var(--text-primary)' }}
                      formatter={(v) => [`${(v*100).toFixed(1)}%`, '']}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Three distinct metric cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
              {/* Card 1: Algorithmic Prediction */}
              <div style={{
                background: 'var(--bg-elevated)',
                border: '1px solid rgba(79, 142, 247, 0.3)',
                borderRadius: 'var(--r-md)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}>
                <div>
                  <div className="flex-between" style={{ marginBottom: 8 }}>
                    <div style={{ fontWeight: 700, fontSize: 14, color: '#4f8ef7' }}>
                      🤖 Algorithmic Surfaced Pairs
                    </div>
                    <span className="badge badge-approved" style={{ fontSize: 10 }}>
                      Score ≥ {erAlgo.evaluation_threshold ?? 0.72}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, margin: '12px 0', textAlign: 'center' }}>
                    <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: 6 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#4f8ef7' }}>{(erAlgo.precision * 100).toFixed(1)}%</div>
                      <div className="text-xs text-muted">Precision</div>
                    </div>
                    <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: 6 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#10b981' }}>{(erAlgo.recall * 100).toFixed(1)}%</div>
                      <div className="text-xs text-muted">Recall</div>
                    </div>
                    <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: 6 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#8b5cf6' }}>{(erAlgo.f1_score * 100).toFixed(1)}%</div>
                      <div className="text-xs text-muted">F1 Score</div>
                    </div>
                  </div>
                  <div className="text-xs monospace" style={{ textAlign: 'center', marginBottom: 10, color: 'var(--text-secondary)' }}>
                    TP: <strong style={{ color: 'var(--accent-emerald)' }}>{erAlgo.true_positives}</strong> · FP: <strong style={{ color: 'var(--accent-rose)' }}>{erAlgo.false_positives}</strong> · FN: <strong style={{ color: 'var(--accent-amber)' }}>{erAlgo.false_negatives}</strong>
                  </div>
                </div>
                <div style={{
                  background: 'rgba(79, 142, 247, 0.06)',
                  borderLeft: '3px solid #4f8ef7',
                  padding: '8px 10px',
                  borderRadius: 4,
                  fontSize: 11,
                  color: 'var(--text-muted)',
                  lineHeight: 1.4,
                }}>
                  {erAlgo.notes || "Measures the resolver's raw similarity-threshold predictions (score >= review threshold), independent of analyst review status."}
                </div>
              </div>

              {/* Card 2: Auto-Merge Only */}
              <div style={{
                background: 'var(--bg-elevated)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: 'var(--r-md)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}>
                <div>
                  <div className="flex-between" style={{ marginBottom: 8 }}>
                    <div style={{ fontWeight: 700, fontSize: 14, color: '#10b981' }}>
                      ⚡ Auto-Merge-Only (Strict)
                    </div>
                    <span className="badge badge-approved" style={{ fontSize: 10 }}>
                      Score ≥ {erAuto?.evaluation_threshold ?? 0.92}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, margin: '12px 0', textAlign: 'center' }}>
                    <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: 6 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#4f8ef7' }}>{erAuto?.precision != null ? `${(erAuto.precision * 100).toFixed(1)}%` : '—'}</div>
                      <div className="text-xs text-muted">Precision</div>
                    </div>
                    <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: 6 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#10b981' }}>{erAuto?.recall != null ? `${(erAuto.recall * 100).toFixed(1)}%` : '—'}</div>
                      <div className="text-xs text-muted">Recall</div>
                    </div>
                    <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: 6 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#8b5cf6' }}>{erAuto?.f1_score != null ? `${(erAuto.f1_score * 100).toFixed(1)}%` : '—'}</div>
                      <div className="text-xs text-muted">F1 Score</div>
                    </div>
                  </div>
                  <div className="text-xs monospace" style={{ textAlign: 'center', marginBottom: 10, color: 'var(--text-secondary)' }}>
                    TP: <strong style={{ color: 'var(--accent-emerald)' }}>{erAuto?.true_positives ?? 0}</strong> · FP: <strong style={{ color: 'var(--accent-rose)' }}>{erAuto?.false_positives ?? 0}</strong> · FN: <strong style={{ color: 'var(--accent-amber)' }}>{erAuto?.false_negatives ?? 0}</strong>
                  </div>
                </div>
                <div style={{
                  background: 'rgba(16, 185, 129, 0.06)',
                  borderLeft: '3px solid #10b981',
                  padding: '8px 10px',
                  borderRadius: 4,
                  fontSize: 11,
                  color: 'var(--text-muted)',
                  lineHeight: 1.4,
                }}>
                  {erAuto?.notes || "Measures only pairs the system auto-merged without human review (stricter, higher-confidence subset)."}
                </div>
              </div>

              {/* Card 3: Analyst Approved */}
              <div style={{
                background: 'var(--bg-elevated)',
                border: '1px solid rgba(139, 92, 246, 0.3)',
                borderRadius: 'var(--r-md)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}>
                <div>
                  <div className="flex-between" style={{ marginBottom: 8 }}>
                    <div style={{ fontWeight: 700, fontSize: 14, color: '#8b5cf6' }}>
                      👤 Analyst-Approved Merges
                    </div>
                    <span className="badge badge-pending" style={{ fontSize: 10 }}>
                      Human Approvals
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, margin: '12px 0', textAlign: 'center' }}>
                    <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: 6 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#4f8ef7' }}>{erAnalyst?.precision != null ? `${(erAnalyst.precision * 100).toFixed(1)}%` : '—'}</div>
                      <div className="text-xs text-muted">Precision</div>
                    </div>
                    <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: 6 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#10b981' }}>{erAnalyst?.recall != null ? `${(erAnalyst.recall * 100).toFixed(1)}%` : '—'}</div>
                      <div className="text-xs text-muted">Recall</div>
                    </div>
                    <div style={{ background: 'var(--bg-card)', padding: '8px', borderRadius: 6 }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#8b5cf6' }}>{erAnalyst?.f1_score != null ? `${(erAnalyst.f1_score * 100).toFixed(1)}%` : '—'}</div>
                      <div className="text-xs text-muted">F1 Score</div>
                    </div>
                  </div>
                  <div className="text-xs monospace" style={{ textAlign: 'center', marginBottom: 10, color: 'var(--text-secondary)' }}>
                    TP: <strong style={{ color: 'var(--accent-emerald)' }}>{erAnalyst?.true_positives ?? 0}</strong> · FP: <strong style={{ color: 'var(--accent-rose)' }}>{erAnalyst?.false_positives ?? 0}</strong> · FN: <strong style={{ color: 'var(--accent-amber)' }}>{erAnalyst?.false_negatives ?? 0}</strong>
                  </div>
                </div>
                <div style={{
                  background: 'rgba(139, 92, 246, 0.06)',
                  borderLeft: '3px solid #8b5cf6',
                  padding: '8px 10px',
                  borderRadius: 4,
                  fontSize: 11,
                  color: 'var(--text-muted)',
                  lineHeight: 1.4,
                }}>
                  {erAnalyst?.notes || "Measures the rate of manually-approved merges — reflects analyst workflow usage, not algorithm quality. Will be 0 or low until an analyst has reviewed candidates in the Analyst Review screen."}
                </div>
              </div>

              {/* Candidate Coverage Breakdown (Diagnostics) */}
              {er?.coverage_breakdown && (
                <div style={{
                  marginTop: 16,
                  padding: '12px 16px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--r-md)',
                  display: 'flex',
                  justifyContent: 'space-around',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 12,
                }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                      {er.coverage_breakdown.ground_truth_positive_pairs}
                    </div>
                    <div className="text-xs text-muted">Ground-Truth Positives</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#4f8ef7' }}>
                      {er.coverage_breakdown.candidate_pairs_surfaced}
                    </div>
                    <div className="text-xs text-muted">Candidate Pairs Surfaced</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#10b981' }}>
                      {er.coverage_breakdown.gt_positives_found_as_candidates}
                    </div>
                    <div className="text-xs text-muted">Positives Found as Candidates</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: er.coverage_breakdown.gt_positives_missed_entirely > 0 ? '#f59e0b' : '#10b981' }}>
                      {er.coverage_breakdown.gt_positives_missed_entirely}
                    </div>
                    <div className="text-xs text-muted">Positives Missed Entirely</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="empty-state" style={{ padding: 24 }}>
            <div className="empty-title">No Entity Resolution Data</div>
            <div className="text-xs text-muted">Click "Run All Tests" to evaluate resolution performance.</div>
          </div>
        )}
      </div>

      {/* Grid for Task 2 & Task 3 */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Task 2: NER Extraction */}
        <div className="card">
          <div className="card-header flex-between">
            <div className="card-title">
              <span style={{ marginRight: 8 }}>2️⃣</span> Task 2: NER Extraction
            </div>
            <span className={`badge badge-${ner?.status === 'evaluated' ? 'approved' : 'flagged'}`} style={{ fontSize: 11 }}>
              {ner?.status === 'evaluated' ? 'Evaluated' : 'No Ground Truth'}
            </span>
          </div>

          {ner?.status === 'evaluated' ? (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, margin: '14px 0' }}>
                <div style={{ background: 'var(--bg-elevated)', borderRadius: 6, padding: 12, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#4f8ef7' }}>{(ner.precision * 100).toFixed(1)}%</div>
                  <div className="text-xs text-muted">Precision</div>
                </div>
                <div style={{ background: 'var(--bg-elevated)', borderRadius: 6, padding: 12, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#10b981' }}>{(ner.recall * 100).toFixed(1)}%</div>
                  <div className="text-xs text-muted">Recall</div>
                </div>
                <div style={{ background: 'var(--bg-elevated)', borderRadius: 6, padding: 12, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#8b5cf6' }}>{(ner.f1_score * 100).toFixed(1)}%</div>
                  <div className="text-xs text-muted">F1 Score</div>
                </div>
              </div>
              <div className="text-xs text-muted" style={{ lineHeight: 1.5 }}>
                {ner.notes} (TP: {ner.true_positives}, FP: {ner.false_positives}, FN: {ner.false_negatives})
              </div>
            </div>
          ) : (
            <div style={{
              background: 'var(--bg-elevated)',
              border: '1px dashed var(--border-subtle)',
              borderRadius: 'var(--r-md)',
              padding: 20,
              textAlign: 'center',
              marginTop: 8,
            }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>🏷️</div>
              <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-secondary)', marginBottom: 6 }}>
                {ner?.message || 'No labelled NER ground-truth dataset available for this prototype run.'}
              </div>
              <p className="text-xs text-muted" style={{ lineHeight: 1.6, maxWidth: 440, margin: '0 auto' }}>
                The ingestion pipeline utilizes spaCy (<code style={{ fontFamily: 'monospace' }}>en_core_web_sm</code>) augmented with Indian regex patterns for Phone, Vehicle, Case, and Account entities.
              </p>
            </div>
          )}
        </div>

        {/* Task 3: Pattern Detection */}
        <div className="card">
          <div className="card-header flex-between">
            <div className="card-title">
              <span style={{ marginRight: 8 }}>3️⃣</span> Task 3: Anomaly & Pattern Detection
            </div>
            <span className={`badge badge-${pat?.status === 'evaluated' ? 'approved' : 'flagged'}`} style={{ fontSize: 11 }}>
              {pat?.status === 'evaluated' ? 'Evaluated' : 'No Ground Truth'}
            </span>
          </div>

          {pat?.status === 'evaluated' ? (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10, margin: '14px 0' }}>
                <div style={{ background: 'var(--bg-elevated)', borderRadius: 6, padding: 12, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#f59e0b' }}>
                    {pat.total_detections ?? pat.total_patterns_flagged ?? 0}
                  </div>
                  <div className="text-xs text-muted">Total Detections</div>
                </div>
                <div style={{ background: 'var(--bg-elevated)', borderRadius: 6, padding: 12, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#10b981' }}>
                    {pat.patterns_fired ?? pat.distinct_pattern_types ?? 0} of {pat.patterns_evaluated ?? 5}
                  </div>
                  <div className="text-xs text-muted">Detectors Fired</div>
                </div>
                <div style={{ background: 'var(--bg-elevated)', borderRadius: 6, padding: 12, textAlign: 'center' }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#4f8ef7' }}>
                    {pat.coverage_pct != null ? `${pat.coverage_pct}%` : `${((pat.detector_coverage ?? 0) * 100).toFixed(0)}%`}
                  </div>
                  <div className="text-xs text-muted">Pattern Coverage</div>
                </div>
              </div>

              {pat.breakdown && (
                <div style={{ marginBottom: 12, border: '1px solid var(--border-subtle)', borderRadius: 6, overflow: 'hidden' }}>
                  <table style={{ width: '100%', fontSize: 12, borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ background: 'var(--bg-elevated)', textAlign: 'left' }}>
                        <th style={{ padding: '6px 10px' }}>Detector</th>
                        <th style={{ padding: '6px 10px', textAlign: 'right' }}>Instances</th>
                        <th style={{ padding: '6px 10px', textAlign: 'right' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(pat.breakdown).map(([detector, count]) => (
                        <tr key={detector} style={{ borderTop: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '6px 10px', fontFamily: 'monospace' }}>{detector}</td>
                          <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 600 }}>{count}</td>
                          <td style={{ padding: '6px 10px', textAlign: 'right' }}>
                            <span className={`badge ${count > 0 ? 'badge-approved' : 'badge-flagged'}`} style={{ fontSize: 10 }}>
                              {count > 0 ? 'Active' : 'Dormant'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="text-xs text-muted" style={{ lineHeight: 1.5, fontStyle: 'italic' }}>
                {pat.notes || "Unsupervised rule-based pattern detection is evaluated by detector coverage across data modalities, not classification accuracy, as ground-truth labels are not defined for synthetic exploratory analysis."}
              </div>
            </div>
          ) : (
            <div style={{
              background: 'var(--bg-elevated)',
              border: '1px dashed var(--border-subtle)',
              borderRadius: 'var(--r-md)',
              padding: 20,
              textAlign: 'center',
              marginTop: 8,
            }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>🔍</div>
              <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-secondary)', marginBottom: 6 }}>
                {pat?.message || 'No labelled pattern detection ground-truth dataset available for this prototype run.'}
              </div>
              <p className="text-xs text-muted" style={{ lineHeight: 1.6, maxWidth: 440, margin: '0 auto' }}>
                Anomalies are surfaced via 5 deterministic graph topology & transaction distribution detectors (Cross-Case Overlap, Unusual Financial Amounts, Top-5% High Frequency Calls, Multi-Source Convergence, Dense Louvain Clusters).
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Task 4: Genuine Explainable ML Component */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header flex-between">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="badge badge-primary">TASK 4</span>
              <div className="card-title">Investigative Priority Classification Model (Explainable ML)</div>
            </div>
            <div className="text-xs text-muted" style={{ marginTop: 4 }}>
              Logistic Regression with L2 regularization trained on 80% development cases (Cases 1–53) and evaluated strictly on 20% held-out cases (Cases 54–60) · <strong style={{ color: 'var(--accent-rose)' }}>SYNTHETIC DATA ONLY</strong>
            </div>
          </div>
          {ml?.status === 'evaluated' && (
            <span className="badge badge-proposed" style={{ fontSize: 12 }}>
              {ml.model_name}
            </span>
          )}
        </div>

        {/* Dataset Disclaimer Notice */}
        <div style={{
          background: 'rgba(239, 68, 68, 0.06)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          borderRadius: 'var(--r-md)',
          padding: '10px 14px',
          marginBottom: 16,
          fontSize: 12,
          color: '#fca5a5',
          lineHeight: 1.5,
        }}>
          <strong>ML Honesty Disclosure:</strong> {ml?.dataset_disclaimer || 'Model trained and evaluated on synthetic investigative data. No real-world criminal/police dataset was used. Results demonstrate prototype behavior and must not be interpreted as real-world law-enforcement performance.'}
        </div>

        {ml?.status === 'evaluated' ? (
          <div>
            {/* Top Stat Metrics */}
            <div className="stat-grid" style={{ marginBottom: 20 }}>
              <div className="stat-card">
                <div className="stat-value" style={{ color: '#4f8ef7' }}>{(ml.precision * 100).toFixed(1)}%</div>
                <div className="stat-label">Held-Out Precision</div>
              </div>
              <div className="stat-card">
                <div className="stat-value" style={{ color: '#10b981' }}>{(ml.recall * 100).toFixed(1)}%</div>
                <div className="stat-label">Held-Out Recall</div>
              </div>
              <div className="stat-card">
                <div className="stat-value" style={{ color: '#8b5cf6' }}>{(ml.f1_score * 100).toFixed(1)}%</div>
                <div className="stat-label">Held-Out F1 Score</div>
              </div>
              <div className="stat-card">
                <div className="stat-value" style={{ color: 'var(--accent-amber)' }}>{ml.held_out_entities_count}</div>
                <div className="stat-label">Held-Out Entities Tested</div>
              </div>
            </div>

            {/* Confusion Matrix and Case Split Overview */}
            <div className="grid-2" style={{ marginBottom: 20 }}>
              {/* Confusion Matrix Card */}
              <div style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--r-md)',
                padding: 16,
              }}>
                <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12, display: 'flex', justifyContent: 'space-between' }}>
                  <span>🔲 Held-Out Confusion Matrix</span>
                  <span className="text-xs text-muted">N = {ml.held_out_entities_count}</span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, textAlign: 'center' }}>
                  <div style={{ padding: 10, borderRadius: 'var(--r-sm)', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)' }}>
                    <div className="text-xs text-muted">True Negatives (TN)</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-emerald)', marginTop: 4 }}>{ml.true_negatives}</div>
                    <div className="text-xs text-muted">Correct Witness / Standard</div>
                  </div>
                  <div style={{ padding: 10, borderRadius: 'var(--r-sm)', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)' }}>
                    <div className="text-xs text-muted">False Positives (FP)</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-rose)', marginTop: 4 }}>{ml.false_positives}</div>
                    <div className="text-xs text-muted">Witness Flagged as Lead</div>
                  </div>
                  <div style={{ padding: 10, borderRadius: 'var(--r-sm)', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)' }}>
                    <div className="text-xs text-muted">False Negatives (FN)</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-amber)', marginTop: 4 }}>{ml.false_negatives}</div>
                    <div className="text-xs text-muted">Lead Missed as Witness</div>
                  </div>
                  <div style={{ padding: 10, borderRadius: 'var(--r-sm)', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-subtle)' }}>
                    <div className="text-xs text-muted">True Positives (TP)</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: '#4f8ef7', marginTop: 4 }}>{ml.true_positives}</div>
                    <div className="text-xs text-muted">Correct High Priority Lead</div>
                  </div>
                </div>
              </div>

              {/* Data Split & Methodological Transparency Card */}
              <div style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--r-md)',
                padding: 16,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 10 }}>📐 Dataset Split & Overlap Audit</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
                    <div className="flex-between">
                      <span className="text-muted">Development Set:</span>
                      <span className="monospace">{ml.train_cases_count} cases ({ml.train_entities_count} entities)</span>
                    </div>
                    <div className="flex-between">
                      <span className="text-muted">Held-Out Test Set:</span>
                      <span className="monospace">{ml.held_out_cases_count} cases ({ml.held_out_entities_count} entities)</span>
                    </div>
                    <div className="flex-between">
                      <span className="text-muted">Cross-Case Entity Overlap:</span>
                      <span className="monospace" style={{ color: ml.train_test_overlap_count > 0 ? 'var(--accent-amber)' : 'inherit' }}>
                        {ml.train_test_overlap_count} entities (syndicate links)
                      </span>
                    </div>
                    <div className="flex-between">
                      <span className="text-muted">Strict Disjoint Held-Out Set:</span>
                      <span className="monospace" style={{ color: 'var(--accent-emerald)' }}>
                        N = {ml.exclusive_held_out_evaluation?.exclusive_entities_count ?? 0} (Overlap = 0)
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-xs text-muted" style={{ marginTop: 12, lineHeight: 1.4, borderTop: '1px solid var(--border-subtle)', paddingTop: 8 }}>
                  ℹ️ {ml.data_limitation_notes}
                </div>
              </div>
            </div>

            {/* Explainable Feature Importances & Odds Ratios */}
            <div style={{ marginTop: 16 }}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>📊 Explainable Feature Coefficients & Odds Ratios</span>
                <span className="text-xs text-muted">Odds Ratio &gt; 1.0 increases probability of High-Priority lead</span>
              </div>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Feature Name</th>
                      <th>Standardized Coef (β)</th>
                      <th>Odds Ratio (e^β)</th>
                      <th>Directional Effect</th>
                      <th>Importance Rank</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ml.feature_importances?.map((feat, idx) => (
                      <tr key={feat.feature_name}>
                        <td className="monospace text-xs" style={{ fontWeight: 600 }}>{feat.feature_name}</td>
                        <td className="monospace text-xs" style={{ color: feat.coefficient >= 0 ? '#4f8ef7' : 'var(--accent-rose)' }}>
                          {feat.coefficient >= 0 ? `+${feat.coefficient.toFixed(4)}` : feat.coefficient.toFixed(4)}
                        </td>
                        <td className="monospace text-xs" style={{ fontWeight: 700, color: feat.odds_ratio >= 1.0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                          {feat.odds_ratio.toFixed(4)}x
                        </td>
                        <td className="text-xs">
                          {feat.coefficient > 0 ? (
                            <span style={{ color: 'var(--accent-emerald)' }}>▲ Increases Priority</span>
                          ) : feat.coefficient < 0 ? (
                            <span style={{ color: 'var(--accent-rose)' }}>▼ Decreases Priority</span>
                          ) : (
                            <span className="text-muted">Neutral</span>
                          )}
                        </td>
                        <td className="text-xs text-muted">#{idx + 1}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">🤖</div>
            <div className="empty-title">Model not evaluated yet</div>
            <div className="empty-desc">Click "Run All Tests" above to train and evaluate the Logistic Regression model.</div>
          </div>
        )}
      </div>

      {/* Validation History Table */}
      <div className="card">
        <div className="card-header"><div className="card-title">Validation Run History</div></div>
        {loading ? (
          <div className="loading-container"><div className="spinner" /></div>
        ) : history.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📊</div>
            <div className="empty-title">No runs recorded</div>
            <div className="empty-desc">Click "Run All Tests" above to execute the validation suite.</div>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Run #</th>
                  <th>ER Precision</th>
                  <th>ER Recall</th>
                  <th>ER F1</th>
                  <th>TP / FP / FN</th>
                  <th>Execution Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {history.map((run) => (
                  <tr key={run.id}>
                    <td className="monospace text-xs">RUN-{run.id}</td>
                    <td style={{ color: '#4f8ef7', fontWeight: 600 }}>
                      {run.precision != null ? `${(run.precision * 100).toFixed(1)}%` : '—'}
                    </td>
                    <td style={{ color: '#10b981', fontWeight: 600 }}>
                      {run.recall != null ? `${(run.recall * 100).toFixed(1)}%` : '—'}
                    </td>
                    <td style={{ color: '#8b5cf6', fontWeight: 600 }}>
                      {run.f1_score != null ? `${(run.f1_score * 100).toFixed(1)}%` : '—'}
                    </td>
                    <td className="text-xs monospace">
                      <span style={{ color: 'var(--accent-emerald)' }}>{run.true_positives}</span> /{' '}
                      <span style={{ color: 'var(--accent-rose)' }}>{run.false_positives}</span> /{' '}
                      <span style={{ color: 'var(--accent-amber)' }}>{run.false_negatives}</span>
                    </td>
                    <td className="text-xs text-muted">
                      {run.created_at ? new Date(run.created_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
