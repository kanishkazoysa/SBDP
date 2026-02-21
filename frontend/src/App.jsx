import { useState } from 'react'
import PredictionForm from './components/PredictionForm'
import PredictionResult from './components/PredictionResult'
import ShapChart from './components/ShapChart'

export default function App() {
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const handlePredict = async (tripData) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tripData),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Prediction failed')
      }
      setResult(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <header className="app-header">
        <h1>🚌 Sri Lanka Bus Delay Predictor</h1>
        <p>
          Predicts intercity bus delays (SLTB / private) using LightGBM.
          Powered by SHAP for real-time explainability.
        </p>
      </header>

      <main className="app-main">
        {/* ── Left: Input Form ─────────────────────────────────────── */}
        <div>
          <PredictionForm onPredict={handlePredict} loading={loading} />
          {error && <div className="error-box">Error: {error}</div>}
        </div>

        {/* ── Right: Results ───────────────────────────────────────── */}
        <div>
          {result ? (
            <>
              <PredictionResult result={result} />
              <ShapChart
                shapValues={result.shap_values}
                featureNames={result.feature_names}
                prediction={result.prediction}
                predIdx={result.pred_class_idx}
              />
            </>
          ) : (
            <div className="card">
              <div className="empty-state">
                <div className="empty-icon">🗺️</div>
                <p>Fill in the trip details and click<br /><strong>Predict Delay</strong> to see the result.</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  )
}
