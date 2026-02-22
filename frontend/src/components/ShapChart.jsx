import { Box, Group, Text } from '@mantine/core'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer, ReferenceLine
} from 'recharts'

export default function ShapChart({ shapFeatures }) {
  const data = (shapFeatures || [])
    .slice(0, 8)
    .map(f => ({
      name: f.feature,
      value: f.importance,
      abs: Math.abs(f.importance)
    }))
    .reverse()

  const maxAbs = Math.max(...data.map(d => d.abs), 0.01)

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const { name, value } = payload[0].payload
    const isPositive = value >= 0
    return (
      <div className="shap-tooltip" style={{
        background: 'rgba(15, 20, 28, 0.95)',
        padding: '12px',
        border: `1px solid ${isPositive ? '#10b98133' : '#ef444433'}`,
        borderRadius: '12px',
        boxShadow: '0 10px 30px rgba(0,0,0,0.6)',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{ fontWeight: 800, fontSize: '0.8rem', marginBottom: 6, color: '#e2e8f0', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{name}</div>
        <div style={{
          fontSize: '1.2rem',
          fontWeight: 900,
          color: isPositive ? '#10b981' : '#ef4444',
          lineHeight: 1
        }}>
          {isPositive ? '+' : ''}{value.toFixed(4)}
        </div>
        <div style={{ fontSize: '0.65rem', color: '#94a3b8', marginTop: 6, fontWeight: 600 }}>
          IMPACT ON YIELD (MT/HEC)
        </div>
      </div>
    )
  }

  return (
    <Box style={{ width: '100%', flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <Group justify="flex-end" mb="md" gap="xl">
        <Group gap={6}>
          <div style={{ width: 10, height: 10, background: '#10b981', borderRadius: 3 }} />
          <Text size="11px" fw={700} c="dimmed">IMPROVES HARVEST</Text>
        </Group>
        <Group gap={6}>
          <div style={{ width: 10, height: 10, background: '#ef4444', borderRadius: 3 }} />
          <Text size="11px" fw={700} c="dimmed">LIMITS HARVEST</Text>
        </Group>
      </Group>

      <div style={{ width: '100%', flex: 1, minHeight: 180 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 40, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="4 4" horizontal={false} stroke="rgba(255,255,255,0.03)" />
            <XAxis
              type="number"
              domain={[-maxAbs * 1.1, maxAbs * 1.1]}
              hide
            />
            <YAxis
              type="category"
              dataKey="name"
              width={160}
              tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 600 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: 'rgba(255,255,255,0.02)' }}
              animationDuration={200}
            />
            <ReferenceLine x={0} stroke="rgba(255,255,255,0.15)" strokeWidth={2} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={22}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.value >= 0 ? '#10b981' : '#ef4444'}
                  fillOpacity={0.9}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <Box mt="xl" p="md" style={{ border: '1px solid rgba(16, 185, 129, 0.1)', borderRadius: 12, background: 'rgba(16, 185, 129, 0.02)' }}>
        <Text size="xs" c="dimmed" ta="center" fw={500}>
          The chart above visualizes the <span style={{ color: 'var(--tea-emerald)', fontWeight: 700 }}>Model Explanation</span>: identifying which environmental factors are mathematically responsible for the current forecast.
        </Text>
      </Box>
    </Box>
  )
}
