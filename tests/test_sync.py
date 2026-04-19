import os
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, "/Users/wielkikrzychmbp/Documents/Intervals-Section-11")

from sync import (
    validate_athlete_id,
    get_config,
    get_headers,
    calculate_stats,
    compute_week_comparison,
    _validate_numeric,
    _read_cache,
    _write_cache,
)


class TestValidateAthleteId:
    def test_valid_id(self):
        assert validate_athlete_id("abc123") == "abc123"
        assert validate_athlete_id("athlete-456") == "athlete-456"
        assert validate_athlete_id("athlete_789") == "athlete_789"

    def test_empty_id_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_athlete_id("")

    def test_invalid_characters_raises(self):
        with pytest.raises(ValueError, match="invalid characters"):
            validate_athlete_id("test@domain.com")
        with pytest.raises(ValueError, match="invalid characters"):
            validate_athlete_id("test/path")


class TestGetHeaders:
    def test_returns_authorization_header(self):
        import base64

        headers = get_headers("test-api-key")
        expected_cred = base64.b64encode(b"API_KEY:test-api-key").decode()
        assert headers["Authorization"] == f"Basic {expected_cred}"
        assert headers["Accept"] == "application/json"


class TestCalculateStats:
    def test_empty_activities(self):
        stats = calculate_stats([], 14)
        assert stats["total_activities"] == 0
        assert stats["total_tss"] == 0
        assert stats["period_days"] == 14

    def test_calculates_stats_correctly(self):
        activities = [
            {"icu_training_load": 100, "moving_time": 3600, "icu_joules": 500000},
            {"icu_training_load": 50, "moving_time": 1800, "icu_joules": 250000},
        ]
        stats = calculate_stats(activities, 7)
        assert stats["total_activities"] == 2
        assert stats["total_tss"] == 150
        assert stats["total_duration_hours"] == 1.5
        assert stats["total_energy_kj"] == 750

    def test_handles_missing_fields(self):
        activities = [{"name": "Test"}]
        stats = calculate_stats(activities, 14)
        assert stats["total_tss"] == 0
        assert stats["total_duration_hours"] == 0


class TestGetConfig:
    @patch.dict(
        os.environ, {"ATHLETE_ID": "test123", "INTERVALS_KEY": "key123"}, clear=True
    )
    def test_loads_config(self):
        config = get_config()
        assert config["athlete_id"] == "test123"
        assert config["api_key"] == "key123"
        assert config["verify_ssl"] is True
        assert config["days"] == 28

    @patch.dict(
        os.environ,
        {"ATHLETE_ID": "test123", "INTERVALS_KEY": "key123", "VERIFY_SSL": "false"},
        clear=True,
    )
    def test_verify_ssl_can_be_disabled(self):
        config = get_config()
        assert config["verify_ssl"] is False

    @patch.dict(
        os.environ,
        {"ATHLETE_ID": "test123", "INTERVALS_KEY": "key123", "SYNC_DAYS": "30"},
        clear=True,
    )
    def test_custom_days(self):
        config = get_config()
        assert config["days"] == 30

    @patch.dict(os.environ, {"ATHLETE_ID": "test123"}, clear=True)
    def test_missing_key_raises(self):
        with pytest.raises(ValueError, match="Missing ATHLETE_ID or INTERVALS_KEY"):
            get_config()


class TestValidateNumeric:
    def test_valid_number(self):
        assert _validate_numeric(42, 0, 100) == 42

    def test_none_returns_default(self):
        assert _validate_numeric(None, 0, 100) == 0
        assert _validate_numeric(None, 0, 100, 5) == 5

    def test_clamps_to_range(self):
        assert _validate_numeric(150, 0, 100) == 100
        assert _validate_numeric(-10, 0, 100) == 0

    def test_string_conversion(self):
        assert _validate_numeric("42", 0, 100) == 42

    def test_invalid_string_returns_default(self):
        assert _validate_numeric("abc", 0, 100) == 0

    def test_float_value(self):
        assert _validate_numeric(3.14, 0, 10) == 3.14

    def test_zero_value(self):
        assert _validate_numeric(0, 0, 100) == 0

    def test_default_used_for_none(self):
        assert _validate_numeric(None, 0, 100, default=42) == 42


class TestComputeWeekComparison:
    def test_empty_activities(self):
        result = compute_week_comparison([])
        assert result["this_week"]["count"] == 0
        assert result["this_week"]["tss"] == 0
        assert result["this_week"]["duration_hours"] == 0
        assert result["previous_week"]["count"] == 0
        assert result["tss_change"] == "N/A"
        assert result["duration_change"] == "N/A"
        assert result["count_change"] == "N/A"

    def test_returns_expected_structure(self):
        activities = [
            {
                "startDate": "2026-01-15T10:00:00",
                "icu_training_load": 100,
                "moving_time": 3600,
            },
            {
                "startDate": "2026-01-10T10:00:00",
                "icu_training_load": 80,
                "moving_time": 3000,
            },
        ]
        result = compute_week_comparison(activities)
        assert "this_week" in result
        assert "previous_week" in result
        assert "tss_change" in result
        assert "duration_change" in result
        assert "count_change" in result
        assert "count" in result["this_week"]
        assert "tss" in result["this_week"]
        assert "duration_hours" in result["this_week"]

    def test_handles_missing_dates(self):
        activities = [
            {"name": "No date activity", "icu_training_load": 50, "moving_time": 1800},
        ]
        result = compute_week_comparison(activities)
        assert isinstance(result["this_week"]["count"], int)

    def test_handles_invalid_date_format(self):
        activities = [
            {"startDate": "not-a-date", "icu_training_load": 50, "moving_time": 1800},
        ]
        result = compute_week_comparison(activities)
        assert isinstance(result["this_week"]["count"], int)


class TestCache:
    def test_write_and_read(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync.CACHE_DIR", tmp_path)
        _write_cache("test_key", {"data": 42})
        result = _read_cache("test_key")
        assert result == {"data": 42}

    def test_read_expired_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync.CACHE_DIR", tmp_path)
        path = tmp_path / "test_key.json"
        old_time = (datetime.now() - timedelta(seconds=600)).isoformat()
        path.write_text(json.dumps({"cached_at": old_time, "value": "old"}))
        assert _read_cache("test_key") is None

    def test_read_nonexistent_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync.CACHE_DIR", tmp_path)
        assert _read_cache("nonexistent") is None

    def test_read_corrupt_file_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync.CACHE_DIR", tmp_path)
        path = tmp_path / "corrupt.json"
        path.write_text("not valid json{{{")
        assert _read_cache("corrupt") is None

    def test_write_creates_directory(self, tmp_path, monkeypatch):
        cache_subdir = tmp_path / "new_cache_dir"
        monkeypatch.setattr("sync.CACHE_DIR", cache_subdir)
        _write_cache("test_key", "value")
        assert cache_subdir.exists()
        assert _read_cache("test_key") == "value"

    def test_cache_key_sanitization(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync.CACHE_DIR", tmp_path)
        _write_cache("key/with/slashes", "value")
        assert _read_cache("key/with/slashes") == "value"
