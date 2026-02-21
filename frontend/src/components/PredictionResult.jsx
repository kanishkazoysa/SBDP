import { Paper, Title, Text, Group, Badge } from '@mantine/core'
import { TrendingUp } from 'lucide-react'

function fmtLKR(v) {
  if (!v) return 'N/A'
  if (v >= 1_000_000) return `Rs. ${(v / 1_000_000).toFixed(2)}M`
  if (v >= 1_000)     return `Rs. ${(v / 1_000).toFixed(0)}K`
  return `Rs. ${v.toFixed(0)}`
}

export default function PredictionResult({ result }) {
  const {
    predicted_price, price_formatted,
    range_low_fmt, range_high_fmt,
    model_r2, model_mae,
  } = result

  const priceMillion = predicted_price / 1_000_000
  let tierColor = '#22c55e'
  let tierLabel = 'Budget'
  if (priceMillion > 100)     { tierColor = '#ef4444'; tierLabel = 'Premium' }
  else if (priceMillion > 30) { tierColor = '#f59e0b'; tierLabel = 'Mid-Range' }
  else if (priceMillion > 10) { tierColor = '#6366f1'; tierLabel = 'Standard' }

  return (
    <Paper withBorder p="xl" radius="md">
      <Title order={4} mb="md">Predicted Price</Title>

      <div style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.25)', borderRadius: 12, padding: '20px 24px', marginBottom: 16, textAlign: 'center' }}>
        <Group justify="center" mb={4}>
          <TrendingUp size={18} color="#6366f1" />
          <Text size="xs" tt="uppercase" fw={700} c="dimmed" style={{ letterSpacing: '1px' }}>
            Estimated Market Price
          </Text>
        </Group>
        <Text fw={800} size="2.4rem" style={{ color: tierColor, lineHeight: 1.1 }}>
          {price_formatted}
        </Text>
        <Text size="sm" c="dimmed" mt={6}>Range: {range_low_fmt} — {range_high_fmt}</Text>
        <Badge color="indigo" variant="light" mt={10} size="md">{tierLabel} Tier</Badge>
      </div>

      <div style={{ marginBottom: 20 }}>
        <Group justify="space-between" mb={4}>
          <Text size="xs" c="dimmed">Confidence Range</Text>
          <Text size="xs" c="dimmed">±1 std deviation</Text>
        </Group>
        <div style={{ position: 'relative', height: 8, background: 'rgba(255,255,255,0.06)', borderRadius: 4 }}>
          <div style={{ position: 'absolute', left: '10%', right: '10%', height: '100%', background: 'rgba(99,102,241,0.3)', borderRadius: 4 }} />
          <div style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%,-50%)', width: 12, height: 12, background: '#6366f1', borderRadius: '50%', border: '2px solid #0f1218' }} />
        </div>
        <Group justify="space-between" mt={4}>
          <Text size="xs" c="dimmed">{range_low_fmt}</Text>
          <Text size="xs" fw={600} c="indigo.3">{price_formatted}</Text>
          <Text size="xs" c="dimmed">{range_high_fmt}</Text>
        </Group>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 8, padding: '10px 14px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <Text size="xs" c="dimmed" mb={2}>Model R²</Text>
          <Text fw={700} size="lg" c="green.4">{(model_r2 * 100).toFixed(1)}%</Text>
          <Text size="xs" c="dimmed">variance explained</Text>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.04)', borderRadius: 8, padding: '10px 14px', border: '1px solid rgba(255,255,255,0.06)' }}>
          <Text size="xs" c="dimmed" mb={2}>Mean Abs Error</Text>
          <Text fw={700} size="lg" c="orange.4">{fmtLKR(model_mae)}</Text>
          <Text size="xs" c="dimmed">on test set</Text>
        </div>
      </div>
    </Paper>
  )
}
