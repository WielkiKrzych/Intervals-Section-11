# Intervals-Section-11

Training data mirror for AI coaching - syncs workout data from Intervals.icu API with beautiful HTML reports.

## Quick Start (macOS)

1. Double-click `TrainingReport.app` to run
2. Report opens automatically in your browser

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

### macOS App (Desktop)
Double-click `TrainingReport.app` - it will:
1. Sync data from Intervals.icu
2. Automatically open the HTML report in your browser

### Menu Bar App
Double-click `MenuBarApp.app` - runs in background with menu:
- **Sync Now** - sync and show notification
- **Open Report** - open HTML report
- **Preferences** - open settings GUI
- **Quit** - exit app

### Python Script
```bash
python3 run_and_report.py
```

### Preferences GUI
```bash
python3 preferences.py
```

## Output Files

| File | Description |
|------|-------------|
| `latest.json` | Raw data for AI processing |
| `latest.md` | Markdown report |
| `latest.csv` | CSV for spreadsheets |
| `latest.html` | Interactive HTML report with charts |

## HTML Report Features

- **Dark mode support** - Automatically follows system theme
- **Interactive charts** - CTL vs ATL fitness chart (Chart.js)
- **Zone distribution pie chart** - Visual breakdown of training zones
- **Sport breakdown table** - Ride, Run, Swim statistics
- **Latest wellness data** - Sleep, HR, HRV, weight, readiness

## Report Contents

The reports include:
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
├── preferences.py            # GUI settings editor
├── run_and_report.py        # Python runner with report
├── TrainingReport.app/      # Desktop app
├── MenuBarApp.app/          # Menu bar app
├── latest.json             # Raw data output
├── latest.md               # Markdown report
├── latest.csv              # CSV export
├── latest.html             # Interactive HTML report
├── .env                    # Credentials (gitignored)
└── tests/                  # Unit tests
```
Intervals-Section-11/
├── sync.py                    # Main sync script
├── run_and_report.py         # Python runner with report
├── TrainingReport.app/       # macOS app
├── latest.json               # Raw data output
├── latest.md                 # Markdown report
├── latest.csv               # CSV export
├── latest.html              # Interactive HTML report
├── .env                     # Credentials (gitignored)
└── tests/                   # Unit tests
```
