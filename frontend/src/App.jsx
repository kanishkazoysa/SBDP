import { useState, useEffect, useCallback } from 'react'
import { Text, Group, ThemeIcon, Alert, Paper, Container, Stack } from '@mantine/core'
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
  const [connectionStatus, setConnectionStatus] = useState('connecting')

  const fetchMeta = useCallback(async (retryCount = 0) => {
    try {
      const res = await fetch(`${API}/meta`)
      if (!res.ok) throw new Error('Failed to fetch metadata')
      const data = await res.json()
      setMeta(data)
      setConnectionStatus('ready')
    } catch (e) {
      console.error('Metadata fetch failed:', e)
      if (retryCount < 5) {
        setTimeout(() => fetchMeta(retryCount + 1), 2000)
      } else {
        setConnectionStatus('error')
        setError('Could not connect to the backend server. Please refresh the page.')
      }
    }
  }, [])

  useEffect(() => {
    fetchMeta()
  }, [fetchMeta])

  const handlePredict = async (formData) => {
    setLoading(true); setError(null)
    try {
      const res = await fetch(`${API}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })
      if (!res.ok) throw new Error((await res.json()).detail || 'Prediction failed')
      setResult(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-root">
      <header className="site-header">
        <Group justify="space-between">
          <Group gap="sm">
            <ThemeIcon variant="light" color="indigo" size={38} radius="md">
              <Home size={19} />
            </ThemeIcon>
            <div>
              <Text fw={700} size="md" c="white" lh={1.3}>Sri Lanka Property Price Predictor</Text>
              <Text size="xs" c="dimmed" lh={1.2}>Predict property values using AI & explainable XAI</Text>
            </div>
          </Group>
          {connectionStatus === 'connecting' && <Text size="xs" c="yellow">Connecting to backend...</Text>}
          {connectionStatus === 'ready' && <Text size="xs" c="teal">● Backend Ready ({meta?.locations?.length} cities)</Text>}
        </Group>
      </header>

      <div className="app-body">
        <Sidebar />
        <div className="main-content">
          <div className="tab-panels-row">
            <div className="left-col">
              <PredictionForm onPredict={handlePredict} loading={loading} meta={meta} />
            </div>
            <div className="right-col">
              <Stack gap="md" style={{ height: '100%' }}>
                {error && (
                  <Alert icon={<AlertCircle size={16} />} color="red" variant="light" title="System Notice" radius="md">
                    {error}
                  </Alert>
                )}

                {result ? (
                  <>
                    <PredictionResult result={result} />
                    <Paper withBorder radius="md" style={{ flex: 1, minHeight: 400 }}>
                      <ShapChart shapFeatures={result.shap_features} />
                    </Paper>
                  </>
                ) : (
                  <Paper withBorder radius="md" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <div className="panel-empty">
                      <BarChart2 size={32} color="#6366f1" style={{ opacity: 0.5 }} />
                      <Text size="sm" fw={500} c="dimmed" mt="sm">Ready for Prediction</Text>
                      <Text size="xs" c="dimmed">Enter property details on the left</Text>
                    </div>
                  </Paper>
                )}
              </Stack>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
