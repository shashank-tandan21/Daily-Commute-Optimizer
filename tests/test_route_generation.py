"""Tests for Route Generation Service."""

import pytest
from datetime import datetime, timedelta
from commute_optimizer.services.route_generation import (
    RouteGenerationService, RouteRequest, RouteType
)
from commute_optimizer.models import Location, TransportationMode


class TestRouteGenerationService:
    """Tests for RouteGenerationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = RouteGenerationService()
        
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
        
        self.departure_time = datetime(2024, 6, 15, 8, 0)  # 8 AM
    
    def test_generate_routes_returns_multiple_options(self):
        """Test that generate_routes returns 2-3 route options."""
        request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time
        )
        
        routes = self.service.generate_routes(request)
        
        # Should return 2-3 routes
        assert 2 <= len(routes) <= 3
        
        # All routes should be valid
        for route in routes:
            assert route.id is not None
            assert len(route.segments) > 0
            assert route.total_distance > 0
            assert route.estimated_time > 0
            assert route.arrival_time > route.departure_time
    
    def test_generate_routes_creates_diverse_options(self):
        """Test that generated routes are diverse."""
        request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time
        )
        
        routes = self.service.generate_routes(request)
        
        # Routes should have different characteristics
        transportation_modes = [set(route.transportation_modes) for route in routes]
        
        # Should have at least some diversity in transportation modes
        unique_mode_combinations = set(tuple(sorted(modes)) for modes in transportation_modes)
        assert len(unique_mode_combinations) >= 2
    
    def test_validate_route_viability_valid_route(self):
        """Test route validation with a valid route."""
        request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time
        )
        
        routes = self.service.generate_routes(request)
        valid_route = routes[0]
        
        # Should validate as viable
        assert self.service.validate_route_viability(valid_route, request) is True
    
    def test_validate_route_viability_invalid_route(self):
        """Test route validation with invalid routes."""
        request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time
        )
        
        # Create route with no segments
        from commute_optimizer.models import Route
        invalid_route = Route(
            id="invalid",
            segments=[],  # No segments - invalid
            total_distance=10.0,
            estimated_time=30,
            estimated_cost=5.0,
            stress_level=5,
            reliability_score=7,
            transportation_modes=[TransportationMode.DRIVING],
            departure_time=self.departure_time,
            arrival_time=self.departure_time + timedelta(minutes=30),
            instructions=[]
        )
        
        # Should not validate
        assert self.service.validate_route_viability(invalid_route, request) is False
    
    def test_diversify_routes_ensures_variety(self):
        """Test that diversify_routes creates variety."""
        request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time
        )
        
        # Generate base routes
        base_routes = self.service._generate_base_routes(request)
        
        # Diversify them
        diverse_routes = self.service.diversify_routes(base_routes, request)
        
        # Should have diverse characteristics
        characteristics = [
            self.service._get_route_characteristics(route) 
            for route in diverse_routes
        ]
        
        # All characteristics should be unique
        assert len(set(characteristics)) == len(characteristics)
    
    def test_route_request_defaults(self):
        """Test RouteRequest default values."""
        request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time
        )
        
        # Should have default values
        assert request.max_walking_distance == 2.0
        assert request.preferred_modes == list(TransportationMode)
        assert request.avoided_features == []
    
    def test_generate_routes_respects_walking_distance_limit(self):
        """Test that routes respect walking distance limits."""
        request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time,
            max_walking_distance=0.5  # Very short walking distance
        )
        
        routes = self.service.generate_routes(request)
        
        # All routes should respect walking distance limit
        for route in routes:
            total_walking = sum(
                seg.distance for seg in route.segments 
                if seg.mode == TransportationMode.WALKING
            )
            assert total_walking <= request.max_walking_distance
    
    def test_routes_connect_origin_to_destination(self):
        """Test that all routes properly connect origin to destination."""
        request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time
        )
        
        routes = self.service.generate_routes(request)
        
        for route in routes:
            # First segment should start at origin
            first_segment = route.segments[0]
            assert self.service._locations_match(first_segment.start_location, self.origin)
            
            # Last segment should end at destination
            last_segment = route.segments[-1]
            assert self.service._locations_match(last_segment.end_location, self.destination)
    
    def test_route_time_consistency(self):
        """Test that route times are consistent."""
        request = RouteRequest(
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure_time
        )
        
        routes = self.service.generate_routes(request)
        
        for route in routes:
            # Arrival should be after departure
            assert route.arrival_time > route.departure_time
            
            # Time difference should match estimated time
            actual_duration = (route.arrival_time - route.departure_time).total_seconds() / 60
            assert abs(actual_duration - route.estimated_time) <= 1  # 1 minute tolerance
            
            # Segment durations should roughly match total time
            total_segment_time = sum(seg.duration for seg in route.segments)
            assert abs(total_segment_time - route.estimated_time) <= 5  # 5 minute tolerance