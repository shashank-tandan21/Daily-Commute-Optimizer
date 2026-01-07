"""Data Collection Service for gathering real-time traffic, transit, and weather data."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from commute_optimizer.models import Location
from commute_optimizer.config import settings


class DataSource(str, Enum):
    """Available data sources."""
    TRAFFIC = "traffic"
    TRANSIT = "transit"
    WEATHER = "weather"
    PARKING = "parking"


@dataclass
class CachedData:
    """Cached data with timestamp and freshness tracking."""
    data: Dict[str, Any]
    timestamp: datetime
    source: DataSource
    location_key: str
    ttl_minutes: int = 5
    
    @property
    def is_fresh(self) -> bool:
        """Check if cached data is still fresh."""
        age = datetime.now() - self.timestamp
        return age.total_seconds() < (self.ttl_minutes * 60)
    
    @property
    def age_minutes(self) -> float:
        """Get age of cached data in minutes."""
        age = datetime.now() - self.timestamp
        return age.total_seconds() / 60


@dataclass
class TrafficData:
    """Traffic data structure."""
    congestion_level: str  # light, moderate, heavy, severe
    pattern: str  # flowing, slow_moving, stop_and_go
    active_incidents: int
    average_speed_kmh: float
    delay_minutes: int
    last_updated: datetime


@dataclass
class TransitData:
    """Public transit data structure."""
    service_status: str  # normal, minor_delays, delays, major_delays, disrupted, suspended, cancelled
    delay_minutes: int
    next_departure: Optional[datetime]
    service_frequency_minutes: int
    route_disruptions: List[str]
    last_updated: datetime


@dataclass
class WeatherData:
    """Weather data structure."""
    condition: str  # clear, cloudy, light_rain, rain, heavy_rain, snow, heavy_snow, fog, storm, ice
    temperature: float  # Celsius
    visibility_km: float
    wind_speed_kmh: float
    precipitation_probability: float  # 0-100%
    last_updated: datetime


@dataclass
class ParkingData:
    """Parking availability data structure."""
    availability: str  # abundant, moderate, limited, scarce
    average_cost_per_hour: float
    walking_distance_to_destination: float  # km
    last_updated: datetime


class DataCollectionService:
    """Service for collecting real-time data from external APIs."""
    
    def __init__(self):
        """Initialize the data collection service."""
        self.cache: Dict[str, CachedData] = {}
        self.logger = logging.getLogger(__name__)
        
        # Data refresh intervals (minutes)
        self.refresh_intervals = {
            DataSource.TRAFFIC: 3,
            DataSource.TRANSIT: 5,
            DataSource.WEATHER: 15,
            DataSource.PARKING: 10
        }
        
        # Mock API endpoints (in real implementation, these would be actual API URLs)
        self.api_endpoints = {
            DataSource.TRAFFIC: "https://api.traffic.example.com/v1/conditions",
            DataSource.TRANSIT: "https://api.transit.example.com/v1/status",
            DataSource.WEATHER: "https://api.weather.example.com/v1/current",
            DataSource.PARKING: "https://api.parking.example.com/v1/availability"
        }
    
    async def collect_traffic_data(
        self, 
        origin: Location, 
        destination: Location,
        force_refresh: bool = False
    ) -> TrafficData:
        """
        Collect real-time traffic data for a route.
        
        Args:
            origin: Starting location
            destination: Ending location
            force_refresh: Force refresh even if cached data is fresh
            
        Returns:
            Current traffic data for the route
            
        Validates: Requirements 4.3, 4.5
        """
        location_key = self._generate_location_key(origin, destination)
        cache_key = f"traffic_{location_key}"
        
        # Check cache first
        if not force_refresh and cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached.is_fresh:
                self.logger.debug(f"Using cached traffic data (age: {cached.age_minutes:.1f}min)")
                return self._dict_to_traffic_data(cached.data)
        
        # Collect fresh data
        try:
            if settings.use_mock_apis:
                traffic_data = await self._mock_traffic_api(origin, destination)
            else:
                traffic_data = await self._call_traffic_api(origin, destination)
            
            # Cache the data
            self._cache_data(cache_key, asdict(traffic_data), DataSource.TRAFFIC, location_key)
            
            self.logger.info(f"Collected fresh traffic data for {location_key}")
            return traffic_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect traffic data: {e}")
            # Return cached data if available, even if stale
            if cache_key in self.cache:
                self.logger.warning("Using stale cached traffic data due to API failure")
                return self._dict_to_traffic_data(self.cache[cache_key].data)
            else:
                # Return default data if no cache available
                return self._get_default_traffic_data()
    
    async def collect_transit_data(
        self, 
        origin: Location, 
        destination: Location,
        force_refresh: bool = False
    ) -> TransitData:
        """
        Collect real-time public transit data.
        
        Args:
            origin: Starting location
            destination: Ending location
            force_refresh: Force refresh even if cached data is fresh
            
        Returns:
            Current transit data for the route
            
        Validates: Requirements 4.3, 4.5
        """
        location_key = self._generate_location_key(origin, destination)
        cache_key = f"transit_{location_key}"
        
        # Check cache first
        if not force_refresh and cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached.is_fresh:
                self.logger.debug(f"Using cached transit data (age: {cached.age_minutes:.1f}min)")
                return self._dict_to_transit_data(cached.data)
        
        # Collect fresh data
        try:
            if settings.use_mock_apis:
                transit_data = await self._mock_transit_api(origin, destination)
            else:
                transit_data = await self._call_transit_api(origin, destination)
            
            # Cache the data
            self._cache_data(cache_key, asdict(transit_data), DataSource.TRANSIT, location_key)
            
            self.logger.info(f"Collected fresh transit data for {location_key}")
            return transit_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect transit data: {e}")
            # Return cached data if available, even if stale
            if cache_key in self.cache:
                self.logger.warning("Using stale cached transit data due to API failure")
                return self._dict_to_transit_data(self.cache[cache_key].data)
            else:
                # Return default data if no cache available
                return self._get_default_transit_data()
    
    async def collect_weather_data(
        self, 
        location: Location,
        force_refresh: bool = False
    ) -> WeatherData:
        """
        Collect current weather data for a location.
        
        Args:
            location: Location to get weather for
            force_refresh: Force refresh even if cached data is fresh
            
        Returns:
            Current weather data
            
        Validates: Requirements 4.3, 4.5
        """
        location_key = f"{location.latitude:.3f},{location.longitude:.3f}"
        cache_key = f"weather_{location_key}"
        
        # Check cache first
        if not force_refresh and cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached.is_fresh:
                self.logger.debug(f"Using cached weather data (age: {cached.age_minutes:.1f}min)")
                return self._dict_to_weather_data(cached.data)
        
        # Collect fresh data
        try:
            if settings.use_mock_apis:
                weather_data = await self._mock_weather_api(location)
            else:
                weather_data = await self._call_weather_api(location)
            
            # Cache the data with longer TTL for weather
            self._cache_data(cache_key, asdict(weather_data), DataSource.WEATHER, location_key, ttl_minutes=15)
            
            self.logger.info(f"Collected fresh weather data for {location_key}")
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect weather data: {e}")
            # Return cached data if available, even if stale
            if cache_key in self.cache:
                self.logger.warning("Using stale cached weather data due to API failure")
                return self._dict_to_weather_data(self.cache[cache_key].data)
            else:
                # Return default data if no cache available
                return self._get_default_weather_data()
    
    async def collect_parking_data(
        self, 
        location: Location,
        force_refresh: bool = False
    ) -> ParkingData:
        """
        Collect parking availability data for a location.
        
        Args:
            location: Location to get parking data for
            force_refresh: Force refresh even if cached data is fresh
            
        Returns:
            Current parking availability data
            
        Validates: Requirements 4.3, 4.5
        """
        location_key = f"{location.latitude:.3f},{location.longitude:.3f}"
        cache_key = f"parking_{location_key}"
        
        # Check cache first
        if not force_refresh and cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached.is_fresh:
                self.logger.debug(f"Using cached parking data (age: {cached.age_minutes:.1f}min)")
                return self._dict_to_parking_data(cached.data)
        
        # Collect fresh data
        try:
            if settings.use_mock_apis:
                parking_data = await self._mock_parking_api(location)
            else:
                parking_data = await self._call_parking_api(location)
            
            # Cache the data
            self._cache_data(cache_key, asdict(parking_data), DataSource.PARKING, location_key, ttl_minutes=10)
            
            self.logger.info(f"Collected fresh parking data for {location_key}")
            return parking_data
            
        except Exception as e:
            self.logger.error(f"Failed to collect parking data: {e}")
            # Return cached data if available, even if stale
            if cache_key in self.cache:
                self.logger.warning("Using stale cached parking data due to API failure")
                return self._dict_to_parking_data(self.cache[cache_key].data)
            else:
                # Return default data if no cache available
                return self._get_default_parking_data()
    
    async def collect_all_data(
        self, 
        origin: Location, 
        destination: Location,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Collect all types of data for a route.
        
        Args:
            origin: Starting location
            destination: Ending location
            force_refresh: Force refresh even if cached data is fresh
            
        Returns:
            Dictionary containing all collected data
            
        Validates: Requirements 4.3, 4.5
        """
        # Collect all data concurrently
        tasks = [
            self.collect_traffic_data(origin, destination, force_refresh),
            self.collect_transit_data(origin, destination, force_refresh),
            self.collect_weather_data(origin, force_refresh),  # Weather for origin
            self.collect_parking_data(destination, force_refresh)  # Parking at destination
        ]
        
        try:
            traffic_data, transit_data, weather_data, parking_data = await asyncio.gather(*tasks)
            
            return {
                'traffic_data': {
                    'congestion_level': traffic_data.congestion_level,
                    'pattern': traffic_data.pattern,
                    'active_incidents': traffic_data.active_incidents,
                    'average_speed_kmh': traffic_data.average_speed_kmh,
                    'delay_minutes': traffic_data.delay_minutes
                },
                'transit_data': {
                    'service_status': transit_data.service_status,
                    'delay_minutes': transit_data.delay_minutes,
                    'next_departure': transit_data.next_departure,
                    'service_frequency_minutes': transit_data.service_frequency_minutes,
                    'route_disruptions': transit_data.route_disruptions
                },
                'weather_data': {
                    'condition': weather_data.condition,
                    'temperature': weather_data.temperature,
                    'visibility_km': weather_data.visibility_km,
                    'wind_speed_kmh': weather_data.wind_speed_kmh,
                    'precipitation_probability': weather_data.precipitation_probability
                },
                'parking_data': {
                    'availability': parking_data.availability,
                    'average_cost_per_hour': parking_data.average_cost_per_hour,
                    'walking_distance_to_destination': parking_data.walking_distance_to_destination
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to collect all data: {e}")
            # Return partial data or defaults
            return self._get_default_all_data()
    
    def get_cache_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all cached data.
        
        Returns:
            Dictionary with cache status information
        """
        status = {}
        for cache_key, cached_data in self.cache.items():
            status[cache_key] = {
                'source': cached_data.source.value,
                'location_key': cached_data.location_key,
                'age_minutes': cached_data.age_minutes,
                'is_fresh': cached_data.is_fresh,
                'ttl_minutes': cached_data.ttl_minutes,
                'timestamp': cached_data.timestamp.isoformat()
            }
        return status
    
    def clear_cache(self, source: Optional[DataSource] = None) -> int:
        """
        Clear cached data.
        
        Args:
            source: Specific data source to clear, or None to clear all
            
        Returns:
            Number of cache entries cleared
        """
        if source is None:
            count = len(self.cache)
            self.cache.clear()
            self.logger.info(f"Cleared all cache entries ({count} items)")
            return count
        else:
            keys_to_remove = [key for key, cached in self.cache.items() 
                             if cached.source == source]
            for key in keys_to_remove:
                del self.cache[key]
            self.logger.info(f"Cleared {len(keys_to_remove)} cache entries for {source.value}")
            return len(keys_to_remove)
    
    def _generate_location_key(self, origin: Location, destination: Location) -> str:
        """Generate a cache key for origin-destination pair."""
        return f"{origin.latitude:.3f},{origin.longitude:.3f}-{destination.latitude:.3f},{destination.longitude:.3f}"
    
    def _cache_data(
        self, 
        cache_key: str, 
        data: Dict[str, Any], 
        source: DataSource, 
        location_key: str,
        ttl_minutes: Optional[int] = None
    ) -> None:
        """Cache data with timestamp and TTL."""
        if ttl_minutes is None:
            ttl_minutes = self.refresh_intervals[source]
        
        self.cache[cache_key] = CachedData(
            data=data,
            timestamp=datetime.now(),
            source=source,
            location_key=location_key,
            ttl_minutes=ttl_minutes
        )
    
    # Mock API implementations (for testing and development)
    async def _mock_traffic_api(self, origin: Location, destination: Location) -> TrafficData:
        """Mock traffic API implementation."""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Generate mock data based on time of day
        current_hour = datetime.now().hour
        
        if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:  # Peak hours
            congestion_level = "heavy"
            pattern = "stop_and_go"
            active_incidents = 2
            average_speed_kmh = 25.0
            delay_minutes = 15
        elif 10 <= current_hour <= 16:  # Midday
            congestion_level = "moderate"
            pattern = "slow_moving"
            active_incidents = 1
            average_speed_kmh = 40.0
            delay_minutes = 5
        else:  # Off-peak
            congestion_level = "light"
            pattern = "flowing"
            active_incidents = 0
            average_speed_kmh = 55.0
            delay_minutes = 0
        
        return TrafficData(
            congestion_level=congestion_level,
            pattern=pattern,
            active_incidents=active_incidents,
            average_speed_kmh=average_speed_kmh,
            delay_minutes=delay_minutes,
            last_updated=datetime.now()
        )
    
    async def _mock_transit_api(self, origin: Location, destination: Location) -> TransitData:
        """Mock transit API implementation."""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Generate mock data based on time of day
        current_hour = datetime.now().hour
        
        if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:  # Peak hours
            service_status = "minor_delays"
            delay_minutes = 5
            service_frequency_minutes = 8
            route_disruptions = ["Line 1: Minor delays due to high passenger volume"]
        elif 22 <= current_hour or current_hour <= 5:  # Late night/early morning
            service_status = "normal"
            delay_minutes = 0
            service_frequency_minutes = 20
            route_disruptions = []
        else:  # Regular hours
            service_status = "normal"
            delay_minutes = 2
            service_frequency_minutes = 12
            route_disruptions = []
        
        # Calculate next departure
        next_departure = datetime.now() + timedelta(minutes=service_frequency_minutes - delay_minutes)
        
        return TransitData(
            service_status=service_status,
            delay_minutes=delay_minutes,
            next_departure=next_departure,
            service_frequency_minutes=service_frequency_minutes,
            route_disruptions=route_disruptions,
            last_updated=datetime.now()
        )
    
    async def _mock_weather_api(self, location: Location) -> WeatherData:
        """Mock weather API implementation."""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Generate mock weather data (simplified)
        import random
        
        conditions = ["clear", "cloudy", "light_rain", "rain"]
        condition = random.choice(conditions)
        
        temperature = random.uniform(5, 25)  # 5-25°C
        visibility_km = 10.0 if condition in ["clear", "cloudy"] else random.uniform(2, 8)
        wind_speed_kmh = random.uniform(5, 25)
        precipitation_probability = 0 if condition == "clear" else random.uniform(20, 80)
        
        return WeatherData(
            condition=condition,
            temperature=temperature,
            visibility_km=visibility_km,
            wind_speed_kmh=wind_speed_kmh,
            precipitation_probability=precipitation_probability,
            last_updated=datetime.now()
        )
    
    async def _mock_parking_api(self, location: Location) -> ParkingData:
        """Mock parking API implementation."""
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Generate mock parking data based on location and time
        current_hour = datetime.now().hour
        
        if 9 <= current_hour <= 17:  # Business hours
            availability = "limited"
            average_cost_per_hour = 8.0
        elif 18 <= current_hour <= 22:  # Evening
            availability = "moderate"
            average_cost_per_hour = 5.0
        else:  # Late night/early morning
            availability = "abundant"
            average_cost_per_hour = 2.0
        
        walking_distance_to_destination = 0.2  # 200m average
        
        return ParkingData(
            availability=availability,
            average_cost_per_hour=average_cost_per_hour,
            walking_distance_to_destination=walking_distance_to_destination,
            last_updated=datetime.now()
        )
    
    # Real API implementations (placeholder - would implement actual API calls)
    async def _call_traffic_api(self, origin: Location, destination: Location) -> TrafficData:
        """Call real traffic API."""
        # Placeholder for real API implementation
        raise NotImplementedError("Real traffic API not implemented yet")
    
    async def _call_transit_api(self, origin: Location, destination: Location) -> TransitData:
        """Call real transit API."""
        # Placeholder for real API implementation
        raise NotImplementedError("Real transit API not implemented yet")
    
    async def _call_weather_api(self, location: Location) -> WeatherData:
        """Call real weather API."""
        # Placeholder for real API implementation
        raise NotImplementedError("Real weather API not implemented yet")
    
    async def _call_parking_api(self, location: Location) -> ParkingData:
        """Call real parking API."""
        # Placeholder for real API implementation
        raise NotImplementedError("Real parking API not implemented yet")
    
    # Data conversion helpers
    def _dict_to_traffic_data(self, data: Dict[str, Any]) -> TrafficData:
        """Convert dictionary to TrafficData object."""
        return TrafficData(**data)
    
    def _dict_to_transit_data(self, data: Dict[str, Any]) -> TransitData:
        """Convert dictionary to TransitData object."""
        # Handle datetime conversion
        if 'next_departure' in data and data['next_departure']:
            if isinstance(data['next_departure'], str):
                data['next_departure'] = datetime.fromisoformat(data['next_departure'])
        return TransitData(**data)
    
    def _dict_to_weather_data(self, data: Dict[str, Any]) -> WeatherData:
        """Convert dictionary to WeatherData object."""
        return WeatherData(**data)
    
    def _dict_to_parking_data(self, data: Dict[str, Any]) -> ParkingData:
        """Convert dictionary to ParkingData object."""
        return ParkingData(**data)
    
    # Default data providers (fallback when APIs fail)
    def _get_default_traffic_data(self) -> TrafficData:
        """Get default traffic data when API fails."""
        return TrafficData(
            congestion_level="moderate",
            pattern="flowing",
            active_incidents=0,
            average_speed_kmh=45.0,
            delay_minutes=0,
            last_updated=datetime.now()
        )
    
    def _get_default_transit_data(self) -> TransitData:
        """Get default transit data when API fails."""
        return TransitData(
            service_status="normal",
            delay_minutes=0,
            next_departure=datetime.now() + timedelta(minutes=10),
            service_frequency_minutes=15,
            route_disruptions=[],
            last_updated=datetime.now()
        )
    
    def _get_default_weather_data(self) -> WeatherData:
        """Get default weather data when API fails."""
        return WeatherData(
            condition="clear",
            temperature=20.0,
            visibility_km=10.0,
            wind_speed_kmh=10.0,
            precipitation_probability=0.0,
            last_updated=datetime.now()
        )
    
    def _get_default_parking_data(self) -> ParkingData:
        """Get default parking data when API fails."""
        return ParkingData(
            availability="moderate",
            average_cost_per_hour=5.0,
            walking_distance_to_destination=0.3,
            last_updated=datetime.now()
        )
    
    def _get_default_all_data(self) -> Dict[str, Any]:
        """Get default data for all sources when collection fails."""
        traffic_data = self._get_default_traffic_data()
        transit_data = self._get_default_transit_data()
        weather_data = self._get_default_weather_data()
        parking_data = self._get_default_parking_data()
        
        return {
            'traffic_data': {
                'congestion_level': traffic_data.congestion_level,
                'pattern': traffic_data.pattern,
                'active_incidents': traffic_data.active_incidents,
                'average_speed_kmh': traffic_data.average_speed_kmh,
                'delay_minutes': traffic_data.delay_minutes
            },
            'transit_data': {
                'service_status': transit_data.service_status,
                'delay_minutes': transit_data.delay_minutes,
                'next_departure': transit_data.next_departure,
                'service_frequency_minutes': transit_data.service_frequency_minutes,
                'route_disruptions': transit_data.route_disruptions
            },
            'weather_data': {
                'condition': weather_data.condition,
                'temperature': weather_data.temperature,
                'visibility_km': weather_data.visibility_km,
                'wind_speed_kmh': weather_data.wind_speed_kmh,
                'precipitation_probability': weather_data.precipitation_probability
            },
            'parking_data': {
                'availability': parking_data.availability,
                'average_cost_per_hour': parking_data.average_cost_per_hour,
                'walking_distance_to_destination': parking_data.walking_distance_to_destination
            }
        }
    
    # Synchronous wrapper methods for compatibility with non-async code
    def get_traffic_data(self, origin: Location = None, destination: Location = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for getting traffic data.
        Returns cached data if available, otherwise returns default data.
        """
        if origin and destination:
            location_key = self._generate_location_key(origin, destination)
            cache_key = f"traffic_{location_key}"
            
            if cache_key in self.cache and self.cache[cache_key].is_fresh:
                cached_data = self.cache[cache_key]
                return {
                    'congestion_level': cached_data.data['congestion_level'],
                    'pattern': cached_data.data['pattern'],
                    'active_incidents': cached_data.data['active_incidents'],
                    'average_speed_kmh': cached_data.data['average_speed_kmh'],
                    'delay_minutes': cached_data.data['delay_minutes']
                }
        
        # Return default data
        traffic_data = self._get_default_traffic_data()
        return {
            'congestion_level': traffic_data.congestion_level,
            'pattern': traffic_data.pattern,
            'active_incidents': traffic_data.active_incidents,
            'average_speed_kmh': traffic_data.average_speed_kmh,
            'delay_minutes': traffic_data.delay_minutes
        }
    
    def get_weather_data(self, location: Location = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for getting weather data.
        Returns cached data if available, otherwise returns default data.
        """
        if location:
            location_key = f"{location.latitude:.3f},{location.longitude:.3f}"
            cache_key = f"weather_{location_key}"
            
            if cache_key in self.cache and self.cache[cache_key].is_fresh:
                cached_data = self.cache[cache_key]
                return {
                    'condition': cached_data.data['condition'],
                    'temperature': cached_data.data['temperature'],
                    'visibility_km': cached_data.data['visibility_km'],
                    'wind_speed_kmh': cached_data.data['wind_speed_kmh'],
                    'precipitation_probability': cached_data.data['precipitation_probability']
                }
        
        # Return default data
        weather_data = self._get_default_weather_data()
        return {
            'condition': weather_data.condition,
            'temperature': weather_data.temperature,
            'visibility_km': weather_data.visibility_km,
            'wind_speed_kmh': weather_data.wind_speed_kmh,
            'precipitation_probability': weather_data.precipitation_probability
        }
    
    def get_transit_data(self, origin: Location = None, destination: Location = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for getting transit data.
        Returns cached data if available, otherwise returns default data.
        """
        if origin and destination:
            location_key = self._generate_location_key(origin, destination)
            cache_key = f"transit_{location_key}"
            
            if cache_key in self.cache and self.cache[cache_key].is_fresh:
                cached_data = self.cache[cache_key]
                return {
                    'service_status': cached_data.data['service_status'],
                    'delay_minutes': cached_data.data['delay_minutes'],
                    'next_departure': cached_data.data['next_departure'],
                    'service_frequency_minutes': cached_data.data['service_frequency_minutes'],
                    'route_disruptions': cached_data.data['route_disruptions']
                }
        
        # Return default data
        transit_data = self._get_default_transit_data()
        return {
            'service_status': transit_data.service_status,
            'delay_minutes': transit_data.delay_minutes,
            'next_departure': transit_data.next_departure,
            'service_frequency_minutes': transit_data.service_frequency_minutes,
            'route_disruptions': transit_data.route_disruptions
        }


class RealTimeDataManager:
    """Manager for real-time data updates and freshness tracking."""
    
    def __init__(self, data_collection_service: DataCollectionService):
        """Initialize the real-time data manager."""
        self.data_service = data_collection_service
        self.logger = logging.getLogger(__name__)
        self._update_tasks: Dict[str, asyncio.Task] = {}
        self._is_running = False
        
        # Freshness thresholds (minutes) - data is considered stale after this time
        self.freshness_thresholds = {
            DataSource.TRAFFIC: 5,
            DataSource.TRANSIT: 8,
            DataSource.WEATHER: 20,
            DataSource.PARKING: 15
        }
        
        # Critical freshness thresholds (minutes) - data is considered critical after this time
        self.critical_thresholds = {
            DataSource.TRAFFIC: 10,
            DataSource.TRANSIT: 15,
            DataSource.WEATHER: 45,
            DataSource.PARKING: 30
        }
    
    async def start_real_time_updates(self) -> None:
        """
        Start real-time data update monitoring.
        
        This will continuously monitor data freshness and trigger updates
        when data becomes stale.
        
        Validates: Requirements 4.3, 4.5
        """
        if self._is_running:
            self.logger.warning("Real-time updates already running")
            return
        
        self._is_running = True
        self.logger.info("Starting real-time data update monitoring")
        
        # Start background task for monitoring data freshness
        self._update_tasks['monitor'] = asyncio.create_task(self._monitor_data_freshness())
    
    async def stop_real_time_updates(self) -> None:
        """Stop real-time data update monitoring."""
        if not self._is_running:
            return
        
        self._is_running = False
        self.logger.info("Stopping real-time data update monitoring")
        
        # Cancel all update tasks
        for task_name, task in self._update_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    self.logger.debug(f"Cancelled update task: {task_name}")
        
        self._update_tasks.clear()
    
    async def _monitor_data_freshness(self) -> None:
        """
        Monitor data freshness and trigger updates when needed.
        
        This runs continuously while real-time updates are enabled.
        """
        while self._is_running:
            try:
                await self._check_and_update_stale_data()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in data freshness monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_and_update_stale_data(self) -> None:
        """Check for stale data and trigger updates."""
        stale_entries = []
        critical_entries = []
        
        # Check all cached data for staleness
        for cache_key, cached_data in self.data_service.cache.items():
            age_minutes = cached_data.age_minutes
            source = cached_data.source
            
            freshness_threshold = self.freshness_thresholds.get(source, 10)
            critical_threshold = self.critical_thresholds.get(source, 20)
            
            if age_minutes > critical_threshold:
                critical_entries.append((cache_key, cached_data, age_minutes))
            elif age_minutes > freshness_threshold:
                stale_entries.append((cache_key, cached_data, age_minutes))
        
        # Log status
        if critical_entries:
            self.logger.warning(f"Found {len(critical_entries)} critical stale data entries")
        if stale_entries:
            self.logger.info(f"Found {len(stale_entries)} stale data entries")
        
        # Update critical entries first (high priority)
        for cache_key, cached_data, age in critical_entries:
            await self._refresh_cached_data(cache_key, cached_data, priority="high")
        
        # Update stale entries (normal priority)
        for cache_key, cached_data, age in stale_entries:
            await self._refresh_cached_data(cache_key, cached_data, priority="normal")
    
    async def _refresh_cached_data(
        self, 
        cache_key: str, 
        cached_data: CachedData, 
        priority: str = "normal"
    ) -> None:
        """
        Refresh a specific cached data entry.
        
        Args:
            cache_key: Cache key to refresh
            cached_data: Cached data object
            priority: Priority level (high, normal, low)
        """
        try:
            # Parse cache key to determine data type and location
            if cache_key.startswith("traffic_"):
                await self._refresh_traffic_data(cache_key, cached_data.location_key)
            elif cache_key.startswith("transit_"):
                await self._refresh_transit_data(cache_key, cached_data.location_key)
            elif cache_key.startswith("weather_"):
                await self._refresh_weather_data(cache_key, cached_data.location_key)
            elif cache_key.startswith("parking_"):
                await self._refresh_parking_data(cache_key, cached_data.location_key)
            
            self.logger.debug(f"Refreshed {priority} priority data: {cache_key}")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh cached data {cache_key}: {e}")
    
    async def _refresh_traffic_data(self, cache_key: str, location_key: str) -> None:
        """Refresh traffic data for a specific location."""
        # Parse location key to get origin and destination
        origin, destination = self._parse_location_key(location_key)
        if origin and destination:
            await self.data_service.collect_traffic_data(origin, destination, force_refresh=True)
    
    async def _refresh_transit_data(self, cache_key: str, location_key: str) -> None:
        """Refresh transit data for a specific location."""
        # Parse location key to get origin and destination
        origin, destination = self._parse_location_key(location_key)
        if origin and destination:
            await self.data_service.collect_transit_data(origin, destination, force_refresh=True)
    
    async def _refresh_weather_data(self, cache_key: str, location_key: str) -> None:
        """Refresh weather data for a specific location."""
        # Parse single location key
        location = self._parse_single_location_key(location_key)
        if location:
            await self.data_service.collect_weather_data(location, force_refresh=True)
    
    async def _refresh_parking_data(self, cache_key: str, location_key: str) -> None:
        """Refresh parking data for a specific location."""
        # Parse single location key
        location = self._parse_single_location_key(location_key)
        if location:
            await self.data_service.collect_parking_data(location, force_refresh=True)
    
    def _parse_location_key(self, location_key: str) -> tuple[Optional[Location], Optional[Location]]:
        """
        Parse location key to extract origin and destination.
        
        Args:
            location_key: Location key in format "lat1,lon1-lat2,lon2"
            
        Returns:
            Tuple of (origin, destination) or (None, None) if parsing fails
        """
        try:
            origin_str, destination_str = location_key.split('-')
            
            origin_lat, origin_lon = map(float, origin_str.split(','))
            dest_lat, dest_lon = map(float, destination_str.split(','))
            
            origin = Location(
                latitude=origin_lat,
                longitude=origin_lon,
                address=f"Origin ({origin_lat:.3f}, {origin_lon:.3f})"
            )
            
            destination = Location(
                latitude=dest_lat,
                longitude=dest_lon,
                address=f"Destination ({dest_lat:.3f}, {dest_lon:.3f})"
            )
            
            return origin, destination
            
        except (ValueError, IndexError) as e:
            self.logger.error(f"Failed to parse location key '{location_key}': {e}")
            return None, None
    
    def _parse_single_location_key(self, location_key: str) -> Optional[Location]:
        """
        Parse single location key to extract location.
        
        Args:
            location_key: Location key in format "lat,lon"
            
        Returns:
            Location object or None if parsing fails
        """
        try:
            lat, lon = map(float, location_key.split(','))
            
            return Location(
                latitude=lat,
                longitude=lon,
                address=f"Location ({lat:.3f}, {lon:.3f})"
            )
            
        except (ValueError, IndexError) as e:
            self.logger.error(f"Failed to parse single location key '{location_key}': {e}")
            return None
    
    def get_data_freshness_status(self) -> Dict[str, Any]:
        """
        Get comprehensive data freshness status.
        
        Returns:
            Dictionary with freshness status for all cached data
            
        Validates: Requirements 4.3, 4.5
        """
        status = {
            'is_monitoring': self._is_running,
            'total_cached_entries': len(self.data_service.cache),
            'freshness_summary': {
                'fresh': 0,
                'stale': 0,
                'critical': 0
            },
            'by_source': {},
            'entries': []
        }
        
        # Analyze each cached entry
        for cache_key, cached_data in self.data_service.cache.items():
            age_minutes = cached_data.age_minutes
            source = cached_data.source.value
            
            freshness_threshold = self.freshness_thresholds.get(cached_data.source, 10)
            critical_threshold = self.critical_thresholds.get(cached_data.source, 20)
            
            # Determine freshness status
            if age_minutes > critical_threshold:
                freshness_status = 'critical'
                status['freshness_summary']['critical'] += 1
            elif age_minutes > freshness_threshold:
                freshness_status = 'stale'
                status['freshness_summary']['stale'] += 1
            else:
                freshness_status = 'fresh'
                status['freshness_summary']['fresh'] += 1
            
            # Update by-source statistics
            if source not in status['by_source']:
                status['by_source'][source] = {
                    'fresh': 0,
                    'stale': 0,
                    'critical': 0,
                    'total': 0
                }
            
            status['by_source'][source][freshness_status] += 1
            status['by_source'][source]['total'] += 1
            
            # Add entry details
            status['entries'].append({
                'cache_key': cache_key,
                'source': source,
                'location_key': cached_data.location_key,
                'age_minutes': round(age_minutes, 1),
                'freshness_status': freshness_status,
                'freshness_threshold': freshness_threshold,
                'critical_threshold': critical_threshold,
                'timestamp': cached_data.timestamp.isoformat()
            })
        
        return status
    
    async def invalidate_cache_by_condition(
        self, 
        condition: str, 
        value: Any = None
    ) -> int:
        """
        Invalidate cache entries based on specific conditions.
        
        Args:
            condition: Condition type ('age', 'source', 'location', 'all')
            value: Value for the condition (e.g., age in minutes, source type)
            
        Returns:
            Number of cache entries invalidated
            
        Validates: Requirements 4.3, 4.5
        """
        keys_to_remove = []
        
        if condition == 'age' and value is not None:
            # Remove entries older than specified age
            for cache_key, cached_data in self.data_service.cache.items():
                if cached_data.age_minutes > value:
                    keys_to_remove.append(cache_key)
        
        elif condition == 'source' and value is not None:
            # Remove entries from specific source
            if isinstance(value, str):
                value = DataSource(value)
            for cache_key, cached_data in self.data_service.cache.items():
                if cached_data.source == value:
                    keys_to_remove.append(cache_key)
        
        elif condition == 'location' and value is not None:
            # Remove entries for specific location
            for cache_key, cached_data in self.data_service.cache.items():
                if cached_data.location_key == value:
                    keys_to_remove.append(cache_key)
        
        elif condition == 'all':
            # Remove all entries
            keys_to_remove = list(self.data_service.cache.keys())
        
        # Remove the identified keys
        for key in keys_to_remove:
            del self.data_service.cache[key]
        
        self.logger.info(f"Invalidated {len(keys_to_remove)} cache entries by condition '{condition}'")
        return len(keys_to_remove)
    
    async def handle_api_failure(
        self, 
        source: DataSource, 
        error: Exception,
        fallback_strategy: str = "cached"
    ) -> Dict[str, Any]:
        """
        Handle API failures gracefully with fallback strategies.
        
        Args:
            source: Data source that failed
            error: Exception that occurred
            fallback_strategy: Strategy to use ('cached', 'default', 'retry')
            
        Returns:
            Dictionary with fallback data and status information
            
        Validates: Requirements 4.3, 4.5
        """
        self.logger.error(f"API failure for {source.value}: {error}")
        
        fallback_info = {
            'source': source.value,
            'error': str(error),
            'fallback_strategy': fallback_strategy,
            'timestamp': datetime.now().isoformat(),
            'data': None,
            'data_age_minutes': None,
            'success': False
        }
        
        if fallback_strategy == "cached":
            # Try to find cached data for this source
            cached_entries = [
                (key, cached) for key, cached in self.data_service.cache.items()
                if cached.source == source
            ]
            
            if cached_entries:
                # Use the most recent cached entry
                most_recent = min(cached_entries, key=lambda x: x[1].age_minutes)
                cache_key, cached_data = most_recent
                
                fallback_info['data'] = cached_data.data
                fallback_info['data_age_minutes'] = cached_data.age_minutes
                fallback_info['success'] = True
                fallback_info['cache_key'] = cache_key
                
                self.logger.info(f"Using cached data for {source.value} (age: {cached_data.age_minutes:.1f}min)")
            else:
                # No cached data available, fall back to default
                fallback_info['fallback_strategy'] = "default"
                fallback_info['data'] = self._get_default_data_for_source(source)
                fallback_info['success'] = True
                
                self.logger.warning(f"No cached data for {source.value}, using default data")
        
        elif fallback_strategy == "default":
            # Use default data
            fallback_info['data'] = self._get_default_data_for_source(source)
            fallback_info['success'] = True
            
            self.logger.info(f"Using default data for {source.value}")
        
        elif fallback_strategy == "retry":
            # This would be handled by the calling code
            fallback_info['success'] = False
            self.logger.info(f"Retry strategy requested for {source.value}")
        
        return fallback_info
    
    def _get_default_data_for_source(self, source: DataSource) -> Dict[str, Any]:
        """Get default data for a specific source."""
        if source == DataSource.TRAFFIC:
            return asdict(self.data_service._get_default_traffic_data())
        elif source == DataSource.TRANSIT:
            return asdict(self.data_service._get_default_transit_data())
        elif source == DataSource.WEATHER:
            return asdict(self.data_service._get_default_weather_data())
        elif source == DataSource.PARKING:
            return asdict(self.data_service._get_default_parking_data())
        else:
            return {}
    
    async def preload_data_for_route(
        self, 
        origin: Location, 
        destination: Location,
        preload_time_minutes: int = 5
    ) -> Dict[str, Any]:
        """
        Preload data for a route to ensure fresh data is available.
        
        This is useful when you know a route will be requested soon and want
        to ensure the data is fresh when needed.
        
        Args:
            origin: Starting location
            destination: Ending location
            preload_time_minutes: How many minutes ahead to preload data
            
        Returns:
            Dictionary with preload status and data
            
        Validates: Requirements 4.3, 4.5
        """
        self.logger.info(f"Preloading data for route: {origin.address} -> {destination.address}")
        
        preload_results = {
            'origin': f"{origin.latitude:.3f},{origin.longitude:.3f}",
            'destination': f"{destination.latitude:.3f},{destination.longitude:.3f}",
            'preload_time_minutes': preload_time_minutes,
            'timestamp': datetime.now().isoformat(),
            'results': {}
        }
        
        # Preload all data types
        try:
            # Collect all data with force refresh
            all_data = await self.data_service.collect_all_data(
                origin, destination, force_refresh=True
            )
            
            preload_results['results'] = {
                'traffic': {'success': True, 'data_available': 'traffic_data' in all_data},
                'transit': {'success': True, 'data_available': 'transit_data' in all_data},
                'weather': {'success': True, 'data_available': 'weather_data' in all_data},
                'parking': {'success': True, 'data_available': 'parking_data' in all_data}
            }
            
            preload_results['overall_success'] = True
            
        except Exception as e:
            self.logger.error(f"Failed to preload data: {e}")
            preload_results['overall_success'] = False
            preload_results['error'] = str(e)
        
        return preload_results