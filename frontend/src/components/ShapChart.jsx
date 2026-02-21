import { Paper, Title, Text } from '@mantine/core'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer,
} from 'recharts'

export default function ShapChart({ shapFeatures }) {
  const data = (shapFeatures || [])
    .slice(0, 6)
    .map(f => ({ name: f.feature, value: f.importance }))
    .reverse()

  const maxVal = Math.max(...data.map(d => d.value), 0.1)

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const { name, value } = payload[0].payload
    return (
      <div className="shap-tooltip">
        <div style={{ fontWeight: 600, fontSize: '0.84rem', marginBottom: 4, color: '#e8eaf2' }}>{name}</div>
        <div style={{ fontSize: '0.8rem', color: '#818cf8' }}>Importance: {value.toFixed(4)}</div>
        <div style={{ fontSize: '0.75rem', color: '#6b7a99', marginTop: 3 }}>Mean |SHAP| in log-price units</div>
      </div>
    )
  }

  return (
    <Paper withBorder p="xl" radius="md" style={{ flex: 1 }}>
      <Title order={4} mb={4}>Feature Importance (SHAP)</Title>
      <Text size="xs" c="dimmed" mb="md">
        How much each feature influences the predicted price — computed via SHAP TreeExplainer.
      </Text>

      {/* Fixed pixel height — required for Recharts ResponsiveContainer */}
      <div style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 24, left: 16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgba(255,255,255,0.05)" />
            <XAxis
              type="number"
              domain={[0, maxVal * 1.15]}
              tickFormatter={v => v.toFixed(2)}
              tick={{ fontSize: 11, fill: '#4a5578' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.07)' }}
              tickLine={{ stroke: 'rgba(255,255,255,0.07)' }}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={170}
              tick={{ fontSize: 11, fill: '#6b7a99' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={
                    i === data.length - 1 ? '#6366f1' :
                      i === data.length - 2 ? '#818cf8' : '#94a3b8'
                  }
                  fillOpacity={0.85}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <Text size="xs" c="dimmed" mt="sm" ta="center">
        SHAP TreeExplainer · LightGBM Regressor · 8,814 listings from ikman.lk
      </Text>
    </Paper>
  )
}
