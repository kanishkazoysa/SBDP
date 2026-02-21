import { useState, useEffect } from 'react'
import { Text, Group, ThemeIcon, Alert } from '@mantine/core'
import { Home, AlertCircle, BarChart2 } from 'lucide-react'
import Sidebar from './components/Sidebar'
import PredictionForm from './components/PredictionForm'
import PredictionResult from './components/PredictionResult'
import ShapChart from './components/ShapChart'

export default function App() {
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)
  const [meta, setMeta]       = useState(null)

  // Load locations + property types from backend on mount
  useEffect(() => {
    fetch('/meta')
      .then(r => r.json())
      .then(setMeta)
      .catch(() => {})
  }, [])

  const handlePredict = async (formData) => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
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
    <div className="app-root">

      {/* ── Header ── */}
      <header className="site-header">
        <Group gap="sm">
          <ThemeIcon variant="light" color="indigo" size={38} radius="md">
            <Home size={19} />
          </ThemeIcon>
          <div>
            <Text fw={700} size="md" c="white" lh={1.3}>
              Sri Lanka Property Price Predictor
            </Text>
            <Text size="xs" c="dimmed" lh={1.2}>
              LightGBM · SHAP Explainability · ikman.lk Data · {meta ? `${meta.dataset_size.toLocaleString()} listings` : '8,791 listings'}
            </Text>
          </div>
        </Group>
      </header>

      {/* ── Body: sidebar + form + results ── */}
      <div className="app-body">

        {/* Sidebar */}
        <Sidebar meta={meta} />

        {/* Form panel */}
        <div className="panel panel-left">
          <PredictionForm onPredict={handlePredict} loading={loading} meta={meta} />
        </div>

        {/* Results panel */}
        <div className="panel panel-right">
          {error && (
            <Alert
              icon={<AlertCircle size={16} />}
              color="red"
              variant="light"
              title="Prediction Error"
              radius="md"
              mb="md"
              style={{ flexShrink: 0 }}
            >
              {error}
            </Alert>
          )}

          {result ? (
            <>
              <div style={{ flexShrink: 0, marginBottom: 16 }}>
                <PredictionResult result={result} />
              </div>
              <ShapChart shapFeatures={result.shap_features} />
            </>
          ) : !error && (
            <div className="panel-empty">
              <div className="empty-icon-wrap">
                <BarChart2 size={24} color="#6366f1" />
              </div>
              <Text size="sm" fw={500} c="dark.1" mt="sm">
                No Prediction Yet
              </Text>
              <Text size="xs" c="dimmed" mt={4}>
                Fill in property details and click Predict Price
              </Text>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
