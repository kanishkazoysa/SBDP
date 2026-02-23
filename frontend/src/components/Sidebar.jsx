import { Text, Stack, Box, Group, Badge, ThemeIcon } from '@mantine/core'
import { Activity, Microscope, Share2, Database, ShieldCheck } from 'lucide-react'

const NAV_ITEMS = [
  { Icon: Activity, label: 'Analytics', sub: 'Yield Forecast', active: true },
]

export default function Sidebar({ meta }) {
  return (
    <aside className="sidebar">
      {/* Brand Section already in App header, so focus on Navigation */}

      <Box className="sidebar-nav">
        <Text size="xs" c="dimmed" tt="uppercase" fw={800} mb="xl" style={{ letterSpacing: '1.5px', paddingLeft: 16 }}>
          Operational Suite
        </Text>

        <Stack gap={6}>
          {NAV_ITEMS.map(({ Icon, label, sub, active }) => (
            <div key={label} className={`sidebar-item ${active ? 'sidebar-item-active' : ''}`}>
              <Icon size={18} />
              <div style={{ minWidth: 0 }}>
                <Text size="sm" fw={700} lh={1.1}>{label}</Text>
                <Text size="xs" c="dimmed" lh={1} mt={4}>{sub}</Text>
              </div>
            </div>
          ))}
        </Stack>
      </Box>

      <Box style={{ flex: 1 }} />

      <Box px={16} mb="xl">
        <Text size="xs" c="dimmed" tt="uppercase" fw={800} mb="lg" style={{ letterSpacing: '1.5px' }}>
          System Integrity
        </Text>

        <Stack gap="sm">
          <Box p="md" style={{ borderRadius: 12, border: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
            <Group justify="space-between" mb={4}>
              <Text size="xs" fw={700} c="dimmed">R² PRECISION</Text>
              <Badge variant="dot" color="green" size="xs">ACTIVE</Badge>
            </Group>
            <Text size="lg" fw={900} c="white">
              {meta?.metrics?.R2 ? (meta.metrics.R2 * 100).toFixed(1) + '%' : '...'}
            </Text>
          </Box>

          <Box p="md" style={{ borderRadius: 12, border: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
            <Text size="xs" fw={700} c="dimmed" mb={4}>TELEMETRY DATA</Text>
            <Group gap={6}>
              <Database size={12} color="var(--tea-emerald)" />
              <Text size="sm" fw={800} c="white">{meta?.dataset_size || '0'}</Text>
              <Text size="xs" c="dimmed">Data Points</Text>
            </Group>
          </Box>
        </Stack>
      </Box>

      <Box className="sidebar-footer">
        <Group gap="xs" mb={8}>
          <ShieldCheck size={14} color="var(--tea-emerald)" />
          <Text size="xs" fw={700} c="white">ENCRYPTED CORE</Text>
        </Group>
        <Text size="xs" c="dimmed">Distributed for Tea Research Institute Sri Lanka (TRI)</Text>
      </Box>
    </aside>
  )
}
