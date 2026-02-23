import { useState, useEffect } from 'react'
import {
  Paper, Title, Text, Select, Grid, Button,
  NumberInput, Stack, Box, Divider, Group,
  Tooltip, ThemeIcon, Loader
} from '@mantine/core'
import {
  CloudRain, Thermometer, FlaskConical, Droplet,
  Sprout, Wind, MapPin, Beaker, Info, Settings,
  RefreshCw
} from 'lucide-react'

const DISTRICT_COORDS = {
  "Nuwara Eliya": { lat: 6.9497, lon: 80.7891, elev: "High" },
  "Kandy": { lat: 7.2906, lon: 80.6337, elev: "Mid" },
  "Ratnapura": { lat: 6.6828, lon: 80.3992, elev: "Low" },
  "Badulla": { lat: 6.9934, lon: 81.0550, elev: "High" },
  "Galle": { lat: 6.0535, lon: 80.2210, elev: "Low" },
  "Matale": { lat: 7.4675, lon: 80.6234, elev: "Mid" },
  "Kalutara": { lat: 6.5854, lon: 79.9607, elev: "Low" },
  "Kegalle": { lat: 7.2513, lon: 80.3464, elev: "Mid" }
}

export default function PredictionForm({ onPredict, loading, meta }) {
  const [form, setForm] = useState({
    district: '',
    elevation: '',
    monthly_rainfall_mm: 200,
    avg_temp_c: 22,
    soil_nitrogen: 50,
    soil_phosphorus: 25,
    soil_potassium: 35,
    soil_ph: 5.0,
    fertilizer_type: 'Combo',
    drainage_quality: 'Good',
  })

  const [weatherLoading, setWeatherLoading] = useState(false)

  const districts = (meta?.districts || []).map(d => ({ value: d, label: d }))
  const elevations = (meta?.elevations || []).map(e => ({ value: e, label: e }))
  const fertilizerTypes = (meta?.fertilizer_types || []).map(t => ({ value: t, label: t }))
  const drainageQualities = (meta?.drainage_qualities || []).map(q => ({ value: q, label: q }))

  useEffect(() => {
    if (!form.district && districts.length > 0) {
      set('district', districts[0].value)
    }
    if (!form.elevation && elevations.length > 0) {
      set('elevation', elevations[0].value)
    }
  }, [districts, elevations])

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const fetchWeather = async (district) => {
    const coords = DISTRICT_COORDS[district]
    if (!coords) return

    setWeatherLoading(true)
    try {
      // Use Open-Meteo (No API key required)
      const res = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${coords.lat}&longitude=${coords.lon}&current=temperature_2m,precipitation&daily=precipitation_sum&timezone=auto&past_days=7`)
      const data = await res.json()

      const currentTemp = data.current.temperature_2m
      // Estimate monthly rainfall based on last 7 days + forecast (simple heuristic for university project)
      const weeklyRain = data.daily.precipitation_sum.reduce((a, b) => a + b, 0)
      const estMonthlyRain = Math.max(50, Math.round(weeklyRain * 4))

      setForm(f => ({
        ...f,
        district: district,
        elevation: coords.elev,
        avg_temp_c: Math.round(currentTemp),
        monthly_rainfall_mm: estMonthlyRain
      }))
    } catch (e) {
      console.error("Weather sync failed", e)
    } finally {
      setWeatherLoading(false)
    }
  }

  const handleDistrictChange = (val) => {
    if (!val) return
    set('district', val)
    fetchWeather(val)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.district) return
    onPredict(form)
  }

  const InputLabel = ({ label, icon: Icon, info }) => (
    <Group gap={6} mb={6}>
      <Icon size={14} color="var(--tea-emerald)" />
      <Text size="sm" fw={700} c="gray.3">{label}</Text>
      {info && (
        <Tooltip label={info} position="top-start" withArrow>
          <Info size={12} color="#94a3b8" style={{ cursor: 'help' }} />
        </Tooltip>
      )}
    </Group>
  )

  return (
    <Paper component="form" onSubmit={handleSubmit} className="premium-card" p="lg" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Group justify="space-between" mb="md">
        <Box>
          <Title order={3} c="white" style={{ letterSpacing: '-0.5px' }}>Estate Assessment</Title>
          <Text size="xs" c="dimmed">Input regional telemetry for Yield Forecasting</Text>
        </Box>
        <ThemeIcon variant="light" color="green" radius="xl" size="xl">
          <FlaskConical size={20} />
        </ThemeIcon>
      </Group>

      <Stack gap="md" style={{ flex: 1 }}>
        <Box>
          <Grid gutter="md">
            <Grid.Col span={6}>
              <Box>
                <InputLabel label="Growth District" icon={MapPin} info="Primary cultivation region in Sri Lanka" />
                <Select
                  placeholder="Select District"
                  data={districts}
                  value={form.district}
                  onChange={handleDistrictChange}
                  searchable
                  required
                  rightSection={weatherLoading ? <Loader size={14} color="green" /> : null}
                />
              </Box>
            </Grid.Col>
            <Grid.Col span={6}>
              <Box>
                <InputLabel label="Elevation Zone" icon={Wind} info="High, Mid, or Low-grown classification" />
                <Select
                  placeholder="Select Zone"
                  data={elevations}
                  value={form.elevation}
                  onChange={val => val && set('elevation', val)}
                  required
                />
              </Box>
            </Grid.Col>
          </Grid>
        </Box>

        <Divider
          label={
            <Group gap={4}>
              <RefreshCw size={10} className={weatherLoading ? 'spin' : ''} />
              <Text size="10px">CLIMATIC SIGNALS SYNCED</Text>
            </Group>
          }
          labelPosition="center"
          color="rgba(16, 185, 129, 0.2)"
        />

        <Box>
          <Grid gutter="md">
            <Grid.Col span={6}>
              <Box>
                <InputLabel label="Monthly Rainfall" icon={CloudRain} info="Synced from Open-Meteo satellite data" />
                <NumberInput
                  description="Estimated (mm)"
                  min={0} max={1000}
                  value={form.monthly_rainfall_mm}
                  onChange={val => set('monthly_rainfall_mm', val)}
                  required
                  className={weatherLoading ? 'fade-pulse' : ''}
                />
              </Box>
            </Grid.Col>
            <Grid.Col span={6}>
              <Box>
                <InputLabel label="Ambient Temp" icon={Thermometer} info="Live regional temperature" />
                <NumberInput
                  description="Live (°C)"
                  min={5} max={45}
                  value={form.avg_temp_c}
                  onChange={val => set('avg_temp_c', val)}
                  required
                  className={weatherLoading ? 'fade-pulse' : ''}
                />
              </Box>
            </Grid.Col>
          </Grid>
        </Box>

        <Divider label="Soil Nutritional Profile" labelPosition="center" color="rgba(255,255,255,0.05)" />

        <Box>
          <Grid gutter="md">
            <Grid.Col span={4}>
              <Box>
                <InputLabel label="Nitrogen (N)" icon={Beaker} />
                <NumberInput min={0} max={150} value={form.soil_nitrogen} onChange={val => set('soil_nitrogen', val)} />
              </Box>
            </Grid.Col>
            <Grid.Col span={4}>
              <Box>
                <InputLabel label="Phos (P)" icon={Beaker} />
                <NumberInput min={0} max={100} value={form.soil_phosphorus} onChange={val => set('soil_phosphorus', val)} />
              </Box>
            </Grid.Col>
            <Grid.Col span={4}>
              <Box>
                <InputLabel label="Potassium (K)" icon={Beaker} />
                <NumberInput min={0} max={150} value={form.soil_potassium} onChange={val => set('soil_potassium', val)} />
              </Box>
            </Grid.Col>
          </Grid>
        </Box>

        <Box>
          <Grid gutter="md">
            <Grid.Col span={6}>
              <Box>
                <InputLabel label="Soil pH Balance" icon={FlaskConical} info="Optimal range for tea is 4.5 - 5.5" />
                <NumberInput min={3} max={9} decimalScale={1} value={form.soil_ph} onChange={val => set('soil_ph', val)} />
              </Box>
            </Grid.Col>
            <Grid.Col span={6}>
              <Box>
                <InputLabel label="Drainage" icon={Droplet} />
                <Select
                  data={drainageQualities}
                  value={form.drainage_quality}
                  onChange={val => val && set('drainage_quality', val)}
                  required
                />
              </Box>
            </Grid.Col>
          </Grid>
        </Box>

        <Box>
          <InputLabel label="Active Management Practice" icon={Settings} />
          <Select
            placeholder="Select Practice"
            data={fertilizerTypes}
            value={form.fertilizer_type}
            onChange={val => val && set('fertilizer_type', val)}
            required
          />
        </Box>

        <Box mt="auto">
          <Button
            type="submit"
            fullWidth
            loading={loading}
            disabled={!meta || !form.district || weatherLoading}
            className="forecast-action-btn"
          >
            GENERATE FORECAST
          </Button>
        </Box>
      </Stack>
    </Paper>
  )
}
