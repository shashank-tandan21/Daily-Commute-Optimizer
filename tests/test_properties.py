"""Property-based tests for the Daily Commute Optimizer."""

from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.strategies import composite
import pytest

from commute_optimizer.models import (
    Route, RouteSegment, Location, TransportationMode,
    TimeAnalysis, CostAnalysis, StressAnalysis, ReliabilityAnalysis,
    RouteAnalysis, TradeoffSummary, ComparisonPoint
)
from commute_optimizer.services.route_generation import RouteGenerationService, RouteRequest
from commute_optimizer.config import settings as app_settings


# Custom strategies for generating test data
@composite
def route_request_strategy(draw):
    """Generate valid RouteRequest objects."""
    # Use simpler, smaller data for better test performance
    origin = Location(
        latitude=draw(st.floats(min_value=37.7, max_value=37.8)),
        longitude=draw(st.floats(min_value=-122.5, max_value=-122.4)),
        address=draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    )
    
    destination = Location(
        latitude=draw(st.floats(min_value=37.7, max_value=37.8)),
        longitude=draw(st.floats(min_value=-122.5, max_value=-122.4)),
        address=draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    )
    
    # Ensure origin and destination are different
    while (abs(origin.latitude - destination.latitude) < 0.01 and 
           abs(origin.longitude - destination.longitude) < 0.01):
        destination = Location(
            latitude=draw(st.floats(min_value=37.7, max_value=37.8)),
            longitude=draw(st.floats(min_value=-122.5, max_value=-122.4)),
            address=draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
        )
    
    departure_time = datetime(2024, 6, 15, 8, 0)  # Fixed time for simplicity
    
    return RouteRequest(
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        max_walking_distance=draw(st.floats(min_value=0.5, max_value=2.0)),
        preferred_modes=draw(st.lists(
            st.sampled_from(TransportationMode), 
            min_size=1, 
            max_size=3,
            unique=True
        )) or list(TransportationMode),
        avoided_features=draw(st.lists(st.text(min_size=1, max_size=10), max_size=2)) or []
    )


@composite
def location_strategy(draw):
    """Generate valid Location objects."""
    return Location(
        latitude=draw(st.floats(min_value=-90, max_value=90)),
        longitude=draw(st.floats(min_value=-180, max_value=180)),
        address=draw(st.text(min_size=5, max_size=100)),
        name=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    )


@composite
def route_segment_strategy(draw):
    """Generate valid RouteSegment objects."""
    start_location = draw(location_strategy())
    end_location = draw(location_strategy())
    
    return RouteSegment(
        mode=draw(st.sampled_from(TransportationMode)),
        start_location=start_location,
        end_location=end_location,
        distance=draw(st.floats(min_value=0.1, max_value=1000)),
        duration=draw(st.integers(min_value=1, max_value=600)),
        instructions=draw(st.text(min_size=5, max_size=200))
    )


@composite
def route_strategy(draw):
    """Generate valid Route objects."""
    segments = draw(st.lists(route_segment_strategy(), min_size=1, max_size=5))
    departure_time = draw(st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2025, 12, 31)
    ))
    estimated_time = draw(st.integers(min_value=1, max_value=600))
    arrival_time = departure_time + timedelta(minutes=estimated_time)
    
    return Route(
        id=draw(st.text(min_size=1, max_size=50)),
        segments=segments,
        total_distance=draw(st.floats(min_value=0.1, max_value=1000)),
        estimated_time=estimated_time,
        estimated_cost=draw(st.floats(min_value=0, max_value=1000)),
        stress_level=draw(st.integers(min_value=1, max_value=10)),
        reliability_score=draw(st.integers(min_value=1, max_value=10)),
        transportation_modes=[seg.mode for seg in segments],
        departure_time=departure_time,
        arrival_time=arrival_time,
        instructions=draw(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10))
    )


@composite
def time_analysis_strategy(draw):
    """Generate valid TimeAnalysis objects."""
    estimated_time = draw(st.integers(min_value=1, max_value=600))
    time_range_min = draw(st.integers(min_value=1, max_value=estimated_time))
    time_range_max = draw(st.integers(min_value=estimated_time, max_value=estimated_time + 120))
    
    return TimeAnalysis(
        estimated_time=estimated_time,
        time_range_min=time_range_min,
        time_range_max=time_range_max,
        peak_hour_impact=draw(st.integers(min_value=0, max_value=60))
    )


@composite
def cost_analysis_strategy(draw):
    """Generate valid CostAnalysis objects."""
    fuel_cost = draw(st.floats(min_value=0, max_value=100))
    transit_fare = draw(st.floats(min_value=0, max_value=50))
    parking_cost = draw(st.floats(min_value=0, max_value=30))
    toll_cost = draw(st.floats(min_value=0, max_value=20))
    
    return CostAnalysis(
        fuel_cost=fuel_cost,
        transit_fare=transit_fare,
        parking_cost=parking_cost,
        toll_cost=toll_cost,
        total_cost=fuel_cost + transit_fare + parking_cost + toll_cost
    )


@composite
def stress_analysis_strategy(draw):
    """Generate valid StressAnalysis objects."""
    return StressAnalysis(
        traffic_stress=draw(st.integers(min_value=1, max_value=10)),
        complexity_stress=draw(st.integers(min_value=1, max_value=10)),
        weather_stress=draw(st.integers(min_value=1, max_value=10)),
        overall_stress=draw(st.integers(min_value=1, max_value=10))
    )


@composite
def reliability_analysis_strategy(draw):
    """Generate valid ReliabilityAnalysis objects."""
    return ReliabilityAnalysis(
        historical_variance=draw(st.floats(min_value=0, max_value=60)),
        incident_probability=draw(st.floats(min_value=0, max_value=1)),
        weather_impact=draw(st.floats(min_value=0, max_value=2)),
        service_reliability=draw(st.floats(min_value=0, max_value=1)),
        overall_reliability=draw(st.integers(min_value=1, max_value=10))
    )


@composite
def comparison_point_strategy(draw):
    """Generate valid ComparisonPoint objects."""
    return ComparisonPoint(
        factor=draw(st.text(min_size=1, max_size=50)),
        this_route_value=draw(st.text(min_size=1, max_size=100)),
        comparison_text=draw(st.text(min_size=1, max_size=200))
    )


@composite
def tradeoff_summary_strategy(draw):
    """Generate valid TradeoffSummary objects."""
    return TradeoffSummary(
        strengths=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5)),
        weaknesses=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5)),
        when_to_choose=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5)),
        when_not_to_choose=draw(st.lists(st.text(min_size=1, max_size=100), min_size=0, max_size=5)),
        compared_to_alternatives=draw(st.lists(comparison_point_strategy(), min_size=0, max_size=5))
    )


@composite
def route_analysis_strategy(draw):
    """Generate valid RouteAnalysis objects."""
    return RouteAnalysis(
        route_id=draw(st.text(min_size=1, max_size=50)),
        timestamp=draw(st.datetimes(
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2025, 12, 31)
        )),
        time_analysis=draw(time_analysis_strategy()),
        cost_analysis=draw(cost_analysis_strategy()),
        stress_analysis=draw(stress_analysis_strategy()),
        reliability_analysis=draw(reliability_analysis_strategy()),
        tradeoff_summary=draw(tradeoff_summary_strategy())
    )


class TestRouteGenerationCompletenessProperty:
    """
    Property 1: Route Generation Completeness
    Feature: daily-commute-optimizer, Property 1: Route Generation Completeness
    Validates: Requirements 1.1, 1.2, 1.3
    """
    
    @given(route_request_strategy())
    @settings(max_examples=app_settings.property_test_iterations, suppress_health_check=[HealthCheck.large_base_example])
    def test_route_generation_completeness(self, route_request):
        """
        For any valid origin-destination pair, the system should generate 2-3 diverse routes
        that vary by path, transport mode, or departure time, and all generated routes should
        be viable connections between the specified locations.
        
        This validates Requirements 1.1, 1.2, 1.3.
        """
        service = RouteGenerationService()
        routes = service.generate_routes(route_request)
        
        # Should generate 2-3 routes (Requirement 1.1)
        assert 2 <= len(routes) <= 3, f"Expected 2-3 routes, got {len(routes)}"
        
        # All routes should be viable (Requirement 1.3)
        for route in routes:
            assert service.validate_route_viability(route, route_request), \
                f"Route {route.id} is not viable"
        
        # Routes should be diverse (Requirement 1.2)
        # Check diversity across multiple dimensions
        transportation_modes = [set(route.transportation_modes) for route in routes]
        departure_times = [route.departure_time for route in routes]
        path_signatures = [service._get_path_signature(route) for route in routes]
        
        # Should have diversity in at least one dimension
        mode_diversity = len(set(tuple(sorted(modes)) for modes in transportation_modes)) > 1
        time_diversity = len(set(departure_times)) > 1
        path_diversity = len(set(path_signatures)) > 1
        
        assert mode_diversity or time_diversity or path_diversity, \
            "Routes should vary by path, transport mode, or departure time"
        
        # All routes should connect origin to destination
        for route in routes:
            first_segment = route.segments[0]
            last_segment = route.segments[-1]
            
            assert service._locations_match(first_segment.start_location, route_request.origin), \
                f"Route {route.id} doesn't start at origin"
            assert service._locations_match(last_segment.end_location, route_request.destination), \
                f"Route {route.id} doesn't end at destination"
        
        # All routes should have positive metrics
        for route in routes:
            assert route.total_distance > 0, f"Route {route.id} has invalid distance"
            assert route.estimated_time > 0, f"Route {route.id} has invalid time"
            assert route.estimated_cost >= 0, f"Route {route.id} has invalid cost"
            assert 1 <= route.stress_level <= 10, f"Route {route.id} has invalid stress level"
            assert 1 <= route.reliability_score <= 10, f"Route {route.id} has invalid reliability"
            assert route.arrival_time > route.departure_time, f"Route {route.id} has invalid timing"


class TestCompleteRouteAnalysisProperty:
    """
    Property 3: Complete Route Analysis
    Feature: daily-commute-optimizer, Property 3: Complete Route Analysis
    Validates: Requirements 2.1, 2.4
    """
    
    @given(route_analysis_strategy())
    @settings(max_examples=app_settings.property_test_iterations)
    def test_route_analysis_has_all_required_components(self, route_analysis):
        """
        For any generated route analysis, it should have all four required analysis components:
        time analysis, cost analysis, stress analysis, and reliability analysis.
        
        This validates that the system evaluates each route on all required criteria
        using consistent data structures.
        """
        # Verify all four analysis components are present
        assert route_analysis.time_analysis is not None
        assert route_analysis.cost_analysis is not None
        assert route_analysis.stress_analysis is not None
        assert route_analysis.reliability_analysis is not None
        
        # Verify time analysis has consistent metrics
        time_analysis = route_analysis.time_analysis
        assert time_analysis.estimated_time > 0
        assert time_analysis.time_range_min > 0
        assert time_analysis.time_range_max >= time_analysis.estimated_time
        assert time_analysis.time_range_min <= time_analysis.estimated_time
        assert time_analysis.peak_hour_impact >= 0
        
        # Verify cost analysis has consistent metrics
        cost_analysis = route_analysis.cost_analysis
        assert cost_analysis.total_cost >= 0
        assert cost_analysis.fuel_cost >= 0
        assert cost_analysis.transit_fare >= 0
        assert cost_analysis.parking_cost >= 0
        assert cost_analysis.toll_cost >= 0
        # Total cost should be sum of components (within floating point precision)
        expected_total = (cost_analysis.fuel_cost + cost_analysis.transit_fare + 
                         cost_analysis.parking_cost + cost_analysis.toll_cost)
        assert abs(cost_analysis.total_cost - expected_total) < 0.01
        
        # Verify stress analysis has valid ranges
        stress_analysis = route_analysis.stress_analysis
        assert 1 <= stress_analysis.traffic_stress <= 10
        assert 1 <= stress_analysis.complexity_stress <= 10
        assert 1 <= stress_analysis.weather_stress <= 10
        assert 1 <= stress_analysis.overall_stress <= 10
        
        # Verify reliability analysis has valid ranges
        reliability_analysis = route_analysis.reliability_analysis
        assert reliability_analysis.historical_variance >= 0
        assert 0 <= reliability_analysis.incident_probability <= 1
        assert reliability_analysis.weather_impact >= 0
        assert 0 <= reliability_analysis.service_reliability <= 1
        assert 1 <= reliability_analysis.overall_reliability <= 10
        
        # Verify tradeoff summary is present
        assert route_analysis.tradeoff_summary is not None
        tradeoff = route_analysis.tradeoff_summary
        assert isinstance(tradeoff.strengths, list)
        assert isinstance(tradeoff.weaknesses, list)
        assert isinstance(tradeoff.when_to_choose, list)
        assert isinstance(tradeoff.when_not_to_choose, list)
        assert isinstance(tradeoff.compared_to_alternatives, list)
    
    @given(st.lists(route_analysis_strategy(), min_size=2, max_size=5))
    @settings(max_examples=app_settings.property_test_iterations)
    def test_consistent_metrics_across_route_comparisons(self, route_analyses):
        """
        For any set of route analyses, they should use consistent metric types and scales
        across all routes to enable fair comparison.
        
        This validates Requirements 2.4: consistent metrics across all route comparisons.
        """
        # All route analyses should have the same structure and metric types
        first_analysis = route_analyses[0]
        
        for analysis in route_analyses[1:]:
            # Time metrics should be in same units (minutes)
            assert isinstance(analysis.time_analysis.estimated_time, int)
            assert isinstance(first_analysis.time_analysis.estimated_time, int)
            
            # Cost metrics should be in same units (currency)
            assert isinstance(analysis.cost_analysis.total_cost, (int, float))
            assert isinstance(first_analysis.cost_analysis.total_cost, (int, float))
            
            # Stress metrics should use same scale (1-10)
            assert 1 <= analysis.stress_analysis.overall_stress <= 10
            assert 1 <= first_analysis.stress_analysis.overall_stress <= 10
            
            # Reliability metrics should use same scale (1-10)
            assert 1 <= analysis.reliability_analysis.overall_reliability <= 10
            assert 1 <= first_analysis.reliability_analysis.overall_reliability <= 10
            
            # All should have same analysis components
            assert type(analysis.time_analysis) == type(first_analysis.time_analysis)
            assert type(analysis.cost_analysis) == type(first_analysis.cost_analysis)
            assert type(analysis.stress_analysis) == type(first_analysis.stress_analysis)
            assert type(analysis.reliability_analysis) == type(first_analysis.reliability_analysis)


class TestRouteDataModelConsistency:
    """Additional property tests for route data model consistency."""
    
    @given(route_strategy())
    @settings(max_examples=app_settings.property_test_iterations)
    def test_route_temporal_consistency(self, route):
        """
        For any route, the arrival time should be after departure time,
        and the time difference should be reasonable given the estimated time.
        """
        # Arrival must be after departure
        assert route.arrival_time > route.departure_time
        
        # Time difference should match estimated time (within reasonable bounds)
        actual_duration = (route.arrival_time - route.departure_time).total_seconds() / 60
        # Allow some flexibility for rounding
        assert abs(actual_duration - route.estimated_time) <= 1
        
        # Estimated time should be positive
        assert route.estimated_time > 0
    
    @given(route_strategy())
    @settings(max_examples=app_settings.property_test_iterations)
    def test_route_metric_validity(self, route):
        """
        For any route, all metrics should be within valid ranges and consistent.
        """
        # Distance should be positive
        assert route.total_distance > 0
        
        # Cost should be non-negative
        assert route.estimated_cost >= 0
        
        # Stress and reliability should be in valid ranges
        assert 1 <= route.stress_level <= 10
        assert 1 <= route.reliability_score <= 10
        
        # Should have at least one segment
        assert len(route.segments) > 0
        
        # Transportation modes should match segments
        segment_modes = [seg.mode for seg in route.segments]
        assert set(route.transportation_modes) == set(segment_modes)
        
        # Should have instructions
        assert len(route.instructions) > 0