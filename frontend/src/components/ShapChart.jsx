import { Paper, Title, Text, Group } from '@mantine/core'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer, ReferenceLine
} from 'recharts'

export default function ShapChart({ shapFeatures }) {
  const data = (shapFeatures || [])
    .slice(0, 7)
    .map(f => ({
      name: f.feature,
      value: f.importance,
      abs: Math.abs(f.importance)
    }))
    .reverse()

  const maxAbs = Math.max(...data.map(d => d.abs), 0.1)

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const { name, value } = payload[0].payload
    const isPositive = value >= 0
    return (
      <div className="shap-tooltip" style={{
        background: '#1a1b1e',
        padding: '10px',
        border: `1px solid ${isPositive ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
      }}>
        <div style={{ fontWeight: 600, fontSize: '0.84rem', marginBottom: 4, color: '#e8eaf2' }}>{name}</div>
        <div style={{
          fontSize: '0.85rem',
          fontWeight: 700,
          color: isPositive ? '#4ade80' : '#f87171'
        }}>
          {isPositive ? '+' : ''}{value.toFixed(4)}
        </div>
        <div style={{ fontSize: '0.7rem', color: '#6b7a99', marginTop: 3 }}>
          Impact on Log-Price units
        </div>
      </div>
    )
  }

  return (
    <Paper withBorder p="xl" radius="md" style={{ flex: 1, position: 'relative' }}>
      <Group justify="space-between" align="flex-start" mb="md">
        <div>
          <Title order={4} mb={4}>Local Explanation (SHAP)</Title>
          <Text size="xs" c="dimmed">
            How features influenced THIS specific prediction.
          </Text>
        </div>
        <Group gap="xs">
          <Group gap={4}><div style={{ width: 8, height: 8, background: '#10b981', borderRadius: 2 }} /><Text size="10px" c="dimmed">Increases Price</Text></Group>
          <Group gap={4}><div style={{ width: 8, height: 8, background: '#ef4444', borderRadius: 2 }} /><Text size="10px" c="dimmed">Decreases Price</Text></Group>
        </Group>
      </Group>

      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
            <XAxis
              type="number"
              domain={[-maxAbs, maxAbs]}
              hide
            />
            <YAxis
              type="category"
              dataKey="name"
              width={140}
              tick={{ fontSize: 11, fill: '#6b7a99' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            <ReferenceLine x={0} stroke="rgba(255,255,255,0.2)" />
            <Bar dataKey="value" radius={4}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.value >= 0 ? '#10b981' : '#ef4444'}
                  fillOpacity={0.8}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <Text size="xs" c="dimmed" mt="xs" ta="center" italic>
        "Why is it this price?" — real-time XAI breakdown.
      </Text>
    </Paper>
  )
}
