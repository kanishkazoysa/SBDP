import { useState } from 'react'
import {
  Paper, Title, Text, Select, Grid, Button, Slider,
  Badge, Stack, Group, Box, Divider,
} from '@mantine/core'
import {
  MapPin, Bus, CloudRain, CalendarDays, Clock,
  Users, AlarmClock, Moon, Flag, Sparkles, Coffee,
  Navigation, Zap,
} from 'lucide-react'

// ── Reference data ────────────────────────────────────────────────────────────
const ROUTES = {
  '01':   { label: 'Route 01 — Colombo → Kandy (116 km)',      distance: 116, duration: { Normal: 210, 'Semi Luxury': 185, Luxury: 165 } },
  '32':   { label: 'Route 32 — Colombo → Galle (119 km)',      distance: 119, duration: { Normal: 195, 'Semi Luxury': 170, Luxury: 150 } },
  '04':   { label: 'Route 04 — Colombo → Kurunegala (94 km)',  distance: 94,  duration: { Normal: 150, 'Semi Luxury': 130, Luxury: 110 } },
  '04-2': { label: 'Route 04-2 — Colombo → Negombo (37 km)',   distance: 37,  duration: { Normal: 75,  'Semi Luxury': 65,  Luxury: 55  } },
  '98':   { label: 'Route 98 — Colombo → Ratnapura (100 km)',  distance: 100, duration: { Normal: 180, 'Semi Luxury': 160, Luxury: 140 } },
}

const POYA_DAYS = new Set([
  '2024-01-25','2024-02-24','2024-03-25','2024-04-23','2024-05-23','2024-06-21',
  '2024-07-21','2024-08-19','2024-09-17','2024-10-17','2024-11-15','2024-12-15',
  '2025-01-13','2025-02-12','2025-03-13','2025-04-12','2025-05-12','2025-06-11',
  '2025-07-10','2025-08-09','2025-09-07','2025-10-06','2025-11-05','2025-12-04',
])

const PUBLIC_HOLIDAYS = new Set([
  '2024-01-15','2024-02-04','2024-03-29','2024-04-11','2024-04-12','2024-04-13',
  '2024-04-14','2024-05-01','2024-05-23','2024-05-24','2024-06-17','2024-06-21',
  '2024-07-21','2024-08-19','2024-09-16','2024-09-17','2024-10-17','2024-10-31',
  '2024-11-15','2024-12-15','2024-12-25',
  '2025-01-14','2025-02-04','2025-04-14','2025-05-01','2025-05-12','2025-12-25',
])

const FESTIVAL_PERIODS = [
  ['2024-04-10','2024-04-16','Sinhala New Year'],
  ['2024-05-20','2024-05-26','Vesak'],
  ['2024-06-18','2024-06-23','Poson'],
  ['2024-07-24','2024-08-10','Kandy Perahera'],
  ['2024-10-29','2024-11-02','Deepavali'],
  ['2024-12-23','2024-12-27','Christmas'],
  ['2025-04-10','2025-04-16','Sinhala New Year'],
  ['2025-05-10','2025-05-16','Vesak'],
]

function getFestival(dateStr) {
  const f = FESTIVAL_PERIODS.find(([s, e]) => dateStr >= s && dateStr <= e)
  return f ? f[2] : null
}

function todayStr() {
  return new Date().toISOString().split('T')[0]
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function PredictionForm({ onPredict, loading }) {
  const [form, setForm] = useState({
    route_no:            '01',
    bus_type:            'Normal',
    departure_date:      todayStr(),
    departure_time:      '07:00',
    weather:             'Clear',
    crowding_level:      'Medium',
    departure_delay_min: 0,
  })

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  // Auto-computed flags
  const d         = form.departure_date
  const dow       = new Date(d).getDay()
  const isWeekend = dow === 0 || dow === 6
  const isPoya    = POYA_DAYS.has(d)
  const isHoliday = PUBLIC_HOLIDAYS.has(d)
  const festival  = getFestival(d)

  const routeInfo = ROUTES[form.route_no]
  const schedMins = routeInfo.duration[form.bus_type]
  const schedH    = Math.floor(schedMins / 60)
  const schedM    = schedMins % 60

  const handleSubmit = (e) => {
    e.preventDefault()
    onPredict({ ...form, departure_delay_min: Number(form.departure_delay_min) })
  }

  const routeData   = Object.entries(ROUTES).map(([no, r]) => ({ value: no, label: r.label }))
  const busTypes    = ['Normal', 'Semi Luxury', 'Luxury'].map(v => ({ value: v, label: v }))
  const weatherOpts = ['Clear', 'Cloudy', 'Light Rain', 'Moderate Rain', 'Heavy Rain'].map(v => ({ value: v, label: v }))
  const crowdOpts   = ['Low', 'Medium', 'High'].map(v => ({ value: v, label: v }))

  const flags = [
    { active: isWeekend,  Icon: Coffee,   label: isWeekend  ? 'Weekend'        : 'Weekday'    },
    { active: isPoya,     Icon: Moon,     label: isPoya     ? 'Poya Day'       : 'No Poya'    },
    { active: isHoliday,  Icon: Flag,     label: isHoliday  ? 'Public Holiday' : 'No Holiday' },
    { active: !!festival, Icon: Sparkles, label: festival   || 'No Festival'                  },
  ]

  return (
    <Paper
      component="form"
      onSubmit={handleSubmit}
      withBorder
      p="xl"
      radius="md"
      style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
    >
      <Title order={4} mb="xl">Trip Details</Title>

      <Stack gap="lg" style={{ flex: 1 }}>
        {/* Route */}
        <Select
          label="Route"
          leftSection={<MapPin size={15} />}
          leftSectionPointerEvents="none"
          data={routeData}
          value={form.route_no}
          onChange={val => val && set('route_no', val)}
          allowDeselect={false}
        />

        {/* Bus Type + Weather */}
        <Grid gutter="md">
          <Grid.Col span={{ base: 12, xs: 6 }}>
            <Select
              label="Bus Type"
              leftSection={<Bus size={15} />}
              leftSectionPointerEvents="none"
              data={busTypes}
              value={form.bus_type}
              onChange={val => val && set('bus_type', val)}
              allowDeselect={false}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, xs: 6 }}>
            <Select
              label="Weather"
              leftSection={<CloudRain size={15} />}
              leftSectionPointerEvents="none"
              data={weatherOpts}
              value={form.weather}
              onChange={val => val && set('weather', val)}
              allowDeselect={false}
            />
          </Grid.Col>
        </Grid>

        {/* Date + Time */}
        <Grid gutter="md">
          <Grid.Col span={{ base: 12, xs: 6 }}>
            <label className="native-label">
              <CalendarDays size={14} /> Travel Date
            </label>
            <input
              type="date"
              className="native-input"
              value={form.departure_date}
              min="2024-01-01"
              max="2026-12-31"
              onChange={e => set('departure_date', e.target.value)}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 12, xs: 6 }}>
            <label className="native-label">
              <Clock size={14} /> Departure Time
            </label>
            <input
              type="time"
              className="native-input"
              value={form.departure_time}
              onChange={e => set('departure_time', e.target.value)}
            />
          </Grid.Col>
        </Grid>

        {/* Crowding */}
        <Select
          label="Expected Crowding"
          leftSection={<Users size={15} />}
          leftSectionPointerEvents="none"
          data={crowdOpts}
          value={form.crowding_level}
          onChange={val => val && set('crowding_level', val)}
          allowDeselect={false}
        />

        {/* Departure delay slider */}
        <Box>
          <Group justify="space-between" mb={6}>
            <label className="native-label" style={{ margin: 0 }}>
              <AlarmClock size={14} /> Departure Delay
            </label>
            <Text
              size="sm"
              fw={600}
              c={form.departure_delay_min > 0 ? 'orange.4' : 'dimmed'}
            >
              {form.departure_delay_min > 0
                ? `+${form.departure_delay_min} min late`
                : 'On time'}
            </Text>
          </Group>
          <Slider
            min={0}
            max={60}
            step={1}
            value={Number(form.departure_delay_min)}
            onChange={val => set('departure_delay_min', val)}
            label={val => `${val} min`}
            marks={[
              { value: 0,  label: '0'   },
              { value: 20, label: '20m' },
              { value: 40, label: '40m' },
              { value: 60, label: '60m' },
            ]}
            mb="lg"
          />
        </Box>

        <Divider my="md" />

        {/* Auto-detected flags */}
        <Box>
          <Text
            size="xs"
            c="dimmed"
            tt="uppercase"
            fw={600}
            mb="md"
            style={{ letterSpacing: '0.6px' }}
          >
            Auto-detected from date
          </Text>

          {/* 2×2 badge grid */}
          <Grid gutter="sm">
            {flags.map(({ active, Icon, label }) => (
              <Grid.Col key={label} span={6}>
                <Badge
                  variant={active ? 'light' : 'outline'}
                  color={active ? 'indigo' : 'gray'}
                  leftSection={<Icon size={12} />}
                  size="md"
                  radius="sm"
                  fullWidth
                  style={{ cursor: 'default', fontWeight: 500, justifyContent: 'flex-start', padding: '8px 12px', height: 'auto' }}
                >
                  {label}
                </Badge>
              </Grid.Col>
            ))}
          </Grid>

          <div className="journey-pill" style={{ marginTop: 14 }}>
            <Navigation size={14} style={{ flexShrink: 0, color: '#6366f1' }} />
            <Text size="sm">
              Scheduled:{' '}
              <Text component="span" fw={700} c="dark.0">
                {schedH}h{schedM > 0 ? ` ${schedM}min` : ''}
              </Text>
              {' '}· {routeInfo.distance} km
            </Text>
          </div>
        </Box>
      </Stack>

      <Button
        type="submit"
        fullWidth
        size="md"
        mt="xl"
        loading={loading}
        leftSection={loading ? null : <Zap size={16} />}
      >
        Predict Delay
      </Button>
    </Paper>
  )
}
