import { useState, useEffect } from 'react'

// ── Reference data (mirrors backend/main.py) ─────────────────────────────────
const ROUTES = {
  '01':   { label: 'Colombo → Kandy (Route 01, 116 km)',      distance: 116, duration: { Normal: 210, 'Semi Luxury': 185, Luxury: 165 } },
  '32':   { label: 'Colombo → Galle (Route 32, 119 km)',      distance: 119, duration: { Normal: 195, 'Semi Luxury': 170, Luxury: 150 } },
  '04':   { label: 'Colombo → Kurunegala (Route 04, 94 km)',  distance: 94,  duration: { Normal: 150, 'Semi Luxury': 130, Luxury: 110 } },
  '04-2': { label: 'Colombo → Negombo (Route 04-2, 37 km)',   distance: 37,  duration: { Normal: 75,  'Semi Luxury': 65,  Luxury: 55  } },
  '98':   { label: 'Colombo → Ratnapura (Route 98, 100 km)',  distance: 100, duration: { Normal: 180, 'Semi Luxury': 160, Luxury: 140 } },
}

const POYA_DAYS = new Set([
  '2024-01-25','2024-02-24','2024-03-25','2024-04-23','2024-05-23','2024-06-21',
  '2024-07-21','2024-08-19','2024-09-17','2024-10-17','2024-11-15','2024-12-15',
  '2025-01-13','2025-02-12','2025-03-13','2025-04-12','2025-05-12','2025-06-11',
  '2025-07-10','2025-08-09','2025-09-07','2025-10-06','2025-11-05','2025-12-04',
])

const PUBLIC_HOLIDAYS = new Set([
  '2024-01-15','2024-02-04','2024-03-29','2024-04-11','2024-04-12','2024-04-13',
  '2024-04-14','2024-05-01','2024-05-23','2024-05-24','2024-06-17','2024-06-21',
  '2024-07-21','2024-08-19','2024-09-16','2024-09-17','2024-10-17','2024-10-31',
  '2024-11-15','2024-12-15','2024-12-25',
  '2025-01-14','2025-02-04','2025-04-14','2025-05-01','2025-05-12','2025-12-25',
])

const FESTIVAL_PERIODS = [
  ['2024-04-10','2024-04-16','Sinhala New Year'],
  ['2024-05-20','2024-05-26','Vesak'],
  ['2024-06-18','2024-06-23','Poson'],
  ['2024-07-24','2024-08-10','Kandy Perahera'],
  ['2024-10-29','2024-11-02','Deepavali'],
  ['2024-12-23','2024-12-27','Christmas'],
  ['2025-04-10','2025-04-16','Sinhala New Year'],
  ['2025-05-10','2025-05-16','Vesak'],
]

function getFestival(dateStr) {
  const f = FESTIVAL_PERIODS.find(([s, e]) => dateStr >= s && dateStr <= e)
  return f ? f[2] : null
}

function todayStr() {
  return new Date().toISOString().split('T')[0]
}

// ── Component ─────────────────────────────────────────────────────────────────
export default function PredictionForm({ onPredict, loading }) {
  const [form, setForm] = useState({
    route_no:            '01',
    bus_type:            'Normal',
    departure_date:      todayStr(),
    departure_time:      '07:00',
    weather:             'Clear',
    crowding_level:      'Medium',
    departure_delay_min: 0,
  })

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }))

  // Auto-computed flags
  const d          = form.departure_date
  const dow        = new Date(d).getDay()                  // 0=Sun
  const isWeekend  = dow === 0 || dow === 6
  const isPoya     = POYA_DAYS.has(d)
  const isHoliday  = PUBLIC_HOLIDAYS.has(d)
  const festival   = getFestival(d)

  const routeInfo     = ROUTES[form.route_no]
  const schedMins     = routeInfo.duration[form.bus_type]
  const schedH        = Math.floor(schedMins / 60)
  const schedM        = schedMins % 60

  const handleSubmit = (e) => {
    e.preventDefault()
    onPredict({ ...form, departure_delay_min: Number(form.departure_delay_min) })
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2 className="card-title">Trip Details</h2>

      <div className="form-grid">
        {/* Route */}
        <div className="form-group full">
          <label>Route</label>
          <select value={form.route_no} onChange={e => set('route_no', e.target.value)}>
            {Object.entries(ROUTES).map(([no, r]) => (
              <option key={no} value={no}>{r.label}</option>
            ))}
          </select>
        </div>

        {/* Bus type */}
        <div className="form-group">
          <label>Bus Type</label>
          <select value={form.bus_type} onChange={e => set('bus_type', e.target.value)}>
            <option>Normal</option>
            <option>Semi Luxury</option>
            <option>Luxury</option>
          </select>
        </div>

        {/* Weather */}
        <div className="form-group">
          <label>Weather Condition</label>
          <select value={form.weather} onChange={e => set('weather', e.target.value)}>
            <option>Clear</option>
            <option>Cloudy</option>
            <option>Light Rain</option>
            <option>Moderate Rain</option>
            <option>Heavy Rain</option>
          </select>
        </div>

        {/* Date */}
        <div className="form-group">
          <label>Travel Date</label>
          <input
            type="date"
            value={form.departure_date}
            min="2024-01-01"
            max="2026-12-31"
            onChange={e => set('departure_date', e.target.value)}
          />
        </div>

        {/* Time */}
        <div className="form-group">
          <label>Departure Time</label>
          <input
            type="time"
            value={form.departure_time}
            onChange={e => set('departure_time', e.target.value)}
          />
        </div>

        {/* Crowding */}
        <div className="form-group full">
          <label>Expected Crowding</label>
          <select value={form.crowding_level} onChange={e => set('crowding_level', e.target.value)}>
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
          </select>
        </div>

        {/* Departure delay */}
        <div className="form-group full">
          <label>Departure Delay (min) — set 0 if bus has not left yet</label>
          <div className="slider-row">
            <input
              type="range"
              min={0} max={60} step={1}
              value={form.departure_delay_min}
              onChange={e => set('departure_delay_min', e.target.value)}
            />
            <span className="slider-val">{form.departure_delay_min}m</span>
          </div>
        </div>
      </div>

      {/* Auto-detected flags */}
      <div style={{ marginTop: 18 }}>
        <p style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px', marginBottom: 8 }}>
          Auto-Detected (from date)
        </p>
        <div className="info-grid">
          <span className={`badge ${isWeekend ? 'badge-yes' : 'badge-no'}`}>
            <span className="badge-icon">{isWeekend ? '🏖️' : '📅'}</span>
            {isWeekend ? 'Weekend' : 'Weekday'}
          </span>
          <span className={`badge ${isPoya ? 'badge-yes' : 'badge-no'}`}>
            <span className="badge-icon">{isPoya ? '🌕' : '🌑'}</span>
            {isPoya ? 'Poya Day' : 'Not Poya'}
          </span>
          <span className={`badge ${isHoliday ? 'badge-yes' : 'badge-no'}`}>
            <span className="badge-icon">{isHoliday ? '🎉' : '🗓️'}</span>
            {isHoliday ? 'Public Holiday' : 'No Holiday'}
          </span>
          <span className={`badge ${festival ? 'badge-yes' : 'badge-no'}`}>
            <span className="badge-icon">{festival ? '🎊' : '📆'}</span>
            {festival || 'No Festival'}
          </span>
        </div>
        <div className="journey-info">
          Scheduled journey: <strong>{schedH}h {schedM > 0 ? `${schedM}min` : ''}</strong>
          &nbsp;({routeInfo.distance} km)
        </div>
      </div>

      <button className="btn-predict" type="submit" disabled={loading}>
        {loading ? <><span className="spinner" />Predicting...</> : 'Predict Delay'}
      </button>
    </form>
  )
}
