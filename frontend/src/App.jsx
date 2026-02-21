import { useState, useEffect } from 'react'
import { Text, Group, ThemeIcon, Alert, Paper } from '@mantine/core'
import { Home, AlertCircle, BarChart2 } from 'lucide-react'
import Sidebar from './components/Sidebar'
import PredictionForm from './components/PredictionForm'
import PredictionResult from './components/PredictionResult'
import ShapChart from './components/ShapChart'

const API = import.meta.env.VITE_API_URL || ''

export default function App() {
  const [meta, setMeta] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API}/meta`).then(r => r.json()).then(setMeta).catch(() => { })
  }, [])

  const handlePredict = async (formData) => {
    setLoading(true); setError(null)
    try {
      const res = await fetch(`${API}/predict`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Prediction failed')
      setResult(await res.json())
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
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
            <Text fw={700} size="md" c="white" lh={1.3}>Sri Lanka Property Price Predictor</Text>
            <Text size="xs" c="dimmed" lh={1.2}>
              Real-time Property Valuation & Market Insights
            </Text>
          </div>
        </Group>
      </header>

      {/* ── Body: sidebar | main ── */}
      <div className="app-body">
        <Sidebar />

        <div className="main-content">
          <div className="tab-panels-row">

            {/* ══ LEFT: Form ══ */}
            <div className="left-col">
              <div className="form-stretch">
                <PredictionForm onPredict={handlePredict} loading={loading} meta={meta} />
              </div>
            </div>

            {/* ══ RIGHT: Results ══ */}
            <div className="right-col">
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 16 }}>

                {/* Errors */}
                {error && (
                  <Alert icon={<AlertCircle size={16} />} color="red" variant="light" title="Prediction Error" radius="md">
                    {error}
                  </Alert>
                )}

                {result ? (
                  <>
                    <div style={{ flexShrink: 0 }}>
                      <PredictionResult result={result} />
                    </div>
                    <div style={{ flex: 1, minHeight: 0 }}>
                      <ShapChart shapFeatures={result.shap_features} />
                    </div>
                  </>
                ) : !error && (
                  <Paper withBorder radius="md" style={{ flex: 1 }}>
                    <div className="panel-empty" style={{ height: '100%', minHeight: 400 }}>
                      <div className="empty-icon-wrap"><BarChart2 size={24} color="#6366f1" /></div>
                      <Text size="sm" fw={500} c="dark.1" mt="sm">No Prediction Yet</Text>
                      <Text size="xs" c="dimmed" mt={4}>Fill in property details and click Predict Price</Text>
                    </div>
                  </Paper>
                )}
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}
