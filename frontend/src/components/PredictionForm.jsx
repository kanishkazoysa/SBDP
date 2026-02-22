import { useState, useEffect } from 'react'
import {
  Paper, Title, Text, Select, Grid, Button,
  NumberInput, Stack, Box, Divider, SegmentedControl, Group,
  Loader,
} from '@mantine/core'
import { MapPin, Home, BedDouble, Bath, Ruler, Zap, Star, Sofa } from 'lucide-react'

const PROPERTY_TYPES = ['Land', 'House', 'Apartment']

const QUALITY_OPTIONS = [
  { label: 'Standard', value: '0' },
  { label: 'Modern', value: '1' },
  { label: 'Luxury', value: '2' },
  { label: 'Super Luxury', value: '3' },
]

const FURNISH_OPTIONS = [
  { label: 'Unfurnished', value: '0' },
  { label: 'Semi', value: '1' },
  { label: 'Furnished', value: '2' },
]

export default function PredictionForm({ onPredict, loading, meta }) {
  const [form, setForm] = useState({
    property_type: 'House',
    location: '',
    bedrooms: 3,
    bathrooms: 2,
    land_size_perches: null,
    quality_tier: 0,
    is_furnished: 0,
  })

  // Sort and format locations from backend
  const locations = (meta?.locations || []).slice().sort().map(l => ({
    value: l,
    label: l
  }))

  // Auto-select first location (or Colombo) when data arrives
  useEffect(() => {
    if (!form.location && locations.length > 0) {
      const defaultLoc = locations.find(opt => opt.value === 'Colombo')
      setForm(f => ({ ...f, location: defaultLoc ? 'Colombo' : locations[0].value }))
    }
  }, [locations, form.location])

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  const isLand = form.property_type === 'Land'
  const isHouseOrApt = !isLand

  const qualityLabel = QUALITY_OPTIONS.find(q => q.value === String(form.quality_tier))?.label || 'Standard'
  const furnishLabel = FURNISH_OPTIONS.find(f => f.value === String(form.is_furnished))?.label || 'Unfurnished'

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!form.location) return
    onPredict({
      ...form,
      bedrooms: isHouseOrApt ? form.bedrooms : null,
      bathrooms: isHouseOrApt ? form.bathrooms : null,
      quality_tier: isHouseOrApt ? form.quality_tier : 0,
      is_furnished: isHouseOrApt ? form.is_furnished : 0,
    })
  }

  return (
    <Paper component="form" onSubmit={handleSubmit} withBorder p="xl" radius="md" style={{ flex: 1 }}>
      <Title order={4} mb="xl">Property Details</Title>

      <Stack gap="lg" style={{ flex: 1 }}>
        <Box>
          <Text size="sm" fw={500} mb={6} c="dimmed">Property Type</Text>
          <SegmentedControl
            fullWidth
            value={form.property_type}
            onChange={val => {
              set('property_type', val)
              if (val === 'Land') {
                set('quality_tier', 0)
                set('is_furnished', 0)
              }
            }}
            data={PROPERTY_TYPES.map(t => ({ label: t, value: t }))}
          />
        </Box>

        <Select
          label="Location"
          placeholder={meta ? "Type to search 300+ locations..." : "Loading locations..."}
          leftSection={meta ? <MapPin size={15} /> : <Loader size={12} />}
          data={locations}
          value={form.location}
          onChange={val => val && set('location', val)}
          searchable
          nothingFoundMessage="No matching location found"
          required
        />

        <Divider label="Specifications" labelPosition="center" />

        {isHouseOrApt && (
          <Grid gutter="md">
            <Grid.Col span={6}>
              <NumberInput
                label="Bedrooms"
                leftSection={<BedDouble size={15} />}
                min={1} max={20}
                value={form.bedrooms}
                onChange={val => set('bedrooms', val)}
              />
            </Grid.Col>
            <Grid.Col span={6}>
              <NumberInput
                label="Bathrooms"
                leftSection={<Bath size={15} />}
                min={1} max={15}
                value={form.bathrooms}
                onChange={val => set('bathrooms', val)}
              />
            </Grid.Col>
          </Grid>
        )}

        <NumberInput
          label="Land Size (Perches)"
          leftSection={<Ruler size={15} />}
          min={0.1} max={1000} decimalScale={1}
          placeholder="e.g. 10"
          value={form.land_size_perches ?? ''}
          onChange={val => set('land_size_perches', val === '' ? null : Number(val))}
          required={isLand}
        />

        {isHouseOrApt && (
          <>
            <Divider label="Quality & Furnishing" labelPosition="center" />
            <Box>
              <Text size="sm" fw={500} mb={6} c="dimmed">Quality Tier</Text>
              <SegmentedControl
                fullWidth
                value={String(form.quality_tier)}
                onChange={val => set('quality_tier', Number(val))}
                data={QUALITY_OPTIONS}
              />
            </Box>
            <Box>
              <Text size="sm" fw={500} mb={6} c="dimmed">Furnishing</Text>
              <SegmentedControl
                fullWidth
                value={String(form.is_furnished)}
                onChange={val => set('is_furnished', Number(val))}
                data={FURNISH_OPTIONS}
              />
            </Box>
          </>
        )}
      </Stack>

      <Button
        type="submit" fullWidth size="md" mt="xl"
        loading={loading}
        disabled={!meta || !form.location}
        leftSection={loading ? null : <Zap size={16} />}
      >
        Predict price
      </Button>
    </Paper>
  )
}
