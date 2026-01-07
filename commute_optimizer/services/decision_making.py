"""Decision Making Engine for route ranking and recommendation generation."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from commute_optimizer.models import (
    Route, RouteAnalysis, PreferenceProfile, UserPreferences,
    TradeoffSummary, ComparisonPoint
)


class DecisionMakingEngine:
    """
    Engine for applying user preferences to route analysis and providing transparent recommendations.
    
    This class implements the core decision-making logic that transforms route analysis data
    into user-centric recommendations with clear explanations and trade-off analysis.
    """
    
    def __init__(self):
        """Initialize the decision making engine."""
        pass
    
    def rank_routes(
        self, 
        routes: List[Route], 
        route_analyses: List[RouteAnalysis],
        user_preferences: PreferenceProfile
    ) -> List[Tuple[Route, RouteAnalysis, float]]:
        """
        Rank routes based on weighted criteria from user preferences.
        
        Args:
            routes: List of routes to rank
            route_analyses: Corresponding route analyses
            user_preferences: User's preference profile with weights
            
        Returns:
            List of tuples (route, analysis, score) sorted by score (highest first)
            
        Validates: Requirements 3.2, 4.1, 4.2
        """
        if len(routes) != len(route_analyses):
            raise ValueError("Number of routes must match number of analyses")
        
        scored_routes = []
        
        for route, analysis in zip(routes, route_analyses):
            score = self._calculate_weighted_score(route, analysis, user_preferences)
            scored_routes.append((route, analysis, score))
        
        # Sort by score (highest first)
        scored_routes.sort(key=lambda x: x[2], reverse=True)
        
        return scored_routes
    
    def generate_recommendation(
        self, 
        ranked_routes: List[Tuple[Route, RouteAnalysis, float]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate contextual recommendation with reasoning.
        
        Args:
            ranked_routes: Routes ranked by preference score
            context: Current conditions and context information
            
        Returns:
            Dictionary containing recommendation with reasoning
            
        Validates: Requirements 3.2, 4.1, 4.2
        """
        if not ranked_routes:
            return {
                "recommended_route": None,
                "reasoning": "No viable routes available",
                "confidence": 0.0,
                "alternatives": []
            }
        
        if context is None:
            context = {}
        
        # Get the top-ranked route
        top_route, top_analysis, top_score = ranked_routes[0]
        
        # Generate reasoning for the recommendation
        reasoning = self._generate_recommendation_reasoning(
            top_route, top_analysis, top_score, ranked_routes[1:], context
        )
        
        # Calculate confidence based on score gap and route characteristics
        confidence = self._calculate_recommendation_confidence(ranked_routes)
        
        # Prepare alternative routes
        alternatives = []
        for route, analysis, score in ranked_routes[1:3]:  # Up to 2 alternatives
            alternatives.append({
                "route": route,
                "analysis": analysis,
                "score": score,
                "why_not_recommended": self._explain_why_not_recommended(
                    route, analysis, top_route, top_analysis
                )
            })
        
        return {
            "recommended_route": top_route,
            "recommended_analysis": top_analysis,
            "score": top_score,
            "reasoning": reasoning,
            "confidence": confidence,
            "alternatives": alternatives,
            "context_factors": self._identify_context_factors(context)
        }
    
    def explain_tradeoffs(
        self, 
        routes: List[Route], 
        route_analyses: List[RouteAnalysis]
    ) -> Dict[str, Any]:
        """
        Generate clear trade-off explanations between routes.
        
        Args:
            routes: List of routes to compare
            route_analyses: Corresponding route analyses
            
        Returns:
            Dictionary containing comprehensive trade-off explanations
            
        Validates: Requirements 3.2, 4.1, 4.2
        """
        if len(routes) != len(route_analyses):
            raise ValueError("Number of routes must match number of analyses")
        
        if len(routes) < 2:
            return {
                "comparison_matrix": [],
                "key_tradeoffs": [],
                "decision_factors": []
            }
        
        # Create comparison matrix
        comparison_matrix = self._create_comparison_matrix(routes, route_analyses)
        
        # Identify key trade-offs
        key_tradeoffs = self._identify_key_tradeoffs(routes, route_analyses)
        
        # Extract decision factors
        decision_factors = self._extract_decision_factors(routes, route_analyses)
        
        return {
            "comparison_matrix": comparison_matrix,
            "key_tradeoffs": key_tradeoffs,
            "decision_factors": decision_factors,
            "summary": self._generate_tradeoff_summary(routes, route_analyses)
        }
    
    def identify_when_not_to_choose(
        self, 
        route: Route, 
        analysis: RouteAnalysis,
        alternatives: List[Tuple[Route, RouteAnalysis]] = None
    ) -> List[str]:
        """
        Generate "when NOT to choose" guidance for a route.
        
        Args:
            route: Route to analyze
            analysis: Route analysis
            alternatives: Alternative routes for comparison
            
        Returns:
            List of scenarios when this route should not be chosen
            
        Validates: Requirements 4.1, 4.2, 5.1, 5.3
        """
        if alternatives is None:
            alternatives = []
        
        warnings = []
        
        # Time-based warnings
        if analysis.time_analysis.estimated_time > 60:
            warnings.append("When you have time constraints - this route takes over an hour")
        
        if analysis.time_analysis.time_range_max - analysis.time_analysis.time_range_min > 20:
            warnings.append("When punctuality is critical - travel time can vary by 20+ minutes")
        
        # Cost-based warnings
        if analysis.cost_analysis.total_cost > 15.0:
            warnings.append("When budget is tight - this is an expensive option")
        
        # Stress-based warnings
        if analysis.stress_analysis.overall_stress >= 7:
            warnings.append("When you're already stressed - this route has high stress levels")
        
        if analysis.stress_analysis.traffic_stress >= 8:
            warnings.append("During heavy traffic periods - expect significant congestion stress")
        
        # Reliability-based warnings
        if analysis.reliability_analysis.overall_reliability <= 5:
            warnings.append("For important appointments - this route has unpredictable timing")
        
        if analysis.reliability_analysis.incident_probability > 0.3:
            warnings.append("When you can't afford delays - high chance of incidents on this route")
        
        # Weather-based warnings
        if analysis.reliability_analysis.weather_impact > 0.4:
            warnings.append("In bad weather - this route is significantly affected by weather conditions")
        
        # Mode-specific warnings
        from commute_optimizer.models import TransportationMode
        
        if TransportationMode.CYCLING in route.transportation_modes:
            warnings.append("In rain, snow, or extreme temperatures")
            warnings.append("When you need to arrive looking professional")
        
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            warnings.append("During transit strikes or major service disruptions")
            warnings.append("When carrying large or heavy items")
        
        if TransportationMode.DRIVING in route.transportation_modes:
            warnings.append("When parking is unavailable or very expensive")
            warnings.append("During major traffic incidents on your route")
        
        # Comparative warnings (when alternatives exist)
        if alternatives:
            self._add_comparative_warnings(warnings, route, analysis, alternatives)
        
        return warnings
    
    def generate_tradeoff_explanation_templates(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis]
    ) -> Dict[str, Any]:
        """
        Generate structured trade-off explanation templates for route comparisons.
        
        Args:
            routes: List of routes to compare
            route_analyses: Corresponding route analyses
            
        Returns:
            Dictionary containing structured explanation templates
            
        Validates: Requirements 4.1, 4.2, 5.1, 5.3
        """
        if len(routes) != len(route_analyses):
            raise ValueError("Number of routes must match number of analyses")
        
        if len(routes) < 2:
            return {
                "templates": [],
                "summary": "Only one route available - no trade-offs to explain."
            }
        
        templates = []
        
        # Generate templates for each route
        for i, (route, analysis) in enumerate(zip(routes, route_analyses)):
            route_name = f"Route {i + 1}"
            
            # Create explanation template for this route
            template = {
                "route_id": route.id,
                "route_name": route_name,
                "strengths": self._identify_route_strengths(route, analysis, routes, route_analyses),
                "weaknesses": self._identify_route_weaknesses(route, analysis, routes, route_analyses),
                "trade_offs": self._generate_specific_tradeoffs(route, analysis, routes, route_analyses),
                "when_to_choose": self._generate_when_to_choose_guidance(route, analysis),
                "when_not_to_choose": self.identify_when_not_to_choose(
                    route, analysis, [(r, a) for r, a in zip(routes, route_analyses) if r.id != route.id]
                ),
                "comparison_highlights": self._generate_comparison_highlights(route, analysis, routes, route_analyses)
            }
            
            templates.append(template)
        
        return {
            "templates": templates,
            "summary": self._generate_overall_tradeoff_summary(routes, route_analyses),
            "decision_guidance": self._generate_decision_guidance(routes, route_analyses)
        }
    
    def make_decision_factors_visible(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        user_preferences: PreferenceProfile,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make all decision factors visible and transparent to users.
        
        Args:
            routes: List of routes being considered
            route_analyses: Corresponding route analyses
            user_preferences: User's preference profile
            context: Current context information
            
        Returns:
            Dictionary containing all visible decision factors
            
        Validates: Requirements 4.1, 4.2, 5.1, 5.3
        """
        if context is None:
            context = {}
        
        # Calculate scores for transparency
        scored_routes = self.rank_routes(routes, route_analyses, user_preferences)
        
        decision_factors = {
            "preference_weights": {
                "time_weight": user_preferences.time_weight,
                "cost_weight": user_preferences.cost_weight,
                "comfort_weight": user_preferences.comfort_weight,
                "reliability_weight": user_preferences.reliability_weight
            },
            "scoring_breakdown": [],
            "context_factors": self._identify_context_factors(context),
            "route_comparisons": self._create_detailed_comparison_matrix(routes, route_analyses),
            "decision_logic": self._explain_decision_logic(scored_routes, user_preferences),
            "uncertainty_factors": self._identify_uncertainty_factors(routes, route_analyses, context),
            "assumptions": self._list_decision_assumptions(routes, route_analyses, context)
        }
        
        # Add detailed scoring breakdown for each route
        for route, analysis, score in scored_routes:
            breakdown = self._calculate_score_breakdown(route, analysis, user_preferences)
            decision_factors["scoring_breakdown"].append({
                "route_id": route.id,
                "total_score": score,
                "component_scores": breakdown,
                "score_explanation": self._explain_score_calculation(breakdown, user_preferences)
            })
        
        return decision_factors
    
    def _calculate_weighted_score(
        self, 
        route: Route, 
        analysis: RouteAnalysis, 
        preferences: PreferenceProfile
    ) -> float:
        """
        Calculate weighted score based on user preferences.
        
        Converts route characteristics to normalized scores (0-1) and applies preference weights.
        """
        # Normalize scores to 0-1 scale (higher is better)
        
        # Time score (lower time is better)
        time_score = max(0, 1 - (analysis.time_analysis.estimated_time / 120))  # 120 min = 0 score
        
        # Cost score (lower cost is better)
        cost_score = max(0, 1 - (analysis.cost_analysis.total_cost / 20))  # $20 = 0 score
        
        # Comfort score (lower stress is better)
        comfort_score = (10 - analysis.stress_analysis.overall_stress) / 9  # Convert 1-10 to 0-1
        
        # Reliability score (higher reliability is better)
        reliability_score = (analysis.reliability_analysis.overall_reliability - 1) / 9  # Convert 1-10 to 0-1
        
        # Apply preference weights (convert percentages to decimals)
        weighted_score = (
            (time_score * preferences.time_weight / 100) +
            (cost_score * preferences.cost_weight / 100) +
            (comfort_score * preferences.comfort_weight / 100) +
            (reliability_score * preferences.reliability_weight / 100)
        )
        
        return max(0.0, min(1.0, weighted_score))  # Ensure score is between 0 and 1
    
    def _generate_recommendation_reasoning(
        self,
        recommended_route: Route,
        recommended_analysis: RouteAnalysis,
        score: float,
        alternatives: List[Tuple[Route, RouteAnalysis, float]],
        context: Dict[str, Any]
    ) -> str:
        """Generate clear reasoning for why a route was recommended."""
        reasons = []
        
        # Score-based reasoning
        if score > 0.8:
            reasons.append("This route scores highly across your priority criteria")
        elif score > 0.6:
            reasons.append("This route provides a good balance for your preferences")
        else:
            reasons.append("This route is the best available option given current conditions")
        
        # Specific strength-based reasoning
        time_minutes = recommended_analysis.time_analysis.estimated_time
        cost = recommended_analysis.cost_analysis.total_cost
        stress = recommended_analysis.stress_analysis.overall_stress
        reliability = recommended_analysis.reliability_analysis.overall_reliability
        
        if time_minutes <= 30:
            reasons.append(f"Quick {time_minutes}-minute journey")
        
        if cost <= 3.0:
            reasons.append(f"Affordable at ${cost:.2f}")
        
        if stress <= 4:
            reasons.append("Low-stress travel experience")
        
        if reliability >= 8:
            reasons.append("Highly reliable timing")
        
        # Context-based reasoning
        weather_data = context.get('weather_data', {})
        if weather_data.get('condition') in ['rain', 'snow']:
            if any(mode.value in ['public_transit', 'driving'] 
                   for mode in recommended_route.transportation_modes):
                reasons.append("Good choice for current weather conditions")
        
        traffic_data = context.get('traffic_data', {})
        if traffic_data.get('congestion_level') == 'heavy':
            if recommended_analysis.stress_analysis.traffic_stress <= 5:
                reasons.append("Avoids the worst traffic congestion")
        
        # Comparative reasoning
        if alternatives:
            best_alternative = alternatives[0]
            alt_analysis = best_alternative[1]
            
            if recommended_analysis.time_analysis.estimated_time < alt_analysis.time_analysis.estimated_time:
                time_diff = alt_analysis.time_analysis.estimated_time - recommended_analysis.time_analysis.estimated_time
                reasons.append(f"Saves {time_diff} minutes compared to alternatives")
            
            if recommended_analysis.cost_analysis.total_cost < alt_analysis.cost_analysis.total_cost:
                cost_diff = alt_analysis.cost_analysis.total_cost - recommended_analysis.cost_analysis.total_cost
                reasons.append(f"Saves ${cost_diff:.2f} compared to alternatives")
        
        return ". ".join(reasons) + "."
    
    def _calculate_recommendation_confidence(
        self, 
        ranked_routes: List[Tuple[Route, RouteAnalysis, float]]
    ) -> float:
        """Calculate confidence in the recommendation based on score gaps."""
        if len(ranked_routes) < 2:
            return 1.0  # Perfect confidence if only one option
        
        top_score = ranked_routes[0][2]
        second_score = ranked_routes[1][2]
        
        # Confidence based on score gap
        score_gap = top_score - second_score
        
        if score_gap > 0.3:
            return 0.9  # High confidence
        elif score_gap > 0.15:
            return 0.7  # Medium confidence
        elif score_gap > 0.05:
            return 0.5  # Low confidence
        else:
            return 0.3  # Very low confidence - routes are very similar
    
    def _explain_why_not_recommended(
        self,
        route: Route,
        analysis: RouteAnalysis,
        recommended_route: Route,
        recommended_analysis: RouteAnalysis
    ) -> str:
        """Explain why an alternative route was not recommended."""
        reasons = []
        
        # Compare key metrics
        time_diff = analysis.time_analysis.estimated_time - recommended_analysis.time_analysis.estimated_time
        if time_diff > 10:
            reasons.append(f"Takes {time_diff} minutes longer")
        
        cost_diff = analysis.cost_analysis.total_cost - recommended_analysis.cost_analysis.total_cost
        if cost_diff > 2.0:
            reasons.append(f"Costs ${cost_diff:.2f} more")
        
        stress_diff = analysis.stress_analysis.overall_stress - recommended_analysis.stress_analysis.overall_stress
        if stress_diff > 2:
            reasons.append("Significantly more stressful")
        
        reliability_diff = recommended_analysis.reliability_analysis.overall_reliability - analysis.reliability_analysis.overall_reliability
        if reliability_diff > 2:
            reasons.append("Less reliable timing")
        
        if not reasons:
            reasons.append("Slightly lower overall score based on your preferences")
        
        return "; ".join(reasons)
    
    def _identify_context_factors(self, context: Dict[str, Any]) -> List[str]:
        """Identify relevant context factors that influenced the recommendation."""
        factors = []
        
        weather_data = context.get('weather_data', {})
        weather_condition = weather_data.get('condition', 'clear')
        if weather_condition != 'clear':
            factors.append(f"Current weather: {weather_condition}")
        
        traffic_data = context.get('traffic_data', {})
        congestion_level = traffic_data.get('congestion_level', 'moderate')
        if congestion_level in ['heavy', 'severe']:
            factors.append(f"Traffic conditions: {congestion_level} congestion")
        
        transit_data = context.get('transit_data', {})
        service_status = transit_data.get('service_status', 'normal')
        if service_status != 'normal':
            factors.append(f"Transit status: {service_status}")
        
        return factors
    
    def _create_comparison_matrix(
        self, 
        routes: List[Route], 
        analyses: List[RouteAnalysis]
    ) -> List[Dict[str, Any]]:
        """Create a matrix comparing routes across all criteria."""
        matrix = []
        
        criteria = ['Time', 'Cost', 'Stress', 'Reliability']
        
        for i, (route, analysis) in enumerate(zip(routes, analyses)):
            route_comparison = {
                'route_id': route.id,
                'route_name': f"Route {i + 1}",
                'transportation_modes': [mode.value for mode in route.transportation_modes],
                'comparisons': {}
            }
            
            # Add values for each criterion
            route_comparison['comparisons']['Time'] = {
                'value': analysis.time_analysis.estimated_time,
                'unit': 'minutes',
                'display': f"{analysis.time_analysis.estimated_time} min"
            }
            
            route_comparison['comparisons']['Cost'] = {
                'value': analysis.cost_analysis.total_cost,
                'unit': 'dollars',
                'display': f"${analysis.cost_analysis.total_cost:.2f}"
            }
            
            route_comparison['comparisons']['Stress'] = {
                'value': analysis.stress_analysis.overall_stress,
                'unit': 'scale_1_10',
                'display': f"{analysis.stress_analysis.overall_stress}/10"
            }
            
            route_comparison['comparisons']['Reliability'] = {
                'value': analysis.reliability_analysis.overall_reliability,
                'unit': 'scale_1_10',
                'display': f"{analysis.reliability_analysis.overall_reliability}/10"
            }
            
            matrix.append(route_comparison)
        
        return matrix
    
    def _identify_key_tradeoffs(
        self, 
        routes: List[Route], 
        analyses: List[RouteAnalysis]
    ) -> List[Dict[str, Any]]:
        """Identify the most significant trade-offs between routes."""
        if len(routes) < 2:
            return []
        
        tradeoffs = []
        
        # Find routes with significant differences
        for i in range(len(routes)):
            for j in range(i + 1, len(routes)):
                route1, analysis1 = routes[i], analyses[i]
                route2, analysis2 = routes[j], analyses[j]
                
                # Time vs Cost tradeoff
                time_diff = analysis2.time_analysis.estimated_time - analysis1.time_analysis.estimated_time
                cost_diff = analysis1.cost_analysis.total_cost - analysis2.cost_analysis.total_cost
                
                if time_diff > 15 and cost_diff > 3.0:  # Route 1 faster but more expensive
                    tradeoffs.append({
                        'type': 'time_vs_cost',
                        'route1': f"Route {i + 1}",
                        'route2': f"Route {j + 1}",
                        'description': f"Route {i + 1} is {time_diff} minutes faster but costs ${cost_diff:.2f} more"
                    })
                
                # Stress vs Time tradeoff
                stress_diff = analysis1.stress_analysis.overall_stress - analysis2.stress_analysis.overall_stress
                if time_diff > 10 and stress_diff > 2:  # Route 1 faster but more stressful
                    tradeoffs.append({
                        'type': 'time_vs_stress',
                        'route1': f"Route {i + 1}",
                        'route2': f"Route {j + 1}",
                        'description': f"Route {i + 1} is {time_diff} minutes faster but {stress_diff} points more stressful"
                    })
                
                # Reliability vs Cost tradeoff
                reliability_diff = analysis1.reliability_analysis.overall_reliability - analysis2.reliability_analysis.overall_reliability
                if reliability_diff > 2 and cost_diff > 2.0:  # Route 1 more reliable but more expensive
                    tradeoffs.append({
                        'type': 'reliability_vs_cost',
                        'route1': f"Route {i + 1}",
                        'route2': f"Route {j + 1}",
                        'description': f"Route {i + 1} is more reliable but costs ${cost_diff:.2f} more"
                    })
        
        return tradeoffs
    
    def _extract_decision_factors(
        self, 
        routes: List[Route], 
        analyses: List[RouteAnalysis]
    ) -> List[Dict[str, Any]]:
        """Extract key factors that should influence the decision."""
        factors = []
        
        # Time factor
        times = [analysis.time_analysis.estimated_time for analysis in analyses]
        min_time, max_time = min(times), max(times)
        if max_time - min_time > 15:  # Significant time difference
            factors.append({
                'factor': 'Travel Time',
                'importance': 'high',
                'description': f"Routes vary from {min_time} to {max_time} minutes",
                'consideration': "Choose based on your schedule flexibility"
            })
        
        # Cost factor
        costs = [analysis.cost_analysis.total_cost for analysis in analyses]
        min_cost, max_cost = min(costs), max(costs)
        if max_cost - min_cost > 3.0:  # Significant cost difference
            factors.append({
                'factor': 'Cost',
                'importance': 'medium',
                'description': f"Routes vary from ${min_cost:.2f} to ${max_cost:.2f}",
                'consideration': "Consider your budget priorities"
            })
        
        # Stress factor
        stress_levels = [analysis.stress_analysis.overall_stress for analysis in analyses]
        min_stress, max_stress = min(stress_levels), max(stress_levels)
        if max_stress - min_stress > 3:  # Significant stress difference
            factors.append({
                'factor': 'Stress Level',
                'importance': 'high',
                'description': f"Routes vary from {min_stress}/10 to {max_stress}/10 stress",
                'consideration': "Consider your tolerance for commute stress"
            })
        
        # Reliability factor
        reliability_scores = [analysis.reliability_analysis.overall_reliability for analysis in analyses]
        min_reliability, max_reliability = min(reliability_scores), max(reliability_scores)
        if max_reliability - min_reliability > 2:  # Significant reliability difference
            factors.append({
                'factor': 'Reliability',
                'importance': 'high',
                'description': f"Routes vary from {min_reliability}/10 to {max_reliability}/10 reliability",
                'consideration': "Consider how important punctuality is today"
            })
        
        return factors
    
    def _generate_tradeoff_summary(
        self, 
        routes: List[Route], 
        analyses: List[RouteAnalysis]
    ) -> str:
        """Generate a high-level summary of the trade-offs."""
        if len(routes) < 2:
            return "Only one route available - no trade-offs to consider."
        
        # Find the route that's best in each category
        times = [(analysis.time_analysis.estimated_time, i) for i, analysis in enumerate(analyses)]
        costs = [(analysis.cost_analysis.total_cost, i) for i, analysis in enumerate(analyses)]
        stress_levels = [(analysis.stress_analysis.overall_stress, i) for i, analysis in enumerate(analyses)]
        reliability_scores = [(analysis.reliability_analysis.overall_reliability, i) for i, analysis in enumerate(analyses)]
        
        fastest_route = min(times)[1] + 1
        cheapest_route = min(costs)[1] + 1
        least_stressful_route = min(stress_levels)[1] + 1
        most_reliable_route = max(reliability_scores)[1] + 1
        
        summary_parts = []
        
        if fastest_route == cheapest_route == least_stressful_route == most_reliable_route:
            summary_parts.append(f"Route {fastest_route} is clearly the best choice across all criteria.")
        else:
            summary_parts.append(f"Route {fastest_route} is fastest")
            if cheapest_route != fastest_route:
                summary_parts.append(f"Route {cheapest_route} is cheapest")
            if least_stressful_route not in [fastest_route, cheapest_route]:
                summary_parts.append(f"Route {least_stressful_route} is least stressful")
            if most_reliable_route not in [fastest_route, cheapest_route, least_stressful_route]:
                summary_parts.append(f"Route {most_reliable_route} is most reliable")
        
        if len(summary_parts) > 1:
            return ", ".join(summary_parts[:-1]) + f", and {summary_parts[-1]}. Choose based on your priorities."
        else:
            return summary_parts[0]
    
    def _add_comparative_warnings(
        self,
        warnings: List[str],
        route: Route,
        analysis: RouteAnalysis,
        alternatives: List[Tuple[Route, RouteAnalysis]]
    ) -> None:
        """Add warnings based on comparison with alternatives."""
        if not alternatives:
            return
        
        # Find if this route is significantly worse in any category
        alt_times = [alt_analysis.time_analysis.estimated_time for _, alt_analysis in alternatives]
        alt_costs = [alt_analysis.cost_analysis.total_cost for _, alt_analysis in alternatives]
        alt_stress = [alt_analysis.stress_analysis.overall_stress for _, alt_analysis in alternatives]
        alt_reliability = [alt_analysis.reliability_analysis.overall_reliability for _, alt_analysis in alternatives]
        
        min_alt_time = min(alt_times)
        min_alt_cost = min(alt_costs)
        min_alt_stress = min(alt_stress)
        max_alt_reliability = max(alt_reliability)
        
        # Time comparison
        if analysis.time_analysis.estimated_time > min_alt_time + 20:
            time_diff = analysis.time_analysis.estimated_time - min_alt_time
            warnings.append(f"When time is important - alternatives are {time_diff} minutes faster")
        
        # Cost comparison
        if analysis.cost_analysis.total_cost > min_alt_cost + 5.0:
            cost_diff = analysis.cost_analysis.total_cost - min_alt_cost
            warnings.append(f"When budget matters - alternatives cost ${cost_diff:.2f} less")
        
        # Stress comparison
        if analysis.stress_analysis.overall_stress > min_alt_stress + 3:
            warnings.append("When you want a relaxing commute - alternatives are much less stressful")
        
        # Reliability comparison
        if analysis.reliability_analysis.overall_reliability < max_alt_reliability - 3:
            warnings.append("When punctuality is critical - alternatives are much more reliable")
    
    def apply_dynamic_preference_weights(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        base_preferences: PreferenceProfile,
        weight_adjustments: Dict[str, int]
    ) -> List[Tuple[Route, RouteAnalysis, float]]:
        """
        Apply dynamic preference weight adjustments and re-rank routes.
        
        Args:
            routes: List of routes to rank
            route_analyses: Corresponding route analyses
            base_preferences: Base preference profile
            weight_adjustments: Dictionary of weight adjustments (e.g., {'time_weight': 40})
            
        Returns:
            List of tuples (route, analysis, score) with updated rankings
            
        Validates: Requirements 3.1, 3.2, 3.4
        """
        # Create adjusted preferences
        adjusted_preferences = self._create_adjusted_preferences(base_preferences, weight_adjustments)
        
        # Validate that weights sum to 100
        self._validate_preference_weights(adjusted_preferences)
        
        # Re-rank routes with new preferences
        return self.rank_routes(routes, route_analyses, adjusted_preferences)
    
    def validate_preference_weights(self, preferences: PreferenceProfile) -> Dict[str, Any]:
        """
        Validate preference weights and return validation results.
        
        Args:
            preferences: Preference profile to validate
            
        Returns:
            Dictionary containing validation results and any errors
            
        Validates: Requirements 3.1, 3.2, 3.4
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'total_weight': 0
        }
        
        try:
            self._validate_preference_weights(preferences)
            validation_result['total_weight'] = (
                preferences.time_weight + preferences.cost_weight + 
                preferences.comfort_weight + preferences.reliability_weight
            )
        except ValueError as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(str(e))
        
        # Add warnings for extreme weight distributions
        weights = [preferences.time_weight, preferences.cost_weight, 
                  preferences.comfort_weight, preferences.reliability_weight]
        
        if max(weights) > 70:
            validation_result['warnings'].append(
                "One preference dominates (>70%) - consider balancing for better results"
            )
        
        if min(weights) == 0:
            validation_result['warnings'].append(
                "Some preferences are ignored (0%) - this may limit route options"
            )
        
        return validation_result
    
    def manage_preference_profiles(
        self,
        user_preferences: UserPreferences,
        action: str,
        profile_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Manage user preference profiles (create, update, delete, list).
        
        Args:
            user_preferences: User's current preferences
            action: Action to perform ('create', 'update', 'delete', 'list', 'set_default')
            profile_data: Data for the profile operation
            
        Returns:
            Dictionary containing operation result and updated preferences
            
        Validates: Requirements 3.1, 3.2, 3.4
        """
        result = {
            'success': False,
            'message': '',
            'updated_preferences': user_preferences,
            'profiles': []
        }
        
        if action == 'list':
            result['success'] = True
            result['profiles'] = [
                {
                    'name': profile.name,
                    'is_default': profile.name == user_preferences.default_profile,
                    'weights': {
                        'time': profile.time_weight,
                        'cost': profile.cost_weight,
                        'comfort': profile.comfort_weight,
                        'reliability': profile.reliability_weight
                    }
                }
                for profile in user_preferences.preference_profiles
            ]
            result['message'] = f"Found {len(result['profiles'])} preference profiles"
            
        elif action == 'create':
            if not profile_data or 'name' not in profile_data:
                result['message'] = "Profile name is required for creation"
                return result
            
            # Check if profile already exists
            if any(p.name == profile_data['name'] for p in user_preferences.preference_profiles):
                result['message'] = f"Profile '{profile_data['name']}' already exists"
                return result
            
            try:
                new_profile = self._create_preference_profile_from_data(profile_data)
                user_preferences.preference_profiles.append(new_profile)
                result['success'] = True
                result['message'] = f"Created profile '{new_profile.name}'"
                result['updated_preferences'] = user_preferences
                
            except ValueError as e:
                result['message'] = f"Failed to create profile: {str(e)}"
        
        elif action == 'update':
            if not profile_data or 'name' not in profile_data:
                result['message'] = "Profile name is required for update"
                return result
            
            # Find existing profile
            profile_to_update = None
            for i, profile in enumerate(user_preferences.preference_profiles):
                if profile.name == profile_data['name']:
                    profile_to_update = i
                    break
            
            if profile_to_update is None:
                result['message'] = f"Profile '{profile_data['name']}' not found"
                return result
            
            try:
                updated_profile = self._create_preference_profile_from_data(profile_data)
                user_preferences.preference_profiles[profile_to_update] = updated_profile
                result['success'] = True
                result['message'] = f"Updated profile '{updated_profile.name}'"
                result['updated_preferences'] = user_preferences
                
            except ValueError as e:
                result['message'] = f"Failed to update profile: {str(e)}"
        
        elif action == 'delete':
            if not profile_data or 'name' not in profile_data:
                result['message'] = "Profile name is required for deletion"
                return result
            
            profile_name = profile_data['name']
            
            # Don't allow deletion of default profile if it's the only one
            if (profile_name == user_preferences.default_profile and 
                len(user_preferences.preference_profiles) == 1):
                result['message'] = "Cannot delete the only remaining profile"
                return result
            
            # Find and remove profile
            original_count = len(user_preferences.preference_profiles)
            user_preferences.preference_profiles = [
                p for p in user_preferences.preference_profiles if p.name != profile_name
            ]
            
            if len(user_preferences.preference_profiles) < original_count:
                # If we deleted the default profile, set a new default
                if profile_name == user_preferences.default_profile:
                    user_preferences.default_profile = user_preferences.preference_profiles[0].name
                
                result['success'] = True
                result['message'] = f"Deleted profile '{profile_name}'"
                result['updated_preferences'] = user_preferences
            else:
                result['message'] = f"Profile '{profile_name}' not found"
        
        elif action == 'set_default':
            if not profile_data or 'name' not in profile_data:
                result['message'] = "Profile name is required to set default"
                return result
            
            profile_name = profile_data['name']
            
            # Check if profile exists
            if not any(p.name == profile_name for p in user_preferences.preference_profiles):
                result['message'] = f"Profile '{profile_name}' not found"
                return result
            
            user_preferences.default_profile = profile_name
            result['success'] = True
            result['message'] = f"Set '{profile_name}' as default profile"
            result['updated_preferences'] = user_preferences
        
        else:
            result['message'] = f"Unknown action: {action}"
        
        return result
    
    def get_preference_impact_analysis(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        current_preferences: PreferenceProfile,
        weight_changes: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Analyze how preference weight changes would impact route rankings.
        
        Args:
            routes: List of routes to analyze
            route_analyses: Corresponding route analyses
            current_preferences: Current preference profile
            weight_changes: Proposed weight changes
            
        Returns:
            Dictionary containing impact analysis
            
        Validates: Requirements 3.2, 3.5
        """
        # Get current rankings
        current_rankings = self.rank_routes(routes, route_analyses, current_preferences)
        
        # Get new rankings with proposed changes
        try:
            new_rankings = self.apply_dynamic_preference_weights(
                routes, route_analyses, current_preferences, weight_changes
            )
        except ValueError as e:
            return {
                'valid': False,
                'error': str(e),
                'impact': None
            }
        
        # Analyze the impact
        impact_analysis = {
            'valid': True,
            'ranking_changes': [],
            'score_changes': [],
            'new_recommendation': None,
            'recommendation_changed': False
        }
        
        # Track ranking changes
        current_order = [route.id for route, _, _ in current_rankings]
        new_order = [route.id for route, _, _ in new_rankings]
        
        for i, route_id in enumerate(current_order):
            old_position = i + 1
            new_position = new_order.index(route_id) + 1
            
            if old_position != new_position:
                impact_analysis['ranking_changes'].append({
                    'route_id': route_id,
                    'old_position': old_position,
                    'new_position': new_position,
                    'change': new_position - old_position
                })
        
        # Track score changes
        current_scores = {route.id: score for route, _, score in current_rankings}
        new_scores = {route.id: score for route, _, score in new_rankings}
        
        for route_id in current_scores:
            score_change = new_scores[route_id] - current_scores[route_id]
            if abs(score_change) > 0.01:  # Only significant changes
                impact_analysis['score_changes'].append({
                    'route_id': route_id,
                    'old_score': current_scores[route_id],
                    'new_score': new_scores[route_id],
                    'change': score_change
                })
        
        # Check if recommendation changed
        current_top_route = current_rankings[0][0].id
        new_top_route = new_rankings[0][0].id
        
        impact_analysis['recommendation_changed'] = current_top_route != new_top_route
        impact_analysis['new_recommendation'] = new_top_route
        
        return impact_analysis
    
    def _create_adjusted_preferences(
        self,
        base_preferences: PreferenceProfile,
        weight_adjustments: Dict[str, int]
    ) -> PreferenceProfile:
        """Create a new preference profile with adjusted weights."""
        # Start with base preferences
        adjusted_weights = {
            'time_weight': base_preferences.time_weight,
            'cost_weight': base_preferences.cost_weight,
            'comfort_weight': base_preferences.comfort_weight,
            'reliability_weight': base_preferences.reliability_weight
        }
        
        # Apply adjustments
        for weight_name, new_value in weight_adjustments.items():
            if weight_name in adjusted_weights:
                adjusted_weights[weight_name] = new_value
        
        # Create new preference profile
        return PreferenceProfile(
            name=f"{base_preferences.name}_adjusted",
            time_weight=adjusted_weights['time_weight'],
            cost_weight=adjusted_weights['cost_weight'],
            comfort_weight=adjusted_weights['comfort_weight'],
            reliability_weight=adjusted_weights['reliability_weight'],
            max_walking_distance=base_preferences.max_walking_distance,
            preferred_modes=base_preferences.preferred_modes.copy(),
            avoided_features=base_preferences.avoided_features.copy()
        )
    
    def _validate_preference_weights(self, preferences: PreferenceProfile) -> None:
        """
        Validate that preference weights sum to 100% and are within valid ranges.
        
        Raises:
            ValueError: If weights are invalid
        """
        total_weight = (preferences.time_weight + preferences.cost_weight + 
                       preferences.comfort_weight + preferences.reliability_weight)
        
        if total_weight != 100:
            raise ValueError(f"Preference weights must sum to 100%, got {total_weight}%")
        
        # Check individual weight ranges
        weights = {
            'time_weight': preferences.time_weight,
            'cost_weight': preferences.cost_weight,
            'comfort_weight': preferences.comfort_weight,
            'reliability_weight': preferences.reliability_weight
        }
        
        for weight_name, weight_value in weights.items():
            if not (0 <= weight_value <= 100):
                raise ValueError(f"{weight_name} must be between 0 and 100, got {weight_value}")
    
    def _create_preference_profile_from_data(self, profile_data: Dict[str, Any]) -> PreferenceProfile:
        """
        Create a PreferenceProfile from dictionary data.
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            PreferenceProfile instance
            
        Raises:
            ValueError: If profile data is invalid
        """
        required_fields = ['name', 'time_weight', 'cost_weight', 'comfort_weight', 'reliability_weight']
        
        for field in required_fields:
            if field not in profile_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create profile with validation
        profile = PreferenceProfile(
            name=profile_data['name'],
            time_weight=profile_data['time_weight'],
            cost_weight=profile_data['cost_weight'],
            comfort_weight=profile_data['comfort_weight'],
            reliability_weight=profile_data['reliability_weight'],
            max_walking_distance=profile_data.get('max_walking_distance', 2.0),
            preferred_modes=profile_data.get('preferred_modes', []),
            avoided_features=profile_data.get('avoided_features', [])
        )
        
        return profile
    
    def _identify_route_strengths(
        self,
        route: Route,
        analysis: RouteAnalysis,
        all_routes: List[Route],
        all_analyses: List[RouteAnalysis]
    ) -> List[str]:
        """Identify the strengths of a route compared to alternatives."""
        strengths = []
        
        # Compare against other routes
        other_analyses = [a for r, a in zip(all_routes, all_analyses) if r.id != route.id]
        
        if not other_analyses:
            return strengths
        
        # Time strengths
        other_times = [a.time_analysis.estimated_time for a in other_analyses]
        if analysis.time_analysis.estimated_time <= min(other_times):
            strengths.append(f"Fastest option at {analysis.time_analysis.estimated_time} minutes")
        elif analysis.time_analysis.estimated_time < sum(other_times) / len(other_times):
            strengths.append("Faster than average")
        
        # Cost strengths
        other_costs = [a.cost_analysis.total_cost for a in other_analyses]
        if analysis.cost_analysis.total_cost <= min(other_costs):
            strengths.append(f"Most affordable at ${analysis.cost_analysis.total_cost:.2f}")
        elif analysis.cost_analysis.total_cost < sum(other_costs) / len(other_costs):
            strengths.append("Below average cost")
        
        # Stress strengths
        other_stress = [a.stress_analysis.overall_stress for a in other_analyses]
        if analysis.stress_analysis.overall_stress <= min(other_stress):
            strengths.append("Least stressful option")
        elif analysis.stress_analysis.overall_stress < sum(other_stress) / len(other_stress):
            strengths.append("Lower stress than alternatives")
        
        # Reliability strengths
        other_reliability = [a.reliability_analysis.overall_reliability for a in other_analyses]
        if analysis.reliability_analysis.overall_reliability >= max(other_reliability):
            strengths.append("Most reliable timing")
        elif analysis.reliability_analysis.overall_reliability > sum(other_reliability) / len(other_reliability):
            strengths.append("More reliable than average")
        
        # Absolute strengths
        if analysis.time_analysis.estimated_time <= 20:
            strengths.append("Very quick commute")
        
        if analysis.cost_analysis.total_cost <= 2.0:
            strengths.append("Very affordable")
        
        if analysis.stress_analysis.overall_stress <= 3:
            strengths.append("Very low stress")
        
        if analysis.reliability_analysis.overall_reliability >= 8:
            strengths.append("Highly predictable")
        
        return strengths
    
    def _identify_route_weaknesses(
        self,
        route: Route,
        analysis: RouteAnalysis,
        all_routes: List[Route],
        all_analyses: List[RouteAnalysis]
    ) -> List[str]:
        """Identify the weaknesses of a route compared to alternatives."""
        weaknesses = []
        
        # Compare against other routes
        other_analyses = [a for r, a in zip(all_routes, all_analyses) if r.id != route.id]
        
        if not other_analyses:
            return weaknesses
        
        # Time weaknesses
        other_times = [a.time_analysis.estimated_time for a in other_analyses]
        if analysis.time_analysis.estimated_time >= max(other_times):
            time_diff = analysis.time_analysis.estimated_time - min(other_times)
            weaknesses.append(f"Slowest option - {time_diff} minutes longer than fastest")
        
        # Cost weaknesses
        other_costs = [a.cost_analysis.total_cost for a in other_analyses]
        if analysis.cost_analysis.total_cost >= max(other_costs):
            cost_diff = analysis.cost_analysis.total_cost - min(other_costs)
            weaknesses.append(f"Most expensive - ${cost_diff:.2f} more than cheapest")
        
        # Stress weaknesses
        other_stress = [a.stress_analysis.overall_stress for a in other_analyses]
        if analysis.stress_analysis.overall_stress >= max(other_stress):
            weaknesses.append("Most stressful option")
        
        # Reliability weaknesses
        other_reliability = [a.reliability_analysis.overall_reliability for a in other_analyses]
        if analysis.reliability_analysis.overall_reliability <= min(other_reliability):
            weaknesses.append("Least reliable timing")
        
        # Absolute weaknesses
        if analysis.time_analysis.estimated_time > 90:
            weaknesses.append("Very long commute")
        
        if analysis.cost_analysis.total_cost > 20.0:
            weaknesses.append("Expensive option")
        
        if analysis.stress_analysis.overall_stress >= 8:
            weaknesses.append("High stress levels")
        
        if analysis.reliability_analysis.overall_reliability <= 4:
            weaknesses.append("Unpredictable timing")
        
        return weaknesses
    
    def _generate_specific_tradeoffs(
        self,
        route: Route,
        analysis: RouteAnalysis,
        all_routes: List[Route],
        all_analyses: List[RouteAnalysis]
    ) -> List[Dict[str, str]]:
        """Generate specific trade-off descriptions for this route."""
        tradeoffs = []
        
        other_analyses = [a for r, a in zip(all_routes, all_analyses) if r.id != route.id]
        
        if not other_analyses:
            return tradeoffs
        
        # Find best alternative in each category
        best_time_analysis = min(other_analyses, key=lambda a: a.time_analysis.estimated_time)
        best_cost_analysis = min(other_analyses, key=lambda a: a.cost_analysis.total_cost)
        best_stress_analysis = min(other_analyses, key=lambda a: a.stress_analysis.overall_stress)
        best_reliability_analysis = max(other_analyses, key=lambda a: a.reliability_analysis.overall_reliability)
        
        # Time trade-offs
        if analysis.time_analysis.estimated_time > best_time_analysis.time_analysis.estimated_time:
            time_diff = analysis.time_analysis.estimated_time - best_time_analysis.time_analysis.estimated_time
            if analysis.cost_analysis.total_cost < best_time_analysis.cost_analysis.total_cost:
                cost_savings = best_time_analysis.cost_analysis.total_cost - analysis.cost_analysis.total_cost
                tradeoffs.append({
                    "type": "time_vs_cost",
                    "description": f"Takes {time_diff} minutes longer but saves ${cost_savings:.2f}"
                })
            elif analysis.stress_analysis.overall_stress < best_time_analysis.stress_analysis.overall_stress:
                stress_reduction = best_time_analysis.stress_analysis.overall_stress - analysis.stress_analysis.overall_stress
                tradeoffs.append({
                    "type": "time_vs_stress",
                    "description": f"Takes {time_diff} minutes longer but reduces stress by {stress_reduction} points"
                })
        
        # Cost trade-offs
        if analysis.cost_analysis.total_cost > best_cost_analysis.cost_analysis.total_cost:
            cost_diff = analysis.cost_analysis.total_cost - best_cost_analysis.cost_analysis.total_cost
            if analysis.time_analysis.estimated_time < best_cost_analysis.time_analysis.estimated_time:
                time_savings = best_cost_analysis.time_analysis.estimated_time - analysis.time_analysis.estimated_time
                tradeoffs.append({
                    "type": "cost_vs_time",
                    "description": f"Costs ${cost_diff:.2f} more but saves {time_savings} minutes"
                })
            elif analysis.reliability_analysis.overall_reliability > best_cost_analysis.reliability_analysis.overall_reliability:
                reliability_gain = analysis.reliability_analysis.overall_reliability - best_cost_analysis.reliability_analysis.overall_reliability
                tradeoffs.append({
                    "type": "cost_vs_reliability",
                    "description": f"Costs ${cost_diff:.2f} more but is {reliability_gain} points more reliable"
                })
        
        return tradeoffs
    
    def _generate_when_to_choose_guidance(
        self,
        route: Route,
        analysis: RouteAnalysis
    ) -> List[str]:
        """Generate guidance on when to choose this route."""
        guidance = []
        
        # Time-based guidance
        if analysis.time_analysis.estimated_time <= 30:
            guidance.append("When you're running late and need the quickest option")
        
        if analysis.time_analysis.time_range_max - analysis.time_analysis.time_range_min <= 10:
            guidance.append("When you need predictable timing")
        
        # Cost-based guidance
        if analysis.cost_analysis.total_cost <= 3.0:
            guidance.append("When budget is a primary concern")
        
        # Stress-based guidance
        if analysis.stress_analysis.overall_stress <= 4:
            guidance.append("When you want a relaxing, low-stress commute")
        
        if analysis.stress_analysis.traffic_stress <= 3:
            guidance.append("When you want to avoid traffic congestion")
        
        # Reliability-based guidance
        if analysis.reliability_analysis.overall_reliability >= 8:
            guidance.append("For important meetings or appointments")
        
        if analysis.reliability_analysis.incident_probability <= 0.1:
            guidance.append("When you can't afford unexpected delays")
        
        # Mode-specific guidance
        from commute_optimizer.models import TransportationMode
        
        if TransportationMode.CYCLING in route.transportation_modes:
            guidance.append("When weather is nice and you want exercise")
        
        if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
            guidance.append("When you want to relax or work during the commute")
        
        if TransportationMode.DRIVING in route.transportation_modes:
            guidance.append("When you need maximum flexibility and control")
        
        return guidance
    
    def _generate_comparison_highlights(
        self,
        route: Route,
        analysis: RouteAnalysis,
        all_routes: List[Route],
        all_analyses: List[RouteAnalysis]
    ) -> List[Dict[str, str]]:
        """Generate key comparison highlights for this route."""
        highlights = []
        
        other_analyses = [a for r, a in zip(all_routes, all_analyses) if r.id != route.id]
        
        if not other_analyses:
            return highlights
        
        # Time comparison
        other_times = [a.time_analysis.estimated_time for a in other_analyses]
        min_time, max_time = min(other_times), max(other_times)
        
        if analysis.time_analysis.estimated_time == min_time:
            highlights.append({
                "category": "time",
                "highlight": f"Fastest route - saves up to {max_time - min_time} minutes"
            })
        elif analysis.time_analysis.estimated_time == max_time:
            highlights.append({
                "category": "time",
                "highlight": f"Slowest route - takes {max_time - min_time} minutes longer"
            })
        
        # Cost comparison
        other_costs = [a.cost_analysis.total_cost for a in other_analyses]
        min_cost, max_cost = min(other_costs), max(other_costs)
        
        if analysis.cost_analysis.total_cost == min_cost:
            highlights.append({
                "category": "cost",
                "highlight": f"Cheapest route - saves up to ${max_cost - min_cost:.2f}"
            })
        elif analysis.cost_analysis.total_cost == max_cost:
            highlights.append({
                "category": "cost",
                "highlight": f"Most expensive - costs ${max_cost - min_cost:.2f} more"
            })
        
        # Stress comparison
        other_stress = [a.stress_analysis.overall_stress for a in other_analyses]
        min_stress, max_stress = min(other_stress), max(other_stress)
        
        if analysis.stress_analysis.overall_stress == min_stress:
            highlights.append({
                "category": "stress",
                "highlight": "Least stressful option"
            })
        elif analysis.stress_analysis.overall_stress == max_stress:
            highlights.append({
                "category": "stress",
                "highlight": "Most stressful option"
            })
        
        # Reliability comparison
        other_reliability = [a.reliability_analysis.overall_reliability for a in other_analyses]
        min_reliability, max_reliability = min(other_reliability), max(other_reliability)
        
        if analysis.reliability_analysis.overall_reliability == max_reliability:
            highlights.append({
                "category": "reliability",
                "highlight": "Most reliable timing"
            })
        elif analysis.reliability_analysis.overall_reliability == min_reliability:
            highlights.append({
                "category": "reliability",
                "highlight": "Least reliable timing"
            })
        
        return highlights
    
    def _generate_overall_tradeoff_summary(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis]
    ) -> str:
        """Generate an overall summary of trade-offs across all routes."""
        if len(routes) < 2:
            return "Only one route available - no trade-offs to consider."
        
        # Find extremes in each category
        times = [a.time_analysis.estimated_time for a in route_analyses]
        costs = [a.cost_analysis.total_cost for a in route_analyses]
        stress_levels = [a.stress_analysis.overall_stress for a in route_analyses]
        reliability_scores = [a.reliability_analysis.overall_reliability for a in route_analyses]
        
        time_range = max(times) - min(times)
        cost_range = max(costs) - min(costs)
        stress_range = max(stress_levels) - min(stress_levels)
        reliability_range = max(reliability_scores) - min(reliability_scores)
        
        summary_parts = []
        
        if time_range > 15:
            summary_parts.append(f"time varies by {time_range} minutes")
        
        if cost_range > 3.0:
            summary_parts.append(f"cost varies by ${cost_range:.2f}")
        
        if stress_range > 3:
            summary_parts.append(f"stress levels vary significantly")
        
        if reliability_range > 2:
            summary_parts.append(f"reliability varies considerably")
        
        if summary_parts:
            return f"Key trade-offs: {', '.join(summary_parts)}. Choose based on your priorities for today."
        else:
            return "Routes are fairly similar - any choice should work well."
    
    def _generate_decision_guidance(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis]
    ) -> List[Dict[str, str]]:
        """Generate decision guidance based on different scenarios."""
        guidance = []
        
        if len(routes) < 2:
            return guidance
        
        # Find best route for each criterion
        fastest_idx = min(range(len(route_analyses)), 
                         key=lambda i: route_analyses[i].time_analysis.estimated_time)
        cheapest_idx = min(range(len(route_analyses)), 
                          key=lambda i: route_analyses[i].cost_analysis.total_cost)
        least_stressful_idx = min(range(len(route_analyses)), 
                                 key=lambda i: route_analyses[i].stress_analysis.overall_stress)
        most_reliable_idx = max(range(len(route_analyses)), 
                               key=lambda i: route_analyses[i].reliability_analysis.overall_reliability)
        
        guidance.append({
            "scenario": "When time is most important",
            "recommendation": f"Choose Route {fastest_idx + 1} - fastest at {route_analyses[fastest_idx].time_analysis.estimated_time} minutes"
        })
        
        guidance.append({
            "scenario": "When cost is most important",
            "recommendation": f"Choose Route {cheapest_idx + 1} - cheapest at ${route_analyses[cheapest_idx].cost_analysis.total_cost:.2f}"
        })
        
        guidance.append({
            "scenario": "When you want minimal stress",
            "recommendation": f"Choose Route {least_stressful_idx + 1} - lowest stress level"
        })
        
        guidance.append({
            "scenario": "When punctuality is critical",
            "recommendation": f"Choose Route {most_reliable_idx + 1} - most reliable timing"
        })
        
        return guidance
    
    def _create_detailed_comparison_matrix(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis]
    ) -> List[Dict[str, Any]]:
        """Create a detailed comparison matrix with all metrics visible."""
        matrix = []
        
        for i, (route, analysis) in enumerate(zip(routes, route_analyses)):
            route_data = {
                'route_id': route.id,
                'route_name': f"Route {i + 1}",
                'transportation_modes': [mode.value for mode in route.transportation_modes],
                'metrics': {
                    'time': {
                        'estimated_minutes': analysis.time_analysis.estimated_time,
                        'range_min': analysis.time_analysis.time_range_min,
                        'range_max': analysis.time_analysis.time_range_max,
                        'peak_impact': analysis.time_analysis.peak_hour_impact,
                        'display': f"{analysis.time_analysis.estimated_time} min ({analysis.time_analysis.time_range_min}-{analysis.time_analysis.time_range_max})"
                    },
                    'cost': {
                        'total': analysis.cost_analysis.total_cost,
                        'fuel': analysis.cost_analysis.fuel_cost,
                        'transit': analysis.cost_analysis.transit_fare,
                        'parking': analysis.cost_analysis.parking_cost,
                        'tolls': analysis.cost_analysis.toll_cost,
                        'display': f"${analysis.cost_analysis.total_cost:.2f}"
                    },
                    'stress': {
                        'overall': analysis.stress_analysis.overall_stress,
                        'traffic': analysis.stress_analysis.traffic_stress,
                        'complexity': analysis.stress_analysis.complexity_stress,
                        'weather': analysis.stress_analysis.weather_stress,
                        'display': f"{analysis.stress_analysis.overall_stress}/10"
                    },
                    'reliability': {
                        'overall': analysis.reliability_analysis.overall_reliability,
                        'variance': analysis.reliability_analysis.historical_variance,
                        'incident_probability': analysis.reliability_analysis.incident_probability,
                        'weather_impact': analysis.reliability_analysis.weather_impact,
                        'service_reliability': analysis.reliability_analysis.service_reliability,
                        'display': f"{analysis.reliability_analysis.overall_reliability}/10"
                    }
                }
            }
            
            matrix.append(route_data)
        
        return matrix
    
    def _explain_decision_logic(
        self,
        scored_routes: List[Tuple[Route, RouteAnalysis, float]],
        user_preferences: PreferenceProfile
    ) -> Dict[str, Any]:
        """Explain the decision logic used for ranking routes."""
        return {
            "ranking_method": "weighted_scoring",
            "preference_weights": {
                "time": f"{user_preferences.time_weight}%",
                "cost": f"{user_preferences.cost_weight}%",
                "comfort": f"{user_preferences.comfort_weight}%",
                "reliability": f"{user_preferences.reliability_weight}%"
            },
            "scoring_explanation": "Each route receives a score (0-1) for each criterion, then scores are weighted by your preferences",
            "ranking_order": [
                {
                    "position": i + 1,
                    "route_id": route.id,
                    "total_score": f"{score:.3f}",
                    "score_percentage": f"{score * 100:.1f}%"
                }
                for i, (route, _, score) in enumerate(scored_routes)
            ]
        }
    
    def _identify_uncertainty_factors(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify factors that introduce uncertainty into the decision."""
        uncertainty_factors = []
        
        # Data freshness uncertainty
        if 'data_freshness' in context:
            data_age = context['data_freshness'].get('traffic_minutes_old', 0)
            if data_age > 10:
                uncertainty_factors.append({
                    "factor": "Traffic Data Age",
                    "description": f"Traffic data is {data_age} minutes old - conditions may have changed",
                    "impact": "medium"
                })
        
        # Weather uncertainty
        weather_data = context.get('weather_data', {})
        if weather_data.get('forecast_confidence', 1.0) < 0.8:
            uncertainty_factors.append({
                "factor": "Weather Forecast",
                "description": "Weather forecast has lower confidence - conditions may vary",
                "impact": "low"
            })
        
        # High variance routes
        for i, analysis in enumerate(route_analyses):
            if analysis.reliability_analysis.historical_variance > 15:
                uncertainty_factors.append({
                    "factor": f"Route {i + 1} Timing Variance",
                    "description": f"This route has high timing variance ({analysis.reliability_analysis.historical_variance:.1f} min)",
                    "impact": "high"
                })
        
        # Incident probability
        for i, analysis in enumerate(route_analyses):
            if analysis.reliability_analysis.incident_probability > 0.3:
                uncertainty_factors.append({
                    "factor": f"Route {i + 1} Incident Risk",
                    "description": f"High probability ({analysis.reliability_analysis.incident_probability:.1%}) of incidents",
                    "impact": "high"
                })
        
        return uncertainty_factors
    
    def _list_decision_assumptions(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        context: Dict[str, Any]
    ) -> List[str]:
        """List key assumptions made in the decision process."""
        from commute_optimizer.models import TransportationMode
        
        assumptions = [
            "Traffic patterns follow historical trends",
            "Weather conditions remain as forecasted",
            "Public transit operates on schedule",
            "Parking availability matches typical patterns",
            "User preferences remain constant during the commute"
        ]
        
        # Add context-specific assumptions
        if context.get('special_events'):
            assumptions.append("Special events do not significantly impact traffic")
        
        if any(TransportationMode.PUBLIC_TRANSIT in route.transportation_modes for route in routes):
            assumptions.append("Transit service disruptions are accounted for in reliability scores")
        
        if any(TransportationMode.CYCLING in route.transportation_modes for route in routes):
            assumptions.append("Cyclist follows traffic laws and uses designated bike infrastructure")
        
        return assumptions
    
    def _calculate_score_breakdown(
        self,
        route: Route,
        analysis: RouteAnalysis,
        preferences: PreferenceProfile
    ) -> Dict[str, Dict[str, float]]:
        """Calculate detailed score breakdown for transparency."""
        # Normalize scores to 0-1 scale (higher is better)
        time_score = max(0, 1 - (analysis.time_analysis.estimated_time / 120))
        cost_score = max(0, 1 - (analysis.cost_analysis.total_cost / 20))
        comfort_score = (10 - analysis.stress_analysis.overall_stress) / 9
        reliability_score = (analysis.reliability_analysis.overall_reliability - 1) / 9
        
        return {
            "time": {
                "raw_score": time_score,
                "weight": preferences.time_weight / 100,
                "weighted_score": time_score * preferences.time_weight / 100,
                "explanation": f"Based on {analysis.time_analysis.estimated_time} minute travel time"
            },
            "cost": {
                "raw_score": cost_score,
                "weight": preferences.cost_weight / 100,
                "weighted_score": cost_score * preferences.cost_weight / 100,
                "explanation": f"Based on ${analysis.cost_analysis.total_cost:.2f} total cost"
            },
            "comfort": {
                "raw_score": comfort_score,
                "weight": preferences.comfort_weight / 100,
                "weighted_score": comfort_score * preferences.comfort_weight / 100,
                "explanation": f"Based on {analysis.stress_analysis.overall_stress}/10 stress level"
            },
            "reliability": {
                "raw_score": reliability_score,
                "weight": preferences.reliability_weight / 100,
                "weighted_score": reliability_score * preferences.reliability_weight / 100,
                "explanation": f"Based on {analysis.reliability_analysis.overall_reliability}/10 reliability score"
            }
        }
    
    def _explain_score_calculation(
        self,
        breakdown: Dict[str, Dict[str, float]],
        preferences: PreferenceProfile
    ) -> str:
        """Explain how the total score was calculated."""
        explanations = []
        
        for criterion, data in breakdown.items():
            explanations.append(
                f"{criterion.title()}: {data['raw_score']:.3f} × {data['weight']:.2f} = {data['weighted_score']:.3f}"
            )
        
        total_score = sum(data['weighted_score'] for data in breakdown.values())
        
        return f"Total Score = {' + '.join(explanations)} = {total_score:.3f}"
    
    def validate_language_compliance(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate text for compliance with language guidelines.
        
        Args:
            text: Text to validate
            context: Optional context about the text source
            
        Returns:
            Dictionary containing validation results and suggestions
            
        Validates: Requirements 1.5, 4.4
        """
        if context is None:
            context = {}
        
        validation_result = {
            "is_compliant": True,
            "violations": [],
            "warnings": [],
            "suggestions": [],
            "forbidden_terms_found": [],
            "superlatives_without_explanation": []
        }
        
        # Check for forbidden terms without explanation
        forbidden_violations = self._check_forbidden_terms(text)
        if forbidden_violations:
            validation_result["is_compliant"] = False
            validation_result["violations"].extend(forbidden_violations)
            validation_result["forbidden_terms_found"] = [v["term"] for v in forbidden_violations]
        
        # Check for superlatives without explanation
        superlative_violations = self._check_superlatives_without_explanation(text)
        if superlative_violations:
            validation_result["is_compliant"] = False
            validation_result["violations"].extend(superlative_violations)
            validation_result["superlatives_without_explanation"] = [v["term"] for v in superlative_violations]
        
        # Generate suggestions for improvement
        if not validation_result["is_compliant"]:
            validation_result["suggestions"] = self._generate_language_suggestions(
                text, validation_result["violations"]
            )
        
        # Add warnings for potentially problematic language
        warnings = self._check_for_language_warnings(text)
        validation_result["warnings"].extend(warnings)
        
        return validation_result
    
    def filter_and_correct_language(
        self,
        text: str,
        explanation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Filter and correct language to ensure compliance with guidelines.
        
        Args:
            text: Text to filter and correct
            explanation_context: Context for generating explanations
            
        Returns:
            Dictionary containing corrected text and changes made
            
        Validates: Requirements 1.5, 4.4
        """
        if explanation_context is None:
            explanation_context = {}
        
        corrected_text = text
        changes_made = []
        
        # Replace forbidden terms with compliant alternatives
        forbidden_replacements = self._get_forbidden_term_replacements()
        
        for forbidden_term, replacement_info in forbidden_replacements.items():
            if self._term_appears_without_explanation(corrected_text, forbidden_term):
                # Replace with explanation-based alternative
                replacement = replacement_info["replacement"]
                if explanation_context:
                    replacement = replacement_info["contextual_replacement"](explanation_context)
                
                corrected_text = self._replace_term_with_explanation(
                    corrected_text, forbidden_term, replacement
                )
                
                changes_made.append({
                    "original_term": forbidden_term,
                    "replacement": replacement,
                    "reason": "Added explanation for superlative claim"
                })
        
        # Add explanations for remaining superlatives
        superlatives = self._find_superlatives_without_explanation(corrected_text)
        for superlative in superlatives:
            explanation = self._generate_superlative_explanation(superlative, explanation_context)
            corrected_text = self._add_explanation_to_superlative(
                corrected_text, superlative, explanation
            )
            
            changes_made.append({
                "original_term": superlative,
                "explanation_added": explanation,
                "reason": "Added required explanation for superlative"
            })
        
        return {
            "original_text": text,
            "corrected_text": corrected_text,
            "changes_made": changes_made,
            "is_compliant": len(changes_made) == 0
        }
    
    def generate_compliant_recommendation_text(
        self,
        route: Route,
        analysis: RouteAnalysis,
        reasoning: str,
        alternatives: List[Tuple[Route, RouteAnalysis]] = None
    ) -> str:
        """
        Generate recommendation text that complies with language guidelines.
        
        Args:
            route: Recommended route
            analysis: Route analysis
            reasoning: Reasoning for recommendation
            alternatives: Alternative routes for context
            
        Returns:
            Compliant recommendation text
            
        Validates: Requirements 1.5, 4.4
        """
        if alternatives is None:
            alternatives = []
        
        # Start with explanation-based language
        recommendation_parts = []
        
        # Avoid "best" or "optimal" - use explanation-based language
        recommendation_parts.append(f"Based on your preferences, this route offers:")
        
        # Add specific strengths with explanations
        strengths = self._identify_route_strengths(
            route, analysis, 
            [alt_route for alt_route, _ in alternatives] + [route],
            [alt_analysis for _, alt_analysis in alternatives] + [analysis]
        )
        
        for strength in strengths[:3]:  # Limit to top 3 strengths
            recommendation_parts.append(f"• {strength}")
        
        # Add reasoning with explanations
        if reasoning:
            # Filter reasoning to ensure compliance
            filtered_reasoning = self.filter_and_correct_language(
                reasoning, 
                {
                    "route": route,
                    "analysis": analysis,
                    "alternatives": alternatives
                }
            )
            recommendation_parts.append(filtered_reasoning["corrected_text"])
        
        # Add context about when this choice makes sense
        when_to_choose = self._generate_when_to_choose_guidance(route, analysis)
        if when_to_choose:
            recommendation_parts.append("This route works well:")
            for guidance in when_to_choose[:2]:  # Limit to top 2
                recommendation_parts.append(f"• {guidance}")
        
        # Add transparency about limitations
        when_not_to_choose = self.identify_when_not_to_choose(route, analysis, alternatives)
        if when_not_to_choose:
            recommendation_parts.append("Consider alternatives:")
            for warning in when_not_to_choose[:2]:  # Limit to top 2
                recommendation_parts.append(f"• {warning}")
        
        return "\n".join(recommendation_parts)
    
    def _check_forbidden_terms(self, text: str) -> List[Dict[str, str]]:
        """Check for forbidden terms used without proper explanation."""
        violations = []
        
        # Define forbidden terms and their contexts
        forbidden_terms = {
            "best": ["best route", "best option", "best choice", "the best"],
            "optimal": ["optimal route", "optimal choice", "optimal solution", "the optimal"],
            "perfect": ["perfect route", "perfect choice", "perfect option", "the perfect"],
            "ideal": ["ideal route", "ideal choice", "ideal option", "the ideal"],
            "recommended": ["recommended route", "recommended option", "is recommended"],
            "should": ["you should take", "you should choose"],
            "must": ["you must take", "you must choose"]
        }
        
        text_lower = text.lower()
        
        for base_term, variations in forbidden_terms.items():
            for variation in variations:
                if variation in text_lower:
                    # Check if there's an explanation nearby
                    if not self._has_nearby_explanation(text, variation):
                        violations.append({
                            "term": variation,
                            "type": "forbidden_without_explanation",
                            "message": f"'{variation}' used without explanation of criteria"
                        })
        
        return violations
    
    def _check_superlatives_without_explanation(self, text: str) -> List[Dict[str, str]]:
        """Check for superlative claims without explanation."""
        violations = []
        
        superlative_patterns = [
            "fastest", "slowest", "cheapest", "most expensive",
            "most reliable", "least reliable", "most stressful", "least stressful",
            "highest", "lowest", "maximum", "minimum",
            "always", "never", "guaranteed", "certain"
        ]
        
        text_lower = text.lower()
        
        for superlative in superlative_patterns:
            if superlative in text_lower:
                # Check if there's an explanation or comparison nearby
                if not self._has_nearby_explanation_or_comparison(text, superlative):
                    violations.append({
                        "term": superlative,
                        "type": "superlative_without_explanation",
                        "message": f"'{superlative}' claim needs explanation or comparison"
                    })
        
        return violations
    
    def _check_for_language_warnings(self, text: str) -> List[Dict[str, str]]:
        """Check for potentially problematic language that should be reviewed."""
        warnings = []
        
        warning_terms = {
            "obviously": "May sound condescending - consider removing",
            "clearly": "May sound condescending - consider 'this shows' instead",
            "definitely": "Consider 'likely' or 'typically' for more accurate language",
            "absolutely": "Consider more nuanced language",
            "impossible": "Consider 'very difficult' or 'not recommended'",
            "terrible": "Consider more specific, constructive language",
            "awful": "Consider more specific, constructive language",
            "horrible": "Consider more specific, constructive language"
        }
        
        text_lower = text.lower()
        
        for term, suggestion in warning_terms.items():
            if term in text_lower:
                warnings.append({
                    "term": term,
                    "type": "language_warning",
                    "suggestion": suggestion
                })
        
        return warnings
    
    def _has_nearby_explanation(self, text: str, term: str) -> bool:
        """Check if there's an explanation near the forbidden term."""
        # Find the position of the term
        text_lower = text.lower()
        term_pos = text_lower.find(term.lower())
        
        if term_pos == -1:
            return False
        
        # Look for explanation keywords within 100 characters
        explanation_keywords = [
            "because", "since", "due to", "based on", "given that",
            "considering", "factors", "criteria", "reasons", "analysis"
        ]
        
        # Check text around the term (50 chars before and after)
        start_pos = max(0, term_pos - 50)
        end_pos = min(len(text), term_pos + len(term) + 50)
        surrounding_text = text[start_pos:end_pos].lower()
        
        return any(keyword in surrounding_text for keyword in explanation_keywords)
    
    def _has_nearby_explanation_or_comparison(self, text: str, term: str) -> bool:
        """Check if there's an explanation or comparison near the superlative."""
        # First check for explanation
        if self._has_nearby_explanation(text, term):
            return True
        
        # Then check for comparison keywords
        text_lower = text.lower()
        term_pos = text_lower.find(term.lower())
        
        if term_pos == -1:
            return False
        
        comparison_keywords = [
            "compared to", "versus", "than", "relative to",
            "among", "between", "of all", "in comparison"
        ]
        
        # Check text around the term
        start_pos = max(0, term_pos - 50)
        end_pos = min(len(text), term_pos + len(term) + 50)
        surrounding_text = text[start_pos:end_pos].lower()
        
        return any(keyword in surrounding_text for keyword in comparison_keywords)
    
    def _get_forbidden_term_replacements(self) -> Dict[str, Dict[str, Any]]:
        """Get replacement patterns for forbidden terms."""
        return {
            "best": {
                "replacement": "highest-scoring based on your preferences",
                "contextual_replacement": lambda ctx: f"highest-scoring for {self._get_preference_context(ctx)}"
            },
            "optimal": {
                "replacement": "most suitable based on analysis",
                "contextual_replacement": lambda ctx: f"most suitable given {self._get_analysis_context(ctx)}"
            },
            "perfect": {
                "replacement": "well-suited",
                "contextual_replacement": lambda ctx: "well-suited for your stated priorities"
            },
            "recommended": {
                "replacement": "suggested based on your preferences",
                "contextual_replacement": lambda ctx: f"suggested because {self._get_reasoning_context(ctx)}"
            }
        }
    
    def _get_preference_context(self, context: Dict[str, Any]) -> str:
        """Get preference context for replacements."""
        if "preferences" in context:
            prefs = context["preferences"]
            top_pref = max(
                [("time", prefs.time_weight), ("cost", prefs.cost_weight),
                 ("comfort", prefs.comfort_weight), ("reliability", prefs.reliability_weight)],
                key=lambda x: x[1]
            )
            return f"your {top_pref[0]} priority"
        return "your preferences"
    
    def _get_analysis_context(self, context: Dict[str, Any]) -> str:
        """Get analysis context for replacements."""
        if "analysis" in context:
            analysis = context["analysis"]
            factors = []
            if analysis.time_analysis.estimated_time <= 30:
                factors.append("quick travel time")
            if analysis.cost_analysis.total_cost <= 5.0:
                factors.append("low cost")
            if analysis.stress_analysis.overall_stress <= 4:
                factors.append("low stress")
            if analysis.reliability_analysis.overall_reliability >= 8:
                factors.append("high reliability")
            
            if factors:
                return " and ".join(factors)
        
        return "current conditions"
    
    def _get_reasoning_context(self, context: Dict[str, Any]) -> str:
        """Get reasoning context for replacements."""
        if "reasoning" in context:
            return context["reasoning"]
        return "it matches your priorities"
    
    def _term_appears_without_explanation(self, text: str, term: str) -> bool:
        """Check if a term appears without explanation."""
        return term.lower() in text.lower() and not self._has_nearby_explanation(text, term)
    
    def _replace_term_with_explanation(self, text: str, term: str, replacement: str) -> str:
        """Replace a term with an explanation-based alternative."""
        # Case-insensitive replacement while preserving original case pattern
        import re
        
        def replace_func(match):
            original = match.group(0)
            if original.isupper():
                return replacement.upper()
            elif original.istitle():
                return replacement.title()
            else:
                return replacement
        
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        return pattern.sub(replace_func, text)
    
    def _find_superlatives_without_explanation(self, text: str) -> List[str]:
        """Find superlatives that lack explanation."""
        superlatives = []
        
        superlative_patterns = [
            "fastest", "slowest", "cheapest", "most expensive",
            "most reliable", "least reliable", "most stressful", "least stressful"
        ]
        
        for superlative in superlative_patterns:
            if (superlative in text.lower() and 
                not self._has_nearby_explanation_or_comparison(text, superlative)):
                superlatives.append(superlative)
        
        return superlatives
    
    def _generate_superlative_explanation(
        self, 
        superlative: str, 
        context: Dict[str, Any]
    ) -> str:
        """Generate an explanation for a superlative claim."""
        explanations = {
            "fastest": "compared to other available routes",
            "slowest": "among the route options",
            "cheapest": "of the available alternatives",
            "most expensive": "compared to other routes",
            "most reliable": "based on historical data",
            "least reliable": "according to timing variance",
            "most stressful": "due to traffic and complexity factors",
            "least stressful": "with minimal traffic exposure"
        }
        
        base_explanation = explanations.get(superlative, "based on analysis")
        
        # Add context if available
        if "alternatives" in context and context["alternatives"]:
            alt_count = len(context["alternatives"])
            return f"{base_explanation} (compared to {alt_count} alternatives)"
        
        return base_explanation
    
    def _add_explanation_to_superlative(
        self, 
        text: str, 
        superlative: str, 
        explanation: str
    ) -> str:
        """Add explanation to a superlative in the text."""
        import re
        
        # Find the superlative and add explanation after it
        pattern = re.compile(f"\\b{re.escape(superlative)}\\b", re.IGNORECASE)
        
        def replace_func(match):
            return f"{match.group(0)} ({explanation})"
        
        return pattern.sub(replace_func, text, count=1)
    
    def _generate_language_suggestions(
        self, 
        text: str, 
        violations: List[Dict[str, str]]
    ) -> List[str]:
        """Generate suggestions for improving language compliance."""
        suggestions = []
        
        for violation in violations:
            term = violation["term"]
            violation_type = violation["type"]
            
            if violation_type == "forbidden_without_explanation":
                suggestions.append(
                    f"Replace '{term}' with explanation-based language like "
                    f"'highest-scoring based on your preferences' or 'most suitable given [criteria]'"
                )
            elif violation_type == "superlative_without_explanation":
                suggestions.append(
                    f"Add explanation or comparison for '{term}' - "
                    f"specify what it's compared to or why it's {term}"
                )
        
        # General suggestions
        if violations:
            suggestions.append(
                "Focus on explaining the reasoning behind claims rather than making absolute statements"
            )
            suggestions.append(
                "Provide context and criteria for any comparative or superlative statements"
            )
        
        return suggestions