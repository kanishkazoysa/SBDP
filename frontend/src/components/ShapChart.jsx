import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ReferenceLine, Cell, ResponsiveContainer,
} from 'recharts'

const PRED_COLORS = ['#27ae60', '#e67e22', '#c0392b']

export default function ShapChart({ shapValues, featureNames, prediction, predIdx }) {
  // Build sorted data: top 10 by |SHAP|
  const data = featureNames
    .map((name, i) => ({ name, value: shapValues[i] }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 10)
    .reverse()   // largest at top in horizontal chart

  const maxAbs = Math.max(...data.map(d => Math.abs(d.value)), 0.1)

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const { name, value } = payload[0].payload
    return (
      <div style={{
        background: 'white', border: '1px solid #dde1e7',
        borderRadius: 7, padding: '8px 12px', fontSize: '0.83rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      }}>
        <strong>{name}</strong>
        <br />
        <span style={{ color: value >= 0 ? '#c0392b' : '#2980b9' }}>
          SHAP: {value >= 0 ? '+' : ''}{value.toFixed(4)}
        </span>
        <br />
        <span style={{ color: '#718096', fontSize: '0.78rem' }}>
          {value >= 0 ? 'Increases delay probability' : 'Decreases delay probability'}
        </span>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="card-title">Why did the model predict this? (SHAP)</h2>
      <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)', marginBottom: 16 }}>
        <span style={{ color: '#c0392b', fontWeight: 600 }}>Red bars</span> push toward a{' '}
        <em>higher delay</em> class.{' '}
        <span style={{ color: '#2980b9', fontWeight: 600 }}>Blue bars</span> push toward{' '}
        <em>on time</em>.
        Showing top 10 features by influence for the <strong>{prediction}</strong> prediction.
      </p>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis
            type="number"
            domain={[-maxAbs * 1.15, maxAbs * 1.15]}
            tickFormatter={v => v.toFixed(2)}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={165}
            tick={{ fontSize: 11 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine x={0} stroke="#aaa" strokeWidth={1.5} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.value >= 0 ? '#e74c3c' : '#3498db'}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 10, textAlign: 'center' }}>
        SHAP (SHapley Additive exPlanations) — TreeExplainer on LightGBM model
      </p>
    </div>
  )
}
