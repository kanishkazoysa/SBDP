import React from 'react'
import ReactDOM from 'react-dom/client'
import { MantineProvider, createTheme } from '@mantine/core'
import '@mantine/core/styles.css'
import App from './App'
import './App.css'

const theme = createTheme({
  primaryColor: 'indigo',
  primaryShade: { dark: 5 },
  fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
  headings: {
    fontFamily: 'Inter, system-ui, sans-serif',
    fontWeight: '600',
  },
  // Custom dark color scale — deeper blue-black palette
  colors: {
    dark: [
      '#e8eaf2',  // 0 — primary text
      '#9ba8c0',  // 1 — secondary text
      '#6b7a99',  // 2 — muted text
      '#4a5578',  // 3 — disabled text
      '#2d3555',  // 4 — borders
      '#1e243a',  // 5 — subtle borders
      '#151820',  // 6 — input backgrounds
      '#0f1218',  // 7 — card backgrounds
      '#0b0d14',  // 8 — page background
      '#080a10',  // 9 — deepest background
    ],
  },
  radius: {
    xs: '4px',
    sm: '6px',
    md: '8px',
    lg: '12px',
    xl: '16px',
  },
})

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="dark">
      <App />
    </MantineProvider>
  </React.StrictMode>
)
