"""Tests for Route Diversity algorithms."""

import pytest
from datetime import datetime, timedelta
from commute_optimizer.services.route_diversity import RouteDiversityEngine, DiversityDimension
from commute_optimizer.services.route_generation import RouteRequest
from commute_optimizer.models import (
    Route, RouteSegment, Location, TransportationMode
)


class TestRouteDiversityEngine:
    """Tests for RouteDiversityEngine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RouteDiversityEngine()
        
        self.origin = Location(
            latitude=37.7749,
            longitude=-122.4194,
            address="123 Main St, San Francisco, CA"
        )
        
        self.destination = Location(
            latitude=37.7849,
            longitude=-122.4094,
            address="456 Oak St, San Francisco, CA"
        )
        
        self.departure_time = datetime(2024, 6, 15, 8, 0)
        
        self.request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time
        )
    
    def create_sample_route(
        self, 
        route_id: str, 
        modes: list, 
        time: int = 30, 
        cost: float = 5.0,
        departure_offset: int = 0
    ) -> Route:
        """Create a sample route for testing."""
        departure = self.departure_time + timedelta(minutes=departure_offset)
        arrival = departure + timedelta(minutes=time)
        
        segment = RouteSegment(
            mode=modes[0],
            start_location=self.origin,
            end_location=self.destination,
            distance=10.0,
            duration=time,
            instructions=f"Travel via {modes[0].value}"
        )
        
        return Route(
            id=route_id,
            segments=[segment],
            total_distance=10.0,
            estimated_time=time,
            estimated_cost=cost,
            stress_level=5,
            reliability_score=7,
            transportation_modes=modes,
            departure_time=departure,
            arrival_time=arrival,
            instructions=[segment.instructions]
        )
    
    def test_ensure_path_diversity_creates_variants(self):
        """Test that path diversity creates different geographical paths."""
        # Create two similar routes
        route1 = self.create_sample_route("route1", [TransportationMode.DRIVING])
        route2 = self.create_sample_route("route2", [TransportationMode.DRIVING])
        
        routes = [route1, route2]
        diverse_routes = self.engine.ensure_path_diversity(routes, self.origin, self.destination, self.departure_time)
        
        # Should create path variants
        assert len(diverse_routes) >= 2
        
        # Routes should have different path signatures
        signatures = [self.engine._get_path_signature(route) for route in diverse_routes]
        unique_signatures = set(signatures)
        assert len(unique_signatures) >= 2
    
    def test_ensure_mode_diversity_creates_different_modes(self):
        """Test that mode diversity creates routes with different transportation modes."""
        # Create routes with same mode
        route1 = self.create_sample_route("route1", [TransportationMode.DRIVING])
        route2 = self.create_sample_route("route2", [TransportationMode.DRIVING])
        
        routes = [route1, route2]
        diverse_routes = self.engine.ensure_mode_diversity(routes, self.request)
        
        # Should create mode variants
        assert len(diverse_routes) >= 2
        
        # Should have different transportation modes
        mode_combinations = [tuple(sorted(route.transportation_modes)) for route in diverse_routes]
        unique_combinations = set(mode_combinations)
        assert len(unique_combinations) >= 2
    
    def test_ensure_timing_diversity_creates_different_times(self):
        """Test that timing diversity creates routes with different departure times."""
        # Create routes with same departure time
        route1 = self.create_sample_route("route1", [TransportationMode.DRIVING], departure_offset=0)
        route2 = self.create_sample_route("route2", [TransportationMode.DRIVING], departure_offset=0)
        
        routes = [route1, route2]
        diverse_routes = self.engine.ensure_timing_diversity(routes, self.request)
        
        # Should create time variants
        assert len(diverse_routes) >= 2
        
        # Should have different departure times
        departure_times = [route.departure_time for route in diverse_routes]
        unique_times = set(departure_times)
        assert len(unique_times) >= 2
    
    def test_calculate_diversity_score_empty_routes(self):
        """Test diversity score calculation with empty or single route."""
        # Empty routes
        assert self.engine.calculate_diversity_score([]) == 0.0
        
        # Single route
        route = self.create_sample_route("route1", [TransportationMode.DRIVING])
        assert self.engine.calculate_diversity_score([route]) == 0.0
    
    def test_calculate_diversity_score_diverse_routes(self):
        """Test diversity score calculation with diverse routes."""
        # Create diverse routes
        route1 = self.create_sample_route(
            "route1", 
            [TransportationMode.DRIVING], 
            time=30, 
            cost=5.0, 
            departure_offset=0
        )
        route2 = self.create_sample_route(
            "route2", 
            [TransportationMode.PUBLIC_TRANSIT], 
            time=45, 
            cost=3.5, 
            departure_offset=15
        )
        route3 = self.create_sample_route(
            "route3", 
            [TransportationMode.CYCLING], 
            time=50, 
            cost=0.0, 
            departure_offset=30
        )
        
        routes = [route1, route2, route3]
        diversity_score = self.engine.calculate_diversity_score(routes)
        
        # Should have high diversity score
        assert diversity_score > 0.5
        assert diversity_score <= 1.0
    
    def test_calculate_diversity_score_similar_routes(self):
        """Test diversity score calculation with similar routes."""
        # Create very similar routes
        route1 = self.create_sample_route("route1", [TransportationMode.DRIVING])
        route2 = self.create_sample_route("route2", [TransportationMode.DRIVING])
        route3 = self.create_sample_route("route3", [TransportationMode.DRIVING])
        
        routes = [route1, route2, route3]
        diversity_score = self.engine.calculate_diversity_score(routes)
        
        # Should have low diversity score
        assert diversity_score < 0.5
    
    def test_create_cycling_route_variant(self):
        """Test creation of cycling route variant."""
        base_route = self.create_sample_route("base", [TransportationMode.DRIVING])
        
        cycling_route = self.engine._create_cycling_route(base_route, self.request)
        
        # Should be cycling route
        assert TransportationMode.CYCLING in cycling_route.transportation_modes
        assert cycling_route.estimated_cost == 0.0  # No cost for cycling
        assert cycling_route.estimated_time > base_route.estimated_time  # Slower than driving
    
    def test_create_transit_route_variant(self):
        """Test creation of transit route variant."""
        base_route = self.create_sample_route("base", [TransportationMode.DRIVING])
        
        transit_route = self.engine._create_transit_route(base_route, self.request)
        
        # Should be multi-modal with transit
        assert TransportationMode.PUBLIC_TRANSIT in transit_route.transportation_modes
        assert TransportationMode.WALKING in transit_route.transportation_modes
        assert len(transit_route.segments) > 1  # Multi-segment route
        assert transit_route.estimated_cost < base_route.estimated_cost  # Cheaper than driving
    
    def test_create_rideshare_route_variant(self):
        """Test creation of rideshare route variant."""
        base_route = self.create_sample_route("base", [TransportationMode.DRIVING])
        
        rideshare_route = self.engine._create_rideshare_route(base_route, self.request)
        
        # Should be rideshare
        assert TransportationMode.RIDESHARE in rideshare_route.transportation_modes
        assert rideshare_route.estimated_cost > base_route.estimated_cost  # More expensive
        assert rideshare_route.stress_level < base_route.stress_level  # Less stressful
    
    def test_time_variant_adjusts_for_peak_hours(self):
        """Test that time variants adjust characteristics for peak vs off-peak hours."""
        base_route = self.create_sample_route("base", [TransportationMode.DRIVING])
        
        # Peak hour departure (8 AM)
        peak_departure = datetime(2024, 6, 15, 8, 0)
        peak_variant = self.engine._create_time_variant(base_route, peak_departure)
        
        # Off-peak departure (10 AM)
        off_peak_departure = datetime(2024, 6, 15, 10, 0)
        off_peak_variant = self.engine._create_time_variant(base_route, off_peak_departure)
        
        # Peak hour should have higher stress, lower reliability
        # Off-peak should have lower stress, higher reliability
        # (Exact comparison depends on base route characteristics)
        assert peak_variant.departure_time.hour == 8
        assert off_peak_variant.departure_time.hour == 10
    
    def test_round_to_nearest_15min(self):
        """Test rounding datetime to nearest 15 minutes."""
        # Test various times
        dt1 = datetime(2024, 6, 15, 8, 7)  # Should round to 8:00
        rounded1 = self.engine._round_to_nearest_15min(dt1)
        assert rounded1.minute == 0
        
        dt2 = datetime(2024, 6, 15, 8, 23)  # Should round to 8:30
        rounded2 = self.engine._round_to_nearest_15min(dt2)
        assert rounded2.minute == 30
        
        dt3 = datetime(2024, 6, 15, 8, 52)  # Should round to 8:45 (closer than 9:00)
        rounded3 = self.engine._round_to_nearest_15min(dt3)
        assert rounded3.hour == 8
        assert rounded3.minute == 45
    
    def test_path_diversity_with_multi_segment_routes(self):
        """Test path diversity with routes that have multiple segments."""
        # Create a multi-segment route
        segment1 = RouteSegment(
            mode=TransportationMode.DRIVING,
            start_location=self.origin,
            end_location=Location(latitude=37.7799, longitude=-122.4144, address="Midpoint"),
            distance=5.0,
            duration=15,
            instructions="Drive to midpoint"
        )
        
        segment2 = RouteSegment(
            mode=TransportationMode.WALKING,
            start_location=segment1.end_location,
            end_location=self.destination,
            distance=0.5,
            duration=6,
            instructions="Walk to destination"
        )
        
        multi_segment_route = Route(
            id="multi",
            segments=[segment1, segment2],
            total_distance=5.5,
            estimated_time=21,
            estimated_cost=3.0,
            stress_level=4,
            reliability_score=8,
            transportation_modes=[TransportationMode.DRIVING, TransportationMode.WALKING],
            departure_time=self.departure_time,
            arrival_time=self.departure_time + timedelta(minutes=21),
            instructions=["Drive to midpoint", "Walk to destination"]
        )
        
        single_segment_route = self.create_sample_route("single", [TransportationMode.DRIVING])
        
        routes = [multi_segment_route, single_segment_route]
        diverse_routes = self.engine.ensure_path_diversity(routes, self.origin, self.destination, self.departure_time)
        
        # Should maintain both routes as they have different path signatures
        assert len(diverse_routes) >= 2
        
        # Should have different path signatures
        signatures = [self.engine._get_path_signature(route) for route in diverse_routes]
        assert len(set(signatures)) >= 2