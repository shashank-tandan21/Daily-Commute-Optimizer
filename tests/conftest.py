"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime, timedelta
from commute_optimizer.models import (
    Location, Route, RouteSegment, TransportationMode,
    PreferenceProfile, UserPreferences, SavedLocation, NotificationSettings
)


@pytest.fixture
def sample_location():
    """Sample location for testing."""
    return Location(
        latitude=37.7749,
        longitude=-122.4194,
        address="123 Main St, San Francisco, CA",
        name="Home"
    )


@pytest.fixture
def sample_route_segment():
    """Sample route segment for testing."""
    start = Location(latitude=37.7749, longitude=-122.4194, address="Start Address")
    end = Location(latitude=37.7849, longitude=-122.4094, address="End Address")
    
    return RouteSegment(
        mode=TransportationMode.DRIVING,
        start_location=start,
        end_location=end,
        distance=5.2,
        duration=15,
        instructions="Drive north on Main St"
    )


@pytest.fixture
def sample_route():
    """Sample route for testing."""
    start = Location(latitude=37.7749, longitude=-122.4194, address="Start Address")
    end = Location(latitude=37.7849, longitude=-122.4094, address="End Address")
    
    segment = RouteSegment(
        mode=TransportationMode.DRIVING,
        start_location=start,
        end_location=end,
        distance=5.2,
        duration=15,
        instructions="Drive north on Main St"
    )
    
    departure_time = datetime.now()
    arrival_time = departure_time + timedelta(minutes=15)
    
    return Route(
        id="route_123",
        segments=[segment],
        total_distance=5.2,
        estimated_time=15,
        estimated_cost=3.50,
        stress_level=4,
        reliability_score=8,
        transportation_modes=[TransportationMode.DRIVING],
        departure_time=departure_time,
        arrival_time=arrival_time,
        instructions=["Drive north on Main St"]
    )


@pytest.fixture
def sample_preference_profile():
    """Sample preference profile for testing."""
    return PreferenceProfile(
        name="Balanced",
        time_weight=30,
        cost_weight=25,
        comfort_weight=25,
        reliability_weight=20,
        max_walking_distance=1.5,
        preferred_modes=[TransportationMode.DRIVING, TransportationMode.PUBLIC_TRANSIT],
        avoided_features=["highways"]
    )


@pytest.fixture
def sample_user_preferences():
    """Sample user preferences for testing."""
    profile = PreferenceProfile(
        name="Default",
        time_weight=40,
        cost_weight=20,
        comfort_weight=20,
        reliability_weight=20
    )
    
    location = SavedLocation(
        name="Home",
        location=Location(latitude=37.7749, longitude=-122.4194, address="123 Main St"),
        is_default=True
    )
    
    notifications = NotificationSettings()
    
    return UserPreferences(
        user_id="user_123",
        preference_profiles=[profile],
        saved_locations=[location],
        notification_settings=notifications,
        default_profile="Default"
    )