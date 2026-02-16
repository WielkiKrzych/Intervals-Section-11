import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
sys.path.insert(0, '/Users/wielkikrzychmbp/Documents/Intervals-Section-11')

from sync import (
    validate_athlete_id,
    get_config,
    get_headers,
    _anonymize_events,
    calculate_stats,
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
        headers = get_headers("test-api-key")
        assert headers["Authorization"] == "Bearer test-api-key"
        assert headers["Accept"] == "application/json"


class TestAnonymizeEvents:
    def test_anonymizes_regular_events(self):
        events = [
            {"name": "Morning Run", "id": "123"},
            {"name": "Evening Ride", "id": "456"},
        ]
        result = _anonymize_events(events)
        assert result[0]["name"] == "Training Session"
        assert result[0]["id"] == "activity_1"
        assert result[1]["name"] == "Training Session"
        assert result[1]["id"] == "activity_2"

    def test_preserves_zwift_events(self):
        events = [{"name": "Zwift Race", "id": "123"}]
        result = _anonymize_events(events)
        assert result[0]["name"] == "Zwift Race"

    def test_preserves_trainer_events(self):
        events = [{"name": "Indoor Trainer", "id": "123"}]
        result = _anonymize_events(events)
        assert result[0]["name"] == "Indoor Trainer"


class TestCalculateStats:
    def test_empty_activities(self):
        stats = calculate_stats([], 14)
        assert stats["total_activities"] == 0
        assert stats["total_tss"] == 0
        assert stats["period_days"] == 14

    def test_calculates_stats_correctly(self):
        activities = [
            {"tss": 100, "moving_time": 3600, "kilojoules": 500},
            {"tss": 50, "moving_time": 1800, "kilojoules": 250},
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
    @patch.dict(os.environ, {"ATHLETE_ID": "test123", "INTERVALS_KEY": "key123"})
    def test_loads_config(self):
        config = get_config()
        assert config["athlete_id"] == "test123"
        assert config["api_key"] == "key123"
        assert config["verify_ssl"] is True
        assert config["days"] == 14

    @patch.dict(os.environ, {"ATHLETE_ID": "test123", "INTERVALS_KEY": "key123", "VERIFY_SSL": "false"})
    def test_verify_ssl_can_be_disabled(self):
        config = get_config()
        assert config["verify_ssl"] is False

    @patch.dict(os.environ, {"ATHLETE_ID": "test123", "INTERVALS_KEY": "key123", "SYNC_DAYS": "30"})
    def test_custom_days(self):
        config = get_config()
        assert config["days"] == 30

    @patch.dict(os.environ, {"ATHLETE_ID": "test123"})
    def test_missing_key_raises(self):
        with pytest.raises(ValueError, match="Missing ATHLETE_ID or INTERVALS_KEY"):
            get_config()
