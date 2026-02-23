import { Paper, Title, Text, Group, Badge, ThemeIcon, Stack, Box } from '@mantine/core'
import { TrendingUp, Wheat, AlertCircle, Sparkles } from 'lucide-react'

export default function PredictionResult({ result }) {
  const {
    predicted_yield, yield_unit,
    model_r2, model_mae,
  } = result

  let tierColor = 'green'
  let tierLabel = 'Optimal'
  let description = "This configuration indicates a high-yield harvest. Environment and nutrients are well-aligned."
  let gradient = { from: '#10b981', to: '#059669', deg: 135 }

  if (predicted_yield < 0.6) {
    tierColor = 'red'
    tierLabel = 'Critical Low'
    gradient = { from: '#ef4444', to: '#991b1b', deg: 135 }
    description = "Yield is significantly below industrial average. Check Phosphorus levels and drainage immediately."
  } else if (predicted_yield < 0.9) {
    tierColor = 'orange'
    tierLabel = 'Sub-Optimal'
    gradient = { from: '#f59e0b', to: '#b45309', deg: 135 }
    description = "Yield is slightly below potential. Consider adjusting Nitrogen balance or Irrigation timing."
  } else if (predicted_yield > 1.4) {
    tierColor = 'teal'
    tierLabel = 'Elite Harvest'
    gradient = { from: '#14b8a6', to: '#0f766e', deg: 135 }
    description = "Exceptional yield parameters. This estate is performing at peak biological efficiency."
  }

  return (
    <Paper className="premium-card" p="lg">
      <Group justify="space-between" mb="md">
        <Group gap="xs">
          <ThemeIcon variant="light" color={tierColor} radius="md">
            <Sparkles size={16} />
          </ThemeIcon>
          <Title order={4} c="white">Yield Forecast Result</Title>
        </Group>
        <Badge variant="filled" color={tierColor} size="lg" radius="sm" p="md">
          {tierLabel}
        </Badge>
      </Group>

      <Box style={{
        background: 'rgba(12, 18, 16, 0.8)',
        border: `1px solid rgba(16, 185, 129, 0.2)`,
        borderRadius: 16,
        padding: '12px 16px',
        marginBottom: 16,
        textAlign: 'center',
        position: 'relative'
      }}>
        <Group justify="center" mb={10} gap={8}>
          <TrendingUp size={14} color="var(--tea-emerald)" />
          <Text size="10px" fw={700} c="dimmed" style={{ letterSpacing: '1.2px', textTransform: 'uppercase' }}>
            Projected Monthly Yield
          </Text>
        </Group>

        <Text fw={900} size="2.8rem" style={{
          color: '#fff',
          lineHeight: 1,
        }}>
          {predicted_yield}
        </Text>
        <Text size="10px" fw={700} c="dimmed" mt={12} style={{ letterSpacing: '1px', textTransform: 'uppercase' }}>
          Metric Tons Per Hectare ({yield_unit.toUpperCase()})
        </Text>
      </Box>

      <Stack gap="md">
        <Paper withBorder p="md" radius="lg" style={{ background: 'rgba(255,255,255,0.02)', borderColor: 'rgba(255,255,255,0.06)' }}>
          <Group gap="md" wrap="nowrap" align="flex-start">
            <ThemeIcon size="md" variant="light" color={tierColor} radius="xl">
              <Wheat size={16} />
            </ThemeIcon>
            <Box>
              <Text size="sm" fw={600} c="white" mb={2}>Harvest Insight</Text>
              <Text size="xs" c="dimmed" lh={1.4}>{description}</Text>
            </Box>
          </Group>
        </Paper>

        <Group gap="sm" wrap="nowrap" px="xs">
          <AlertCircle size={14} color="#94a3b8" />
          <Text size="xs" c="dimmed" fw={500}>
            Forecast Reliability: <span style={{ color: 'var(--tea-emerald)', fontWeight: 700 }}>{model_r2 ? (model_r2 * 100).toFixed(1) + '%' : 'N/A'} Confidence</span>
          </Text>
        </Group>
      </Stack>
    </Paper>
  )
}
