import { useState } from 'react'
import {
  Paper, Title, Text, Select, Grid, Button,
  NumberInput, Stack, Box, Divider, SegmentedControl, Group,
} from '@mantine/core'
import { MapPin, Home, BedDouble, Bath, Ruler, Zap } from 'lucide-react'

const DEFAULT_LOCATIONS = [
  'Colombo', 'Gampaha', 'Kalutara', 'Kandy', 'Matara',
  'Kurunegala', 'Hambantota', 'Galle', 'Anuradhapura', 'Matale',
  'Ratnapura', 'Badulla', 'Monaragala', 'Polonnaruwa', 'Trincomalee',
]

const PROPERTY_TYPES = ['Land', 'House', 'Apartment']

export default function PredictionForm({ onPredict, loading, meta }) {
  const [form, setForm] = useState({
    property_type: 'House',
    location: 'Colombo',
    bedrooms: 3,
    bathrooms: 2,
    land_size_perches: null,
    is_for_rent: 0,
  })

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const locations = meta?.locations?.length
    ? meta.locations.map(l => ({ value: l, label: l }))
    : DEFAULT_LOCATIONS.map(l => ({ value: l, label: l }))

  const isLand = form.property_type === 'Land'
  const isHouseOrApt = !isLand

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      property_type: form.property_type,
      location: form.location,
      bedrooms: isHouseOrApt ? form.bedrooms : null,
      bathrooms: isHouseOrApt ? form.bathrooms : null,
      land_size_perches: isLand ? form.land_size_perches : form.land_size_perches,
      is_for_rent: form.is_for_rent,
    }
    onPredict(payload)
  }

  return (
    <Paper
      component="form"
      onSubmit={handleSubmit}
      withBorder
      p="xl"
      radius="md"
      style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
    >
      <Title order={4} mb="xl">Property Details</Title>

      <Stack gap="lg" style={{ flex: 1 }}>

        {/* Sale vs Rent */}
        <Box>
          <Text size="sm" fw={500} mb={6} c="dimmed">Listing Type</Text>
          <SegmentedControl
            fullWidth
            value={String(form.is_for_rent)}
            onChange={val => set('is_for_rent', Number(val))}
            data={[
              { label: 'For Sale', value: '0' },
              { label: 'For Rent', value: '1' },
            ]}
          />
        </Box>

        {/* Property Type */}
        <Box>
          <Text size="sm" fw={500} mb={6} c="dimmed">Property Type</Text>
          <SegmentedControl
            fullWidth
            value={form.property_type}
            onChange={val => set('property_type', val)}
            data={PROPERTY_TYPES.map(t => ({ label: t, value: t }))}
          />
        </Box>

        {/* Location */}
        <Select
          label="District / Location"
          leftSection={<MapPin size={15} />}
          leftSectionPointerEvents="none"
          data={locations}
          value={form.location}
          onChange={val => val && set('location', val)}
          searchable
          allowDeselect={false}
        />

        <Divider label="Property Specifications" labelPosition="center" />

        {/* Bedrooms + Bathrooms (houses/apartments only) */}
        {isHouseOrApt && (
          <Grid gutter="md">
            <Grid.Col span={6}>
              <NumberInput
                label="Bedrooms"
                leftSection={<BedDouble size={15} />}
                min={1}
                max={20}
                value={form.bedrooms}
                onChange={val => set('bedrooms', val)}
              />
            </Grid.Col>
            <Grid.Col span={6}>
              <NumberInput
                label="Bathrooms"
                leftSection={<Bath size={15} />}
                min={1}
                max={15}
                value={form.bathrooms}
                onChange={val => set('bathrooms', val)}
              />
            </Grid.Col>
          </Grid>
        )}

        {/* Land size */}
        <NumberInput
          label={isLand ? 'Land Size (Perches)' : 'Land Size (Perches) — optional'}
          leftSection={<Ruler size={15} />}
          min={0.1}
          max={1000}
          decimalScale={1}
          step={0.5}
          placeholder={isLand ? 'e.g. 10' : 'Leave blank if unknown'}
          value={form.land_size_perches ?? ''}
          onChange={val => set('land_size_perches', val === '' ? null : Number(val))}
          required={isLand}
        />

        {/* Summary pill */}
        <Box
          p="sm"
          style={{
            background: 'rgba(99,102,241,0.08)',
            borderRadius: 8,
            border: '1px solid rgba(99,102,241,0.2)',
          }}
        >
          <Group gap="xs">
            <Home size={14} color="#6366f1" />
            <Text size="sm" c="dimmed">
              <Text component="span" fw={600} c="dark.0">{form.property_type}</Text>
              {' · '}
              <Text component="span" fw={600} c="dark.0">{form.location}</Text>
              {isHouseOrApt && (
                <>{' · '}<Text component="span">{form.bedrooms} bed / {form.bathrooms} bath</Text></>
              )}
              {form.land_size_perches && (
                <>{' · '}<Text component="span">{form.land_size_perches} perches</Text></>
              )}
            </Text>
          </Group>
        </Box>

      </Stack>

      <Button
        type="submit"
        fullWidth
        size="md"
        mt="xl"
        loading={loading}
        leftSection={loading ? null : <Zap size={16} />}
      >
        Predict Price
      </Button>
    </Paper>
  )
}
