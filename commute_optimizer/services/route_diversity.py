"""Route diversity algorithms for ensuring varied route options."""

from typing import List, Set, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid

from commute_optimizer.models import Route, RouteSegment, TransportationMode
from commute_optimizer.services.route_generation import RouteRequest


class DiversityDimension(str, Enum):
    """Dimensions along which routes can be diversified."""
    PATH = "path"
    TRANSPORTATION_MODE = "transportation_mode"
    DEPARTURE_TIME = "departure_time"
    COST_OPTIMIZATION = "cost_optimization"
    TIME_OPTIMIZATION = "time_optimization"


class RouteDiversityEngine:
    """Engine for creating diverse route options."""
    
    def __init__(self):
        """Initialize the diversity engine."""
        self.min_time_difference = 10  # Minimum 10 minutes difference
        self.min_cost_difference = 1.0  # Minimum $1 cost difference
        self.min_mode_difference = 1  # At least 1 different transportation mode
    
    def ensure_path_diversity(
        self, 
        routes: List[Route], 
        origin, 
        destination, 
        departure_time
    ) -> List[Route]:
        """
        Create path diversity by generating routes with different geographical paths.
        
        Args:
            routes: Existing routes to diversify
            origin: Origin location
            destination: Destination location  
            departure_time: Departure time
            
        Returns:
            Routes with diverse geographical paths
            
        Validates: Requirements 1.2 - path diversity
        """
        diverse_routes = []
        path_signatures = set()
        
        for route in routes:
            path_signature = self._get_path_signature(route)
            
            if path_signature not in path_signatures:
                diverse_routes.append(route)
                path_signatures.add(path_signature)
            else:
                # Create path variant
                variant = self._create_path_variant(route, origin, destination, departure_time)
                if variant:
                    variant_signature = self._get_path_signature(variant)
                    if variant_signature not in path_signatures:
                        diverse_routes.append(variant)
                        path_signatures.add(variant_signature)
        
        # If we still don't have enough path diversity, create additional variants
        while len(diverse_routes) < min(3, len(routes) + 1):
            base_route = diverse_routes[0] if diverse_routes else routes[0]
            variant = self._create_alternative_path(base_route, origin, destination, departure_time, path_signatures)
            if variant:
                diverse_routes.append(variant)
                path_signatures.add(self._get_path_signature(variant))
            else:
                break
        
        return diverse_routes
    
    def ensure_mode_diversity(
        self, 
        routes: List[Route], 
        request: RouteRequest
    ) -> List[Route]:
        """
        Create transportation mode diversity.
        
        Args:
            routes: Existing routes to diversify
            request: Original route request
            
        Returns:
            Routes with diverse transportation modes
            
        Validates: Requirements 1.2 - transport mode diversity
        """
        diverse_routes = []
        mode_combinations = set()
        
        for route in routes:
            mode_combo = tuple(sorted(route.transportation_modes))
            
            if mode_combo not in mode_combinations:
                diverse_routes.append(route)
                mode_combinations.add(mode_combo)
        
        # Create additional mode variants if needed
        target_modes = [
            [TransportationMode.DRIVING],
            [TransportationMode.PUBLIC_TRANSIT, TransportationMode.WALKING],
            [TransportationMode.CYCLING],
            [TransportationMode.DRIVING, TransportationMode.WALKING],
            [TransportationMode.RIDESHARE]
        ]
        
        for target_mode_set in target_modes:
            mode_combo = tuple(sorted(target_mode_set))
            if mode_combo not in mode_combinations and len(diverse_routes) < 3:
                variant = self._create_mode_variant(
                    diverse_routes[0] if diverse_routes else routes[0],
                    request,
                    target_mode_set
                )
                if variant:
                    diverse_routes.append(variant)
                    mode_combinations.add(mode_combo)
        
        return diverse_routes
    
    def ensure_timing_diversity(
        self, 
        routes: List[Route], 
        request: RouteRequest
    ) -> List[Route]:
        """
        Create departure time diversity.
        
        Args:
            routes: Existing routes to diversify
            request: Original route request
            
        Returns:
            Routes with diverse departure times
            
        Validates: Requirements 1.2 - departure time diversity
        """
        diverse_routes = []
        departure_times = set()
        
        for route in routes:
            # Round to nearest 15 minutes for grouping
            rounded_departure = self._round_to_nearest_15min(route.departure_time)
            
            if rounded_departure not in departure_times:
                diverse_routes.append(route)
                departure_times.add(rounded_departure)
        
        # Create time variants
        time_offsets = [-15, -30, 15, 30]  # Minutes before/after original time
        
        for offset in time_offsets:
            if len(diverse_routes) >= 3:
                break
                
            new_departure = request.departure_time + timedelta(minutes=offset)
            rounded_new_departure = self._round_to_nearest_15min(new_departure)
            
            if rounded_new_departure not in departure_times:
                base_route = diverse_routes[0] if diverse_routes else routes[0]
                variant = self._create_time_variant(base_route, new_departure)
                if variant:
                    diverse_routes.append(variant)
                    departure_times.add(rounded_new_departure)
        
        return diverse_routes
    
    def calculate_diversity_score(self, routes: List[Route]) -> float:
        """
        Calculate overall diversity score for a set of routes.
        
        Args:
            routes: Routes to evaluate
            
        Returns:
            Diversity score between 0 and 1 (higher is more diverse)
        """
        if len(routes) <= 1:
            return 0.0
        
        # Calculate diversity across different dimensions
        path_diversity = self._calculate_path_diversity(routes)
        mode_diversity = self._calculate_mode_diversity(routes)
        time_diversity = self._calculate_time_diversity(routes)
        cost_diversity = self._calculate_cost_diversity(routes)
        
        # Weighted average of diversity dimensions
        weights = {
            'path': 0.3,
            'mode': 0.3,
            'time': 0.2,
            'cost': 0.2
        }
        
        total_score = (
            path_diversity * weights['path'] +
            mode_diversity * weights['mode'] +
            time_diversity * weights['time'] +
            cost_diversity * weights['cost']
        )
        
        return min(1.0, total_score)
    
    def _get_path_signature(self, route: Route) -> Tuple:
        """Get a signature representing the geographical path of a route."""
        # Use number of segments and total distance as path signature
        return (
            len(route.segments),
            round(route.total_distance, 1),
            tuple(seg.mode for seg in route.segments)
        )
    
    def _create_path_variant(self, base_route: Route, origin, destination, departure_time) -> Optional[Route]:
        """Create a variant with a different geographical path."""
        # Create a longer, more scenic route
        new_distance = base_route.total_distance * 1.3
        new_time = int(base_route.estimated_time * 1.2)
        new_cost = base_route.estimated_cost * 1.1
        
        # Create new segments with scenic path
        new_segments = []
        for i, segment in enumerate(base_route.segments):
            new_segment = RouteSegment(
                mode=segment.mode,
                start_location=segment.start_location,
                end_location=segment.end_location,
                distance=segment.distance * 1.3,
                duration=int(segment.duration * 1.2),
                instructions=f"Take scenic route: {segment.instructions}"
            )
            new_segments.append(new_segment)
        
        arrival_time = departure_time + timedelta(minutes=new_time)
        
        return Route(
            id=str(uuid.uuid4()),
            segments=new_segments,
            total_distance=new_distance,
            estimated_time=new_time,
            estimated_cost=new_cost,
            stress_level=max(1, base_route.stress_level - 1),  # Less stressful scenic route
            reliability_score=base_route.reliability_score,
            transportation_modes=base_route.transportation_modes.copy(),
            departure_time=departure_time,
            arrival_time=arrival_time,
            instructions=[seg.instructions for seg in new_segments]
        )
    
    def _create_alternative_path(
        self, 
        base_route: Route, 
        origin,
        destination,
        departure_time,
        existing_signatures: Set[Tuple]
    ) -> Optional[Route]:
        """Create an alternative path that's different from existing ones."""
        # Try creating a route with more segments (more complex path)
        if len(base_route.segments) == 1:
            # Split single segment into multiple segments
            return self._create_multi_segment_variant(base_route, origin, destination, departure_time)
        
        return None
    
    def _create_multi_segment_variant(self, base_route: Route, origin, destination, departure_time) -> Route:
        """Create a multi-segment variant of a single-segment route."""
        base_segment = base_route.segments[0]
        
        # Create intermediate point
        mid_lat = (origin.latitude + destination.latitude) / 2
        mid_lon = (origin.longitude + destination.longitude) / 2
        
        from commute_optimizer.models import Location
        intermediate_point = Location(
            latitude=mid_lat + 0.002,  # Slight detour
            longitude=mid_lon + 0.002,
            address="Intermediate point"
        )
        
        # First segment to intermediate point
        segment1 = RouteSegment(
            mode=base_segment.mode,
            start_location=origin,
            end_location=intermediate_point,
            distance=base_segment.distance * 0.6,
            duration=int(base_segment.duration * 0.6),
            instructions=f"Head to intermediate point via {base_segment.mode.value}"
        )
        
        # Second segment to destination
        segment2 = RouteSegment(
            mode=base_segment.mode,
            start_location=intermediate_point,
            end_location=destination,
            distance=base_segment.distance * 0.4,
            duration=int(base_segment.duration * 0.4),
            instructions=f"Continue to destination via {base_segment.mode.value}"
        )
        
        new_segments = [segment1, segment2]
        arrival_time = departure_time + timedelta(minutes=base_route.estimated_time)
        
        return Route(
            id=str(uuid.uuid4()),
            segments=new_segments,
            total_distance=base_route.total_distance,
            estimated_time=base_route.estimated_time,
            estimated_cost=base_route.estimated_cost,
            stress_level=base_route.stress_level,
            reliability_score=base_route.reliability_score,
            transportation_modes=base_route.transportation_modes.copy(),
            departure_time=departure_time,
            arrival_time=arrival_time,
            instructions=[seg.instructions for seg in new_segments]
        )
    
    def _create_mode_variant(
        self, 
        base_route: Route, 
        request: RouteRequest, 
        target_modes: List[TransportationMode]
    ) -> Optional[Route]:
        """Create a variant using specific transportation modes."""
        if TransportationMode.CYCLING in target_modes:
            return self._create_cycling_route(base_route, request)
        elif TransportationMode.PUBLIC_TRANSIT in target_modes:
            return self._create_transit_route(base_route, request)
        elif TransportationMode.RIDESHARE in target_modes:
            return self._create_rideshare_route(base_route, request)
        
        return None
    
    def _create_cycling_route(self, base_route: Route, request: RouteRequest) -> Route:
        """Create a cycling variant."""
        cycling_time = int(base_route.estimated_time * 1.8)  # Cycling is slower
        cycling_distance = base_route.total_distance * 0.9  # Can take more direct paths
        
        cycling_segment = RouteSegment(
            mode=TransportationMode.CYCLING,
            start_location=request.origin,
            end_location=request.destination,
            distance=cycling_distance,
            duration=cycling_time,
            instructions=f"Cycle from {request.origin.address} to {request.destination.address}"
        )
        
        arrival_time = request.departure_time + timedelta(minutes=cycling_time)
        
        return Route(
            id=str(uuid.uuid4()),
            segments=[cycling_segment],
            total_distance=cycling_distance,
            estimated_time=cycling_time,
            estimated_cost=0.0,  # No cost for cycling
            stress_level=6,  # Physical exertion
            reliability_score=7,  # Weather dependent
            transportation_modes=[TransportationMode.CYCLING],
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[cycling_segment.instructions]
        )
    
    def _create_transit_route(self, base_route: Route, request: RouteRequest) -> Route:
        """Create a public transit variant."""
        # Transit typically takes longer but is cheaper
        transit_time = int(base_route.estimated_time * 1.5)
        
        from commute_optimizer.models import Location
        
        # Walking to transit
        walk_to_transit = RouteSegment(
            mode=TransportationMode.WALKING,
            start_location=request.origin,
            end_location=Location(
                latitude=request.origin.latitude + 0.001,
                longitude=request.origin.longitude + 0.001,
                address="Transit Stop"
            ),
            distance=0.4,
            duration=5,
            instructions="Walk to transit stop"
        )
        
        # Transit segment
        transit_segment = RouteSegment(
            mode=TransportationMode.PUBLIC_TRANSIT,
            start_location=walk_to_transit.end_location,
            end_location=Location(
                latitude=request.destination.latitude - 0.001,
                longitude=request.destination.longitude - 0.001,
                address="Destination Transit Stop"
            ),
            distance=base_route.total_distance - 0.8,
            duration=transit_time - 10,
            instructions="Take bus/train"
        )
        
        # Walking from transit
        walk_from_transit = RouteSegment(
            mode=TransportationMode.WALKING,
            start_location=transit_segment.end_location,
            end_location=request.destination,
            distance=0.4,
            duration=5,
            instructions="Walk to destination"
        )
        
        segments = [walk_to_transit, transit_segment, walk_from_transit]
        arrival_time = request.departure_time + timedelta(minutes=transit_time)
        
        return Route(
            id=str(uuid.uuid4()),
            segments=segments,
            total_distance=base_route.total_distance,
            estimated_time=transit_time,
            estimated_cost=3.50,  # Transit fare
            stress_level=3,  # Low stress
            reliability_score=6,  # Subject to delays
            transportation_modes=[TransportationMode.WALKING, TransportationMode.PUBLIC_TRANSIT],
            departure_time=request.departure_time,
            arrival_time=arrival_time,
            instructions=[seg.instructions for seg in segments]
        )
    
    def _create_rideshare_route(self, base_route: Route, request: RouteRequest) -> Route:
        """Create a rideshare variant."""
        # Rideshare is similar to driving but more expensive
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
    
    def _create_time_variant(self, base_route: Route, new_departure: datetime) -> Route:
        """Create a time-shifted variant of a route."""
        new_arrival = new_departure + timedelta(minutes=base_route.estimated_time)
        
        # Adjust characteristics based on departure time
        hour = new_departure.hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Peak hours
            stress_adjustment = 1
            reliability_adjustment = -1
        else:  # Off-peak
            stress_adjustment = -1
            reliability_adjustment = 1
        
        new_stress = max(1, min(10, base_route.stress_level + stress_adjustment))
        new_reliability = max(1, min(10, base_route.reliability_score + reliability_adjustment))
        
        return Route(
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
    
    def _round_to_nearest_15min(self, dt: datetime) -> datetime:
        """Round datetime to nearest 15 minutes."""
        minutes = dt.minute
        
        # Calculate which 15-minute mark is closest
        # Options are: 0, 15, 30, 45, or next hour (60)
        options = [0, 15, 30, 45, 60]
        
        # Find the closest option
        closest_minutes = min(options, key=lambda x: abs(x - minutes))
        
        if closest_minutes == 60:
            # Round to next hour
            return dt.replace(hour=dt.hour + 1, minute=0, second=0, microsecond=0)
        else:
            return dt.replace(minute=closest_minutes, second=0, microsecond=0)
    
    def _calculate_path_diversity(self, routes: List[Route]) -> float:
        """Calculate path diversity score."""
        if len(routes) <= 1:
            return 0.0
        
        path_signatures = [self._get_path_signature(route) for route in routes]
        unique_signatures = set(path_signatures)
        
        return len(unique_signatures) / len(routes)
    
    def _calculate_mode_diversity(self, routes: List[Route]) -> float:
        """Calculate transportation mode diversity score."""
        if len(routes) <= 1:
            return 0.0
        
        mode_combinations = [tuple(sorted(route.transportation_modes)) for route in routes]
        unique_combinations = set(mode_combinations)
        
        return len(unique_combinations) / len(routes)
    
    def _calculate_time_diversity(self, routes: List[Route]) -> float:
        """Calculate departure time diversity score."""
        if len(routes) <= 1:
            return 0.0
        
        departure_times = [route.departure_time for route in routes]
        time_differences = []
        
        for i in range(len(departure_times)):
            for j in range(i + 1, len(departure_times)):
                diff_minutes = abs((departure_times[i] - departure_times[j]).total_seconds() / 60)
                time_differences.append(diff_minutes)
        
        if not time_differences:
            return 0.0
        
        avg_difference = sum(time_differences) / len(time_differences)
        # Normalize: 30+ minutes difference = full diversity
        return min(1.0, avg_difference / 30)
    
    def _calculate_cost_diversity(self, routes: List[Route]) -> float:
        """Calculate cost diversity score."""
        if len(routes) <= 1:
            return 0.0
        
        costs = [route.estimated_cost for route in routes]
        min_cost = min(costs)
        max_cost = max(costs)
        
        if max_cost == min_cost:
            return 0.0
        
        cost_range = max_cost - min_cost
        # Normalize: $10+ difference = full diversity
        return min(1.0, cost_range / 10)