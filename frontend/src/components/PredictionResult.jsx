const CLASS_META = [
  { label: 'On Time',          emoji: '✅', cls: 'on-time',  desc: 'Expected to arrive within 10 minutes of schedule.' },
  { label: 'Slightly Delayed', emoji: '⚠️', cls: 'slightly', desc: 'Expected to arrive 11–30 minutes late.' },
  { label: 'Heavily Delayed',  emoji: '🔴', cls: 'heavily',  desc: 'Expected to arrive more than 30 minutes late.' },
]

export default function PredictionResult({ result }) {
  const { prediction, pred_class_idx: idx, probabilities, meta } = result

  const factors = []
  if (meta.is_festival)  factors.push({ icon: '🎊', text: `Festival period active` })
  if (meta.is_holiday)   factors.push({ icon: '🎉', text: 'Public holiday — expect heavy travel' })
  if (meta.is_poya)      factors.push({ icon: '🌕', text: 'Poya day — significant travel surge' })
  if (meta.is_weekend)   factors.push({ icon: '🏖️', text: 'Weekend travel' })
  if (['Morning Peak','Evening Peak'].includes(meta.time_slot))
    factors.push({ icon: '🚦', text: `${meta.time_slot} — Colombo congestion` })

  const cm = CLASS_META[idx]

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h2 className="card-title">Prediction Result</h2>

      {/* Banner */}
      <div className={`result-banner ${cm.cls}`}>
        <span className="result-emoji">{cm.emoji}</span>
        <div>
          <div className="result-label">{prediction}</div>
          <div className="result-desc">{cm.desc}</div>
        </div>
      </div>

      {/* Probability cards */}
      <div className="prob-grid">
        {CLASS_META.map((c, i) => (
          <div key={c.label} className={`prob-card${i === idx ? ` active-${i}` : ''}`}>
            <div className="prob-pct">{(probabilities[i] * 100).toFixed(1)}%</div>
            <div className="prob-name">{c.emoji} {c.label}</div>
          </div>
        ))}
      </div>

      {/* Contributing factors */}
      {factors.length > 0 && (
        <>
          <p style={{ fontSize:'0.8rem', fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.4px', marginBottom:6 }}>
            Contributing Factors
          </p>
          <ul className="factors-list">
            {factors.map((f, i) => (
              <li key={i}>
                <span style={{ fontSize: '1rem' }}>{f.icon}</span>
                {f.text}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
