import { Paper, Title, Text } from '@mantine/core'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, Cell, ResponsiveContainer,
} from 'recharts'

export default function ShapChart({ shapValues, featureNames, prediction }) {
  // Top 10 features by absolute SHAP value, largest at top
  const data = featureNames
    .map((name, i) => ({ name, value: shapValues[i] }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 10)
    .reverse()

  const maxAbs = Math.max(...data.map(d => Math.abs(d.value)), 0.1)

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const { name, value } = payload[0].payload
    return (
      <div className="shap-tooltip">
        <div style={{ fontWeight: 600, fontSize: '0.84rem', marginBottom: 4, color: '#e8eaf2' }}>
          {name}
        </div>
        <div style={{ fontSize: '0.8rem', color: value >= 0 ? '#f87171' : '#60a5fa' }}>
          SHAP: {value >= 0 ? '+' : ''}{value.toFixed(4)}
        </div>
        <div style={{ fontSize: '0.75rem', color: '#6b7a99', marginTop: 3 }}>
          {value >= 0 ? 'Increases delay probability' : 'Decreases delay probability'}
        </div>
      </div>
    )
  }

  return (
    // Paper fills the full flex column of panel-right
    <Paper
      withBorder
      p="xl"
      radius="md"
      style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
    >
      <Title order={4} mb={4}>Model Explanation (SHAP)</Title>
      <Text size="xs" c="dimmed" mb="md">
        Top 10 features for the{' '}
        <Text component="span" fw={600} c="dark.0">{prediction}</Text>{' '}
        prediction.{' '}
        <Text component="span" c="red.4">Red</Text> = increases delay,{' '}
        <Text component="span" c="blue.4">blue</Text> = decreases it.
      </Text>

      {/* Chart fills remaining vertical space */}
      <div style={{ flex: 1, minHeight: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 0, right: 20, left: 12, bottom: 0 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={false}
              stroke="rgba(255,255,255,0.05)"
            />
            <XAxis
              type="number"
              domain={[-maxAbs * 1.15, maxAbs * 1.15]}
              tickFormatter={v => v.toFixed(2)}
              tick={{ fontSize: 11, fill: '#4a5578' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.07)' }}
              tickLine={{ stroke: 'rgba(255,255,255,0.07)' }}
            />
            <YAxis
              type="category"
              dataKey="name"
              width={160}
              tick={{ fontSize: 11, fill: '#6b7a99' }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ fill: 'rgba(255,255,255,0.03)' }}
            />
            <ReferenceLine x={0} stroke="rgba(255,255,255,0.1)" strokeWidth={1.5} />
            <Bar dataKey="value" radius={[0, 3, 3, 0]}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={entry.value >= 0 ? '#f87171' : '#60a5fa'}
                  fillOpacity={0.88}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <Text size="xs" c="dimmed" mt="sm" ta="center">
        SHAP TreeExplainer — LightGBM multiclass model
      </Text>
    </Paper>
  )
}
