import { useState, useEffect, useRef } from 'react'
import { Text, Group, ThemeIcon, Alert, Paper, SegmentedControl } from '@mantine/core'
import { Home, AlertCircle, BarChart2, TrendingUp } from 'lucide-react'
import Sidebar from './components/Sidebar'
import PredictionForm from './components/PredictionForm'
import PredictionResult from './components/PredictionResult'
import ShapChart from './components/ShapChart'
import ForecastInput from './components/ForecastInput'
import ForecastResult from './components/ForecastResult'

const API = import.meta.env.VITE_API_URL || ''

// City → District lookup (frontend copy for mapping prediction location to forecast district)
const CITY_TO_DISTRICT = {
  "Dehiwala": "Colombo", "Mount Lavinia": "Colombo", "Moratuwa": "Colombo",
  "Nugegoda": "Colombo", "Maharagama": "Colombo", "Battaramulla": "Colombo",
  "Kaduwela": "Colombo", "Malabe": "Colombo", "Pannipitiya": "Colombo",
  "Homagama": "Colombo", "Piliyandala": "Colombo", "Kottawa": "Colombo",
  "Boralesgamuwa": "Colombo", "Angoda": "Colombo", "Kolonnawa": "Colombo",
  "Rajagiriya": "Colombo", "Talawatugoda": "Colombo", "Thalawathugoda": "Colombo",
  "Nawala": "Colombo", "Kotte": "Colombo", "Athurugiriya": "Colombo",
  "Padukka": "Colombo", "Avissawella": "Colombo", "Colombo": "Colombo",
  "Negombo": "Gampaha", "Wattala": "Gampaha", "Ja-Ela": "Gampaha",
  "Kelaniya": "Gampaha", "Kiribathgoda": "Gampaha", "Kadawatha": "Gampaha",
  "Ragama": "Gampaha", "Gampaha": "Gampaha", "Minuwangoda": "Gampaha",
  "Ekala": "Gampaha", "Veyangoda": "Gampaha", "Nittambuwa": "Gampaha",
  "Mirigama": "Gampaha", "Ganemulla": "Gampaha", "Peliyagoda": "Gampaha",
  "Kalutara": "Kalutara", "Panadura": "Kalutara", "Horana": "Kalutara",
  "Bandaragama": "Kalutara", "Aluthgama": "Kalutara", "Beruwala": "Kalutara",
  "Wadduwa": "Kalutara", "Matugama": "Kalutara",
  "Kandy": "Kandy", "Peradeniya": "Kandy", "Katugastota": "Kandy", "Gampola": "Kandy",
  "Galle": "Galle", "Hikkaduwa": "Galle", "Ambalangoda": "Galle",
  "Matara": "Matara", "Weligama": "Matara", "Mirissa": "Matara",
  "Hambantota": "Hambantota", "Tangalle": "Hambantota",
  "Kurunegala": "Kurunegala", "Kuliyapitiya": "Kurunegala",
  "Puttalam": "Puttalam", "Chilaw": "Puttalam",
  "Anuradhapura": "Anuradhapura", "Polonnaruwa": "Polonnaruwa",
  "Badulla": "Badulla", "Bandarawela": "Badulla", "Ella": "Badulla",
  "Monaragala": "Monaragala", "Ratnapura": "Ratnapura",
  "Kegalle": "Kegalle", "Matale": "Matale",
  "Nuwara Eliya": "Nuwara Eliya", "Jaffna": "Jaffna",
  "Vavuniya": "Vavuniya", "Trincomalee": "Trincomalee",
  "Batticaloa": "Batticaloa", "Ampara": "Ampara",
}

function getDistrict(location) {
  if (!location) return 'Colombo'
  return CITY_TO_DISTRICT[location] || location
}

export default function App() {
  const [activeTab, setActiveTab] = useState('current')
  const [meta, setMeta] = useState(null)

  // ── Current price state ─────────────────────────────────────────
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [lastPredictData, setLastPredictData] = useState(null)  // ← stores last form input

  // ── Forecast state ──────────────────────────────────────────────
  const [forecastForm, setForecastForm] = useState({ district: 'Colombo', property_type: 'Land', land_size_perches: null })
  const [forecastResult, setForecastResult] = useState(null)
  const [forecastLoading, setForecastLoading] = useState(false)
  const [forecastError, setForecastError] = useState(null)

  // track last auto-submitted forecast key to avoid re-triggering
  const lastAutoKey = useRef(null)

  useEffect(() => {
    fetch(`${API}/meta`).then(r => r.json()).then(setMeta).catch(() => { })
  }, [])

  // ── Auto-fill + auto-run forecast when switching to forecast tab ─
  useEffect(() => {
    if (activeTab !== 'forecast' || !lastPredictData) return

    const district = getDistrict(lastPredictData.location)
    const property_type = lastPredictData.property_type
    const land_size = lastPredictData.land_size_perches || null

    const newForm = { district, property_type, land_size_perches: land_size }
    const autoKey = `${district}|${property_type}|${land_size}`

    // Only re-run if the data changed since last auto-forecast
    if (lastAutoKey.current === autoKey) return
    lastAutoKey.current = autoKey

    setForecastForm(newForm)
    runForecast(newForm)          // auto-submit!
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, lastPredictData])

  const handlePredict = async (formData) => {
    setLastPredictData(formData)  // ← save for forecast pre-fill
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

  const runForecast = async (form) => {
    setForecastLoading(true); setForecastError(null)
    try {
      const res = await fetch(`${API}/forecast`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          district: form.district,
          property_type: form.property_type,
          land_size_perches: form.land_size_perches || null,
        }),
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      setForecastResult(await res.json())
    } catch (e) { setForecastError(e.message) }
    finally { setForecastLoading(false) }
  }

  // manual submit from ForecastInput form
  const handleForecast = (form) => {
    lastAutoKey.current = null  // allow re-run
    runForecast(form)
  }

  const districts = meta?.forecast_districts ?? []

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
              LightGBM · SHAP Explainability · ikman.lk Data ·{' '}
              {meta ? `${meta.dataset_size.toLocaleString()} listings` : '8,814 listings'}
            </Text>
          </div>
        </Group>
      </header>

      {/* ── Body: sidebar | main ── */}
      <div className="app-body">
        <Sidebar meta={meta} />

        <div className="main-content">
          <div className="tab-panels-row">

            {/* ══ LEFT: tab switcher + form ══ */}
            <div className="left-col">

              <SegmentedControl
                fullWidth value={activeTab} onChange={setActiveTab} mb="md"
                data={[
                  {
                    value: 'current',
                    label: (
                      <Group gap={6} justify="center" wrap="nowrap">
                        <Home size={14} /><span>Current Price</span>
                      </Group>
                    ),
                  },
                  {
                    value: 'forecast',
                    label: (
                      <Group gap={6} justify="center" wrap="nowrap">
                        <TrendingUp size={14} /><span>Future Forecast 2026–2030</span>
                      </Group>
                    ),
                  },
                ]}
              />

              <div className="form-stretch">
                {activeTab === 'current'
                  ? <PredictionForm onPredict={handlePredict} loading={loading} meta={meta} />
                  : <ForecastInput
                    form={forecastForm}
                    setForm={setForecastForm}
                    onSubmit={handleForecast}
                    loading={forecastLoading}
                    districts={districts}
                    // Show hint if auto-filled from prediction
                    autoFilled={!!lastPredictData}
                  />
                }
              </div>
            </div>

            {/* ══ RIGHT: results ══ */}
            <div className="right-col">
              {activeTab === 'current' ? (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 16 }}>
                  {error && (
                    <Alert icon={<AlertCircle size={16} />} color="red" variant="light"
                      title="Prediction Error" radius="md" style={{ flexShrink: 0 }}>{error}</Alert>
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
                      <div className="panel-empty" style={{ height: '100%', minHeight: 320 }}>
                        <div className="empty-icon-wrap"><BarChart2 size={24} color="#6366f1" /></div>
                        <Text size="sm" fw={500} c="dark.1" mt="sm">No Prediction Yet</Text>
                        <Text size="xs" c="dimmed" mt={4}>Fill in property details and click Predict Price</Text>
                      </div>
                    </Paper>
                  )}
                </div>
              ) : (
                <Paper withBorder p="xl" radius="md" style={{ height: '100%', overflowY: 'auto' }}>
                  <ForecastResult result={forecastResult} loading={forecastLoading} error={forecastError} />
                </Paper>
              )}
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}
