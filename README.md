# 🏃‍♂️ Intervals-Section-11

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12+-blue?style=flat&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/macOS-ready-green?style=flat&logo=apple" alt="macOS">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat" alt="License">
</p>

> Training data mirror for AI coaching — syncs workout data from Intervals.icu with beautiful, fast interactive reports.

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
- 📈 **TSB (Form) Chart** — TSB line on the CTL vs ATL performance chart
- 📊 **Weekly TSS** — Bar chart showing training load per week
- 📋 **Recent Activities** — Table showing latest 10 activities with details
- 📊 **Week Comparison** — Current vs previous week with percentage changes
- 📅 **Daily Training Load** — Bar chart showing TSS distribution per day
- ⚖️ **Weight Trend** — Line chart tracking body weight
- 💡 **Recovery Recommendation** — AI-powered advice based on TSB
- 🥧 **Zone Distribution** — Pie chart of training zones
- 🚴 **Sport Breakdown** — Ride/Run/Swim stats with totals row
- 🏃 **Avg Speed & Pace** — Speed (km/h) and pace (min/km) in sport breakdown
- 💤 **Wellness Data** — Sleep, HR, HRV, weight, readiness
- 🔄 **Smart Energy** — Uses kJ for cycling, calories for run/swim
- 📱 **Mobile Responsive** — Optimized layout for phone and tablet screens

---

## ⚡ Performance

<p align="center">
  <img src="https://img.shields.io/badge/Parallel-3x%20faster-green?style=flat" alt="Parallel">
  <img src="https://img.shields.io/badge/Cache-5%20min%20TTL-orange?style=flat" alt="Cache">
  <img src="https://img.shields.io/badge/Retry-auto%20backoff-blue?style=flat" alt="Retry">
</p>

- 🚀 **Parallel API Calls** — Fetches wellness, activities & profile simultaneously (3x faster)
- 💾 **Smart Caching** — 5-minute response cache avoids redundant API calls
- 🔄 **Auto Retry** — Exponential backoff on network errors (up to 3 retries)
- 🛡️ **Data Validation** — Numeric range validation on all API responses
- 🔒 **HTML Escaping** — Protection against injection in report rendering

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
├── 📦 .cache/              # API response cache (gitignored)
└── 🧪 tests/               # Unit tests (29 tests)
```

---

## 🧪 Testing

```bash
python3 -m pytest tests/ -v
```

29 tests covering: config validation, API headers, stats computation, numeric validation, week comparison, response caching.

---

## 📸 Sample Report

```
┌─────────────────────────────────────────────┐
│  🏃‍♂️ Training Report                      │
│  📅 2025-12-18 to 2026-02-16 (60 days)  │
├─────────────────────────────────────────────┤
│  📈 Training Status                        │
│  ├─ Fitness (CTL): 90.5                 │
│  ├─ Fatigue (ATL): 88.2                  │
│  ├─ Form (TSB): +2.3 🟢                 │
│  ├─ Ramp Rate: 0.54                      │
│  └─ 💡 Recovery: Normal - Maintain        │
├─────────────────────────────────────────────┤
│  📊 Activity Summary                       │
│  ├─ Activities: 66                        │
│  ├─ Duration: 87.19h                     │
│  ├─ TSS: 5490                             │
│  └─ Energy: 68175 kJ                      │
├─────────────────────────────────────────────┤
│  🚴 Sport Breakdown                       │
│  ├─ Ride: 67.9h • 68175 kJ • 4885 TSS  │
│  ├─ Run: 17.7h • 212 km • 538 TSS      │
│  └─ Swim: 1.5h • 3.8 km • 67 TSS       │
├─────────────────────────────────────────────┤
│  📊 Week Comparison                        │
│  ├─ TSS: 245 (↑ 15%)                      │
│  ├─ Duration: 8.5h (↓ 5%)                 │
│  └─ Activities: 5 (= 0%)                   │
├─────────────────────────────────────────────┤
│  📋 Recent Activities                      │
│  ├─ 🚴 Morning Ride — 2.1h — 120 TSS     │
│  ├─ 🏃 Evening Run — 0.8h — 65 TSS       │
│  └─ ... (10 most recent)                   │
├─────────────────────────────────────────────┤
│  💤 Latest Wellness                        │
│  ├─ Sleep: 6.8h                          │
│  ├─ Resting HR: 49 bpm                    │
│  └─ Weight: 97.5 kg                       │
└─────────────────────────────────────────────┘
```

---

## 📜 License

MIT License — feel free to use and modify!

---

<p align="center">
  Made with ❤️ for athletes
</p>
