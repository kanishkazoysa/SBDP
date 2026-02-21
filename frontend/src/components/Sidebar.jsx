import { Text, ThemeIcon, Divider, Stack, Box } from '@mantine/core'
import { Home, BarChart2, MapPin, Info, Cpu, Database } from 'lucide-react'

const NAV_ITEMS = [
  { Icon: BarChart2, label: 'Predict',    sub: 'Price forecast',      active: true  },
  { Icon: MapPin,    label: 'Districts',  sub: 'All Sri Lanka',        active: false },
  { Icon: Info,      label: 'About',      sub: 'Model & data',         active: false },
]

export default function Sidebar({ meta }) {
  const r2  = meta?.metrics?.R2   ? `${(meta.metrics.R2 * 100).toFixed(1)}%` : '81.6%'
  const n   = meta?.dataset_size  ? meta.dataset_size.toLocaleString()        : '8,791'

  const STATS = [
    { Icon: Cpu,      label: 'Algorithm', value: 'LightGBM v4' },
    { Icon: Database, label: 'Listings',  value: `${n} rows`   },
    { Icon: BarChart2,label: 'R² Score',  value: r2            },
  ]

  return (
    <aside className="sidebar">

      {/* Brand */}
      <div className="sidebar-brand">
        <ThemeIcon variant="light" color="indigo" size={40} radius="md">
          <Home size={20} />
        </ThemeIcon>
        <div>
          <Text size="sm" fw={700} c="white" lh={1.2}>SLPPP</Text>
          <Text size="xs" c="dimmed" lh={1.1}>Price Predictor</Text>
        </div>
      </div>

      <Divider />

      {/* Navigation */}
      <Stack gap={4} className="sidebar-nav">
        <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={6} style={{ letterSpacing: '0.55px' }}>
          Menu
        </Text>
        {NAV_ITEMS.map(({ Icon, label, sub, active }) => (
          <div key={label} className={`sidebar-item ${active ? 'sidebar-item-active' : ''}`}>
            <Icon size={16} style={{ flexShrink: 0 }} />
            <div style={{ minWidth: 0 }}>
              <Text size="sm" fw={500} lh={1.2} truncate>{label}</Text>
              <Text size="xs" c="dimmed" lh={1.1} truncate>{sub}</Text>
            </div>
          </div>
        ))}
      </Stack>

      <Divider />

      {/* Model stats */}
      <Stack gap={4} className="sidebar-nav">
        <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={6} style={{ letterSpacing: '0.55px' }}>
          Model
        </Text>
        {STATS.map(({ Icon, label, value }) => (
          <div key={label} className="sidebar-stat">
            <Icon size={13} style={{ flexShrink: 0, color: '#6366f1' }} />
            <div style={{ minWidth: 0 }}>
              <Text size="xs" c="dimmed" lh={1.1}>{label}</Text>
              <Text size="xs" fw={600} c="dark.0" lh={1.2}>{value}</Text>
            </div>
          </div>
        ))}
      </Stack>

      {/* Footer */}
      <Box className="sidebar-footer">
        <Text size="xs" c="dimmed">Sri Lanka · ikman.lk</Text>
        <Text size="xs" c="dimmed" mt={2}>SHAP · LightGBM</Text>
      </Box>

    </aside>
  )
}
