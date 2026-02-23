import { useState, useEffect, useCallback } from 'react'
import { Text, Group, ThemeIcon, Alert, Paper, Stack, Box } from '@mantine/core'
import { Sprout, AlertCircle, BarChart2, Leaf, ShieldCheck } from 'lucide-react'
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
        setError('Could not connect to the Intelligent Harvest server. Please refresh.')
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
      if (!res.ok) throw new Error((await res.json()).detail || 'Forecast failed')
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
        <Group justify="space-between" align="center">
          <Group gap="md">
            <ThemeIcon variant="gradient" gradient={{ from: 'teal', to: 'lime', deg: 90 }} size={42} radius="lg">
              <Sprout size={22} weight="bold" />
            </ThemeIcon>
            <Box>
              <Text fw={900} size="xl" c="white" style={{ letterSpacing: '-0.5px', textTransform: 'uppercase' }}>
                LankaTea <span style={{ color: 'var(--tea-emerald)', fontWeight: 300 }}>Intelligence</span>
              </Text>
              <Group gap={6}>
                <ShieldCheck size={12} color="var(--tea-emerald)" />
                <Text size="xs" c="dimmed" fw={500}>Verified Harvest Prediction Module v2.1</Text>
              </Group>
            </Box>
          </Group>

          <Group gap="xl">
            <Box style={{ textAlign: 'right' }}>
              {connectionStatus === 'connecting' && (
                <Group gap="xs">
                  <div className="pulse-yellow" />
                  <Text size="xs" c="yellow.5" fw={600}>TRI SIGNAL SEARCH...</Text>
                </Group>
              )}
              {connectionStatus === 'ready' && (
                <Group gap="xs">
                  <Text size="xs" c="green.4" fw={700}>● SYSTEM ONLINE</Text>
                  <Text size="xs" c="dimmed">{meta?.dataset_size}+ RECORDS</Text>
                </Group>
              )}
            </Box>
          </Group>
        </Group>
      </header>

      <div className="app-body">
        <Sidebar meta={meta} />
        <div className="main-content">
          <div className="tab-panels-row">
            <div className="left-col">
              <PredictionForm onPredict={handlePredict} loading={loading} meta={meta} />
            </div>
            <div className="right-col">
              <Stack gap="md" style={{ height: '100%' }}>
                {error && (
                  <Alert icon={<AlertCircle size={16} />} color="red" variant="filled" title="Operational Alert" radius="md">
                    {error}
                  </Alert>
                )}

                {result ? (
                  <>
                    <PredictionResult result={result} />
                    <Paper className="premium-card" p="lg" style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                      <Group mb="sm" justify="space-between">
                        <Box>
                          <Text fw={800} size="lg" c="white">Forecast Drivers</Text>
                          <Text size="xs" c="dimmed">SHAP Explainable AI attribution analysis</Text>
                        </Box>
                        <BarChart2 size={20} color="var(--tea-emerald)" opacity={0.6} />
                      </Group>
                      <ShapChart shapFeatures={result.shap_features} />
                    </Paper>
                  </>
                ) : (
                  <Paper className="premium-card" style={{ flex: 1, display: 'flex' }}>
                    <div className="panel-empty" style={{ width: '100%' }}>
                      <div className="empty-icon-wrap">
                        <Leaf size={32} color="var(--tea-emerald)" />
                      </div>
                      <Text size="xl" fw={900} c="white" mb="xs">Ready for Analysis</Text>
                      <Text size="md" c="dimmed" maxW={300}>
                        Complete the Estate Assessment form to generate a high-precision harvest forecast using LightGBM.
                      </Text>
                      <Box mt="xl" p="md" style={{ border: '1px dashed rgba(255,255,255,0.1)', borderRadius: 12 }}>
                        <Text size="xs" c="dimmed">Awaiting telemetry from Sri Lankan tea-growing regions...</Text>
                      </Box>
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
