# Live Monitoring Dashboard

Industrial-style telemetry dashboard built with React and TypeScript.

**Status:** Not yet implemented — begins in Phase 7.

## Planned Features

- Machine status banner (NORMAL / WARNING / CRITICAL)
- Real-time gauges: temperature, vibration RMS, peak, dominant frequency
- Historical trend charts with configurable time range
- Active alerts panel with feature-level explanations
- Device connectivity indicator (MQTT last-seen)
- Dark industrial theme

## Planned Structure

```
dashboard/
├── src/
│   ├── components/         # Gauges, charts, alert panel, status banner
│   ├── hooks/              # WebSocket, API data fetching
│   ├── types/              # Telemetry TypeScript interfaces
│   └── App.tsx
├── package.json
└── vite.config.ts
```

See [docs/roadmap.md](../docs/roadmap.md) for Phase 7 deliverables.
