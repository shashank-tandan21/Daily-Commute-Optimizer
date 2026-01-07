"""Main application orchestration for the Daily Commute Optimizer."""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from .models import (
    Route, UserPreferences, PreferenceProfile, Location, RouteAnalysis
)
from .services import (
    RouteGenerationService, RouteRequest, RouteAnalysisService,
    DataCollectionService, DecisionMakingEngine, RouteComparisonService,
    AlternativeContextService, ConditionMonitoringService
)


class CommuteOptimizerApp:
    """Main application class that orchestrates all services."""
    
    def __init__(self):
        """Initialize the application with all required services."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize services in dependency order
        self.data_collection = DataCollectionService()
        self.route_generation = RouteGenerationService()
        self.route_analysis = RouteAnalysisService()
        self.decision_engine = DecisionMakingEngine()
        self.route_comparison = RouteComparisonService()
        self.alternative_context = AlternativeContextService()
        self.condition_monitoring = ConditionMonitoringService(self.data_collection)
        
        self.logger.info("CommuteOptimizerApp initialized successfully")
    
    def optimize_commute(
        self,
        origin: Location,
        destination: Location,
        departure_time: datetime,
        user_preferences: UserPreferences,
        profile_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main application flow: generate routes, analyze them, and provide recommendations.
        
        Args:
            origin: Starting location
            destination: Ending location  
            departure_time: When to depart
            user_preferences: User's preferences and settings
            profile_name: Specific preference profile to use (defaults to user's default)
            
        Returns:
            Complete optimization result with routes, analysis, and recommendations
        """
        try:
            self.logger.info(f"Starting commute optimization from {origin.address} to {destination.address}")
            
            # Step 1: Get current conditions
            current_conditions = self._get_current_conditions()
            
            # Step 2: Generate multiple route options
            routes = self._generate_routes(origin, destination, departure_time, user_preferences)
            
            if not routes:
                return self._handle_no_routes_error(origin, destination)
            
            # Step 3: Analyze each route
            route_analyses = self._analyze_routes(routes, current_conditions)
            
            # Step 4: Get user's preference profile
            preference_profile = self._get_preference_profile(user_preferences, profile_name)
            
            # Step 5: Rank routes and generate recommendation
            recommendation = self._generate_recommendation(
                routes, route_analyses, preference_profile, current_conditions
            )
            
            # Step 6: Create route comparisons
            comparisons = self._create_route_comparisons(routes, route_analyses)
            
            # Step 7: Generate alternative context
            alternative_contexts = self._generate_alternative_contexts(routes, route_analyses)
            
            # Step 8: Package complete response
            result = {
                'timestamp': datetime.now(),
                'origin': origin,
                'destination': destination,
                'departure_time': departure_time,
                'routes': routes,
                'analyses': route_analyses,
                'recommendation': recommendation,
                'comparisons': comparisons,
                'alternative_contexts': alternative_contexts,
                'current_conditions': current_conditions,
                'preference_profile_used': preference_profile.name
            }
            
            self.logger.info(f"Commute optimization completed successfully with {len(routes)} routes")
            return result
            
        except Exception as e:
            self.logger.error(f"Error during commute optimization: {str(e)}")
            return self._handle_optimization_error(e, origin, destination)
    
    def update_conditions_and_recommendations(
        self,
        previous_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check for significant condition changes and update recommendations if needed.
        
        Args:
            previous_result: Previous optimization result to check for updates
            
        Returns:
            Updated result if conditions changed significantly, None otherwise
        """
        try:
            # Check for significant condition changes
            update_trigger = self.condition_monitoring.check_for_updates(
                previous_result['routes'],
                previous_result['current_conditions']
            )
            
            if update_trigger.should_update:
                self.logger.info(f"Significant condition change detected: {update_trigger.reason}")
                
                # Re-run optimization with updated conditions
                return self.optimize_commute(
                    previous_result['origin'],
                    previous_result['destination'],
                    previous_result['departure_time'],
                    # Note: We'd need to store user preferences in the result to fully support this
                    # For now, we'll return the trigger information
                    None  # This would need user preferences from the original call
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking for condition updates: {str(e)}")
            return None
    
    def _get_current_conditions(self) -> Dict[str, Any]:
        """Get current traffic, weather, and transit conditions."""
        try:
            return {
                'traffic_data': self.data_collection.get_traffic_data(),
                'weather_data': self.data_collection.get_weather_data(),
                'transit_data': self.data_collection.get_transit_data(),
                'timestamp': datetime.now()
            }
        except Exception as e:
            self.logger.warning(f"Error getting current conditions: {str(e)}")
            return {
                'traffic_data': {},
                'weather_data': {},
                'transit_data': {},
                'timestamp': datetime.now(),
                'error': str(e)
            }
    
    def _generate_routes(
        self,
        origin: Location,
        destination: Location,
        departure_time: datetime,
        user_preferences: UserPreferences
    ) -> List[Route]:
        """Generate multiple diverse route options."""
        try:
            route_request = RouteRequest(
                origin=origin,
                destination=destination,
                departure_time=departure_time,
                max_walking_distance=user_preferences.preference_profiles[0].max_walking_distance,
                preferred_modes=user_preferences.preference_profiles[0].preferred_modes,
                avoided_features=user_preferences.preference_profiles[0].avoided_features
            )
            
            return self.route_generation.generate_routes(route_request)
            
        except Exception as e:
            self.logger.error(f"Error generating routes: {str(e)}")
            return []
    
    def _analyze_routes(
        self,
        routes: List[Route],
        current_conditions: Dict[str, Any]
    ) -> List[RouteAnalysis]:
        """Analyze all routes for time, cost, stress, and reliability."""
        analyses = []
        
        for route in routes:
            try:
                analysis = self.route_analysis.analyze_route(route, current_conditions)
                analyses.append(analysis)
            except Exception as e:
                self.logger.warning(f"Error analyzing route {route.id}: {str(e)}")
                # Continue with other routes even if one fails
                continue
        
        return analyses
    
    def _get_preference_profile(
        self,
        user_preferences: UserPreferences,
        profile_name: Optional[str]
    ) -> PreferenceProfile:
        """Get the specified preference profile or the default one."""
        target_profile = profile_name or user_preferences.default_profile
        
        for profile in user_preferences.preference_profiles:
            if profile.name == target_profile:
                return profile
        
        # Fallback to first profile if default not found
        if user_preferences.preference_profiles:
            self.logger.warning(f"Profile '{target_profile}' not found, using first available profile")
            return user_preferences.preference_profiles[0]
        
        # Create emergency default profile if none exist
        self.logger.warning("No preference profiles found, creating default profile")
        return PreferenceProfile(
            name="default",
            time_weight=40,
            cost_weight=20,
            comfort_weight=20,
            reliability_weight=20
        )
    
    def _generate_recommendation(
        self,
        routes: List[Route],
        analyses: List[RouteAnalysis],
        preference_profile: PreferenceProfile,
        current_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate contextual recommendation with explanation."""
        try:
            # Rank routes based on preferences
            ranked_routes = self.decision_engine.rank_routes(routes, analyses, preference_profile)
            
            # Generate recommendation with reasoning
            recommendation = self.decision_engine.generate_recommendation(
                ranked_routes, current_conditions
            )
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {str(e)}")
            return {
                'recommended_route_id': routes[0].id if routes else None,
                'reasoning': f"Error generating recommendation: {str(e)}",
                'confidence': 'low',
                'caveats': ['Recommendation system encountered an error']
            }
    
    def _create_route_comparisons(
        self,
        routes: List[Route],
        analyses: List[RouteAnalysis]
    ) -> Dict[str, Any]:
        """Create side-by-side route comparisons."""
        try:
            return self.route_comparison.create_comparison(routes, analyses)
        except Exception as e:
            self.logger.error(f"Error creating route comparisons: {str(e)}")
            return {'error': str(e), 'comparisons': []}
    
    def _generate_alternative_contexts(
        self,
        routes: List[Route],
        analyses: List[RouteAnalysis]
    ) -> Dict[str, Any]:
        """Generate context about when alternative routes might be preferable."""
        try:
            contexts = {}
            for route, analysis in zip(routes, analyses):
                context = self.alternative_context.generate_context(route, analysis, routes)
                contexts[route.id] = context
            return contexts
        except Exception as e:
            self.logger.error(f"Error generating alternative contexts: {str(e)}")
            return {}
    
    def _handle_no_routes_error(
        self,
        origin: Location,
        destination: Location
    ) -> Dict[str, Any]:
        """Handle the case when no routes can be generated."""
        return {
            'timestamp': datetime.now(),
            'origin': origin,
            'destination': destination,
            'routes': [],
            'error': 'no_routes_available',
            'message': 'No viable routes could be generated for the specified origin and destination. '
                      'Please check that both locations are accessible and try again.',
            'suggestions': [
                'Verify that both addresses are correct and accessible',
                'Try adjusting your departure time',
                'Consider expanding your preferred transportation modes',
                'Check if there are any service disruptions in the area'
            ]
        }
    
    def _handle_optimization_error(
        self,
        error: Exception,
        origin: Location,
        destination: Location
    ) -> Dict[str, Any]:
        """Handle general optimization errors with graceful degradation."""
        return {
            'timestamp': datetime.now(),
            'origin': origin,
            'destination': destination,
            'routes': [],
            'error': 'optimization_failed',
            'message': f'An error occurred during route optimization: {str(error)}',
            'suggestions': [
                'Please try again in a few moments',
                'Check your internet connection',
                'Verify that your locations are valid',
                'Contact support if the problem persists'
            ]
        }