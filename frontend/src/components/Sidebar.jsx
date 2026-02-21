import { Text, ThemeIcon, Divider, Stack, Box } from '@mantine/core'
import { Bus, BarChart2, MapPin, Info, Cpu, Database } from 'lucide-react'

const NAV_ITEMS = [
  { Icon: BarChart2, label: 'Predict',    sub: 'Delay forecast',     active: true  },
  { Icon: MapPin,    label: 'Routes',     sub: '5 intercity routes', active: false },
  { Icon: Info,      label: 'About',      sub: 'Model & data',       active: false },
]

const STATS = [
  { Icon: Cpu,      label: 'Algorithm', value: 'LightGBM v4'  },
  { Icon: Database, label: 'Dataset',   value: '500 trips'    },
  { Icon: BarChart2,label: 'Accuracy',  value: '81.3%'        },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">

      {/* Brand */}
      <div className="sidebar-brand">
        <ThemeIcon variant="light" color="indigo" size={40} radius="md">
          <Bus size={20} />
        </ThemeIcon>
        <div>
          <Text size="sm" fw={700} c="white" lh={1.2}>SBDP</Text>
          <Text size="xs" c="dimmed" lh={1.1}>Bus Predictor</Text>
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
        <Text size="xs" c="dimmed">Sri Lanka · 2024</Text>
        <Text size="xs" c="dimmed" mt={2}>SHAP · LIME · PDP</Text>
      </Box>

    </aside>
  )
}
