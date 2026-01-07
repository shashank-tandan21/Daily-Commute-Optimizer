"""Core data models for the Daily Commute Optimizer."""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class TransportationMode(str, Enum):
    """Available transportation modes."""
    DRIVING = "driving"
    PUBLIC_TRANSIT = "public_transit"
    WALKING = "walking"
    CYCLING = "cycling"
    RIDESHARE = "rideshare"


class Location(BaseModel):
    """Geographic location with coordinates and address."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: str
    name: Optional[str] = None


class RouteSegment(BaseModel):
    """Individual segment of a route."""
    mode: TransportationMode
    start_location: Location
    end_location: Location
    distance: float = Field(..., gt=0, description="Distance in kilometers")
    duration: int = Field(..., gt=0, description="Duration in minutes")
    instructions: str
    real_time_data: Optional[Dict[str, Any]] = None


class Route(BaseModel):
    """Complete route from origin to destination."""
    id: str
    segments: List[RouteSegment]
    total_distance: float = Field(..., gt=0, description="Total distance in kilometers")
    estimated_time: int = Field(..., gt=0, description="Estimated time in minutes")
    estimated_cost: float = Field(..., ge=0, description="Estimated cost in currency units")
    stress_level: int = Field(..., ge=1, le=10, description="Stress level on 1-10 scale")
    reliability_score: int = Field(..., ge=1, le=10, description="Reliability score on 1-10 scale")
    transportation_modes: List[TransportationMode]
    departure_time: datetime
    arrival_time: datetime
    instructions: List[str]

    @field_validator('arrival_time')
    @classmethod
    def arrival_after_departure(cls, v, info):
        """Ensure arrival time is after departure time."""
        if 'departure_time' in info.data and v <= info.data['departure_time']:
            raise ValueError('Arrival time must be after departure time')
        return v


class PreferenceProfile(BaseModel):
    """User preference profile for route ranking."""
    name: str
    time_weight: int = Field(..., ge=0, le=100, description="Weight for time priority (0-100)")
    cost_weight: int = Field(..., ge=0, le=100, description="Weight for cost priority (0-100)")
    comfort_weight: int = Field(..., ge=0, le=100, description="Weight for comfort priority (0-100)")
    reliability_weight: int = Field(..., ge=0, le=100, description="Weight for reliability priority (0-100)")
    max_walking_distance: float = Field(default=2.0, gt=0, description="Maximum walking distance in kilometers")
    preferred_modes: List[TransportationMode] = Field(default_factory=list)
    avoided_features: List[str] = Field(default_factory=list, description="Features to avoid (highways, tolls, etc.)")

    @field_validator('reliability_weight')
    @classmethod
    def weights_sum_to_100(cls, v, info):
        """Ensure all weights sum to 100."""
        data = info.data
        total = v + data.get('time_weight', 0) + data.get('cost_weight', 0) + data.get('comfort_weight', 0)
        if total != 100:
            raise ValueError(f'Preference weights must sum to 100, got {total}')
        return v


class SavedLocation(BaseModel):
    """User's saved location (home, work, etc.)."""
    name: str
    location: Location
    is_default: bool = False


class NotificationSettings(BaseModel):
    """User notification preferences."""
    delay_alerts: bool = True
    weather_alerts: bool = True
    departure_reminders: bool = True
    route_updates: bool = True
    min_delay_threshold: int = Field(default=10, ge=1, description="Minimum delay in minutes to trigger alert")


class UserPreferences(BaseModel):
    """Complete user preferences and settings."""
    user_id: str
    preference_profiles: List[PreferenceProfile]
    saved_locations: List[SavedLocation]
    notification_settings: NotificationSettings
    default_profile: str

    @field_validator('default_profile')
    @classmethod
    def default_profile_exists(cls, v, info):
        """Ensure default profile exists in preference profiles."""
        if 'preference_profiles' in info.data:
            profile_names = [p.name for p in info.data['preference_profiles']]
            if v not in profile_names:
                raise ValueError(f'Default profile "{v}" not found in preference profiles')
        return v


class TimeAnalysis(BaseModel):
    """Time-related analysis for a route."""
    estimated_time: int = Field(..., gt=0, description="Estimated time in minutes")
    time_range_min: int = Field(..., gt=0, description="Best case time in minutes")
    time_range_max: int = Field(..., gt=0, description="Worst case time in minutes")
    peak_hour_impact: int = Field(default=0, description="Additional minutes during peak hours")


class CostAnalysis(BaseModel):
    """Cost-related analysis for a route."""
    fuel_cost: float = Field(default=0.0, ge=0)
    transit_fare: float = Field(default=0.0, ge=0)
    parking_cost: float = Field(default=0.0, ge=0)
    toll_cost: float = Field(default=0.0, ge=0)
    total_cost: float = Field(..., ge=0)


class StressAnalysis(BaseModel):
    """Stress-related analysis for a route."""
    traffic_stress: int = Field(..., ge=1, le=10, description="Stress from traffic congestion")
    complexity_stress: int = Field(..., ge=1, le=10, description="Stress from route complexity")
    weather_stress: int = Field(..., ge=1, le=10, description="Stress from weather conditions")
    overall_stress: int = Field(..., ge=1, le=10, description="Overall stress level")


class ReliabilityAnalysis(BaseModel):
    """Reliability-related analysis for a route."""
    historical_variance: float = Field(..., ge=0, description="Historical time variance in minutes")
    incident_probability: float = Field(..., ge=0, le=1, description="Probability of incidents (0-1)")
    weather_impact: float = Field(..., ge=0, description="Weather impact factor")
    service_reliability: float = Field(..., ge=0, le=1, description="Transit service reliability (0-1)")
    overall_reliability: int = Field(..., ge=1, le=10, description="Overall reliability score")


class ComparisonPoint(BaseModel):
    """Single point of comparison between routes."""
    factor: str
    this_route_value: str
    comparison_text: str


class TradeoffSummary(BaseModel):
    """Summary of trade-offs for a route."""
    strengths: List[str]
    weaknesses: List[str]
    when_to_choose: List[str]
    when_not_to_choose: List[str]
    compared_to_alternatives: List[ComparisonPoint]


class RouteAnalysis(BaseModel):
    """Complete analysis of a route."""
    route_id: str
    timestamp: datetime
    time_analysis: TimeAnalysis
    cost_analysis: CostAnalysis
    stress_analysis: StressAnalysis
    reliability_analysis: ReliabilityAnalysis
    tradeoff_summary: TradeoffSummary