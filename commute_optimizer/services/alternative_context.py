"""Alternative Context Service for providing context about when alternative routes are preferable."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from commute_optimizer.models import (
    Route, RouteAnalysis, PreferenceProfile, TransportationMode
)


class ContextType(str, Enum):
    """Types of alternative context."""
    SITUATIONAL = "situational"
    PREFERENCE_BASED = "preference_based"
    CONDITION_BASED = "condition_based"
    TRADE_OFF_BASED = "trade_off_based"


class AlternativeContextService:
    """
    Service for providing comprehensive context about when alternative routes are preferable.
    
    This service implements functionality to help users understand the full decision landscape
    by providing context about when each route option might be the better choice based on
    different scenarios, conditions, and personal priorities.
    """
    
    def __init__(self):
        """Initialize the alternative context service."""
        pass
    
    def generate_context(
        self,
        route: Route,
        analysis: RouteAnalysis,
        all_routes: List[Route],
        current_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate context for when this specific route might be preferable.
        
        Args:
            route: Route to generate context for
            analysis: Analysis of the route
            all_routes: All available routes for comparison
            current_conditions: Current conditions
            
        Returns:
            Dictionary containing context about when this route is preferable
            
        Validates: Requirements 5.4, 5.5
        """
        if current_conditions is None:
            current_conditions = {}
        
        context = {
            "route_id": route.id,
            "when_to_choose": [],
            "when_not_to_choose": [],
            "ideal_conditions": [],
            "avoid_conditions": [],
            "trade_offs": []
        }
        
        # Analyze when this route is preferable
        if analysis.time_analysis.estimated_time <= 30:
            context["when_to_choose"].append("When you need to arrive quickly")
        
        if analysis.cost_analysis.total_cost <= 3.0:
            context["when_to_choose"].append("When budget is a priority")
        
        if analysis.stress_analysis.overall_stress <= 4:
            context["when_to_choose"].append("When you want a relaxing commute")
        
        if analysis.reliability_analysis.overall_reliability >= 8:
            context["when_to_choose"].append("For important appointments requiring punctuality")
        
        # Analyze when to avoid this route
        if analysis.time_analysis.estimated_time > 60:
            context["when_not_to_choose"].append("When you have time constraints")
        
        if analysis.cost_analysis.total_cost > 10.0:
            context["when_not_to_choose"].append("When budget is tight")
        
        if analysis.stress_analysis.overall_stress >= 7:
            context["when_not_to_choose"].append("When you're already stressed")
        
        if analysis.reliability_analysis.overall_reliability <= 5:
            context["when_not_to_choose"].append("For critical appointments")
        
        # Add mode-specific context
        if TransportationMode.CYCLING in route.transportation_modes:
            context["ideal_conditions"].append("Clear, mild weather")
            context["avoid_conditions"].append("Rain, snow, or extreme temperatures")
        
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            context["ideal_conditions"].append("Normal transit service")
            context["avoid_conditions"].append("Transit strikes or major delays")
        
        if TransportationMode.DRIVING in route.transportation_modes:
            context["ideal_conditions"].append("Light traffic conditions")
            context["avoid_conditions"].append("Heavy traffic or major incidents")
        
        return context
    
    def provide_alternative_context(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        current_conditions: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[PreferenceProfile] = None
    ) -> Dict[str, Any]:
        """
        Provide comprehensive context about when alternative routes are preferable.
        
        Args:
            routes: List of routes to analyze
            route_analyses: Corresponding route analyses
            current_conditions: Current weather, traffic, and transit conditions
            user_preferences: User's preference profile
            
        Returns:
            Dictionary containing alternative context for each route
            
        Validates: Requirements 5.4, 5.5
        """
        if len(routes) != len(route_analyses):
            raise ValueError("Number of routes must match number of analyses")
        
        if not routes:
            return {
                "alternative_contexts": [],
                "decision_scenarios": [],
                "summary": "No routes available for context analysis"
            }
        
        if current_conditions is None:
            current_conditions = {}
        
        alternative_contexts = []
        
        # Generate context for each route
        for i, (route, analysis) in enumerate(zip(routes, route_analyses)):
            route_context = self._generate_route_alternative_context(
                route, analysis, routes, route_analyses, i, current_conditions, user_preferences
            )
            alternative_contexts.append(route_context)
        
        # Generate decision scenarios
        decision_scenarios = self._generate_decision_scenarios(
            routes, route_analyses, current_conditions, user_preferences
        )
        
        # Generate comprehensive decision factors
        decision_factors = self._generate_comprehensive_decision_factors(
            routes, route_analyses, current_conditions, user_preferences
        )
        
        return {
            "alternative_contexts": alternative_contexts,
            "decision_scenarios": decision_scenarios,
            "decision_factors": decision_factors,
            "summary": self._generate_context_summary(alternative_contexts, decision_scenarios),
            "timestamp": datetime.now().isoformat()
        }
    
    def create_context_about_when_alternatives_are_preferable(
        self,
        primary_route: Route,
        primary_analysis: RouteAnalysis,
        alternative_routes: List[Route],
        alternative_analyses: List[RouteAnalysis],
        context_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create specific context about when alternative routes are preferable to a primary route.
        
        Args:
            primary_route: The primary/recommended route
            primary_analysis: Analysis of the primary route
            alternative_routes: List of alternative routes
            alternative_analyses: Corresponding analyses of alternatives
            context_conditions: Current conditions and context
            
        Returns:
            Dictionary containing context about when alternatives are preferable
            
        Validates: Requirements 5.4, 5.5
        """
        if len(alternative_routes) != len(alternative_analyses):
            raise ValueError("Number of alternative routes must match number of analyses")
        
        if context_conditions is None:
            context_conditions = {}
        
        alternative_preferences = []
        
        for i, (alt_route, alt_analysis) in enumerate(zip(alternative_routes, alternative_analyses)):
            alt_context = {
                "route_id": alt_route.id,
                "route_name": f"Alternative {i + 1}",
                "when_preferable": self._identify_when_alternative_is_preferable(
                    primary_route, primary_analysis, alt_route, alt_analysis, context_conditions
                ),
                "key_advantages": self._identify_alternative_advantages(
                    primary_analysis, alt_analysis
                ),
                "situational_benefits": self._identify_situational_benefits(
                    alt_route, alt_analysis, context_conditions
                ),
                "user_scenarios": self._generate_user_scenarios_for_alternative(
                    primary_route, primary_analysis, alt_route, alt_analysis
                )
            }
            alternative_preferences.append(alt_context)
        
        return {
            "primary_route": {
                "id": primary_route.id,
                "limitations": self._identify_primary_route_limitations(
                    primary_route, primary_analysis, alternative_routes, alternative_analyses
                )
            },
            "alternatives": alternative_preferences,
            "decision_guidance": self._generate_alternative_decision_guidance(
                primary_route, primary_analysis, alternative_routes, alternative_analyses
            ),
            "context_summary": self._generate_alternative_context_summary(alternative_preferences)
        }
    
    def display_comprehensive_decision_factors(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        current_conditions: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[PreferenceProfile] = None
    ) -> Dict[str, Any]:
        """
        Display all decision factors that should be visible to users.
        
        Args:
            routes: List of routes being considered
            route_analyses: Corresponding route analyses
            current_conditions: Current conditions affecting the decision
            user_preferences: User's preference profile
            
        Returns:
            Dictionary containing all visible decision factors
            
        Validates: Requirements 5.4, 5.5
        """
        if current_conditions is None:
            current_conditions = {}
        
        decision_factors = {
            "route_characteristics": self._analyze_route_characteristics(routes, route_analyses),
            "environmental_factors": self._analyze_environmental_factors(current_conditions),
            "personal_factors": self._analyze_personal_factors(user_preferences),
            "temporal_factors": self._analyze_temporal_factors(routes, current_conditions),
            "risk_factors": self._analyze_risk_factors(routes, route_analyses, current_conditions),
            "opportunity_costs": self._analyze_opportunity_costs(routes, route_analyses),
            "decision_tree": self._create_decision_tree(routes, route_analyses, current_conditions),
            "factor_interactions": self._analyze_factor_interactions(
                routes, route_analyses, current_conditions, user_preferences
            )
        }
        
        return {
            "decision_factors": decision_factors,
            "factor_importance": self._rank_factor_importance(decision_factors, user_preferences),
            "decision_complexity": self._assess_decision_complexity(decision_factors),
            "recommendations": self._generate_decision_factor_recommendations(decision_factors),
            "visibility_summary": self._generate_visibility_summary(decision_factors)
        }
    
    def _generate_route_alternative_context(
        self,
        route: Route,
        analysis: RouteAnalysis,
        all_routes: List[Route],
        all_analyses: List[RouteAnalysis],
        route_index: int,
        current_conditions: Dict[str, Any],
        user_preferences: Optional[PreferenceProfile]
    ) -> Dict[str, Any]:
        """Generate alternative context for a specific route."""
        route_name = f"Route {route_index + 1}"
        
        # Get other routes for comparison
        other_routes = [(r, a, i) for i, (r, a) in enumerate(zip(all_routes, all_analyses)) if i != route_index]
        
        context = {
            "route_id": route.id,
            "route_name": route_name,
            "when_to_choose": self._generate_when_to_choose_context(
                route, analysis, other_routes, current_conditions
            ),
            "when_not_to_choose": self._generate_when_not_to_choose_context(
                route, analysis, other_routes, current_conditions
            ),
            "ideal_conditions": self._identify_ideal_conditions_for_route(
                route, analysis, current_conditions
            ),
            "risk_scenarios": self._identify_risk_scenarios_for_route(
                route, analysis, current_conditions
            ),
            "user_profiles": self._identify_user_profiles_for_route(
                route, analysis, user_preferences
            ),
            "comparative_advantages": self._identify_comparative_advantages(
                route, analysis, other_routes
            ),
            "situational_context": self._generate_situational_context(
                route, analysis, current_conditions
            )
        }
        
        return context
    
    def _generate_decision_scenarios(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        current_conditions: Dict[str, Any],
        user_preferences: Optional[PreferenceProfile]
    ) -> List[Dict[str, Any]]:
        """Generate decision scenarios that help users understand when to choose each route."""
        scenarios = []
        
        # Time-critical scenario
        scenarios.append({
            "scenario": "Time-Critical Situation",
            "description": "When you're running late or have a tight schedule",
            "recommended_route": self._find_fastest_route(routes, route_analyses),
            "reasoning": "Prioritizes speed over other factors",
            "considerations": [
                "Accept higher cost if necessary",
                "Be prepared for potentially higher stress",
                "Check for traffic incidents before departing"
            ]
        })
        
        # Budget-conscious scenario
        scenarios.append({
            "scenario": "Budget-Conscious Day",
            "description": "When minimizing cost is the top priority",
            "recommended_route": self._find_cheapest_route(routes, route_analyses),
            "reasoning": "Minimizes total travel cost",
            "considerations": [
                "Allow extra time for potentially slower travel",
                "Consider comfort trade-offs",
                "Factor in any hidden costs"
            ]
        })
        
        # Stress-free scenario
        scenarios.append({
            "scenario": "Stress-Free Commute",
            "description": "When you want a relaxing, low-stress journey",
            "recommended_route": self._find_least_stressful_route(routes, route_analyses),
            "reasoning": "Minimizes commute stress and complexity",
            "considerations": [
                "May take longer than other options",
                "Could cost more for comfort",
                "Weather conditions may affect stress levels"
            ]
        })
        
        # Reliability-focused scenario
        scenarios.append({
            "scenario": "Important Appointment",
            "description": "When punctuality is absolutely critical",
            "recommended_route": self._find_most_reliable_route(routes, route_analyses),
            "reasoning": "Maximizes timing predictability",
            "considerations": [
                "Leave extra buffer time regardless",
                "Have backup plan ready",
                "Monitor conditions before departure"
            ]
        })
        
        # Weather-dependent scenarios
        weather_condition = current_conditions.get('weather_data', {}).get('condition', 'clear')
        if weather_condition != 'clear':
            scenarios.append({
                "scenario": f"Bad Weather ({weather_condition.replace('_', ' ').title()})",
                "description": f"When dealing with {weather_condition.replace('_', ' ')} conditions",
                "recommended_route": self._find_weather_appropriate_route(routes, route_analyses, weather_condition),
                "reasoning": "Accounts for weather impact on different transportation modes",
                "considerations": [
                    "Allow extra time for weather delays",
                    "Consider mode-specific weather risks",
                    "Have weather-appropriate backup plan"
                ]
            })
        
        # Traffic-dependent scenario
        traffic_level = current_conditions.get('traffic_data', {}).get('congestion_level', 'moderate')
        if traffic_level in ['heavy', 'severe']:
            scenarios.append({
                "scenario": f"Heavy Traffic Conditions",
                "description": "When traffic congestion is significant",
                "recommended_route": self._find_traffic_avoiding_route(routes, route_analyses),
                "reasoning": "Minimizes exposure to traffic congestion",
                "considerations": [
                    "Consider alternative transportation modes",
                    "Factor in parking availability",
                    "Monitor real-time traffic updates"
                ]
            })
        
        return scenarios
    
    def _generate_comprehensive_decision_factors(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        current_conditions: Dict[str, Any],
        user_preferences: Optional[PreferenceProfile]
    ) -> Dict[str, Any]:
        """Generate comprehensive decision factors display."""
        return {
            "route_performance": self._analyze_route_performance_factors(routes, route_analyses),
            "external_conditions": self._analyze_external_condition_factors(current_conditions),
            "personal_priorities": self._analyze_personal_priority_factors(user_preferences),
            "risk_assessment": self._analyze_risk_assessment_factors(routes, route_analyses, current_conditions),
            "trade_off_analysis": self._analyze_trade_off_factors(routes, route_analyses),
            "decision_confidence": self._analyze_decision_confidence_factors(routes, route_analyses)
        }
    
    def _generate_when_to_choose_context(
        self,
        route: Route,
        analysis: RouteAnalysis,
        other_routes: List[Tuple[Route, RouteAnalysis, int]],
        current_conditions: Dict[str, Any]
    ) -> List[str]:
        """Generate context about when to choose this specific route."""
        when_to_choose = []
        
        # Time-based context
        if analysis.time_analysis.estimated_time <= 30:
            when_to_choose.append("When you need a quick commute (under 30 minutes)")
        
        if other_routes:
            fastest_time = min(other_analysis.time_analysis.estimated_time for _, other_analysis, _ in other_routes)
            if analysis.time_analysis.estimated_time <= fastest_time + 5:
                when_to_choose.append("When speed is your top priority")
        
        # Cost-based context
        if analysis.cost_analysis.total_cost <= 3.0:
            when_to_choose.append("When you want to keep costs low (under $3)")
        
        if other_routes:
            cheapest_cost = min(other_analysis.cost_analysis.total_cost for _, other_analysis, _ in other_routes)
            if analysis.cost_analysis.total_cost <= cheapest_cost + 1.0:
                when_to_choose.append("When budget is a major concern")
        
        # Stress-based context
        if analysis.stress_analysis.overall_stress <= 4:
            when_to_choose.append("When you want a relaxing, low-stress journey")
        
        if analysis.stress_analysis.traffic_stress <= 3:
            when_to_choose.append("When you want to avoid traffic stress")
        
        # Reliability-based context
        if analysis.reliability_analysis.overall_reliability >= 8:
            when_to_choose.append("For important appointments requiring punctuality")
        
        if analysis.reliability_analysis.incident_probability <= 0.15:
            when_to_choose.append("When you can't afford unexpected delays")
        
        # Mode-specific context
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            when_to_choose.append("When you want to relax or work during the commute")
            when_to_choose.append("When parking is expensive or unavailable")
        
        if TransportationMode.CYCLING in route.transportation_modes:
            weather_condition = current_conditions.get('weather_data', {}).get('condition', 'clear')
            if weather_condition in ['clear', 'cloudy']:
                when_to_choose.append("When weather is nice and you want exercise")
        
        if TransportationMode.DRIVING in route.transportation_modes:
            when_to_choose.append("When you need maximum flexibility and control")
            when_to_choose.append("When carrying heavy items or multiple passengers")
        
        # Comparative context
        if other_routes:
            # Check if this route is best in any category
            times = [other_analysis.time_analysis.estimated_time for _, other_analysis, _ in other_routes]
            costs = [other_analysis.cost_analysis.total_cost for _, other_analysis, _ in other_routes]
            stress_levels = [other_analysis.stress_analysis.overall_stress for _, other_analysis, _ in other_routes]
            reliability_scores = [other_analysis.reliability_analysis.overall_reliability for _, other_analysis, _ in other_routes]
            
            if analysis.time_analysis.estimated_time < min(times):
                when_to_choose.append("When you want the fastest available option")
            
            if analysis.cost_analysis.total_cost < min(costs):
                when_to_choose.append("When you want the most economical option")
            
            if analysis.stress_analysis.overall_stress < min(stress_levels):
                when_to_choose.append("When you want the least stressful option")
            
            if analysis.reliability_analysis.overall_reliability > max(reliability_scores):
                when_to_choose.append("When you want the most reliable option")
        
        return when_to_choose
    
    def _generate_when_not_to_choose_context(
        self,
        route: Route,
        analysis: RouteAnalysis,
        other_routes: List[Tuple[Route, RouteAnalysis, int]],
        current_conditions: Dict[str, Any]
    ) -> List[str]:
        """Generate context about when NOT to choose this specific route."""
        when_not_to_choose = []
        
        # Time-based warnings
        if analysis.time_analysis.estimated_time > 60:
            when_not_to_choose.append("When you have time constraints (takes over an hour)")
        
        if analysis.time_analysis.time_range_max - analysis.time_analysis.time_range_min > 20:
            when_not_to_choose.append("When punctuality is critical (high time variance)")
        
        # Cost-based warnings
        if analysis.cost_analysis.total_cost > 15.0:
            when_not_to_choose.append("When budget is tight (expensive option)")
        
        # Stress-based warnings
        if analysis.stress_analysis.overall_stress >= 7:
            when_not_to_choose.append("When you're already stressed or want to relax")
        
        if analysis.stress_analysis.traffic_stress >= 8:
            when_not_to_choose.append("During heavy traffic periods")
        
        # Reliability-based warnings
        if analysis.reliability_analysis.overall_reliability <= 5:
            when_not_to_choose.append("For important appointments (unpredictable timing)")
        
        if analysis.reliability_analysis.incident_probability > 0.3:
            when_not_to_choose.append("When you can't afford delays (high incident risk)")
        
        # Weather-based warnings
        weather_condition = current_conditions.get('weather_data', {}).get('condition', 'clear')
        if TransportationMode.CYCLING in route.transportation_modes:
            if weather_condition in ['rain', 'heavy_rain', 'snow', 'heavy_snow', 'storm']:
                when_not_to_choose.append(f"In {weather_condition.replace('_', ' ')} conditions")
            
            temperature = current_conditions.get('weather_data', {}).get('temperature', 20)
            if temperature < 0 or temperature > 35:
                when_not_to_choose.append("In extreme temperatures")
        
        if TransportationMode.WALKING in route.transportation_modes:
            if weather_condition in ['heavy_rain', 'heavy_snow', 'storm']:
                when_not_to_choose.append(f"In severe weather ({weather_condition.replace('_', ' ')})")
        
        # Mode-specific warnings
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            transit_status = current_conditions.get('transit_data', {}).get('service_status', 'normal')
            if transit_status in ['disrupted', 'delayed']:
                when_not_to_choose.append("During transit service disruptions")
            
            when_not_to_choose.append("When carrying large or heavy items")
        
        if TransportationMode.DRIVING in route.transportation_modes:
            when_not_to_choose.append("When parking is unavailable or very expensive")
            when_not_to_choose.append("During major traffic incidents on your route")
        
        # Comparative warnings
        if other_routes:
            times = [other_analysis.time_analysis.estimated_time for _, other_analysis, _ in other_routes]
            costs = [other_analysis.cost_analysis.total_cost for _, other_analysis, _ in other_routes]
            stress_levels = [other_analysis.stress_analysis.overall_stress for _, other_analysis, _ in other_routes]
            reliability_scores = [other_analysis.reliability_analysis.overall_reliability for _, other_analysis, _ in other_routes]
            
            min_time = min(times)
            if analysis.time_analysis.estimated_time > min_time + 20:
                time_diff = analysis.time_analysis.estimated_time - min_time
                when_not_to_choose.append(f"When time matters (alternatives are {time_diff:.0f} minutes faster)")
            
            min_cost = min(costs)
            if analysis.cost_analysis.total_cost > min_cost + 5.0:
                cost_diff = analysis.cost_analysis.total_cost - min_cost
                when_not_to_choose.append(f"When budget matters (alternatives cost ${cost_diff:.2f} less)")
            
            min_stress = min(stress_levels)
            if analysis.stress_analysis.overall_stress > min_stress + 3:
                when_not_to_choose.append("When you want a relaxing commute (alternatives are much less stressful)")
            
            max_reliability = max(reliability_scores)
            if analysis.reliability_analysis.overall_reliability < max_reliability - 3:
                when_not_to_choose.append("When punctuality is critical (alternatives are much more reliable)")
        
        return when_not_to_choose
    def _identify_ideal_conditions_for_route(
        self,
        route: Route,
        analysis: RouteAnalysis,
        current_conditions: Dict[str, Any]
    ) -> List[str]:
        """Identify ideal conditions for this route to perform well."""
        ideal_conditions = []
        
        # Weather conditions
        if TransportationMode.CYCLING in route.transportation_modes:
            ideal_conditions.append("Clear, mild weather (15-25°C)")
            ideal_conditions.append("Low wind speeds (under 15 km/h)")
        
        if TransportationMode.WALKING in route.transportation_modes:
            ideal_conditions.append("Dry weather conditions")
            ideal_conditions.append("Comfortable temperatures")
        
        if TransportationMode.DRIVING in route.transportation_modes:
            ideal_conditions.append("Light to moderate traffic conditions")
            ideal_conditions.append("Good visibility and dry roads")
        
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            ideal_conditions.append("Normal transit service operations")
            ideal_conditions.append("Off-peak travel times")
        
        # Time-based conditions
        departure_hour = route.departure_time.hour
        if 7 <= departure_hour <= 9 or 17 <= departure_hour <= 19:
            ideal_conditions.append("Allow extra time during peak hours")
        else:
            ideal_conditions.append("Off-peak timing works well for this route")
        
        # Stress-related conditions
        if analysis.stress_analysis.overall_stress <= 4:
            ideal_conditions.append("Any stress tolerance level")
        else:
            ideal_conditions.append("When you're feeling energetic and alert")
        
        # Reliability conditions
        if analysis.reliability_analysis.overall_reliability >= 7:
            ideal_conditions.append("Most weather and traffic conditions")
        else:
            ideal_conditions.append("Stable weather and traffic patterns")
        
        return ideal_conditions
    
    def _identify_risk_scenarios_for_route(
        self,
        route: Route,
        analysis: RouteAnalysis,
        current_conditions: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify risk scenarios that could affect this route."""
        risk_scenarios = []
        
        # High incident probability
        if analysis.reliability_analysis.incident_probability > 0.25:
            risk_scenarios.append({
                "risk": "Traffic Incidents",
                "probability": f"{analysis.reliability_analysis.incident_probability:.1%}",
                "impact": "Significant delays possible",
                "mitigation": "Monitor traffic conditions and have backup route ready"
            })
        
        # High time variance
        if analysis.reliability_analysis.historical_variance > 15:
            risk_scenarios.append({
                "risk": "Unpredictable Timing",
                "probability": "Medium",
                "impact": f"Travel time could vary by ±{analysis.reliability_analysis.historical_variance:.0f} minutes",
                "mitigation": "Allow extra buffer time for important appointments"
            })
        
        # Weather vulnerability
        weather_impact = analysis.reliability_analysis.weather_impact
        if weather_impact > 0.3:
            risk_scenarios.append({
                "risk": "Weather Sensitivity",
                "probability": "High in bad weather",
                "impact": f"Up to {weather_impact:.0%} performance degradation",
                "mitigation": "Check weather forecast and consider alternatives in bad weather"
            })
        
        # Mode-specific risks
        if TransportationMode.CYCLING in route.transportation_modes:
            risk_scenarios.append({
                "risk": "Cycling Safety",
                "probability": "Low but present",
                "impact": "Safety concerns in traffic or bad weather",
                "mitigation": "Use bike lanes, wear safety gear, avoid cycling in severe weather"
            })
        
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            if analysis.reliability_analysis.service_reliability < 0.8:
                risk_scenarios.append({
                    "risk": "Transit Service Disruptions",
                    "probability": f"{(1 - analysis.reliability_analysis.service_reliability):.0%}",
                    "impact": "Service delays or cancellations",
                    "mitigation": "Check service alerts before departure, have backup transportation"
                })
        
        # High stress scenarios
        if analysis.stress_analysis.overall_stress >= 7:
            risk_scenarios.append({
                "risk": "High Stress Commute",
                "probability": "High",
                "impact": "Mental fatigue and stress accumulation",
                "mitigation": "Consider stress management techniques or alternative routes on difficult days"
            })
        
        return risk_scenarios
    
    def _identify_user_profiles_for_route(
        self,
        route: Route,
        analysis: RouteAnalysis,
        user_preferences: Optional[PreferenceProfile]
    ) -> List[str]:
        """Identify user profiles that would benefit most from this route."""
        user_profiles = []
        
        # Time-focused users
        if analysis.time_analysis.estimated_time <= 30:
            user_profiles.append("Time-conscious commuters who prioritize speed")
        
        # Budget-conscious users
        if analysis.cost_analysis.total_cost <= 5.0:
            user_profiles.append("Budget-conscious travelers looking to minimize costs")
        
        # Comfort-focused users
        if analysis.stress_analysis.overall_stress <= 4:
            user_profiles.append("Comfort-seekers who want a relaxing commute")
        
        # Reliability-focused users
        if analysis.reliability_analysis.overall_reliability >= 8:
            user_profiles.append("Professionals with strict schedules requiring punctuality")
        
        # Mode-specific profiles
        if TransportationMode.CYCLING in route.transportation_modes:
            user_profiles.append("Fitness enthusiasts who want exercise in their commute")
            user_profiles.append("Environmentally conscious travelers")
        
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            user_profiles.append("Commuters who want to work or relax during travel")
            user_profiles.append("Urban dwellers without access to parking")
        
        if TransportationMode.DRIVING in route.transportation_modes:
            user_profiles.append("Commuters who need maximum flexibility and control")
            user_profiles.append("Parents or caregivers with complex schedules")
        
        # Preference-based profiles
        if user_preferences:
            if user_preferences.time_weight >= 40:
                if analysis.time_analysis.estimated_time <= 35:
                    user_profiles.append("Users who heavily prioritize time savings")
            
            if user_preferences.cost_weight >= 40:
                if analysis.cost_analysis.total_cost <= 6.0:
                    user_profiles.append("Users who heavily prioritize cost savings")
            
            if user_preferences.comfort_weight >= 40:
                if analysis.stress_analysis.overall_stress <= 5:
                    user_profiles.append("Users who heavily prioritize comfort and low stress")
            
            if user_preferences.reliability_weight >= 40:
                if analysis.reliability_analysis.overall_reliability >= 7:
                    user_profiles.append("Users who heavily prioritize reliability and predictability")
        
        return user_profiles
    
    def _identify_comparative_advantages(
        self,
        route: Route,
        analysis: RouteAnalysis,
        other_routes: List[Tuple[Route, RouteAnalysis, int]]
    ) -> List[str]:
        """Identify this route's advantages compared to alternatives."""
        if not other_routes:
            return []
        
        advantages = []
        
        # Time advantages
        other_times = [other_analysis.time_analysis.estimated_time for _, other_analysis, _ in other_routes]
        min_other_time = min(other_times)
        if analysis.time_analysis.estimated_time <= min_other_time:
            if analysis.time_analysis.estimated_time < min_other_time - 5:
                time_saved = min_other_time - analysis.time_analysis.estimated_time
                advantages.append(f"Saves {time_saved:.0f} minutes compared to alternatives")
            else:
                advantages.append("Fastest available option")
        
        # Cost advantages
        other_costs = [other_analysis.cost_analysis.total_cost for _, other_analysis, _ in other_routes]
        min_other_cost = min(other_costs)
        if analysis.cost_analysis.total_cost <= min_other_cost:
            if analysis.cost_analysis.total_cost < min_other_cost - 1.0:
                cost_saved = min_other_cost - analysis.cost_analysis.total_cost
                advantages.append(f"Saves ${cost_saved:.2f} compared to alternatives")
            else:
                advantages.append("Most economical option")
        
        # Stress advantages
        other_stress = [other_analysis.stress_analysis.overall_stress for _, other_analysis, _ in other_routes]
        min_other_stress = min(other_stress)
        if analysis.stress_analysis.overall_stress <= min_other_stress:
            if analysis.stress_analysis.overall_stress < min_other_stress - 1:
                stress_reduction = min_other_stress - analysis.stress_analysis.overall_stress
                advantages.append(f"Reduces stress by {stress_reduction:.0f} points compared to alternatives")
            else:
                advantages.append("Least stressful option")
        
        # Reliability advantages
        other_reliability = [other_analysis.reliability_analysis.overall_reliability for _, other_analysis, _ in other_routes]
        max_other_reliability = max(other_reliability)
        if analysis.reliability_analysis.overall_reliability >= max_other_reliability:
            if analysis.reliability_analysis.overall_reliability > max_other_reliability + 1:
                reliability_gain = analysis.reliability_analysis.overall_reliability - max_other_reliability
                advantages.append(f"More reliable by {reliability_gain:.0f} points compared to alternatives")
            else:
                advantages.append("Most reliable option")
        
        # Mode-specific advantages
        other_modes = set()
        for other_route, _, _ in other_routes:
            other_modes.update(other_route.transportation_modes)
        
        route_modes = set(route.transportation_modes)
        unique_modes = route_modes - other_modes
        
        if TransportationMode.CYCLING in unique_modes:
            advantages.append("Only option that includes exercise and environmental benefits")
        
        if TransportationMode.PUBLIC_TRANSIT in unique_modes:
            advantages.append("Only option that allows working or relaxing during travel")
        
        if TransportationMode.DRIVING in unique_modes:
            advantages.append("Only option with maximum flexibility and control")
        
        return advantages
    
    def _generate_situational_context(
        self,
        route: Route,
        analysis: RouteAnalysis,
        current_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate situational context for the route."""
        return {
            "current_weather_impact": self._assess_current_weather_impact(route, current_conditions),
            "current_traffic_impact": self._assess_current_traffic_impact(route, analysis, current_conditions),
            "current_transit_impact": self._assess_current_transit_impact(route, current_conditions),
            "time_of_day_factors": self._assess_time_of_day_factors(route, analysis),
            "seasonal_considerations": self._assess_seasonal_considerations(route, current_conditions)
        }
    
    def _find_fastest_route(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> int:
        """Find the index of the fastest route."""
        times = [analysis.time_analysis.estimated_time for analysis in route_analyses]
        return times.index(min(times)) + 1  # 1-based indexing
    
    def _find_cheapest_route(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> int:
        """Find the index of the cheapest route."""
        costs = [analysis.cost_analysis.total_cost for analysis in route_analyses]
        return costs.index(min(costs)) + 1  # 1-based indexing
    
    def _find_least_stressful_route(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> int:
        """Find the index of the least stressful route."""
        stress_levels = [analysis.stress_analysis.overall_stress for analysis in route_analyses]
        return stress_levels.index(min(stress_levels)) + 1  # 1-based indexing
    
    def _find_most_reliable_route(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> int:
        """Find the index of the most reliable route."""
        reliability_scores = [analysis.reliability_analysis.overall_reliability for analysis in route_analyses]
        return reliability_scores.index(max(reliability_scores)) + 1  # 1-based indexing
    
    def _find_weather_appropriate_route(
        self, 
        routes: List[Route], 
        route_analyses: List[RouteAnalysis], 
        weather_condition: str
    ) -> int:
        """Find the route most appropriate for current weather conditions."""
        # Score routes based on weather appropriateness
        weather_scores = []
        
        for route, analysis in zip(routes, route_analyses):
            score = 0
            
            # Prefer covered transportation in bad weather
            if weather_condition in ['rain', 'heavy_rain', 'snow', 'heavy_snow', 'storm']:
                if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
                    score += 3  # Covered transportation
                elif TransportationMode.DRIVING in route.transportation_modes:
                    score += 2  # Enclosed transportation
                elif TransportationMode.RIDESHARE in route.transportation_modes:
                    score += 2  # Enclosed transportation
                else:
                    score -= 2  # Exposed to weather
            
            # Factor in weather impact from analysis
            weather_impact = analysis.reliability_analysis.weather_impact
            score -= weather_impact * 5  # Lower weather impact is better
            
            weather_scores.append(score)
        
        return weather_scores.index(max(weather_scores)) + 1  # 1-based indexing
    
    def _find_traffic_avoiding_route(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> int:
        """Find the route that best avoids traffic."""
        traffic_scores = []
        
        for route, analysis in zip(routes, route_analyses):
            score = 0
            
            # Prefer non-driving modes during heavy traffic
            if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
                score += 3  # Not affected by road traffic
            elif TransportationMode.CYCLING in route.transportation_modes:
                score += 2  # Can use bike lanes
            elif TransportationMode.WALKING in route.transportation_modes:
                score += 1  # Not affected by road traffic
            
            # Factor in traffic stress from analysis
            traffic_stress = analysis.stress_analysis.traffic_stress
            score -= traffic_stress  # Lower traffic stress is better
            
            traffic_scores.append(score)
        
        return traffic_scores.index(max(traffic_scores)) + 1  # 1-based indexing
    
    def _generate_context_summary(
        self,
        alternative_contexts: List[Dict[str, Any]],
        decision_scenarios: List[Dict[str, Any]]
    ) -> str:
        """Generate a summary of the alternative context analysis."""
        if not alternative_contexts:
            return "No alternative context available."
        
        summary_parts = []
        
        # Count routes with specific advantages
        time_advantaged = sum(1 for ctx in alternative_contexts 
                             if any("fastest" in advantage.lower() or "quick" in advantage.lower() 
                                   for advantage in ctx.get("comparative_advantages", [])))
        
        cost_advantaged = sum(1 for ctx in alternative_contexts 
                             if any("cheapest" in advantage.lower() or "economical" in advantage.lower() 
                                   for advantage in ctx.get("comparative_advantages", [])))
        
        stress_advantaged = sum(1 for ctx in alternative_contexts 
                               if any("stress" in advantage.lower() 
                                     for advantage in ctx.get("comparative_advantages", [])))
        
        reliability_advantaged = sum(1 for ctx in alternative_contexts 
                                    if any("reliable" in advantage.lower() 
                                          for advantage in ctx.get("comparative_advantages", [])))
        
        summary_parts.append(f"Analysis of {len(alternative_contexts)} route options:")
        
        if time_advantaged > 0:
            summary_parts.append(f"• {time_advantaged} route(s) optimized for speed")
        
        if cost_advantaged > 0:
            summary_parts.append(f"• {cost_advantaged} route(s) optimized for cost")
        
        if stress_advantaged > 0:
            summary_parts.append(f"• {stress_advantaged} route(s) optimized for low stress")
        
        if reliability_advantaged > 0:
            summary_parts.append(f"• {reliability_advantaged} route(s) optimized for reliability")
        
        summary_parts.append(f"• {len(decision_scenarios)} decision scenarios provided")
        summary_parts.append("Choose based on your current priorities and conditions.")
        
        return "\n".join(summary_parts)
    
    def _identify_when_alternative_is_preferable(
        self,
        primary_route: Route,
        primary_analysis: RouteAnalysis,
        alt_route: Route,
        alt_analysis: RouteAnalysis,
        context_conditions: Dict[str, Any]
    ) -> List[str]:
        """Identify when an alternative route is preferable to the primary route."""
        preferable_scenarios = []
        
        # Time-based scenarios
        if alt_analysis.time_analysis.estimated_time < primary_analysis.time_analysis.estimated_time - 10:
            time_saved = primary_analysis.time_analysis.estimated_time - alt_analysis.time_analysis.estimated_time
            preferable_scenarios.append(f"When time is critical - saves {time_saved:.0f} minutes")
        
        # Cost-based scenarios
        if alt_analysis.cost_analysis.total_cost < primary_analysis.cost_analysis.total_cost - 2.0:
            cost_saved = primary_analysis.cost_analysis.total_cost - alt_analysis.cost_analysis.total_cost
            preferable_scenarios.append(f"When budget is tight - saves ${cost_saved:.2f}")
        
        # Stress-based scenarios
        if alt_analysis.stress_analysis.overall_stress < primary_analysis.stress_analysis.overall_stress - 2:
            stress_reduction = primary_analysis.stress_analysis.overall_stress - alt_analysis.stress_analysis.overall_stress
            preferable_scenarios.append(f"When you want a relaxing commute - {stress_reduction:.0f} points less stressful")
        
        # Reliability-based scenarios
        if alt_analysis.reliability_analysis.overall_reliability > primary_analysis.reliability_analysis.overall_reliability + 2:
            reliability_gain = alt_analysis.reliability_analysis.overall_reliability - primary_analysis.reliability_analysis.overall_reliability
            preferable_scenarios.append(f"For important appointments - {reliability_gain:.0f} points more reliable")
        
        # Weather-based scenarios
        weather_condition = context_conditions.get('weather_data', {}).get('condition', 'clear')
        if weather_condition in ['rain', 'heavy_rain', 'snow', 'heavy_snow']:
            primary_weather_impact = primary_analysis.reliability_analysis.weather_impact
            alt_weather_impact = alt_analysis.reliability_analysis.weather_impact
            
            if alt_weather_impact < primary_weather_impact - 0.2:
                preferable_scenarios.append(f"In {weather_condition.replace('_', ' ')} conditions - less weather-sensitive")
        
        # Mode-specific scenarios
        if TransportationMode.PUBLIC_TRANSIT in alt_route.transportation_modes:
            if TransportationMode.DRIVING in primary_route.transportation_modes:
                preferable_scenarios.append("When parking is expensive or unavailable")
                preferable_scenarios.append("When you want to work or relax during the commute")
        
        if TransportationMode.CYCLING in alt_route.transportation_modes:
            if weather_condition in ['clear', 'cloudy']:
                preferable_scenarios.append("When you want exercise and environmental benefits")
        
        return preferable_scenarios
    
    def _identify_alternative_advantages(
        self,
        primary_analysis: RouteAnalysis,
        alt_analysis: RouteAnalysis
    ) -> List[str]:
        """Identify key advantages of an alternative route."""
        advantages = []
        
        # Time advantage
        if alt_analysis.time_analysis.estimated_time < primary_analysis.time_analysis.estimated_time:
            time_diff = primary_analysis.time_analysis.estimated_time - alt_analysis.time_analysis.estimated_time
            if time_diff >= 10:
                advantages.append(f"Significantly faster ({time_diff:.0f} minutes saved)")
            else:
                advantages.append(f"Faster ({time_diff:.0f} minutes saved)")
        
        # Cost advantage
        if alt_analysis.cost_analysis.total_cost < primary_analysis.cost_analysis.total_cost:
            cost_diff = primary_analysis.cost_analysis.total_cost - alt_analysis.cost_analysis.total_cost
            if cost_diff >= 3.0:
                advantages.append(f"Much cheaper (${cost_diff:.2f} saved)")
            else:
                advantages.append(f"Cheaper (${cost_diff:.2f} saved)")
        
        # Stress advantage
        if alt_analysis.stress_analysis.overall_stress < primary_analysis.stress_analysis.overall_stress:
            stress_diff = primary_analysis.stress_analysis.overall_stress - alt_analysis.stress_analysis.overall_stress
            if stress_diff >= 3:
                advantages.append(f"Much less stressful ({stress_diff:.0f} points lower)")
            else:
                advantages.append(f"Less stressful ({stress_diff:.0f} points lower)")
        
        # Reliability advantage
        if alt_analysis.reliability_analysis.overall_reliability > primary_analysis.reliability_analysis.overall_reliability:
            reliability_diff = alt_analysis.reliability_analysis.overall_reliability - primary_analysis.reliability_analysis.overall_reliability
            if reliability_diff >= 3:
                advantages.append(f"Much more reliable ({reliability_diff:.0f} points higher)")
            else:
                advantages.append(f"More reliable ({reliability_diff:.0f} points higher)")
        
        return advantages
    
    def _identify_situational_benefits(
        self,
        alt_route: Route,
        alt_analysis: RouteAnalysis,
        context_conditions: Dict[str, Any]
    ) -> List[str]:
        """Identify situational benefits of an alternative route."""
        benefits = []
        
        # Weather-related benefits
        weather_condition = context_conditions.get('weather_data', {}).get('condition', 'clear')
        if weather_condition != 'clear':
            if alt_analysis.reliability_analysis.weather_impact < 0.3:
                benefits.append(f"Less affected by current {weather_condition.replace('_', ' ')} conditions")
        
        # Traffic-related benefits
        traffic_level = context_conditions.get('traffic_data', {}).get('congestion_level', 'moderate')
        if traffic_level in ['heavy', 'severe']:
            if alt_analysis.stress_analysis.traffic_stress <= 5:
                benefits.append("Avoids heavy traffic congestion")
        
        # Transit-related benefits
        if TransportationMode.PUBLIC_TRANSIT in alt_route.transportation_modes:
            transit_status = context_conditions.get('transit_data', {}).get('service_status', 'normal')
            if transit_status == 'normal' and alt_analysis.reliability_analysis.service_reliability > 0.8:
                benefits.append("Takes advantage of reliable transit service")
        
        # Time-of-day benefits
        departure_hour = alt_route.departure_time.hour
        if 10 <= departure_hour <= 15:  # Mid-day
            benefits.append("Benefits from off-peak timing")
        
        return benefits
    
    def _generate_user_scenarios_for_alternative(
        self,
        primary_route: Route,
        primary_analysis: RouteAnalysis,
        alt_route: Route,
        alt_analysis: RouteAnalysis
    ) -> List[Dict[str, str]]:
        """Generate user scenarios where the alternative might be preferred."""
        scenarios = []
        
        # Time-critical scenario
        if alt_analysis.time_analysis.estimated_time < primary_analysis.time_analysis.estimated_time - 5:
            scenarios.append({
                "scenario": "Running Late",
                "description": "When you're behind schedule and need to make up time",
                "benefit": f"Saves {primary_analysis.time_analysis.estimated_time - alt_analysis.time_analysis.estimated_time:.0f} minutes"
            })
        
        # Budget scenario
        if alt_analysis.cost_analysis.total_cost < primary_analysis.cost_analysis.total_cost - 1.0:
            scenarios.append({
                "scenario": "Budget Day",
                "description": "When you want to minimize travel expenses",
                "benefit": f"Saves ${primary_analysis.cost_analysis.total_cost - alt_analysis.cost_analysis.total_cost:.2f}"
            })
        
        # Stress scenario
        if alt_analysis.stress_analysis.overall_stress < primary_analysis.stress_analysis.overall_stress - 1:
            scenarios.append({
                "scenario": "Stressful Day",
                "description": "When you're already stressed and want an easier commute",
                "benefit": f"Reduces stress by {primary_analysis.stress_analysis.overall_stress - alt_analysis.stress_analysis.overall_stress:.0f} points"
            })
        
        # Reliability scenario
        if alt_analysis.reliability_analysis.overall_reliability > primary_analysis.reliability_analysis.overall_reliability + 1:
            scenarios.append({
                "scenario": "Important Meeting",
                "description": "When punctuality is absolutely critical",
                "benefit": f"More reliable by {alt_analysis.reliability_analysis.overall_reliability - primary_analysis.reliability_analysis.overall_reliability:.0f} points"
            })
        
        return scenarios
    
    def _identify_primary_route_limitations(
        self,
        primary_route: Route,
        primary_analysis: RouteAnalysis,
        alternative_routes: List[Route],
        alternative_analyses: List[RouteAnalysis]
    ) -> List[str]:
        """Identify limitations of the primary route compared to alternatives."""
        limitations = []
        
        if not alternative_routes:
            return limitations
        
        # Time limitations
        alt_times = [analysis.time_analysis.estimated_time for analysis in alternative_analyses]
        min_alt_time = min(alt_times)
        if primary_analysis.time_analysis.estimated_time > min_alt_time + 10:
            time_diff = primary_analysis.time_analysis.estimated_time - min_alt_time
            limitations.append(f"Takes {time_diff:.0f} minutes longer than fastest alternative")
        
        # Cost limitations
        alt_costs = [analysis.cost_analysis.total_cost for analysis in alternative_analyses]
        min_alt_cost = min(alt_costs)
        if primary_analysis.cost_analysis.total_cost > min_alt_cost + 2.0:
            cost_diff = primary_analysis.cost_analysis.total_cost - min_alt_cost
            limitations.append(f"Costs ${cost_diff:.2f} more than cheapest alternative")
        
        # Stress limitations
        alt_stress = [analysis.stress_analysis.overall_stress for analysis in alternative_analyses]
        min_alt_stress = min(alt_stress)
        if primary_analysis.stress_analysis.overall_stress > min_alt_stress + 2:
            stress_diff = primary_analysis.stress_analysis.overall_stress - min_alt_stress
            limitations.append(f"More stressful by {stress_diff:.0f} points than least stressful alternative")
        
        # Reliability limitations
        alt_reliability = [analysis.reliability_analysis.overall_reliability for analysis in alternative_analyses]
        max_alt_reliability = max(alt_reliability)
        if primary_analysis.reliability_analysis.overall_reliability < max_alt_reliability - 2:
            reliability_diff = max_alt_reliability - primary_analysis.reliability_analysis.overall_reliability
            limitations.append(f"Less reliable by {reliability_diff:.0f} points than most reliable alternative")
        
        return limitations
    
    def _generate_alternative_decision_guidance(
        self,
        primary_route: Route,
        primary_analysis: RouteAnalysis,
        alternative_routes: List[Route],
        alternative_analyses: List[RouteAnalysis]
    ) -> List[str]:
        """Generate decision guidance for choosing between primary and alternatives."""
        guidance = []
        
        guidance.append("Consider alternatives when:")
        
        # Find best alternatives in each category
        if alternative_routes:
            times = [analysis.time_analysis.estimated_time for analysis in alternative_analyses]
            costs = [analysis.cost_analysis.total_cost for analysis in alternative_analyses]
            stress_levels = [analysis.stress_analysis.overall_stress for analysis in alternative_analyses]
            reliability_scores = [analysis.reliability_analysis.overall_reliability for analysis in alternative_analyses]
            
            fastest_idx = times.index(min(times))
            cheapest_idx = costs.index(min(costs))
            least_stressful_idx = stress_levels.index(min(stress_levels))
            most_reliable_idx = reliability_scores.index(max(reliability_scores))
            
            # Time guidance
            if alternative_analyses[fastest_idx].time_analysis.estimated_time < primary_analysis.time_analysis.estimated_time - 10:
                guidance.append(f"• Time is critical - Alternative {fastest_idx + 1} is significantly faster")
            
            # Cost guidance
            if alternative_analyses[cheapest_idx].cost_analysis.total_cost < primary_analysis.cost_analysis.total_cost - 2.0:
                guidance.append(f"• Budget is important - Alternative {cheapest_idx + 1} is much cheaper")
            
            # Stress guidance
            if alternative_analyses[least_stressful_idx].stress_analysis.overall_stress < primary_analysis.stress_analysis.overall_stress - 2:
                guidance.append(f"• You want a relaxing commute - Alternative {least_stressful_idx + 1} is much less stressful")
            
            # Reliability guidance
            if alternative_analyses[most_reliable_idx].reliability_analysis.overall_reliability > primary_analysis.reliability_analysis.overall_reliability + 2:
                guidance.append(f"• Punctuality is critical - Alternative {most_reliable_idx + 1} is much more reliable")
        
        guidance.append("Stick with the primary route when:")
        guidance.append("• It meets your needs adequately")
        guidance.append("• The trade-offs of alternatives aren't worth it")
        guidance.append("• You're familiar with this route and prefer consistency")
        
        return guidance
    
    def _generate_alternative_context_summary(self, alternative_preferences: List[Dict[str, Any]]) -> str:
        """Generate a summary of alternative context analysis."""
        if not alternative_preferences:
            return "No alternatives available for context analysis."
        
        summary_parts = []
        summary_parts.append(f"Analysis of {len(alternative_preferences)} alternative routes:")
        
        # Count alternatives with significant advantages
        time_alternatives = sum(1 for alt in alternative_preferences 
                               if any("faster" in adv.lower() for adv in alt.get("key_advantages", [])))
        
        cost_alternatives = sum(1 for alt in alternative_preferences 
                               if any("cheaper" in adv.lower() for adv in alt.get("key_advantages", [])))
        
        stress_alternatives = sum(1 for alt in alternative_preferences 
                                 if any("stress" in adv.lower() for adv in alt.get("key_advantages", [])))
        
        reliability_alternatives = sum(1 for alt in alternative_preferences 
                                      if any("reliable" in adv.lower() for adv in alt.get("key_advantages", [])))
        
        if time_alternatives > 0:
            summary_parts.append(f"• {time_alternatives} alternative(s) offer time savings")
        
        if cost_alternatives > 0:
            summary_parts.append(f"• {cost_alternatives} alternative(s) offer cost savings")
        
        if stress_alternatives > 0:
            summary_parts.append(f"• {stress_alternatives} alternative(s) offer stress reduction")
        
        if reliability_alternatives > 0:
            summary_parts.append(f"• {reliability_alternatives} alternative(s) offer better reliability")
        
        summary_parts.append("Review each alternative's context to make the best choice for your situation.")
        
        return "\n".join(summary_parts)
    
    # Helper methods for comprehensive decision factors
    def _analyze_route_characteristics(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> Dict[str, Any]:
        """Analyze route characteristics for decision factors."""
        return {
            "time_distribution": [analysis.time_analysis.estimated_time for analysis in route_analyses],
            "cost_distribution": [analysis.cost_analysis.total_cost for analysis in route_analyses],
            "stress_distribution": [analysis.stress_analysis.overall_stress for analysis in route_analyses],
            "reliability_distribution": [analysis.reliability_analysis.overall_reliability for analysis in route_analyses],
            "mode_diversity": list(set().union(*[route.transportation_modes for route in routes]))
        }
    
    def _analyze_environmental_factors(self, current_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze environmental factors affecting the decision."""
        return {
            "weather": current_conditions.get('weather_data', {}),
            "traffic": current_conditions.get('traffic_data', {}),
            "transit": current_conditions.get('transit_data', {}),
            "time_of_day": datetime.now().hour
        }
    
    def _analyze_personal_factors(self, user_preferences: Optional[PreferenceProfile]) -> Dict[str, Any]:
        """Analyze personal factors affecting the decision."""
        if not user_preferences:
            return {"preferences": "Not specified"}
        
        return {
            "priority_weights": {
                "time": user_preferences.time_weight,
                "cost": user_preferences.cost_weight,
                "comfort": user_preferences.comfort_weight,
                "reliability": user_preferences.reliability_weight
            },
            "preferred_modes": user_preferences.preferred_modes,
            "avoided_features": user_preferences.avoided_features,
            "max_walking_distance": user_preferences.max_walking_distance
        }
    
    def _analyze_temporal_factors(self, routes: List[Route], current_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temporal factors affecting the decision."""
        current_hour = datetime.now().hour
        
        return {
            "current_hour": current_hour,
            "is_peak_hour": 7 <= current_hour <= 9 or 17 <= current_hour <= 19,
            "departure_times": [route.departure_time.hour for route in routes],
            "day_of_week": datetime.now().weekday()
        }
    
    def _analyze_risk_factors(
        self, 
        routes: List[Route], 
        route_analyses: List[RouteAnalysis], 
        current_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze risk factors affecting the decision."""
        return {
            "incident_probabilities": [analysis.reliability_analysis.incident_probability for analysis in route_analyses],
            "weather_impacts": [analysis.reliability_analysis.weather_impact for analysis in route_analyses],
            "time_variances": [analysis.reliability_analysis.historical_variance for analysis in route_analyses],
            "service_reliabilities": [analysis.reliability_analysis.service_reliability for analysis in route_analyses]
        }
    
    def _analyze_opportunity_costs(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> Dict[str, Any]:
        """Analyze opportunity costs of choosing each route."""
        if len(routes) < 2:
            return {"opportunity_costs": "No alternatives to compare"}
        
        # Calculate what you give up by choosing each route
        times = [analysis.time_analysis.estimated_time for analysis in route_analyses]
        costs = [analysis.cost_analysis.total_cost for analysis in route_analyses]
        stress_levels = [analysis.stress_analysis.overall_stress for analysis in route_analyses]
        reliability_scores = [analysis.reliability_analysis.overall_reliability for analysis in route_analyses]
        
        min_time = min(times)
        min_cost = min(costs)
        min_stress = min(stress_levels)
        max_reliability = max(reliability_scores)
        
        opportunity_costs = []
        for i, analysis in enumerate(route_analyses):
            cost_analysis = {
                "route": f"Route {i + 1}",
                "time_cost": analysis.time_analysis.estimated_time - min_time,
                "money_cost": analysis.cost_analysis.total_cost - min_cost,
                "stress_cost": analysis.stress_analysis.overall_stress - min_stress,
                "reliability_cost": max_reliability - analysis.reliability_analysis.overall_reliability
            }
            opportunity_costs.append(cost_analysis)
        
        return {"opportunity_costs": opportunity_costs}
    
    def _create_decision_tree(
        self, 
        routes: List[Route], 
        route_analyses: List[RouteAnalysis], 
        current_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a decision tree for route selection."""
        # Simplified decision tree based on primary factors
        tree = {
            "root": "What is your primary concern?",
            "branches": {
                "time": {
                    "question": "Do you need the fastest possible route?",
                    "yes": f"Choose Route {self._find_fastest_route(routes, route_analyses)}",
                    "no": "Consider other factors"
                },
                "cost": {
                    "question": "Is minimizing cost your top priority?",
                    "yes": f"Choose Route {self._find_cheapest_route(routes, route_analyses)}",
                    "no": "Consider other factors"
                },
                "comfort": {
                    "question": "Do you want the least stressful commute?",
                    "yes": f"Choose Route {self._find_least_stressful_route(routes, route_analyses)}",
                    "no": "Consider other factors"
                },
                "reliability": {
                    "question": "Is punctuality absolutely critical?",
                    "yes": f"Choose Route {self._find_most_reliable_route(routes, route_analyses)}",
                    "no": "Consider balanced approach"
                }
            }
        }
        
        return tree
    
    def _analyze_factor_interactions(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        current_conditions: Dict[str, Any],
        user_preferences: Optional[PreferenceProfile]
    ) -> Dict[str, Any]:
        """Analyze how different factors interact with each other."""
        interactions = {}
        
        # Weather-mode interactions
        weather_condition = current_conditions.get('weather_data', {}).get('condition', 'clear')
        if weather_condition != 'clear':
            interactions["weather_mode"] = self._analyze_weather_mode_interactions(routes, weather_condition)
        
        # Traffic-time interactions
        traffic_level = current_conditions.get('traffic_data', {}).get('congestion_level', 'moderate')
        if traffic_level in ['heavy', 'severe']:
            interactions["traffic_time"] = self._analyze_traffic_time_interactions(routes, route_analyses)
        
        # Preference-performance interactions
        if user_preferences:
            interactions["preference_performance"] = self._analyze_preference_performance_interactions(
                route_analyses, user_preferences
            )
        
        return interactions
    
    def _rank_factor_importance(
        self, 
        decision_factors: Dict[str, Any], 
        user_preferences: Optional[PreferenceProfile]
    ) -> List[Dict[str, Any]]:
        """Rank the importance of different decision factors."""
        factor_importance = []
        
        # Base importance rankings
        base_rankings = [
            {"factor": "route_characteristics", "base_importance": 0.9},
            {"factor": "personal_factors", "base_importance": 0.8},
            {"factor": "environmental_factors", "base_importance": 0.7},
            {"factor": "risk_factors", "base_importance": 0.6},
            {"factor": "temporal_factors", "base_importance": 0.5},
            {"factor": "opportunity_costs", "base_importance": 0.4}
        ]
        
        # Adjust based on user preferences if available
        if user_preferences:
            for ranking in base_rankings:
                if ranking["factor"] == "personal_factors":
                    ranking["adjusted_importance"] = 0.95  # Always high if preferences specified
                else:
                    ranking["adjusted_importance"] = ranking["base_importance"]
        else:
            for ranking in base_rankings:
                ranking["adjusted_importance"] = ranking["base_importance"]
        
        # Sort by adjusted importance
        factor_importance = sorted(base_rankings, key=lambda x: x["adjusted_importance"], reverse=True)
        
        return factor_importance
    
    def _assess_decision_complexity(self, decision_factors: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the complexity of the decision based on available factors."""
        complexity_score = 0
        complexity_factors = []
        
        # Route diversity adds complexity
        route_chars = decision_factors.get("route_characteristics", {})
        if "mode_diversity" in route_chars:
            mode_count = len(route_chars["mode_diversity"])
            if mode_count > 2:
                complexity_score += 0.2
                complexity_factors.append("Multiple transportation modes available")
        
        # Environmental factors add complexity
        env_factors = decision_factors.get("environmental_factors", {})
        if env_factors.get("weather", {}).get("condition", "clear") != "clear":
            complexity_score += 0.1
            complexity_factors.append("Weather conditions affect choice")
        
        if env_factors.get("traffic", {}).get("congestion_level", "moderate") in ["heavy", "severe"]:
            complexity_score += 0.1
            complexity_factors.append("Heavy traffic affects choice")
        
        # Risk factors add complexity
        risk_factors = decision_factors.get("risk_factors", {})
        high_risk_routes = sum(1 for prob in risk_factors.get("incident_probabilities", []) if prob > 0.25)
        if high_risk_routes > 0:
            complexity_score += 0.15
            complexity_factors.append("Some routes have high incident risk")
        
        # Determine complexity level
        if complexity_score < 0.2:
            complexity_level = "Low"
        elif complexity_score < 0.4:
            complexity_level = "Medium"
        else:
            complexity_level = "High"
        
        return {
            "complexity_score": complexity_score,
            "complexity_level": complexity_level,
            "contributing_factors": complexity_factors,
            "recommendation": self._get_complexity_recommendation(complexity_level)
        }
    
    def _generate_decision_factor_recommendations(self, decision_factors: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on decision factors."""
        recommendations = []
        
        # Route characteristic recommendations
        route_chars = decision_factors.get("route_characteristics", {})
        if "time_distribution" in route_chars:
            time_range = max(route_chars["time_distribution"]) - min(route_chars["time_distribution"])
            if time_range > 20:
                recommendations.append("Consider time carefully - routes vary significantly in duration")
        
        # Environmental factor recommendations
        env_factors = decision_factors.get("environmental_factors", {})
        weather = env_factors.get("weather", {})
        if weather.get("condition", "clear") in ["rain", "heavy_rain", "snow", "heavy_snow"]:
            recommendations.append("Factor in weather impact - some routes more affected than others")
        
        # Risk factor recommendations
        risk_factors = decision_factors.get("risk_factors", {})
        if any(prob > 0.3 for prob in risk_factors.get("incident_probabilities", [])):
            recommendations.append("Consider incident risk - some routes have high delay probability")
        
        return recommendations
    
    def _generate_visibility_summary(self, decision_factors: Dict[str, Any]) -> str:
        """Generate a summary of decision factor visibility."""
        visible_factors = len([k for k, v in decision_factors.items() if v])
        
        summary_parts = [
            f"Decision analysis includes {visible_factors} factor categories:",
            "• Route performance characteristics",
            "• Current environmental conditions",
            "• Personal preferences and priorities",
            "• Risk assessment and mitigation",
            "• Temporal considerations",
            "• Opportunity cost analysis"
        ]
        
        return "\n".join(summary_parts)
    
    # Additional helper methods
    def _assess_current_weather_impact(self, route: Route, current_conditions: Dict[str, Any]) -> str:
        """Assess how current weather impacts this route."""
        weather_data = current_conditions.get('weather_data', {})
        weather_condition = weather_data.get('condition', 'clear')
        
        if weather_condition == 'clear':
            return "No weather impact"
        
        impact_descriptions = {
            'rain': 'Light rain may slow travel and increase stress',
            'heavy_rain': 'Heavy rain significantly impacts travel time and safety',
            'snow': 'Snow conditions affect all transportation modes',
            'heavy_snow': 'Severe snow creates major travel disruptions',
            'fog': 'Fog reduces visibility and increases travel time',
            'storm': 'Storm conditions create significant safety and timing risks'
        }
        
        return impact_descriptions.get(weather_condition, f'Weather condition ({weather_condition}) may affect travel')
    
    def _assess_current_traffic_impact(
        self, 
        route: Route, 
        analysis: RouteAnalysis, 
        current_conditions: Dict[str, Any]
    ) -> str:
        """Assess how current traffic impacts this route."""
        traffic_data = current_conditions.get('traffic_data', {})
        congestion_level = traffic_data.get('congestion_level', 'moderate')
        
        if TransportationMode.DRIVING not in route.transportation_modes and TransportationMode.RIDESHARE not in route.transportation_modes:
            return "Not affected by road traffic"
        
        impact_descriptions = {
            'light': 'Minimal traffic impact expected',
            'moderate': 'Some traffic delays possible',
            'heavy': 'Significant traffic delays likely',
            'severe': 'Major traffic congestion expected'
        }
        
        base_impact = impact_descriptions.get(congestion_level, 'Traffic impact unknown')
        
        if analysis.stress_analysis.traffic_stress >= 7:
            return f"{base_impact} - High stress route in traffic"
        else:
            return base_impact
    
    def _assess_current_transit_impact(self, route: Route, current_conditions: Dict[str, Any]) -> str:
        """Assess how current transit conditions impact this route."""
        if TransportationMode.PUBLIC_TRANSIT not in route.transportation_modes:
            return "No transit dependency"
        
        transit_data = current_conditions.get('transit_data', {})
        service_status = transit_data.get('service_status', 'normal')
        
        impact_descriptions = {
            'normal': 'Normal transit service expected',
            'minor_delays': 'Minor transit delays possible',
            'delays': 'Transit delays likely',
            'major_delays': 'Significant transit disruptions',
            'disrupted': 'Major transit service issues',
            'suspended': 'Transit service suspended'
        }
        
        return impact_descriptions.get(service_status, 'Transit status unknown')
    
    def _assess_time_of_day_factors(self, route: Route, analysis: RouteAnalysis) -> str:
        """Assess time of day factors for this route."""
        departure_hour = route.departure_time.hour
        
        if 7 <= departure_hour <= 9:
            return f"Morning peak hour departure - expect {analysis.time_analysis.peak_hour_impact} min additional time"
        elif 17 <= departure_hour <= 19:
            return f"Evening peak hour departure - expect {analysis.time_analysis.peak_hour_impact} min additional time"
        elif 22 <= departure_hour or departure_hour <= 5:
            return "Off-peak/night departure - generally faster but limited transit options"
        else:
            return "Mid-day departure - typically good conditions"
    
    def _assess_seasonal_considerations(self, route: Route, current_conditions: Dict[str, Any]) -> str:
        """Assess seasonal considerations for this route."""
        current_month = datetime.now().month
        
        # Winter considerations (Dec, Jan, Feb)
        if current_month in [12, 1, 2]:
            if TransportationMode.CYCLING in route.transportation_modes:
                return "Winter cycling requires extra caution and appropriate gear"
            elif TransportationMode.WALKING in route.transportation_modes:
                return "Winter walking may involve icy conditions"
            else:
                return "Winter conditions may affect travel times"
        
        # Summer considerations (Jun, Jul, Aug)
        elif current_month in [6, 7, 8]:
            if TransportationMode.CYCLING in route.transportation_modes or TransportationMode.WALKING in route.transportation_modes:
                return "Summer heat may increase physical exertion"
            else:
                return "Summer conditions generally favorable for travel"
        
        # Spring/Fall
        else:
            return "Seasonal conditions generally favorable"
    
    def _get_complexity_recommendation(self, complexity_level: str) -> str:
        """Get recommendation based on decision complexity."""
        recommendations = {
            "Low": "Decision is straightforward - choose based on your primary priority",
            "Medium": "Consider multiple factors - review trade-offs carefully",
            "High": "Complex decision - take time to evaluate all factors and consider your specific situation"
        }
        
        return recommendations.get(complexity_level, "Evaluate based on your priorities")
    
    def _analyze_weather_mode_interactions(self, routes: List[Route], weather_condition: str) -> Dict[str, str]:
        """Analyze how weather interacts with different transportation modes."""
        interactions = {}
        
        for i, route in enumerate(routes):
            route_name = f"Route {i + 1}"
            
            if TransportationMode.CYCLING in route.transportation_modes:
                if weather_condition in ['rain', 'heavy_rain']:
                    interactions[route_name] = "Cycling in rain increases difficulty and safety risk"
                elif weather_condition in ['snow', 'heavy_snow']:
                    interactions[route_name] = "Cycling in snow is dangerous and not recommended"
                else:
                    interactions[route_name] = "Weather may affect cycling comfort"
            
            elif TransportationMode.WALKING in route.transportation_modes:
                if weather_condition in ['heavy_rain', 'heavy_snow', 'storm']:
                    interactions[route_name] = "Walking in severe weather is uncomfortable and potentially unsafe"
                else:
                    interactions[route_name] = "Weather affects walking comfort but route remains viable"
            
            elif TransportationMode.DRIVING in route.transportation_modes:
                if weather_condition in ['heavy_rain', 'snow', 'fog']:
                    interactions[route_name] = "Driving conditions affected - reduced visibility and traction"
                else:
                    interactions[route_name] = "Driving minimally affected by weather"
            
            elif TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
                interactions[route_name] = "Transit provides weather protection but may have weather-related delays"
        
        return interactions
    
    def _analyze_traffic_time_interactions(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> Dict[str, str]:
        """Analyze how traffic interacts with timing for different routes."""
        interactions = {}
        
        for i, (route, analysis) in enumerate(zip(routes, route_analyses)):
            route_name = f"Route {i + 1}"
            
            if TransportationMode.DRIVING in route.transportation_modes or TransportationMode.RIDESHARE in route.transportation_modes:
                if analysis.stress_analysis.traffic_stress >= 7:
                    interactions[route_name] = "Heavy traffic significantly increases travel time and stress"
                else:
                    interactions[route_name] = "Moderate traffic impact on timing"
            else:
                interactions[route_name] = "Not directly affected by road traffic"
        
        return interactions
    
    def _analyze_preference_performance_interactions(
        self, 
        route_analyses: List[RouteAnalysis], 
        user_preferences: PreferenceProfile
    ) -> Dict[str, str]:
        """Analyze how user preferences interact with route performance."""
        interactions = {}
        
        # Find which preference is highest
        preferences = {
            'time': user_preferences.time_weight,
            'cost': user_preferences.cost_weight,
            'comfort': user_preferences.comfort_weight,
            'reliability': user_preferences.reliability_weight
        }
        
        top_preference = max(preferences, key=preferences.get)
        
        for i, analysis in enumerate(route_analyses):
            route_name = f"Route {i + 1}"
            
            if top_preference == 'time':
                if analysis.time_analysis.estimated_time <= 30:
                    interactions[route_name] = "Aligns well with your time priority"
                else:
                    interactions[route_name] = "May not meet your time expectations"
            
            elif top_preference == 'cost':
                if analysis.cost_analysis.total_cost <= 5.0:
                    interactions[route_name] = "Aligns well with your cost priority"
                else:
                    interactions[route_name] = "May exceed your cost preferences"
            
            elif top_preference == 'comfort':
                if analysis.stress_analysis.overall_stress <= 4:
                    interactions[route_name] = "Aligns well with your comfort priority"
                else:
                    interactions[route_name] = "May be more stressful than you prefer"
            
            elif top_preference == 'reliability':
                if analysis.reliability_analysis.overall_reliability >= 7:
                    interactions[route_name] = "Aligns well with your reliability priority"
                else:
                    interactions[route_name] = "May not meet your reliability expectations"
        
        return interactions
    def _analyze_route_performance_factors(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> Dict[str, Any]:
        """Analyze route performance factors for decision making."""
        if not routes or not route_analyses:
            return {}
        
        times = [analysis.time_analysis.estimated_time for analysis in route_analyses]
        costs = [analysis.cost_analysis.total_cost for analysis in route_analyses]
        stress_levels = [analysis.stress_analysis.overall_stress for analysis in route_analyses]
        reliability_scores = [analysis.reliability_analysis.overall_reliability for analysis in route_analyses]
        
        return {
            "time_performance": {
                "fastest": min(times),
                "slowest": max(times),
                "average": sum(times) / len(times),
                "variance": max(times) - min(times)
            },
            "cost_performance": {
                "cheapest": min(costs),
                "most_expensive": max(costs),
                "average": sum(costs) / len(costs),
                "variance": max(costs) - min(costs)
            },
            "stress_performance": {
                "least_stressful": min(stress_levels),
                "most_stressful": max(stress_levels),
                "average": sum(stress_levels) / len(stress_levels),
                "variance": max(stress_levels) - min(stress_levels)
            },
            "reliability_performance": {
                "most_reliable": max(reliability_scores),
                "least_reliable": min(reliability_scores),
                "average": sum(reliability_scores) / len(reliability_scores),
                "variance": max(reliability_scores) - min(reliability_scores)
            }
        }
    
    def _analyze_external_condition_factors(self, current_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze external condition factors affecting the decision."""
        weather_data = current_conditions.get('weather_data', {})
        traffic_data = current_conditions.get('traffic_data', {})
        transit_data = current_conditions.get('transit_data', {})
        
        return {
            "weather_conditions": {
                "condition": weather_data.get('condition', 'clear'),
                "temperature": weather_data.get('temperature', 20),
                "impact_level": self._assess_weather_impact_level(weather_data.get('condition', 'clear'))
            },
            "traffic_conditions": {
                "congestion_level": traffic_data.get('congestion_level', 'moderate'),
                "impact_level": self._assess_traffic_impact_level(traffic_data.get('congestion_level', 'moderate'))
            },
            "transit_conditions": {
                "service_status": transit_data.get('service_status', 'normal'),
                "impact_level": self._assess_transit_impact_level(transit_data.get('service_status', 'normal'))
            }
        }
    
    def _analyze_personal_priority_factors(self, user_preferences: Optional[PreferenceProfile]) -> Dict[str, Any]:
        """Analyze personal priority factors affecting the decision."""
        if not user_preferences:
            return {"preferences_specified": False}
        
        # Find top priority
        priorities = {
            'time': user_preferences.time_weight,
            'cost': user_preferences.cost_weight,
            'comfort': user_preferences.comfort_weight,
            'reliability': user_preferences.reliability_weight
        }
        
        top_priority = max(priorities, key=priorities.get)
        
        return {
            "preferences_specified": True,
            "priority_weights": priorities,
            "top_priority": top_priority,
            "top_priority_weight": priorities[top_priority],
            "preference_distribution": self._categorize_preference_distribution(priorities),
            "preferred_modes": user_preferences.preferred_modes,
            "avoided_features": user_preferences.avoided_features
        }
    
    def _analyze_risk_assessment_factors(
        self, 
        routes: List[Route], 
        route_analyses: List[RouteAnalysis], 
        current_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze risk assessment factors for decision making."""
        if not route_analyses:
            return {}
        
        incident_probs = [analysis.reliability_analysis.incident_probability for analysis in route_analyses]
        weather_impacts = [analysis.reliability_analysis.weather_impact for analysis in route_analyses]
        time_variances = [analysis.reliability_analysis.historical_variance for analysis in route_analyses]
        
        return {
            "incident_risk": {
                "highest_risk": max(incident_probs),
                "lowest_risk": min(incident_probs),
                "average_risk": sum(incident_probs) / len(incident_probs),
                "high_risk_routes": sum(1 for prob in incident_probs if prob > 0.25)
            },
            "weather_risk": {
                "highest_impact": max(weather_impacts),
                "lowest_impact": min(weather_impacts),
                "average_impact": sum(weather_impacts) / len(weather_impacts),
                "weather_sensitive_routes": sum(1 for impact in weather_impacts if impact > 0.3)
            },
            "timing_risk": {
                "highest_variance": max(time_variances),
                "lowest_variance": min(time_variances),
                "average_variance": sum(time_variances) / len(time_variances),
                "unpredictable_routes": sum(1 for variance in time_variances if variance > 15)
            }
        }
    
    def _analyze_trade_off_factors(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> Dict[str, Any]:
        """Analyze trade-off factors between routes."""
        if len(route_analyses) < 2:
            return {"trade_offs_available": False}
        
        # Find best route in each category
        times = [analysis.time_analysis.estimated_time for analysis in route_analyses]
        costs = [analysis.cost_analysis.total_cost for analysis in route_analyses]
        stress_levels = [analysis.stress_analysis.overall_stress for analysis in route_analyses]
        reliability_scores = [analysis.reliability_analysis.overall_reliability for analysis in route_analyses]
        
        fastest_idx = times.index(min(times))
        cheapest_idx = costs.index(min(costs))
        least_stressful_idx = stress_levels.index(min(stress_levels))
        most_reliable_idx = reliability_scores.index(max(reliability_scores))
        
        # Check if different routes excel in different areas
        unique_leaders = len(set([fastest_idx, cheapest_idx, least_stressful_idx, most_reliable_idx]))
        
        trade_offs = []
        
        # Time vs Cost trade-off
        if fastest_idx != cheapest_idx:
            time_diff = times[cheapest_idx] - times[fastest_idx]
            cost_diff = costs[fastest_idx] - costs[cheapest_idx]
            if time_diff > 10 and cost_diff > 2.0:
                trade_offs.append({
                    "type": "time_vs_cost",
                    "description": f"Fastest route costs ${cost_diff:.2f} more but saves {time_diff:.0f} minutes"
                })
        
        # Stress vs Time trade-off
        if fastest_idx != least_stressful_idx:
            time_diff = times[least_stressful_idx] - times[fastest_idx]
            stress_diff = stress_levels[fastest_idx] - stress_levels[least_stressful_idx]
            if time_diff > 10 and stress_diff > 2:
                trade_offs.append({
                    "type": "time_vs_stress",
                    "description": f"Fastest route is {stress_diff:.0f} points more stressful but saves {time_diff:.0f} minutes"
                })
        
        return {
            "trade_offs_available": True,
            "unique_category_leaders": unique_leaders,
            "identified_trade_offs": trade_offs,
            "trade_off_complexity": "high" if unique_leaders > 2 else "medium" if unique_leaders > 1 else "low"
        }
    
    def _analyze_decision_confidence_factors(self, routes: List[Route], route_analyses: List[RouteAnalysis]) -> Dict[str, Any]:
        """Analyze factors that affect decision confidence."""
        if not route_analyses:
            return {}
        
        # Calculate performance gaps between routes
        times = [analysis.time_analysis.estimated_time for analysis in route_analyses]
        costs = [analysis.cost_analysis.total_cost for analysis in route_analyses]
        stress_levels = [analysis.stress_analysis.overall_stress for analysis in route_analyses]
        reliability_scores = [analysis.reliability_analysis.overall_reliability for analysis in route_analyses]
        
        time_gap = max(times) - min(times)
        cost_gap = max(costs) - min(costs)
        stress_gap = max(stress_levels) - min(stress_levels)
        reliability_gap = max(reliability_scores) - min(reliability_scores)
        
        # Assess confidence based on gaps
        confidence_factors = []
        
        if time_gap > 20:
            confidence_factors.append("Large time differences make choice clearer")
        elif time_gap < 5:
            confidence_factors.append("Similar travel times make choice more difficult")
        
        if cost_gap > 5.0:
            confidence_factors.append("Significant cost differences aid decision")
        elif cost_gap < 1.0:
            confidence_factors.append("Similar costs require considering other factors")
        
        if stress_gap > 3:
            confidence_factors.append("Clear stress level differences help prioritize")
        
        if reliability_gap > 3:
            confidence_factors.append("Reliability differences provide clear guidance")
        
        # Overall confidence assessment
        significant_gaps = sum([
            1 for gap in [time_gap, cost_gap, stress_gap, reliability_gap]
            if gap > 0.3 * (max(times) if gap == time_gap else 
                           max(costs) if gap == cost_gap else
                           max(stress_levels) if gap == stress_gap else
                           max(reliability_scores))
        ])
        
        confidence_level = "high" if significant_gaps >= 3 else "medium" if significant_gaps >= 2 else "low"
        
        return {
            "performance_gaps": {
                "time_gap": time_gap,
                "cost_gap": cost_gap,
                "stress_gap": stress_gap,
                "reliability_gap": reliability_gap
            },
            "confidence_factors": confidence_factors,
            "confidence_level": confidence_level,
            "significant_differences": significant_gaps
        }
    
    def _assess_weather_impact_level(self, weather_condition: str) -> str:
        """Assess the impact level of weather conditions."""
        impact_levels = {
            'clear': 'none',
            'cloudy': 'minimal',
            'light_rain': 'low',
            'rain': 'medium',
            'heavy_rain': 'high',
            'snow': 'medium',
            'heavy_snow': 'high',
            'fog': 'medium',
            'storm': 'high',
            'ice': 'very_high'
        }
        return impact_levels.get(weather_condition, 'unknown')
    
    def _assess_traffic_impact_level(self, congestion_level: str) -> str:
        """Assess the impact level of traffic conditions."""
        impact_levels = {
            'light': 'low',
            'moderate': 'medium',
            'heavy': 'high',
            'severe': 'very_high'
        }
        return impact_levels.get(congestion_level, 'unknown')
    
    def _assess_transit_impact_level(self, service_status: str) -> str:
        """Assess the impact level of transit conditions."""
        impact_levels = {
            'normal': 'none',
            'minor_delays': 'low',
            'delays': 'medium',
            'major_delays': 'high',
            'disrupted': 'high',
            'suspended': 'very_high',
            'cancelled': 'very_high'
        }
        return impact_levels.get(service_status, 'unknown')
    
    def _categorize_preference_distribution(self, priorities: Dict[str, int]) -> str:
        """Categorize the distribution of user preferences."""
        max_weight = max(priorities.values())
        min_weight = min(priorities.values())
        
        if max_weight >= 70:
            return "heavily_weighted"  # One preference dominates
        elif max_weight - min_weight <= 20:
            return "balanced"  # Relatively even distribution
        elif max_weight >= 50:
            return "moderately_weighted"  # Some preference but not extreme
        else:
            return "unclear"  # No clear preference pattern