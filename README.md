# Intervals-Section-11

Training data mirror for AI coaching - syncs workout data from Intervals.icu API.

## Quick Start (macOS)

1. Double-click `TrainingReport.app` to run
2. Report opens automatically in Markdown viewer

Or via terminal:
```bash
python3 sync.py
```

## Setup

### 1. Get API Credentials
1. Log into [Intervals.icu](https://intervals.icu)
2. Go to **Settings** → **Developer Settings** (bottom)
3. Copy your **Athlete ID** and generate an **API Key**

### 2. Configure Credentials

Create `.env` file (already in `.gitignore`):
```bash
ATHLETE_ID=your_athlete_id
INTERVALS_KEY=your_api_key
```

Or set environment variables:
```bash
export ATHLETE_ID=your_athlete_id
export INTERVALS_KEY=your_api_key
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ATHLETE_ID` | Yes | - | Your Intervals.icu athlete ID |
| `INTERVALS_KEY` | Yes | - | API key from Intervals.icu |
| `VERIFY_SSL` | No | `true` | Enable/disable SSL verification |
| `SYNC_DAYS` | No | `28` | Number of days to sync |
| `OUTPUT_PATH` | No | `latest.json` | Output file path |

## Usage

### Terminal
```bash
python3 sync.py
```

### macOS App
Double-click `TrainingReport.app` - it will:
1. Sync data from Intervals.icu
2. Automatically open the report

### Python Script
```bash
python3 run_and_report.py
```

## Output Files

| File | Description |
|------|-------------|
| `latest.json` | Raw data for AI processing |
| `latest.md` | Human-readable training report |

## Report Contents

The Markdown report includes:
- **Training Status**: CTL (Fitness), ATL (Fatigue), TSB (Form), Ramp Rate
- **Activity Summary**: Total activities, duration, TSS, energy
- **Sport Breakdown**: Ride, Run, Swim (time, distance, load)
- **Zone Distribution**: Time in each power/heart rate zone
- **Daily Wellness**: Sleep, HR, HRV, weight, readiness, soreness, fatigue

## Testing

```bash
pytest tests/
```

## Files

```
Intervals-Section-11/
├── sync.py                    # Main sync script
├── run_and_report.py         # Python runner with report
├── TrainingReport.app/      # macOS app
├── latest.json              # Raw data output
├── latest.md                # Markdown report
├── .env                     # Credentials (gitignored)
└── tests/                   # Unit tests
```
