"""Route Analysis Service for evaluating routes across multiple criteria."""

from datetime import datetime
from typing import Dict, Any, Optional, List
import math

from commute_optimizer.models import (
    Route, RouteAnalysis, TimeAnalysis, CostAnalysis, StressAnalysis, 
    ReliabilityAnalysis, TradeoffSummary, ComparisonPoint, TransportationMode
)


class RouteAnalysisService:
    """Service for analyzing routes across time, cost, stress, and reliability criteria."""
    
    def __init__(self):
        """Initialize the route analysis service."""
        # Base rates for cost calculations
        self.fuel_cost_per_km = 0.12  # $0.12 per km for fuel
        self.parking_cost_base = 5.0  # $5 base parking cost
        self.transit_fare_base = 3.50  # $3.50 base transit fare
        self.rideshare_rate_per_km = 1.5  # $1.50 per km for rideshare
        
        # Stress calculation factors
        self.traffic_stress_multiplier = 1.2
        self.weather_stress_multiplier = 1.1
        self.complexity_stress_base = 2.0
        
        # Reliability calculation factors
        self.base_reliability_score = 8.0
        self.incident_probability_factor = 0.1
        self.weather_impact_factor = 0.15
    
    def analyze_route(
        self, 
        route: Route, 
        current_conditions: Optional[Dict[str, Any]] = None
    ) -> RouteAnalysis:
        """
        Perform comprehensive analysis of a route across all criteria.
        
        Args:
            route: Route to analyze
            current_conditions: Current traffic, weather, and transit conditions
            
        Returns:
            Complete route analysis with all evaluation criteria
            
        Validates: Requirements 2.1, 2.4
        """
        if current_conditions is None:
            current_conditions = {}
        
        # Perform analysis across all four criteria
        time_analysis = self._analyze_time(route, current_conditions)
        cost_analysis = self.calculate_cost(route, current_conditions)
        stress_analysis = self._analyze_stress(route, current_conditions)
        reliability_analysis = self._analyze_reliability(route, current_conditions)
        
        # Generate trade-off summary
        tradeoff_summary = self._generate_tradeoff_summary(
            route, time_analysis, cost_analysis, stress_analysis, reliability_analysis
        )
        
        return RouteAnalysis(
            route_id=route.id,
            timestamp=datetime.now(),
            time_analysis=time_analysis,
            cost_analysis=cost_analysis,
            stress_analysis=stress_analysis,
            reliability_analysis=reliability_analysis,
            tradeoff_summary=tradeoff_summary
        )
    
    def calculate_travel_time(
        self, 
        route: Route, 
        traffic_data: Optional[Dict[str, Any]] = None,
        transit_data: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Calculate total travel time with traffic and transit integration.
        
        Args:
            route: Route to calculate time for
            traffic_data: Real-time traffic information
            transit_data: Real-time transit schedule information
            
        Returns:
            Total estimated travel time in minutes
            
        Validates: Requirements 2.1, 2.4
        """
        if traffic_data is None:
            traffic_data = {}
        if transit_data is None:
            transit_data = {}
        
        base_time = route.estimated_time
        
        # Apply traffic adjustments for driving segments
        traffic_multiplier = 1.0
        if any(mode in [TransportationMode.DRIVING, TransportationMode.RIDESHARE] 
               for mode in route.transportation_modes):
            # Get traffic conditions
            congestion_level = traffic_data.get('congestion_level', 'moderate')
            if congestion_level == 'heavy':
                traffic_multiplier = 1.4
            elif congestion_level == 'moderate':
                traffic_multiplier = 1.2
            elif congestion_level == 'light':
                traffic_multiplier = 1.0
        
        # Apply transit delays for public transit segments
        transit_delay = 0
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            # Check for transit delays
            service_status = transit_data.get('service_status', 'normal')
            if service_status == 'delayed':
                transit_delay = transit_data.get('delay_minutes', 10)
            elif service_status == 'disrupted':
                transit_delay = transit_data.get('delay_minutes', 20)
        
        # Calculate final time
        adjusted_time = int(base_time * traffic_multiplier) + transit_delay
        
        return max(base_time, adjusted_time)  # Never less than base time
    
    def calculate_cost(
        self, 
        route: Route, 
        current_conditions: Optional[Dict[str, Any]] = None
    ) -> CostAnalysis:
        """
        Calculate comprehensive monetary cost for a route.
        
        Args:
            route: Route to calculate cost for
            current_conditions: Current pricing conditions (fuel, parking, etc.)
            
        Returns:
            Detailed cost analysis breakdown
            
        Validates: Requirements 2.1, 2.4
        """
        if current_conditions is None:
            current_conditions = {}
        
        fuel_cost = 0.0
        transit_fare = 0.0
        parking_cost = 0.0
        toll_cost = 0.0
        
        # Calculate costs based on transportation modes
        for mode in route.transportation_modes:
            if mode == TransportationMode.DRIVING:
                # Fuel cost based on distance
                fuel_rate = current_conditions.get('fuel_cost_per_km', self.fuel_cost_per_km)
                fuel_cost = route.total_distance * fuel_rate
                
                # Parking cost (if driving to destination)
                parking_rate = current_conditions.get('parking_cost', self.parking_cost_base)
                parking_cost = parking_rate
                
                # Toll costs (simplified - assume some routes have tolls)
                if route.total_distance > 20:  # Long routes might have tolls
                    toll_cost = current_conditions.get('toll_cost', 3.0)
            
            elif mode == TransportationMode.PUBLIC_TRANSIT:
                # Transit fare
                fare_rate = current_conditions.get('transit_fare', self.transit_fare_base)
                transit_fare = fare_rate
            
            elif mode == TransportationMode.RIDESHARE:
                # Rideshare cost based on distance
                rideshare_rate = current_conditions.get('rideshare_rate_per_km', self.rideshare_rate_per_km)
                fuel_cost = route.total_distance * rideshare_rate  # Using fuel_cost field for rideshare
            
            # Cycling and walking have no monetary cost
        
        total_cost = fuel_cost + transit_fare + parking_cost + toll_cost
        
        return CostAnalysis(
            fuel_cost=fuel_cost,
            transit_fare=transit_fare,
            parking_cost=parking_cost,
            toll_cost=toll_cost,
            total_cost=total_cost
        )
    
    def _analyze_time(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> TimeAnalysis:
        """Analyze time-related aspects of the route."""
        base_time = self.calculate_travel_time(
            route, 
            current_conditions.get('traffic_data'),
            current_conditions.get('transit_data')
        )
        
        # Calculate time range (best case to worst case)
        time_variance = max(5, int(base_time * 0.2))  # 20% variance or 5 minutes minimum
        time_range_min = max(int(base_time * 0.8), base_time - time_variance)
        time_range_max = base_time + time_variance
        
        # Peak hour impact
        departure_hour = route.departure_time.hour
        peak_hour_impact = 0
        if 7 <= departure_hour <= 9 or 17 <= departure_hour <= 19:  # Peak hours
            peak_hour_impact = max(5, int(base_time * 0.15))  # 15% increase during peak
        
        return TimeAnalysis(
            estimated_time=base_time,
            time_range_min=time_range_min,
            time_range_max=time_range_max,
            peak_hour_impact=peak_hour_impact
        )
    
    def _analyze_stress(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> StressAnalysis:
        """
        Analyze stress-related aspects of the route.
        
        Calculates stress based on traffic congestion patterns, route predictability,
        weather conditions, transfer complexity, and parking availability.
        
        Validates: Requirements 2.1
        """
        # Calculate individual stress components
        traffic_stress = self._calculate_traffic_stress(route, current_conditions)
        complexity_stress = self._calculate_complexity_stress(route, current_conditions)
        weather_stress = self._calculate_weather_stress(route, current_conditions)
        
        # Overall stress is weighted average of components
        overall_stress = int((traffic_stress * 0.5 + complexity_stress * 0.3 + weather_stress * 0.2))
        overall_stress = max(1, min(10, overall_stress))
        
        return StressAnalysis(
            traffic_stress=traffic_stress,
            complexity_stress=complexity_stress,
            weather_stress=weather_stress,
            overall_stress=overall_stress
        )
    
    def _calculate_traffic_stress(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> int:
        """
        Calculate stress from traffic congestion patterns.
        
        Factors in:
        - Current congestion levels
        - Stop-and-go traffic patterns
        - Route predictability during peak hours
        - Highway vs surface street stress differences
        """
        base_stress = 3  # Base traffic stress level
        
        # Only apply traffic stress to driving/rideshare routes
        if not any(mode in [TransportationMode.DRIVING, TransportationMode.RIDESHARE] 
                  for mode in route.transportation_modes):
            return 1  # Minimal traffic stress for non-driving routes
        
        traffic_conditions = current_conditions.get('traffic_data', {})
        congestion_level = traffic_conditions.get('congestion_level', 'moderate')
        
        # Congestion level impact
        congestion_multipliers = {
            'light': 0.7,
            'moderate': 1.0,
            'heavy': 1.6,
            'severe': 2.0
        }
        
        congestion_stress = base_stress * congestion_multipliers.get(congestion_level, 1.0)
        
        # Stop-and-go pattern stress
        traffic_pattern = traffic_conditions.get('pattern', 'flowing')
        if traffic_pattern == 'stop_and_go':
            congestion_stress *= 1.3
        elif traffic_pattern == 'slow_moving':
            congestion_stress *= 1.1
        
        # Peak hour predictability stress
        departure_hour = route.departure_time.hour
        if 7 <= departure_hour <= 9 or 17 <= departure_hour <= 19:  # Peak hours
            # Peak hours are more stressful due to unpredictability
            congestion_stress *= 1.2
        
        # Route type stress (highways vs surface streets)
        # Longer routes likely use highways which can be more stressful
        if route.total_distance > 15:  # Likely highway route
            congestion_stress *= 1.1
        
        return max(1, min(10, int(congestion_stress)))
    
    def _calculate_complexity_stress(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> int:
        """
        Calculate stress from route complexity.
        
        Factors in:
        - Number of transfers or mode changes
        - Navigation complexity (number of segments)
        - Parking availability and walking distances
        - Multi-modal coordination requirements
        """
        base_complexity = 2  # Base complexity stress
        
        # Mode change stress
        num_modes = len(route.transportation_modes)
        mode_change_stress = (num_modes - 1) * 1.5  # Each additional mode adds stress
        
        # Segment complexity stress
        segment_stress = len(route.segments) * 0.3  # More segments = more navigation stress
        
        # Transfer complexity for transit routes
        transfer_stress = 0
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            # Estimate transfers based on segments
            transit_segments = sum(1 for seg in route.segments 
                                 if seg.mode == TransportationMode.PUBLIC_TRANSIT)
            if transit_segments > 1:
                transfer_stress = (transit_segments - 1) * 2  # Each transfer adds stress
        
        # Parking availability stress
        parking_stress = 0
        if TransportationMode.DRIVING in route.transportation_modes:
            parking_conditions = current_conditions.get('parking_data', {})
            parking_availability = parking_conditions.get('availability', 'moderate')
            
            parking_stress_levels = {
                'abundant': 0,
                'moderate': 1,
                'limited': 2,
                'scarce': 3
            }
            parking_stress = parking_stress_levels.get(parking_availability, 1)
        
        # Walking distance stress
        walking_stress = 0
        total_walking_distance = sum(seg.distance for seg in route.segments 
                                   if seg.mode == TransportationMode.WALKING)
        if total_walking_distance > 1.0:  # More than 1km walking
            walking_stress = min(2, total_walking_distance - 1.0)  # Cap at 2 points
        
        total_complexity = (base_complexity + mode_change_stress + segment_stress + 
                          transfer_stress + parking_stress + walking_stress)
        
        return max(1, min(10, int(total_complexity)))
    
    def _calculate_weather_stress(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> int:
        """
        Calculate stress from weather conditions.
        
        Factors in:
        - Current weather conditions and visibility
        - Transportation mode vulnerability to weather
        - Seasonal weather impact patterns
        """
        weather_conditions = current_conditions.get('weather_data', {})
        weather_condition = weather_conditions.get('condition', 'clear')
        temperature = weather_conditions.get('temperature', 20)  # Celsius
        visibility = weather_conditions.get('visibility_km', 10)  # km
        wind_speed = weather_conditions.get('wind_speed_kmh', 0)  # km/h
        
        base_weather_stress = 1
        
        # Weather condition impact
        weather_stress_levels = {
            'clear': 1,
            'cloudy': 1,
            'light_rain': 2,
            'rain': 3,
            'heavy_rain': 5,
            'snow': 4,
            'heavy_snow': 6,
            'fog': 4,
            'storm': 7,
            'ice': 8
        }
        
        condition_stress = weather_stress_levels.get(weather_condition, 2)
        
        # Transportation mode vulnerability
        mode_weather_multipliers = {
            TransportationMode.CYCLING: 2.0,  # Most vulnerable to weather
            TransportationMode.WALKING: 1.8,  # Very vulnerable
            TransportationMode.DRIVING: 1.2,  # Somewhat vulnerable
            TransportationMode.RIDESHARE: 1.1,  # Slightly vulnerable (pickup/dropoff)
            TransportationMode.PUBLIC_TRANSIT: 1.0  # Least vulnerable (covered)
        }
        
        # Apply highest vulnerability multiplier from route's modes
        max_multiplier = max(mode_weather_multipliers.get(mode, 1.0) 
                           for mode in route.transportation_modes)
        
        weather_stress = condition_stress * max_multiplier
        
        # Visibility impact (especially for driving/cycling)
        if visibility < 5 and any(mode in [TransportationMode.DRIVING, TransportationMode.CYCLING] 
                                 for mode in route.transportation_modes):
            weather_stress *= 1.3
        
        # Temperature extremes (especially for walking/cycling)
        if any(mode in [TransportationMode.WALKING, TransportationMode.CYCLING] 
               for mode in route.transportation_modes):
            if temperature < -5 or temperature > 35:  # Extreme temperatures
                weather_stress *= 1.2
        
        # High wind impact (especially for cycling)
        if (wind_speed > 30 and TransportationMode.CYCLING in route.transportation_modes):
            weather_stress *= 1.4
        
        return max(1, min(10, int(weather_stress)))
    
    def _analyze_reliability(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> ReliabilityAnalysis:
        """
        Analyze reliability-related aspects of the route.
        
        Calculates historical variance in travel times, real-time incident probability,
        weather impact, and transit service reliability.
        
        Validates: Requirements 2.1
        """
        # Calculate individual reliability components
        historical_variance = self._calculate_historical_variance(route, current_conditions)
        incident_probability = self._calculate_incident_probability(route, current_conditions)
        weather_impact = self._calculate_weather_impact(route, current_conditions)
        service_reliability = self._calculate_service_reliability(route, current_conditions)
        
        # Calculate overall reliability score
        overall_reliability = self._calculate_overall_reliability(
            route, historical_variance, incident_probability, weather_impact, service_reliability
        )
        
        return ReliabilityAnalysis(
            historical_variance=historical_variance,
            incident_probability=incident_probability,
            weather_impact=weather_impact,
            service_reliability=service_reliability,
            overall_reliability=overall_reliability
        )
    
    def _calculate_historical_variance(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> float:
        """
        Calculate historical variance in travel times.
        
        Factors in:
        - Route complexity and number of variables
        - Transportation mode reliability patterns
        - Time of day consistency patterns
        - Seasonal variance patterns
        """
        base_variance = 3.0  # 3 minutes base variance
        
        # Route complexity variance
        complexity_variance = len(route.segments) * 1.2  # More segments = more variance
        
        # Distance-based variance (longer routes have more variables)
        distance_variance = route.total_distance * 0.15  # 0.15 minutes per km
        
        # Transportation mode variance
        mode_variance = 0
        mode_variance_factors = {
            TransportationMode.WALKING: 1.0,  # Very consistent
            TransportationMode.CYCLING: 2.0,  # Weather dependent
            TransportationMode.DRIVING: 4.0,  # Traffic dependent
            TransportationMode.RIDESHARE: 5.0,  # Pickup time + traffic
            TransportationMode.PUBLIC_TRANSIT: 6.0  # Schedule dependent
        }
        
        # Use maximum variance from all modes (worst case)
        max_mode_variance = max(mode_variance_factors.get(mode, 3.0) 
                               for mode in route.transportation_modes)
        mode_variance = max_mode_variance
        
        # Time of day variance
        departure_hour = route.departure_time.hour
        time_variance = 0
        if 7 <= departure_hour <= 9 or 17 <= departure_hour <= 19:  # Peak hours
            time_variance = 5.0  # Higher variance during peak hours
        elif 22 <= departure_hour or departure_hour <= 5:  # Late night/early morning
            time_variance = 2.0  # Lower variance during off-peak
        else:
            time_variance = 3.0  # Moderate variance during regular hours
        
        # Multi-modal coordination variance
        coordination_variance = 0
        if len(route.transportation_modes) > 1:
            # Each mode change adds coordination uncertainty
            coordination_variance = (len(route.transportation_modes) - 1) * 2.0
        
        # Weather-related historical variance
        weather_variance = 0
        weather_conditions = current_conditions.get('weather_data', {})
        weather_condition = weather_conditions.get('condition', 'clear')
        
        if weather_condition in ['rain', 'snow', 'fog', 'storm']:
            # Bad weather increases historical variance
            weather_variance = 3.0
            # Cycling and walking more affected
            if any(mode in [TransportationMode.CYCLING, TransportationMode.WALKING] 
                   for mode in route.transportation_modes):
                weather_variance *= 1.5
        
        total_variance = (base_variance + complexity_variance + distance_variance + 
                         mode_variance + time_variance + coordination_variance + weather_variance)
        
        return min(45.0, total_variance)  # Cap at 45 minutes variance
    
    def _calculate_incident_probability(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> float:
        """
        Calculate real-time incident probability.
        
        Factors in:
        - Current traffic incident reports
        - Route type and incident susceptibility
        - Weather-related incident probability
        - Time of day incident patterns
        """
        base_probability = 0.05  # 5% base incident probability
        
        # Transportation mode incident susceptibility
        mode_incident_rates = {
            TransportationMode.WALKING: 0.01,  # Very low incident rate
            TransportationMode.CYCLING: 0.03,  # Low incident rate
            TransportationMode.PUBLIC_TRANSIT: 0.08,  # Service disruptions
            TransportationMode.RIDESHARE: 0.12,  # Traffic + pickup issues
            TransportationMode.DRIVING: 0.15   # Highest incident rate
        }
        
        # Use maximum incident rate from all modes
        max_mode_rate = max(mode_incident_rates.get(mode, 0.05) 
                           for mode in route.transportation_modes)
        
        # Distance-based incident probability
        distance_factor = min(0.1, route.total_distance * 0.002)  # Longer routes = higher probability
        
        # Time of day incident patterns
        departure_hour = route.departure_time.hour
        time_factor = 0
        if 7 <= departure_hour <= 9 or 17 <= departure_hour <= 19:  # Peak hours
            time_factor = 0.05  # Higher incident probability during peak
        elif 22 <= departure_hour or departure_hour <= 5:  # Late night/early morning
            time_factor = 0.02  # Lower incident probability during off-peak
        
        # Current traffic incident reports
        traffic_data = current_conditions.get('traffic_data', {})
        active_incidents = traffic_data.get('active_incidents', 0)
        incident_factor = min(0.1, active_incidents * 0.02)  # Each incident adds 2% probability
        
        # Weather-related incident probability
        weather_conditions = current_conditions.get('weather_data', {})
        weather_condition = weather_conditions.get('condition', 'clear')
        
        weather_incident_factors = {
            'clear': 0.0,
            'rain': 0.03,
            'heavy_rain': 0.06,
            'snow': 0.08,
            'heavy_snow': 0.12,
            'fog': 0.05,
            'storm': 0.10,
            'ice': 0.15
        }
        
        weather_factor = weather_incident_factors.get(weather_condition, 0.01)
        
        # Route complexity incident factor
        complexity_factor = len(route.segments) * 0.005  # More segments = more incident points
        
        total_probability = (max_mode_rate + distance_factor + time_factor + 
                           incident_factor + weather_factor + complexity_factor)
        
        return min(0.8, total_probability)  # Cap at 80% probability
    
    def _calculate_weather_impact(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> float:
        """
        Calculate weather impact on route reliability.
        
        Factors in:
        - Current weather conditions
        - Transportation mode weather vulnerability
        - Seasonal weather patterns
        - Weather forecast reliability
        """
        weather_conditions = current_conditions.get('weather_data', {})
        weather_condition = weather_conditions.get('condition', 'clear')
        temperature = weather_conditions.get('temperature', 20)  # Celsius
        wind_speed = weather_conditions.get('wind_speed_kmh', 0)  # km/h
        precipitation_probability = weather_conditions.get('precipitation_probability', 0)  # %
        
        # Base weather impact by condition
        weather_impact_levels = {
            'clear': 0.0,
            'cloudy': 0.05,
            'light_rain': 0.15,
            'rain': 0.25,
            'heavy_rain': 0.45,
            'snow': 0.35,
            'heavy_snow': 0.60,
            'fog': 0.30,
            'storm': 0.55,
            'ice': 0.70
        }
        
        base_impact = weather_impact_levels.get(weather_condition, 0.1)
        
        # Transportation mode weather vulnerability
        mode_weather_vulnerability = {
            TransportationMode.PUBLIC_TRANSIT: 0.3,  # Least vulnerable (covered)
            TransportationMode.RIDESHARE: 0.5,      # Pickup/dropoff exposure
            TransportationMode.DRIVING: 0.7,        # Road condition dependent
            TransportationMode.WALKING: 1.2,        # Very vulnerable
            TransportationMode.CYCLING: 1.5         # Most vulnerable
        }
        
        # Apply maximum vulnerability from route's modes
        max_vulnerability = max(mode_weather_vulnerability.get(mode, 0.5) 
                               for mode in route.transportation_modes)
        
        weather_impact = base_impact * max_vulnerability
        
        # Temperature impact on reliability
        if any(mode in [TransportationMode.WALKING, TransportationMode.CYCLING] 
               for mode in route.transportation_modes):
            if temperature < -10 or temperature > 40:  # Extreme temperatures
                weather_impact += 0.2
            elif temperature < 0 or temperature > 35:  # Very hot/cold
                weather_impact += 0.1
        
        # Wind impact (especially for cycling)
        if TransportationMode.CYCLING in route.transportation_modes and wind_speed > 25:
            weather_impact += min(0.3, (wind_speed - 25) * 0.01)
        
        # Precipitation probability impact
        if precipitation_probability > 50:
            weather_impact += (precipitation_probability - 50) * 0.002  # 0.2% per % over 50%
        
        return min(1.0, weather_impact)  # Cap at 100% impact
    
    def _calculate_service_reliability(
        self, 
        route: Route, 
        current_conditions: Dict[str, Any]
    ) -> float:
        """
        Calculate transit service reliability.
        
        Factors in:
        - Current service status and delays
        - Historical service performance
        - Service type reliability patterns
        - Real-time service updates
        """
        # Non-transit routes have perfect service reliability
        if TransportationMode.PUBLIC_TRANSIT not in route.transportation_modes:
            return 1.0
        
        # Base service reliability
        base_reliability = 0.85  # 85% base reliability for transit
        
        # Current service status
        transit_data = current_conditions.get('transit_data', {})
        service_status = transit_data.get('service_status', 'normal')
        
        service_reliability_factors = {
            'normal': 1.0,
            'minor_delays': 0.9,
            'delays': 0.75,
            'major_delays': 0.6,
            'disrupted': 0.4,
            'suspended': 0.1,
            'cancelled': 0.0
        }
        
        status_factor = service_reliability_factors.get(service_status, 0.8)
        
        # Current delay impact
        current_delay = transit_data.get('delay_minutes', 0)
        delay_factor = max(0.5, 1.0 - (current_delay * 0.02))  # 2% reduction per minute delay
        
        # Time of day service reliability
        departure_hour = route.departure_time.hour
        time_reliability = 1.0
        if 6 <= departure_hour <= 9 or 17 <= departure_hour <= 19:  # Peak hours
            time_reliability = 0.9  # Slightly less reliable during peak
        elif 22 <= departure_hour or departure_hour <= 5:  # Late night/early morning
            time_reliability = 0.7  # Less reliable during off-peak hours
        
        # Service type reliability (mock - based on route complexity)
        service_type_reliability = 1.0
        transit_segments = sum(1 for seg in route.segments 
                              if seg.mode == TransportationMode.PUBLIC_TRANSIT)
        if transit_segments > 1:
            # Multiple transit segments = transfers = lower reliability
            service_type_reliability = max(0.6, 1.0 - ((transit_segments - 1) * 0.1))
        
        # Weather impact on service reliability
        weather_conditions = current_conditions.get('weather_data', {})
        weather_condition = weather_conditions.get('condition', 'clear')
        
        weather_service_impact = {
            'clear': 1.0,
            'rain': 0.95,
            'heavy_rain': 0.85,
            'snow': 0.8,
            'heavy_snow': 0.6,
            'storm': 0.7,
            'ice': 0.5
        }
        
        weather_factor = weather_service_impact.get(weather_condition, 0.9)
        
        # Calculate final service reliability
        final_reliability = (base_reliability * status_factor * delay_factor * 
                           time_reliability * service_type_reliability * weather_factor)
        
        return max(0.0, min(1.0, final_reliability))
    
    def _calculate_overall_reliability(
        self,
        route: Route,
        historical_variance: float,
        incident_probability: float,
        weather_impact: float,
        service_reliability: float
    ) -> int:
        """Calculate overall reliability score from individual components."""
        # Start with route's base reliability
        base_reliability = route.reliability_score
        
        # Convert components to reliability contributions (0-10 scale)
        variance_score = max(1, 10 - (historical_variance / 5))  # Lower variance = higher score
        incident_score = max(1, 10 - (incident_probability * 10))  # Lower probability = higher score
        weather_score = max(1, 10 - (weather_impact * 10))  # Lower impact = higher score
        service_score = service_reliability * 10  # Direct conversion
        
        # Weighted combination of reliability factors
        reliability_factors = [
            (base_reliability, 0.2),      # Base reliability weight
            (variance_score, 0.3),        # Historical variance weight
            (incident_score, 0.25),       # Incident probability weight
            (weather_score, 0.15),        # Weather impact weight
            (service_score, 0.1)          # Service reliability weight
        ]
        
        overall_reliability = sum(score * weight for score, weight in reliability_factors)
        
        return max(1, min(10, int(overall_reliability)))
    
    def _generate_tradeoff_summary(
        self,
        route: Route,
        time_analysis: TimeAnalysis,
        cost_analysis: CostAnalysis,
        stress_analysis: StressAnalysis,
        reliability_analysis: ReliabilityAnalysis
    ) -> TradeoffSummary:
        """Generate a summary of trade-offs for the route."""
        strengths = []
        weaknesses = []
        when_to_choose = []
        when_not_to_choose = []
        
        # Analyze strengths and weaknesses based on scores
        if time_analysis.estimated_time <= 30:
            strengths.append("Quick travel time")
            when_to_choose.append("When you're running late")
        elif time_analysis.estimated_time >= 60:
            weaknesses.append("Long travel time")
            when_not_to_choose.append("When you have time constraints")
        
        if cost_analysis.total_cost <= 2.0:
            strengths.append("Very affordable")
            when_to_choose.append("When budget is a priority")
        elif cost_analysis.total_cost >= 10.0:
            weaknesses.append("Expensive option")
            when_not_to_choose.append("When trying to save money")
        
        if stress_analysis.overall_stress <= 3:
            strengths.append("Low stress journey")
            when_to_choose.append("When you want a relaxing commute")
        elif stress_analysis.overall_stress >= 7:
            weaknesses.append("High stress route")
            when_not_to_choose.append("When you're already stressed")
        
        if reliability_analysis.overall_reliability >= 8:
            strengths.append("Highly reliable")
            when_to_choose.append("When punctuality is critical")
        elif reliability_analysis.overall_reliability <= 5:
            weaknesses.append("Unpredictable timing")
            when_not_to_choose.append("For important appointments")
        
        # Add mode-specific insights
        if TransportationMode.CYCLING in route.transportation_modes:
            strengths.append("Environmentally friendly")
            strengths.append("Good exercise")
            when_not_to_choose.append("In bad weather")
        
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            strengths.append("No parking needed")
            when_not_to_choose.append("During service disruptions")
        
        return TradeoffSummary(
            strengths=strengths,
            weaknesses=weaknesses,
            when_to_choose=when_to_choose,
            when_not_to_choose=when_not_to_choose,
            compared_to_alternatives=[]  # Will be populated when comparing multiple routes
        )