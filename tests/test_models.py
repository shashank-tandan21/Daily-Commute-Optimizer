"""Tests for core data models."""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from commute_optimizer.models import (
    Location, Route, RouteSegment, TransportationMode,
    PreferenceProfile, UserPreferences
)


class TestLocation:
    """Tests for Location model."""
    
    def test_valid_location(self):
        """Test creating a valid location."""
        location = Location(
            latitude=37.7749,
            longitude=-122.4194,
            address="123 Main St, San Francisco, CA"
        )
        assert location.latitude == 37.7749
        assert location.longitude == -122.4194
        assert location.address == "123 Main St, San Francisco, CA"
    
    def test_invalid_latitude(self):
        """Test invalid latitude values."""
        with pytest.raises(ValidationError):
            Location(latitude=91, longitude=0, address="Test")
        
        with pytest.raises(ValidationError):
            Location(latitude=-91, longitude=0, address="Test")
    
    def test_invalid_longitude(self):
        """Test invalid longitude values."""
        with pytest.raises(ValidationError):
            Location(latitude=0, longitude=181, address="Test")
        
        with pytest.raises(ValidationError):
            Location(latitude=0, longitude=-181, address="Test")


class TestRoute:
    """Tests for Route model."""
    
    def test_valid_route(self, sample_route):
        """Test creating a valid route."""
        assert sample_route.id == "route_123"
        assert sample_route.total_distance == 5.2
        assert sample_route.estimated_time == 15
        assert sample_route.stress_level == 4
        assert sample_route.reliability_score == 8
    
    def test_arrival_before_departure_fails(self, sample_route_segment):
        """Test that arrival time before departure time fails validation."""
        departure_time = datetime.now()
        arrival_time = departure_time - timedelta(minutes=5)  # Invalid: before departure
        
        with pytest.raises(ValidationError):
            Route(
                id="invalid_route",
                segments=[sample_route_segment],
                total_distance=5.2,
                estimated_time=15,
                estimated_cost=3.50,
                stress_level=4,
                reliability_score=8,
                transportation_modes=[TransportationMode.DRIVING],
                departure_time=departure_time,
                arrival_time=arrival_time,
                instructions=["Drive north"]
            )
    
    def test_invalid_stress_level(self, sample_route_segment):
        """Test invalid stress level values."""
        departure_time = datetime.now()
        arrival_time = departure_time + timedelta(minutes=15)
        
        with pytest.raises(ValidationError):
            Route(
                id="invalid_route",
                segments=[sample_route_segment],
                total_distance=5.2,
                estimated_time=15,
                estimated_cost=3.50,
                stress_level=11,  # Invalid: > 10
                reliability_score=8,
                transportation_modes=[TransportationMode.DRIVING],
                departure_time=departure_time,
                arrival_time=arrival_time,
                instructions=["Drive north"]
            )


class TestPreferenceProfile:
    """Tests for PreferenceProfile model."""
    
    def test_valid_preference_profile(self, sample_preference_profile):
        """Test creating a valid preference profile."""
        assert sample_preference_profile.name == "Balanced"
        assert sample_preference_profile.time_weight == 30
        assert sample_preference_profile.cost_weight == 25
        assert sample_preference_profile.comfort_weight == 25
        assert sample_preference_profile.reliability_weight == 20
    
    def test_weights_must_sum_to_100(self):
        """Test that preference weights must sum to 100."""
        with pytest.raises(ValidationError):
            PreferenceProfile(
                name="Invalid",
                time_weight=30,
                cost_weight=30,
                comfort_weight=30,
                reliability_weight=30  # Total = 120, should fail
            )
    
    def test_weights_sum_to_100_valid(self):
        """Test that weights summing to 100 are valid."""
        profile = PreferenceProfile(
            name="Valid",
            time_weight=25,
            cost_weight=25,
            comfort_weight=25,
            reliability_weight=25  # Total = 100, should pass
        )
        assert profile.time_weight + profile.cost_weight + profile.comfort_weight + profile.reliability_weight == 100


class TestUserPreferences:
    """Tests for UserPreferences model."""
    
    def test_valid_user_preferences(self, sample_user_preferences):
        """Test creating valid user preferences."""
        assert sample_user_preferences.user_id == "user_123"
        assert len(sample_user_preferences.preference_profiles) == 1
        assert sample_user_preferences.default_profile == "Default"
    
    def test_default_profile_must_exist(self):
        """Test that default profile must exist in preference profiles."""
        from commute_optimizer.models import SavedLocation, NotificationSettings
        
        profile = PreferenceProfile(
            name="Existing",
            time_weight=25,
            cost_weight=25,
            comfort_weight=25,
            reliability_weight=25
        )
        
        with pytest.raises(ValidationError):
            UserPreferences(
                user_id="user_123",
                preference_profiles=[profile],
                saved_locations=[],
                notification_settings=NotificationSettings(),
                default_profile="NonExistent"  # This profile doesn't exist
            )