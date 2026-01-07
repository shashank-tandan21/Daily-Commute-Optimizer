"""Route Generation Service for creating multiple diverse route options."""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from commute_optimizer.models import (
    Route, RouteSegment, Location, TransportationMode
)
from commute_optimizer.config import settings


class RouteType(str, Enum):
    """Types of routes for diversity."""
    FASTEST = "fastest"
    CHEAPEST = "cheapest"
    MOST_RELIABLE = "most_reliable"
    LEAST_STRESSFUL = "least_stressful"
    BALANCED = "balanced"


@dataclass
class RouteRequest:
    """Request for route generation."""
    origin: Location
    destination: Location
    departure_time: datetime
    max_walking_distance: float = 2.0
    preferred_modes: List[TransportationMode] = None
    avoided_features: List[str] = None

    def __post_init__(self):
        if self.preferred_modes is None:
            self.preferred_modes = list(TransportationMode)
        if self.avoided_features is None:
            self.avoided_features = []


class RouteGenerationService:
    """Service for generating multiple diverse route options."""
    
    def __init__(self):
        """Initialize the route generation service."""
        self.max_routes = settings.max_routes_per_request
    
    def generate_routes(
        self, 
        request: RouteRequest
    ) -> List[Route]:
        """
        Generate multiple route options for the given request.
        
        Args:
            request: RouteRequest containing origin, destination, and preferences
            
        Returns:
            List of 2-3 diverse route options
            
        Validates: Requirements 1.1, 1.2, 1.3
        """
        # Generate base routes using different strategies
        base_routes = self._generate_base_routes(request)
        
        # Ensure route diversity using dedicated diversity engine
        diverse_routes = self.diversify_routes(base_routes, request)
        
        # Validate all routes are viable
        viable_routes = []
        for route in diverse_routes:
            if self.validate_route_viability(route, request):
                viable_routes.append(route)
        
        # Ensure we have at least 2 routes, up to max_routes
        if len(viable_routes) < 2:
            # Generate additional routes if needed
            additional_routes = self._generate_fallback_routes(request, viable_routes)
            viable_routes.extend(additional_routes)
        
        # Limit to max_routes
        return viable_routes[:self.max_routes]
    
    def diversify_routes(
        self, 
        routes: List[Route], 
        request: RouteRequest
    ) -> List[Route]:
        """
        Ensure route diversity across path, transport mode, and timing.
        
        Args:
            routes: List of base routes to diversify
            request: Original route request
            
        Returns:
            List of diversified routes
            
        Validates: Requirements 1.2
        """
        if not routes:
            return routes
        
        # Apply comprehensive diversity algorithms
        diverse_routes = self._ensure_path_diversity(routes, request)
        diverse_routes = self._ensure_mode_diversity(diverse_routes, request)
        diverse_routes = self._ensure_timing_diversity(diverse_routes, request)
        
        return diverse_routes
    
    def _ensure_path_diversity(self, routes: List[Route], request: RouteRequest) -> List[Route]:
        """
        Ensure path diversity by creating routes with different geographical paths.
        
        Creates routes that use different geographical paths between the same origin and destination.
        This includes highway vs surface streets, direct vs scenic routes, and routes with different
        intermediate waypoints.
        
        Args:
            routes: List of existing routes
            request: Original route request
            
        Returns:
            List of routes with diverse geographical paths
        """
        diverse_routes = []
        path_signatures = set()
        
        # First, preserve all existing routes that have unique path signatures
        for route in routes:
            path_signature = self._get_path_signature(route)
            
            if path_signature not in path_signatures:
                diverse_routes.append(route)
                path_signatures.add(path_signature)
        
        # Only create path variants if we have fewer than 3 routes
        # and avoid replacing existing diverse routes
        while len(diverse_routes) < min(3, len(routes) + 1):
            base_route = routes[0] if routes else diverse_routes[0]
            variant = self._create_alternative_path_variant(base_route, request, path_signatures)
            if variant:
                variant_signature = self._get_path_signature(variant)
                if variant_signature not in path_signatures:
                    diverse_routes.append(variant)
                    path_signatures.add(variant_signature)
                else:
                    break
            else:
                break
        
        return diverse_routes
    
    def _ensure_mode_diversity(self, routes: List[Route], request: RouteRequest) -> List[Route]:
        """
        Ensure transportation mode diversity.
        
        Creates routes that use different transportation methods including:
        - Single-mode routes (driving only, cycling only, transit only)
        - Multi-modal routes (drive + walk, transit + walk)
        - Alternative modes (rideshare, cycling)
        
        Args:
            routes: List of existing routes
            request: Original route request
            
        Returns:
            List of routes with diverse transportation modes
        """
        diverse_routes = []
        mode_combinations = set()
        
        # First, add existing routes that have unique mode combinations
        for route in routes:
            mode_combo = tuple(sorted(route.transportation_modes))
            
            if mode_combo not in mode_combinations:
                diverse_routes.append(route)
                mode_combinations.add(mode_combo)
        
        # Force creation of different transportation modes if we don't have enough diversity
        target_modes = [
            [TransportationMode.DRIVING],
            [TransportationMode.PUBLIC_TRANSIT, TransportationMode.WALKING],
            [TransportationMode.CYCLING],
            [TransportationMode.RIDESHARE],
            [TransportationMode.DRIVING, TransportationMode.WALKING]
        ]
        
        for target_mode_set in target_modes:
            if len(diverse_routes) >= 3:
                break
                
            mode_combo = tuple(sorted(target_mode_set))
            if mode_combo not in mode_combinations:
                # Always create the variant regardless of preferences for diversity
                base_route = diverse_routes[0] if diverse_routes else routes[0]
                variant = self._create_mode_variant_for_target(
                    base_route,
                    request,
                    target_mode_set
                )
                if variant:
                    diverse_routes.append(variant)
                    mode_combinations.add(mode_combo)
        
        return diverse_routes
    
    def _ensure_timing_diversity(self, routes: List[Route], request: RouteRequest) -> List[Route]:
        """
        Ensure departure time diversity.
        
        Creates routes with different departure times to account for:
        - Peak vs off-peak traffic conditions
        - Different transit schedules
        - User flexibility in departure timing
        - Traffic pattern variations throughout the day
        
        Args:
            routes: List of existing routes
            request: Original route request
            
        Returns:
            List of routes with diverse departure times
        """
        # If we already have good diversity from previous steps, preserve it
        # and only add timing variants if we need more routes
        if len(routes) >= 2:
            # Check if routes already have different transportation modes
            mode_combinations = set(tuple(sorted(route.transportation_modes)) for route in routes)
            if len(mode_combinations) >= 2:
                # We have good mode diversity, just return the routes as-is
                # or add minimal timing variants
                return routes[:3]  # Limit to 3 routes
        
        diverse_routes = []
        departure_times = set()
        
        # First, preserve all existing routes that have unique departure times
        for route in routes:
            # Round to nearest 15 minutes for grouping
            rounded_departure = self._round_to_nearest_15min(route.departure_time)
            
            if rounded_departure not in departure_times:
                diverse_routes.append(route)
                departure_times.add(rounded_departure)
        
        # Only create time variants if we have fewer than 3 routes
        time_offsets = [-15, -30, 15, 30]  # Minutes before/after original time
        
        for offset in time_offsets:
            if len(diverse_routes) >= 3:
                break
                
            new_departure = request.departure_time + timedelta(minutes=offset)
            rounded_new_departure = self._round_to_nearest_15min(new_departure)
            
            if rounded_new_departure not in departure_times:
                # Use the first route as base, but preserve its transportation modes
                base_route = diverse_routes[0] if diverse_routes else routes[0]
                variant = self._create_time_variant(base_route, request, new_departure)
                if variant:
                    diverse_routes.append(variant)
                    departure_times.add(rounded_new_departure)
        
        return diverse_routes
    
    def _create_alternative_path_variant(
        self, 
        base_route: Route, 
        request: RouteRequest, 
        existing_signatures: Set[Tuple]
    ) -> Optional[Route]:
        """
        Create an alternative path variant that's different from existing ones.
        
        Args:
            base_route: Base route to create variant from
            request: Original route request
            existing_signatures: Set of existing path signatures to avoid duplicates
            
        Returns:
            Alternative path variant or None if no viable variant can be created
        """
        # Try creating a route with more segments (more complex path)
        if len(base_route.segments) == 1:
            # Split single segment into multiple segments for path diversity
            return self._create_multi_segment_path_variant(base_route, request)
        
        # Try creating a scenic/longer route variant
        scenic_variant = self._create_scenic_path_variant(base_route, request)
        if scenic_variant:
            scenic_signature = self._get_path_signature(scenic_variant)
            if scenic_signature not in existing_signatures:
                return scenic_variant
        
        return None
    
    def _create_multi_segment_path_variant(self, base_route: Route, request: RouteRequest) -> Route:
        """
        Create a multi-segment variant of a single-segment route.
        
        This creates path diversity by adding intermediate waypoints, simulating
        a route that takes a different geographical path.
        """
        base_segment = base_route.segments[0]
        
        # Create intermediate point for path diversity
        mid_lat = (request.origin.latitude + request.destination.latitude) / 2
        mid_lon = (request.origin.longitude + request.destination.longitude) / 2
        
        # Add slight detour for different path
        intermediate_point = Location(
            latitude=mid_lat + 0.003,  # Larger detour for more path diversity
            longitude=mid_lon + 0.003,
            address="Alternative route waypoint"
        )
        
        # First segment to intermediate point
        segment1 = RouteSegment(
            mode=base_segment.mode,
            start_location=request.origin,
            end_location=intermediate_point,
            distance=base_segment.distance * 0.65,  # Slightly longer due to detour
            duration=int(base_segment.duration * 0.65),
            instructions=f"Take alternative route to waypoint via {base_segment.mode.value}"
        )
        
        # Second segment to destination
        segment2 = RouteSegment(
            mode=base_segment.mode,
            start_location=intermediate_point,
            end_location=request.destination,
            distance=base_segment.distance * 0.45,
            duration=int(base_segment.duration * 0.45),
            instructions=f"Continue to destination via {base_segment.mode.value}"
        )
        
        new_segments = [segment1, segment2]
        total_time = sum(seg.duration for seg in new_segments)
        arrival_time = request.departure_time + timedelta(minutes=total_time)
        
        return Route(
            id=str(uuid.uuid4()),
            segments=new_segments,
            total_distance=base_route.total_distance * 1.1,  # Slightly longer
            estimated_time=total_time,
            estimated_cost=base_route.estimated_cost * 1.05,  # Slightly more expensive
            stress_level=base_route.stress_level,
            reliability_score=base_route.reliability_score,
            transportation_modes=base_route.transportation_modes.copy(),
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[seg.instructions for seg in new_segments]
        )
    
    def _create_scenic_path_variant(self, base_route: Route, request: RouteRequest) -> Route:
        """
        Create a scenic path variant that's longer but potentially less stressful.
        
        This represents taking surface streets instead of highways, or choosing
        a more pleasant route that might take longer.
        """
        # Scenic route is typically 20-40% longer but less stressful
        scenic_distance = base_route.total_distance * 1.3
        scenic_time = int(base_route.estimated_time * 1.25)
        scenic_cost = base_route.estimated_cost * 1.15
        
        # Create new segments representing scenic path
        new_segments = []
        for i, segment in enumerate(base_route.segments):
            new_segment = RouteSegment(
                mode=segment.mode,
                start_location=segment.start_location,
                end_location=segment.end_location,
                distance=segment.distance * 1.3,
                duration=int(segment.duration * 1.25),
                instructions=f"Take scenic route: {segment.instructions}"
            )
            new_segments.append(new_segment)
        
        arrival_time = request.departure_time + timedelta(minutes=scenic_time)
        
        return Route(
            id=str(uuid.uuid4()),
            segments=new_segments,
            total_distance=scenic_distance,
            estimated_time=scenic_time,
            estimated_cost=scenic_cost,
            stress_level=max(1, base_route.stress_level - 2),  # Less stressful scenic route
            reliability_score=min(10, base_route.reliability_score + 1),  # More predictable
            transportation_modes=base_route.transportation_modes.copy(),
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[seg.instructions for seg in new_segments]
        )
        """Get a signature representing the geographical path of a route."""
        return (
            len(route.segments),
            round(route.total_distance, 1),
            tuple(seg.mode for seg in route.segments)
        )
    
    def _get_route_characteristics(self, route: Route) -> Tuple:
        """Get characteristic signature of a route for diversity checking."""
        return (
            tuple(sorted(route.transportation_modes)),  # Transportation modes
            round(route.estimated_time / 10) * 10,  # Time bucket (10-minute intervals)
            round(route.estimated_cost, 1),  # Cost rounded to nearest 0.1
            route.stress_level,  # Stress level
            len(route.segments)  # Number of segments (complexity)
        )
    
    def _get_path_signature(self, route: Route) -> Tuple:
        """
        Get a signature representing the geographical path of a route.
        
        This signature is used to identify routes that take similar geographical paths,
        helping ensure path diversity by avoiding duplicate routes.
        
        Args:
            route: Route to generate signature for
            
        Returns:
            Tuple representing the route's path characteristics
        """
        return (
            len(route.segments),
            round(route.total_distance, 1),
            tuple(seg.mode for seg in route.segments),
            round(route.estimated_time / 10) * 10  # Time bucket for grouping
        )
    
    def _round_to_nearest_15min(self, dt: datetime) -> datetime:
        """Round datetime to nearest 15 minutes."""
        minutes = dt.minute
        rounded_minutes = round(minutes / 15) * 15
        
        if rounded_minutes == 60:
            return dt.replace(hour=dt.hour + 1, minute=0, second=0, microsecond=0)
        else:
            return dt.replace(minute=rounded_minutes, second=0, microsecond=0)
    
    def _create_mode_variant_for_target(
        self, 
        base_route: Route, 
        request: RouteRequest, 
        target_modes: List[TransportationMode]
    ) -> Optional[Route]:
        """Create a variant using specific transportation modes."""
        if TransportationMode.CYCLING in target_modes:
            return self._create_cycling_variant(base_route, request)
        elif TransportationMode.PUBLIC_TRANSIT in target_modes:
            return self._create_transit_route(request, str(uuid.uuid4()))
        elif TransportationMode.RIDESHARE in target_modes:
            return self._create_rideshare_variant(base_route, request)
        elif TransportationMode.DRIVING in target_modes and TransportationMode.WALKING in target_modes:
            return self._create_mixed_route(request, str(uuid.uuid4()))
        elif TransportationMode.DRIVING in target_modes:
            return self._create_driving_route(request, str(uuid.uuid4()))
        
        return None
    
    def _create_rideshare_variant(self, base_route: Route, request: RouteRequest) -> Route:
        """Create a rideshare variant."""
        rideshare_time = int(base_route.estimated_time * 1.1)  # Slightly longer due to pickup
        rideshare_cost = base_route.total_distance * 1.5  # More expensive than driving
        
        rideshare_segment = RouteSegment(
            mode=TransportationMode.RIDESHARE,
            start_location=request.origin,
            end_location=request.destination,
            distance=base_route.total_distance,
            duration=rideshare_time,
            instructions=f"Take rideshare from {request.origin.address} to {request.destination.address}"
        )
        
        arrival_time = request.departure_time + timedelta(minutes=rideshare_time)
        
        return Route(
            id=str(uuid.uuid4()),
            segments=[rideshare_segment],
            total_distance=base_route.total_distance,
            estimated_time=rideshare_time,
            estimated_cost=rideshare_cost,
            stress_level=2,  # Very low stress
            reliability_score=8,  # Generally reliable
            transportation_modes=[TransportationMode.RIDESHARE],
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[rideshare_segment.instructions]
        )
    
    def validate_route_viability(
        self, 
        route: Route, 
        request: RouteRequest
    ) -> bool:
        """
        Validate that a route is viable and realistic.
        
        Args:
            route: Route to validate
            request: Original route request
            
        Returns:
            True if route is viable, False otherwise
            
        Validates: Requirements 1.3
        """
        # Check basic route validity
        if not route.segments:
            return False
        
        # Check that route connects origin to destination
        first_segment = route.segments[0]
        last_segment = route.segments[-1]
        
        if not self._locations_match(first_segment.start_location, request.origin):
            return False
        
        if not self._locations_match(last_segment.end_location, request.destination):
            return False
        
        # Check segment connectivity
        for i in range(len(route.segments) - 1):
            current_end = route.segments[i].end_location
            next_start = route.segments[i + 1].start_location
            if not self._locations_match(current_end, next_start):
                return False
        
        # Check walking distance constraints
        total_walking_distance = sum(
            seg.distance for seg in route.segments 
            if seg.mode == TransportationMode.WALKING
        )
        if total_walking_distance > request.max_walking_distance:
            return False
        
        # Check time consistency
        if route.arrival_time <= route.departure_time:
            return False
        
        # Check that estimated time matches segment durations
        total_segment_time = sum(seg.duration for seg in route.segments)
        if abs(total_segment_time - route.estimated_time) > 5:  # 5 minute tolerance
            return False
        
        # Check reasonable bounds
        if route.estimated_time > 600:  # More than 10 hours is unrealistic
            return False
        
        if route.total_distance > 1000:  # More than 1000km is unrealistic for daily commute
            return False
        
        return True
    
    def _generate_base_routes(self, request: RouteRequest) -> List[Route]:
        """Generate base routes using different optimization strategies."""
        routes = []
        
        # Generate different types of routes
        route_types = [RouteType.FASTEST, RouteType.CHEAPEST, RouteType.MOST_RELIABLE]
        
        for route_type in route_types:
            route = self._create_route_for_type(request, route_type)
            if route:
                routes.append(route)
        
        return routes
    
    def _create_route_for_type(
        self, 
        request: RouteRequest, 
        route_type: RouteType
    ) -> Optional[Route]:
        """Create a route optimized for a specific type."""
        # This is a mock implementation - in real system would call external APIs
        
        route_id = str(uuid.uuid4())
        
        # Create different route characteristics based on type
        if route_type == RouteType.FASTEST:
            return self._create_driving_route(request, route_id, optimize_for="time")
        elif route_type == RouteType.CHEAPEST:
            return self._create_transit_route(request, route_id, optimize_for="cost")
        elif route_type == RouteType.MOST_RELIABLE:
            return self._create_mixed_route(request, route_id, optimize_for="reliability")
        else:
            return self._create_driving_route(request, route_id, optimize_for="balanced")
    
    def _create_driving_route(
        self, 
        request: RouteRequest, 
        route_id: str, 
        optimize_for: str = "time"
    ) -> Route:
        """Create a driving-based route."""
        # Mock driving route - in real system would use mapping APIs
        
        # Calculate rough distance (simplified)
        distance = self._calculate_distance(request.origin, request.destination)
        
        # Adjust based on optimization
        if optimize_for == "time":
            # Faster route, might use highways
            estimated_time = max(15, int(distance * 2))  # ~30km/h average in city
            cost = distance * 0.15  # Higher fuel cost for faster route
            stress_level = 6  # Higher stress due to traffic
            reliability = 7
        else:
            # More balanced route
            estimated_time = max(20, int(distance * 2.5))
            cost = distance * 0.12
            stress_level = 4
            reliability = 8
        
        # Create route segment
        segment = RouteSegment(
            mode=TransportationMode.DRIVING,
            start_location=request.origin,
            end_location=request.destination,
            distance=distance,
            duration=estimated_time,
            instructions=f"Drive from {request.origin.address} to {request.destination.address}"
        )
        
        arrival_time = request.departure_time + timedelta(minutes=estimated_time)
        
        return Route(
            id=route_id,
            segments=[segment],
            total_distance=distance,
            estimated_time=estimated_time,
            estimated_cost=cost,
            stress_level=stress_level,
            reliability_score=reliability,
            transportation_modes=[TransportationMode.DRIVING],
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[segment.instructions]
        )
    
    def _create_transit_route(
        self, 
        request: RouteRequest, 
        route_id: str, 
        optimize_for: str = "cost"
    ) -> Route:
        """Create a public transit route."""
        # Mock transit route
        
        distance = self._calculate_distance(request.origin, request.destination)
        
        # Transit is typically slower but cheaper
        estimated_time = max(25, int(distance * 3.5))  # Includes waiting time
        cost = 3.50  # Fixed transit fare
        stress_level = 3  # Lower stress, no driving
        reliability = 6  # Subject to delays
        
        # Create walking segment to transit
        walk_to_transit = RouteSegment(
            mode=TransportationMode.WALKING,
            start_location=request.origin,
            end_location=Location(
                latitude=request.origin.latitude + 0.001,
                longitude=request.origin.longitude + 0.001,
                address="Transit Station"
            ),
            distance=0.3,
            duration=4,
            instructions="Walk to transit station"
        )
        
        # Transit segment
        transit_segment = RouteSegment(
            mode=TransportationMode.PUBLIC_TRANSIT,
            start_location=walk_to_transit.end_location,
            end_location=Location(
                latitude=request.destination.latitude - 0.001,
                longitude=request.destination.longitude - 0.001,
                address="Destination Transit Station"
            ),
            distance=distance - 0.6,
            duration=estimated_time - 8,
            instructions="Take bus/train to destination area"
        )
        
        # Walking segment from transit
        walk_from_transit = RouteSegment(
            mode=TransportationMode.WALKING,
            start_location=transit_segment.end_location,
            end_location=request.destination,
            distance=0.3,
            duration=4,
            instructions="Walk from transit station to destination"
        )
        
        segments = [walk_to_transit, transit_segment, walk_from_transit]
        arrival_time = request.departure_time + timedelta(minutes=estimated_time)
        
        return Route(
            id=route_id,
            segments=segments,
            total_distance=distance,
            estimated_time=estimated_time,
            estimated_cost=cost,
            stress_level=stress_level,
            reliability_score=reliability,
            transportation_modes=[TransportationMode.WALKING, TransportationMode.PUBLIC_TRANSIT],
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[seg.instructions for seg in segments]
        )
    
    def _create_mixed_route(
        self, 
        request: RouteRequest, 
        route_id: str, 
        optimize_for: str = "reliability"
    ) -> Route:
        """Create a mixed-mode route (e.g., drive + walk)."""
        # Mock mixed route - drive most of the way, walk the rest
        
        distance = self._calculate_distance(request.origin, request.destination)
        
        # More reliable but potentially longer
        estimated_time = max(20, int(distance * 2.2))
        cost = distance * 0.10  # Lower fuel cost, some walking
        stress_level = 4  # Moderate stress
        reliability = 9  # Very reliable
        
        # Drive segment (80% of distance)
        drive_distance = distance * 0.8
        drive_segment = RouteSegment(
            mode=TransportationMode.DRIVING,
            start_location=request.origin,
            end_location=Location(
                latitude=request.origin.latitude + (request.destination.latitude - request.origin.latitude) * 0.8,
                longitude=request.origin.longitude + (request.destination.longitude - request.origin.longitude) * 0.8,
                address="Parking area near destination"
            ),
            distance=drive_distance,
            duration=int(estimated_time * 0.7),
            instructions="Drive to parking area near destination"
        )
        
        # Walk segment (20% of distance)
        walk_distance = distance * 0.2
        walk_segment = RouteSegment(
            mode=TransportationMode.WALKING,
            start_location=drive_segment.end_location,
            end_location=request.destination,
            distance=walk_distance,
            duration=int(estimated_time * 0.3),
            instructions="Walk from parking to destination"
        )
        
        segments = [drive_segment, walk_segment]
        arrival_time = request.departure_time + timedelta(minutes=estimated_time)
        
        return Route(
            id=route_id,
            segments=segments,
            total_distance=distance,
            estimated_time=estimated_time,
            estimated_cost=cost,
            stress_level=stress_level,
            reliability_score=reliability,
            transportation_modes=[TransportationMode.DRIVING, TransportationMode.WALKING],
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[seg.instructions for seg in segments]
        )
    
    def _generate_fallback_routes(
        self, 
        request: RouteRequest, 
        existing_routes: List[Route]
    ) -> List[Route]:
        """Generate additional routes if we don't have enough viable options."""
        fallback_routes = []
        
        # If we have no routes, create a basic driving route
        if not existing_routes:
            basic_route = self._create_driving_route(request, str(uuid.uuid4()))
            if self.validate_route_viability(basic_route, request):
                fallback_routes.append(basic_route)
        
        # If we only have one route, create a variant
        if len(existing_routes) + len(fallback_routes) < 2:
            base_route = existing_routes[0] if existing_routes else fallback_routes[0]
            # Create a time variant with 15 minutes earlier departure
            new_departure = request.departure_time + timedelta(minutes=-15)
            variant = self._create_time_variant(base_route, request, new_departure)
            if variant and self.validate_route_viability(variant, request):
                fallback_routes.append(variant)
        
        return fallback_routes
    
    def _create_route_variant(
        self, 
        base_route: Route, 
        request: RouteRequest, 
        used_characteristics: Set[Tuple]
    ) -> Optional[Route]:
        """Create a variant of an existing route."""
        # Try different variations
        variants = [
            self._create_time_variant(base_route, request),
            self._create_mode_variant(base_route, request),
            self._create_path_variant(base_route, request)
        ]
        
        for variant in variants:
            if variant:
                characteristic = self._get_route_characteristics(variant)
                if not self._is_too_similar(characteristic, used_characteristics):
                    return variant
        
        return None
    
    def _create_time_variant(self, base_route: Route, request: RouteRequest, new_departure: datetime) -> Optional[Route]:
        """Create a time-shifted variant of a route."""
        new_arrival = new_departure + timedelta(minutes=base_route.estimated_time)
        
        # Adjust characteristics for different time
        new_stress = max(1, base_route.stress_level - 1)  # Less stress with earlier departure
        new_reliability = min(10, base_route.reliability_score + 1)  # More reliable
        
        new_route = Route(
            id=str(uuid.uuid4()),
            segments=base_route.segments.copy(),
            total_distance=base_route.total_distance,
            estimated_time=base_route.estimated_time,
            estimated_cost=base_route.estimated_cost,
            stress_level=new_stress,
            reliability_score=new_reliability,
            transportation_modes=base_route.transportation_modes.copy(),
            departure_time=new_departure,
            arrival_time=new_arrival,
            instructions=base_route.instructions.copy()
        )
        
        return new_route
    
    def _create_mode_variant(self, base_route: Route, request: RouteRequest) -> Optional[Route]:
        """Create a variant with different transportation mode."""
        # If base route is driving, create cycling variant
        if TransportationMode.DRIVING in base_route.transportation_modes:
            return self._create_cycling_variant(base_route, request)
        return None
    
    def _create_cycling_variant(self, base_route: Route, request: RouteRequest) -> Route:
        """Create a cycling variant of a driving route."""
        # Cycling is slower but cheaper and more environmentally friendly
        cycling_time = int(base_route.estimated_time * 1.5)  # 50% longer
        
        cycling_segment = RouteSegment(
            mode=TransportationMode.CYCLING,
            start_location=request.origin,
            end_location=request.destination,
            distance=base_route.total_distance,
            duration=cycling_time,
            instructions=f"Cycle from {request.origin.address} to {request.destination.address}"
        )
        
        arrival_time = request.departure_time + timedelta(minutes=cycling_time)
        
        return Route(
            id=str(uuid.uuid4()),
            segments=[cycling_segment],
            total_distance=base_route.total_distance,
            estimated_time=cycling_time,
            estimated_cost=0.0,  # No cost for cycling
            stress_level=5,  # Moderate stress from physical exertion
            reliability_score=8,  # Weather dependent but generally reliable
            transportation_modes=[TransportationMode.CYCLING],
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[cycling_segment.instructions]
        )
    
    def _create_path_variant(self, base_route: Route, request: RouteRequest) -> Optional[Route]:
        """Create a variant with different path (scenic route)."""
        # Create a longer but potentially less stressful route
        longer_distance = base_route.total_distance * 1.2
        longer_time = int(base_route.estimated_time * 1.15)
        
        # Assume same mode as base route
        main_mode = base_route.transportation_modes[0]
        
        segment = RouteSegment(
            mode=main_mode,
            start_location=request.origin,
            end_location=request.destination,
            distance=longer_distance,
            duration=longer_time,
            instructions=f"Take scenic route via {main_mode.value}"
        )
        
        arrival_time = request.departure_time + timedelta(minutes=longer_time)
        
        return Route(
            id=str(uuid.uuid4()),
            segments=[segment],
            total_distance=longer_distance,
            estimated_time=longer_time,
            estimated_cost=base_route.estimated_cost * 1.1,  # Slightly higher cost
            stress_level=max(1, base_route.stress_level - 2),  # Less stressful scenic route
            reliability_score=base_route.reliability_score,
            transportation_modes=base_route.transportation_modes.copy(),
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[segment.instructions]
        )
    
    def _get_route_characteristics(self, route: Route) -> Tuple:
        """Get characteristic signature of a route for diversity checking."""
        return (
            tuple(sorted(route.transportation_modes)),  # Transportation modes
            round(route.estimated_time / 10) * 10,  # Time bucket (10-minute intervals)
            round(route.estimated_cost, 1),  # Cost rounded to nearest 0.1
            route.stress_level,  # Stress level
            len(route.segments)  # Number of segments (complexity)
        )
    
    def _is_too_similar(
        self, 
        characteristic: Tuple, 
        used_characteristics: Set[Tuple]
    ) -> bool:
        """Check if a route characteristic is too similar to existing ones."""
        for used_char in used_characteristics:
            # Check if transportation modes are the same
            if characteristic[0] == used_char[0]:
                # Check if time and cost are very similar
                time_diff = abs(characteristic[1] - used_char[1])
                cost_diff = abs(characteristic[2] - used_char[2])
                
                if time_diff <= 10 and cost_diff <= 1.0:  # Very similar
                    return True
        
        return False
    
    def _calculate_distance(self, origin: Location, destination: Location) -> float:
        """Calculate approximate distance between two locations (simplified)."""
        # Simplified distance calculation - in real system would use proper geospatial calculation
        lat_diff = abs(destination.latitude - origin.latitude)
        lon_diff = abs(destination.longitude - origin.longitude)
        
        # Rough approximation: 1 degree ≈ 111 km
        distance = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111
        
        # Ensure minimum distance for realistic routes
        return max(1.0, distance)
    
    def _locations_match(self, loc1: Location, loc2: Location, tolerance: float = 0.001) -> bool:
        """Check if two locations are approximately the same."""
        lat_diff = abs(loc1.latitude - loc2.latitude)
        lon_diff = abs(loc1.longitude - loc2.longitude)
        
        return lat_diff <= tolerance and lon_diff <= tolerance