import {
    Paper, Title, Text, Select, Button, Stack, Box,
    SegmentedControl, Group, ThemeIcon, NumberInput, Badge
} from '@mantine/core'
import { TrendingUp, MapPin, Home, Zap } from 'lucide-react'

const PROPERTY_TYPES = ['Land', 'House', 'Apartment']

export default function ForecastInput({ form, setForm, onSubmit, loading, districts, autoFilled }) {
    const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

    const districtOptions = (districts && districts.length > 0 ? districts : [
        'Colombo', 'Gampaha', 'Kalutara', 'Kandy', 'Matara',
        'Galle', 'Kurunegala', 'Hambantota', 'Anuradhapura', 'Matale',
        'Ratnapura', 'Badulla', 'Puttalam', 'Trincomalee',
    ]).map(d => ({ value: d, label: d }))

    const handleSubmit = (e) => {
        e.preventDefault()
        onSubmit(form)
    }

    return (
        <Paper
            component="form"
            onSubmit={handleSubmit}
            withBorder p="xl" radius="md"
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
        >
            {/* Header row with optional auto-filled badge */}
            <Group mb="xl" gap="xs" justify="space-between" align="flex-start" wrap="nowrap">
                <Group gap="xs">
                    <ThemeIcon size="lg" radius="md" color="violet">
                        <TrendingUp size={18} />
                    </ThemeIcon>
                    <div>
                        <Title order={4}>Forecast Details</Title>
                        <Text size="xs" c="dimmed">Predict property prices 2026 – 2030</Text>
                    </div>
                </Group>
                {autoFilled && (
                    <Badge
                        size="sm" variant="light" color="violet"
                        leftSection={<Zap size={10} />}
                        style={{ flexShrink: 0, marginTop: 4 }}
                    >
                        Auto-filled from prediction
                    </Badge>
                )}
            </Group>

            <Stack gap="lg" style={{ flex: 1 }}>
                {/* District */}
                <Box>
                    <Text size="sm" fw={500} mb={6} c="dimmed">
                        <Group gap={4} component="span"><MapPin size={13} /> District</Group>
                    </Text>
                    <Select
                        id="forecast-district"
                        value={form.district}
                        onChange={val => set('district', val)}
                        data={districtOptions}
                        searchable
                        required
                    />
                </Box>

                {/* Property Type */}
                <Box>
                    <Text size="sm" fw={500} mb={6} c="dimmed">
                        <Group gap={4} component="span"><Home size={13} /> Property Type</Group>
                    </Text>
                    <SegmentedControl
                        id="forecast-property-type"
                        fullWidth
                        value={form.property_type}
                        onChange={val => set('property_type', val)}
                        data={PROPERTY_TYPES.map(t => ({ label: t, value: t }))}
                    />
                </Box>

                {/* Land Size */}
                <Box>
                    <Text size="sm" fw={500} mb={6} c="dimmed">Land Size — perches (optional)</Text>
                    <NumberInput
                        id="forecast-land-size"
                        value={form.land_size_perches ?? ''}
                        onChange={val => set('land_size_perches', val || null)}
                        placeholder="e.g. 10"
                        min={1}
                        max={500}
                    />
                </Box>

                {/* Spacer so button goes to bottom */}
                <Box style={{ flex: 1 }} />

                <Button
                    id="forecast-submit-btn"
                    type="submit"
                    fullWidth
                    loading={loading}
                    leftSection={<TrendingUp size={16} />}
                    variant="gradient"
                    gradient={{ from: 'violet', to: 'indigo', deg: 135 }}
                    size="md"
                >
                    Forecast 2026 – 2030
                </Button>
            </Stack>
        </Paper>
    )
}
