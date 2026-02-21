import { Paper, Title, Text, Box } from '@mantine/core'
import {
  CheckCircle2, AlertTriangle, XCircle,
  Coffee, Moon, Flag, Sparkles, TrendingUp,
} from 'lucide-react'

const CLASS_META = [
  {
    label: 'On Time',
    Icon:  CheckCircle2,
    color: '#22c55e',
    cls:   'on-time',
    desc:  'Expected within 10 minutes of schedule',
  },
  {
    label: 'Slightly Delayed',
    Icon:  AlertTriangle,
    color: '#f59e0b',
    cls:   'slightly',
    desc:  'Expected 11–30 minutes late',
  },
  {
    label: 'Heavily Delayed',
    Icon:  XCircle,
    color: '#ef4444',
    cls:   'heavily',
    desc:  'Expected more than 30 minutes late',
  },
]

export default function PredictionResult({ result }) {
  const { prediction, pred_class_idx: idx, probabilities, meta } = result
  const { Icon, color, cls, desc } = CLASS_META[idx]

  const factors = []
  if (meta.is_festival) factors.push({ Icon: Sparkles,   text: 'Festival period active' })
  if (meta.is_holiday)  factors.push({ Icon: Flag,       text: 'Public holiday' })
  if (meta.is_poya)     factors.push({ Icon: Moon,       text: 'Poya day — significant travel surge' })
  if (meta.is_weekend)  factors.push({ Icon: Coffee,     text: 'Weekend travel' })
  if (['Morning Peak', 'Evening Peak'].includes(meta.time_slot))
    factors.push({ Icon: TrendingUp, text: `${meta.time_slot} — Colombo congestion` })

  return (
    <Paper withBorder p="xl" radius="md">
      <Title order={4} mb="md">Prediction Result</Title>

      {/* Status banner */}
      <div className={`result-banner ${cls}`}>
        <Icon size={30} color={color} strokeWidth={2} />
        <div>
          <Text fw={700} size="lg" style={{ color, lineHeight: 1.2 }}>
            {prediction}
          </Text>
          <Text size="sm" c="dimmed" mt={2}>{desc}</Text>
        </div>
      </div>

      {/* Probability cards */}
      <div className="prob-grid">
        {CLASS_META.map((c, i) => (
          <div key={c.label} className={`prob-card ${i === idx ? `active-${i}` : ''}`}>
            <div className={`prob-pct c-${i}`}>
              {(probabilities[i] * 100).toFixed(1)}%
            </div>
            <div className="prob-name">{c.label}</div>
          </div>
        ))}
      </div>

      {/* Contributing factors */}
      {factors.length > 0 && (
        <Box mt="md">
          <Text
            size="xs"
            c="dimmed"
            tt="uppercase"
            fw={600}
            mb={8}
            style={{ letterSpacing: '0.5px' }}
          >
            Contributing Factors
          </Text>
          <ul className="factors-list">
            {factors.map(({ Icon: FIcon, text }, i) => (
              <li key={i}>
                <FIcon size={14} color="#6366f1" style={{ flexShrink: 0 }} />
                {text}
              </li>
            ))}
          </ul>
        </Box>
      )}
    </Paper>
  )
}
