import { Text, Stack, Box } from '@mantine/core'
import { BarChart2 } from 'lucide-react'

const NAV_ITEMS = [
  { Icon: BarChart2, label: 'Valuation', sub: 'Price predictor', active: true },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">

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

      <Box style={{ flex: 1 }} />

      {/* Footer */}
      <Box className="sidebar-footer">
        <Text size="xs" c="dimmed">Sri Lanka Real Estate</Text>
        <Text size="xs" c="dimmed" mt={2}>Property Valuation v1.0</Text>
      </Box>

    </aside>
  )
}
