# 🏃‍♂️ Intervals-Section-11

<p align="center">
  <img src="https://img.shields.io/badge/python-3.14+-blue?style=flat&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/macOS-ready-green?style=flat&logo=apple" alt="macOS">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat" alt="License">
</p>

> Training data mirror for AI coaching — syncs workout data from Intervals.icu with beautiful interactive reports.

---

## 🚀 Quick Start

### macOS (Recommended)

| App | Description | Use Case |
|-----|-------------|-----------|
| 🖥️ `TrainingReport.app` | Desktop app | Double-click to sync & view report |
| 📱 `MenuBarApp.app` | Menu bar app | Run in background, quick access |

```bash
# Or via terminal
python3 sync.py
```

---

## ⚙️ Setup

### 1. Get API Credentials

1. 🔐 Login to [Intervals.icu](https://intervals.icu)
2. Go to **Settings** → **Developer Settings** (bottom of page)
3. Copy your **Athlete ID** 🔢
4. Generate an **API Key** 🔑

### 2. Configure

Create `.env` file:
```bash
ATHLETE_ID=your_athlete_id
INTERVALS_KEY=your_api_key
```

Or set environment variables:
```bash
export ATHLETE_ID=your_athlete_id
export INTERVALS_KEY=your_api_key
```

---

## 📋 Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `ATHLETE_ID` | ✅ | - | Your Intervals.icu athlete ID |
| `INTERVALS_KEY` | ✅ | - | API key from Intervals.icu |
| `SYNC_DAYS` | | `28` | Number of days to sync |
| `VERIFY_SSL` | | `true` | Enable/disable SSL verification |
| `OUTPUT_PATH` | | `latest.json` | Output file path |

---

## 💻 Usage

### Terminal
```bash
python3 sync.py
```

### Desktop App
```
🖥️ TrainingReport.app
   └── Sync → Open HTML Report
```

### Menu Bar App
```
📱 MenuBarApp.app (runs in background)
   ├── 🔄 Sync Now
   ├── 🌐 Open Report  
   ├── ⚙️ Preferences
   └── ❌ Quit
```

### Python Scripts
```bash
# Run and auto-open report
python3 run_and_report.py

# Open preferences GUI
python3 preferences.py
```

---

## 📊 Output Files

| File | Format | Description |
|------|--------|-------------|
| 📄 `latest.json` | JSON | Raw data for AI processing |
| 📝 `latest.md` | Markdown | Human-readable report |
| 📊 `latest.csv` | CSV | Spreadsheet export |
| 🌐 `latest.html` | HTML | **Interactive report with charts** |

---

## 🎨 HTML Report Features

<p align="center">
  <img src="https://img.shields.io/badge/Dark%20Mode-auto-purple?style=flat&theme=dark" alt="Dark Mode">
  <img src="https://img.shields.io/badge/Chart.js-charts-blue?style=flat" alt="Charts">
</p>

- 🌙 **Dark Mode** — Auto-follows system theme
- 📈 **CTL vs ATL Chart** — Fitness & fatigue over time
- 🥧 **Zone Distribution** — Pie chart of training zones
- 🚴 **Sport Breakdown** — Ride/Run/Swim stats
- 💤 **Wellness Data** — Sleep, HR, HRV, weight, readiness

---

## 📁 Project Structure

```
Intervals-Section-11/
│
├── 🐍 sync.py                  # Main sync script
├── ⚙️ preferences.py          # GUI settings
├── 📜 run_and_report.py      # Run & open report
│
├── 🖥️ TrainingReport.app    # Desktop app
├── 📱 MenuBarApp.app        # Menu bar app
│
├── 📄 latest.json           # Raw data
├── 📝 latest.md             # Markdown
├── 📊 latest.csv            # CSV export
├── 🌐 latest.html           # Interactive HTML
│
├── 🔐 .env                 # Credentials (gitignored)
└── 🧪 tests/               # Unit tests
```

---

## 🧪 Testing

```bash
pytest tests/
```

---

## 📸 Sample Report

```
┌─────────────────────────────────────────────┐
│  🏃‍♂️ Training Report                      │
│  📅 2026-01-19 to 2026-02-16            │
├─────────────────────────────────────────────┤
│  📈 Training Status                        │
│  ├─ Fitness (CTL): 91.5                 │
│  ├─ Fatigue (ATL): 93.6                  │
│  ├─ Form (TSB): -2.2 🔴                  │
│  └─ Ramp Rate: 0.54                       │
├─────────────────────────────────────────────┤
│  🚴 Sport Breakdown                       │
│  ├─ Ride: 8.58h • 8828 kJ                │
│  ├─ Run: 2.18h • 25.4 km                │
│  └─ Swim: 0.67h • 2.0 km                │
├─────────────────────────────────────────────┤
│  💤 Latest Wellness                        │
│  ├─ Sleep: 6.8h                          │
│  ├─ Resting HR: 67 bpm                    │
│  └─ Readiness: 34% 🔴                    │
└─────────────────────────────────────────────┘
```

---

## 📜 License

MIT License — feel free to use and modify!

---

<p align="center">
  Made with ❤️ for athletes
</p>
