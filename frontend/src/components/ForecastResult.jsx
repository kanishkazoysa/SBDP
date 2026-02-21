import {
    Paper, Title, Text, Stack, Box, Badge, Divider, Group, Loader
} from '@mantine/core'
import { TrendingUp, CheckCircle, AlertCircle, Clock } from 'lucide-react'

const SIGNAL_CONFIG = {
    BUY: { color: '#10b981', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.25)', label: '✅ BUY — Strong Investment' },
    HOLD: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.25)', label: '⚠️ HOLD — Moderate Growth' },
    WAIT: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.25)', label: '🔴 WAIT — Slow Growth' },
}

export default function ForecastResult({ result, loading, error }) {
    const signal = result ? (SIGNAL_CONFIG[result.investment_signal] ?? SIGNAL_CONFIG.HOLD) : null

    if (loading) return (
        <Box style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, padding: '4rem 0' }}>
            <Loader color="violet" size="lg" />
            <Text c="dimmed">Forecasting prices...</Text>
        </Box>
    )

    if (error) return (
        <Box style={{ padding: '2rem', textAlign: 'center' }}>
            <AlertCircle size={36} color="#ef4444" />
            <Text c="red" fw={600} mt="sm">{error}</Text>
        </Box>
    )

    if (!result) return (
        <Box style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, padding: '4rem 0', opacity: 0.4 }}>
            <TrendingUp size={52} strokeWidth={1} />
            <Text c="dimmed" ta="center" size="sm">
                Select a district and property type,<br />then click Forecast 2026–2030.
            </Text>
        </Box>
    )

    return (
        <Stack gap="lg">
            {/* Header row */}
            <Group justify="space-between" align="flex-start" wrap="nowrap">
                <Box>
                    <Text size="xs" tt="uppercase" fw={700} c="dimmed" mb={2}>Forecast Result</Text>
                    <Title order={4}>{result.district} · {result.property_type}</Title>
                    <Text size="sm" c="dimmed">Price timeline 2026 – 2030</Text>
                </Box>
                <Badge
                    size="lg" variant="light"
                    style={{
                        background: signal.bg,
                        color: signal.color,
                        border: `1px solid ${signal.border}`,
                        whiteSpace: 'nowrap',
                        flexShrink: 0,
                    }}
                >
                    {signal.label}
                </Badge>
            </Group>

            <Divider />

            {/* Year-by-year timeline */}
            <Stack gap="xs">
                {result.yearly.map((yr) => {
                    const isCurrent = yr.year === 2026
                    const pct = yr.growth_from_2026_pct
                    const barPct = Math.min(100, Math.max(8, 35 + pct * 2))
                    const barColor = isCurrent ? '#6366f1'
                        : pct >= 15 ? '#10b981'
                            : pct >= 5 ? '#f59e0b'
                                : '#94a3b8'

                    return (
                        <Box key={yr.year} style={{
                            display: 'flex', alignItems: 'center', gap: 12,
                            padding: '10px 14px', borderRadius: 10,
                            background: isCurrent ? 'rgba(99,102,241,0.09)' : 'rgba(255,255,255,0.025)',
                            border: isCurrent
                                ? '1.5px solid rgba(99,102,241,0.4)'
                                : '1px solid rgba(255,255,255,0.07)',
                            transition: 'background 0.2s',
                        }}>
                            {/* Year label */}
                            <Box style={{ width: 50, textAlign: 'center', flexShrink: 0 }}>
                                <Text fw={700} size="sm" c={isCurrent ? 'indigo.4' : 'dimmed'}>{yr.year}</Text>
                                {isCurrent && <Text size="9px" c="violet" fw={700} lh={1}>BASE</Text>}
                            </Box>

                            {/* Progress bar */}
                            <Box style={{ flex: 1, background: 'rgba(255,255,255,0.07)', borderRadius: 99, height: 8, overflow: 'hidden' }}>
                                <Box style={{
                                    width: `${barPct}%`, height: '100%', borderRadius: 99,
                                    background: barColor, transition: 'width 0.7s ease',
                                }} />
                            </Box>

                            {/* Price */}
                            <Text fw={700} size="sm" style={{ minWidth: 100, textAlign: 'right', color: '#f1f5f9' }}>
                                {yr.price_formatted}
                            </Text>

                            {/* Growth badge */}
                            {!isCurrent && (
                                <Badge size="sm" variant="light"
                                    color={pct >= 15 ? 'green' : pct >= 5 ? 'yellow' : 'gray'}
                                    style={{ minWidth: 64, flexShrink: 0 }}
                                >
                                    +{pct.toFixed(1)}%
                                </Badge>
                            )}
                        </Box>
                    )
                })}
            </Stack>

            <Divider />

            {/* Summary stat cards */}
            <Group grow gap="sm">
                {[
                    { label: '4-Year Growth', value: `+${result.growth_4yr_pct}%`, grad: 'linear-gradient(135deg,#6366f1,#8b5cf6)' },
                    { label: '~Yearly Growth', value: `+${(result.growth_4yr_pct / 4).toFixed(1)}%`, grad: 'linear-gradient(135deg,#10b981,#059669)' },
                    { label: 'Model R²', value: result.model_r2, grad: 'linear-gradient(135deg,#f59e0b,#d97706)' },
                ].map(s => (
                    <Box key={s.label} style={{
                        padding: '12px 16px', borderRadius: 10,
                        background: s.grad, color: 'white', textAlign: 'center',
                    }}>
                        <Text size="xs" opacity={0.85} mb={2}>{s.label}</Text>
                        <Text fw={800} size="xl">{s.value}</Text>
                    </Box>
                ))}
            </Group>

            {/* Investment insight */}
            <Box style={{
                padding: '14px 16px', borderRadius: 10,
                background: signal.bg, border: `1px solid ${signal.border}`,
            }}>
                <Text size="sm" fw={500} style={{ color: signal.color }}>💡 {result.insight}</Text>
            </Box>

            <Text size="xs" c="dimmed" ta="center">
                Based on CBSL economic data (2018–2026) + 9,000+ scraped listings · IMF projections 2027–2030
            </Text>
        </Stack>
    )
}
