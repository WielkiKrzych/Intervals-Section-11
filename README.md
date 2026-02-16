# Intervals-Section-11

Training data mirror for AI coaching - syncs workout data from Intervals.icu API.

## Setup

```bash
# Set environment variables
export ATHLETE_ID=your_athlete_id
export INTERVALS_KEY=your_api_key
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ATHLETE_ID` | Yes | - | Your Intervals.icu athlete ID |
| `INTERVALS_KEY` | Yes | - | API key from Intervals.icu |
| `VERIFY_SSL` | No | `true` | Enable/disable SSL verification |
| `SYNC_DAYS` | No | `14` | Number of days to sync |
| `OUTPUT_PATH` | No | `latest.json` | Output file path |

## Usage

```bash
python3 sync.py
```

## Output

Generates `latest.json` with:
- Wellness data
- Activity sessions (anonymized)
- Profile data (ID redacted)
- Quick stats (TSS, duration, energy)

## Testing

```bash
pytest tests/
```
