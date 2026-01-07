"""Route Comparison Service for side-by-side route analysis and presentation."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from commute_optimizer.models import (
    Route, RouteAnalysis, TransportationMode
)


class ComparisonIndicator(str, Enum):
    """Indicators for route comparison improvements/degradations."""
    MUCH_BETTER = "much_better"
    BETTER = "better"
    SIMILAR = "similar"
    WORSE = "worse"
    MUCH_WORSE = "much_worse"


class RouteComparisonService:
    """
    Service for creating side-by-side route comparisons with improvement/degradation indicators.
    
    This service implements comprehensive route comparison functionality that presents
    routes in a consistent, easy-to-understand format with clear indicators of
    relative performance across all criteria.
    """
    
    def __init__(self):
        """Initialize the route comparison service."""
        # Thresholds for comparison indicators
        self.time_thresholds = {
            'much_better': -20,  # 20+ minutes faster
            'better': -10,       # 10+ minutes faster
            'similar': 5,        # Within 5 minutes
            'worse': 15,         # 10-15 minutes slower
            'much_worse': float('inf')  # 15+ minutes slower
        }
        
        self.cost_thresholds = {
            'much_better': -5.0,   # $5+ cheaper
            'better': -2.0,        # $2+ cheaper
            'similar': 1.0,        # Within $1
            'worse': 3.0,          # $1-3 more expensive
            'much_worse': float('inf')  # $3+ more expensive
        }
        
        self.stress_thresholds = {
            'much_better': -3,     # 3+ points less stressful
            'better': -2,          # 2+ points less stressful
            'similar': 1,          # Within 1 point
            'worse': 2,            # 1-2 points more stressful
            'much_worse': float('inf')  # 2+ points more stressful
        }
        
        self.reliability_thresholds = {
            'much_better': 3,      # 3+ points more reliable
            'better': 2,           # 2+ points more reliable
            'similar': 1,          # Within 1 point
            'worse': -2,           # 1-2 points less reliable
            'much_worse': float('-inf')  # 2+ points less reliable
        }
    
    def create_comparison(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis]
    ) -> Dict[str, Any]:
        """
        Create route comparisons (wrapper for create_side_by_side_comparison).
        
        Args:
            routes: List of routes to compare
            route_analyses: Corresponding route analyses
            
        Returns:
            Dictionary containing route comparisons
            
        Validates: Requirements 2.2, 2.3, 2.4
        """
        return self.create_side_by_side_comparison(routes, route_analyses)
    
    def create_side_by_side_comparison(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        reference_route_index: int = 0
    ) -> Dict[str, Any]:
        """
        Create a side-by-side comparison of routes with improvement/degradation indicators.
        
        Args:
            routes: List of routes to compare
            route_analyses: Corresponding route analyses
            reference_route_index: Index of route to use as comparison baseline
            
        Returns:
            Dictionary containing formatted side-by-side comparison
            
        Validates: Requirements 2.2, 2.3, 2.4
        """
        if len(routes) != len(route_analyses):
            raise ValueError("Number of routes must match number of analyses")
        
        if not routes:
            return {
                "comparison_matrix": [],
                "summary": "No routes available for comparison",
                "reference_route": None
            }
        
        if reference_route_index >= len(routes):
            reference_route_index = 0
        
        reference_route = routes[reference_route_index]
        reference_analysis = route_analyses[reference_route_index]
        
        # Create comparison matrix
        comparison_matrix = []
        
        for i, (route, analysis) in enumerate(zip(routes, route_analyses)):
            route_comparison = self._create_route_comparison_entry(
                route, analysis, reference_analysis, i, i == reference_route_index
            )
            comparison_matrix.append(route_comparison)
        
        # Generate comparison summary
        summary = self._generate_comparison_summary(routes, route_analyses, reference_route_index)
        
        return {
            "comparison_matrix": comparison_matrix,
            "summary": summary,
            "reference_route": {
                "id": reference_route.id,
                "name": f"Route {reference_route_index + 1}",
                "index": reference_route_index
            },
            "criteria_explanations": self._get_criteria_explanations(),
            "indicator_legend": self._get_indicator_legend(),
            "timestamp": datetime.now().isoformat()
        }
    
    def format_comparison_for_display(
        self,
        comparison_data: Dict[str, Any],
        format_type: str = "table"
    ) -> str:
        """
        Format comparison data for display in various formats.
        
        Args:
            comparison_data: Comparison data from create_side_by_side_comparison
            format_type: Format type ("table", "list", "detailed")
            
        Returns:
            Formatted string representation of the comparison
            
        Validates: Requirements 2.2, 2.3, 2.4
        """
        if format_type == "table":
            return self._format_as_table(comparison_data)
        elif format_type == "list":
            return self._format_as_list(comparison_data)
        elif format_type == "detailed":
            return self._format_as_detailed(comparison_data)
        else:
            raise ValueError(f"Unknown format type: {format_type}")
    
    def identify_key_differences(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis]
    ) -> Dict[str, Any]:
        """
        Identify the most significant differences between routes.
        
        Args:
            routes: List of routes to analyze
            route_analyses: Corresponding route analyses
            
        Returns:
            Dictionary containing key differences and insights
            
        Validates: Requirements 2.2, 2.3, 2.4
        """
        if len(routes) < 2:
            return {
                "significant_differences": [],
                "trade_offs": [],
                "standout_routes": {}
            }
        
        significant_differences = []
        trade_offs = []
        standout_routes = {
            "fastest": None,
            "cheapest": None,
            "least_stressful": None,
            "most_reliable": None
        }
        
        # Find standout routes in each category
        times = [(analysis.time_analysis.estimated_time, i) for i, analysis in enumerate(route_analyses)]
        costs = [(analysis.cost_analysis.total_cost, i) for i, analysis in enumerate(route_analyses)]
        stress_levels = [(analysis.stress_analysis.overall_stress, i) for i, analysis in enumerate(route_analyses)]
        reliability_scores = [(analysis.reliability_analysis.overall_reliability, i) for i, analysis in enumerate(route_analyses)]
        
        standout_routes["fastest"] = min(times)[1]
        standout_routes["cheapest"] = min(costs)[1]
        standout_routes["least_stressful"] = min(stress_levels)[1]
        standout_routes["most_reliable"] = max(reliability_scores)[1]
        
        # Identify significant differences
        time_range = max(times)[0] - min(times)[0]
        if time_range > 15:  # 15+ minute difference
            significant_differences.append({
                "category": "time",
                "description": f"Travel times vary by {time_range:.0f} minutes",
                "impact": "high" if time_range > 30 else "medium",
                "fastest_route": standout_routes["fastest"] + 1,
                "slowest_route": max(times)[1] + 1
            })
        
        cost_range = max(costs)[0] - min(costs)[0]
        if cost_range > 3.0:  # $3+ difference
            significant_differences.append({
                "category": "cost",
                "description": f"Costs vary by ${cost_range:.2f}",
                "impact": "high" if cost_range > 8.0 else "medium",
                "cheapest_route": standout_routes["cheapest"] + 1,
                "most_expensive_route": max(costs)[1] + 1
            })
        
        stress_range = max(stress_levels)[0] - min(stress_levels)[0]
        if stress_range > 2:  # 2+ point difference
            significant_differences.append({
                "category": "stress",
                "description": f"Stress levels vary by {stress_range} points",
                "impact": "high" if stress_range > 4 else "medium",
                "least_stressful_route": standout_routes["least_stressful"] + 1,
                "most_stressful_route": max(stress_levels)[1] + 1
            })
        
        reliability_range = max(reliability_scores)[0] - min(reliability_scores)[0]
        if reliability_range > 2:  # 2+ point difference
            significant_differences.append({
                "category": "reliability",
                "description": f"Reliability scores vary by {reliability_range} points",
                "impact": "high" if reliability_range > 4 else "medium",
                "most_reliable_route": standout_routes["most_reliable"] + 1,
                "least_reliable_route": min(reliability_scores)[1] + 1
            })
        
        # Identify trade-offs
        trade_offs = self._identify_route_tradeoffs(routes, route_analyses, standout_routes)
        
        return {
            "significant_differences": significant_differences,
            "trade_offs": trade_offs,
            "standout_routes": {k: v + 1 for k, v in standout_routes.items()},  # Convert to 1-based indexing
            "summary": self._generate_differences_summary(significant_differences, trade_offs)
        }
    
    def create_improvement_degradation_indicators(
        self,
        route_analysis: RouteAnalysis,
        reference_analysis: RouteAnalysis
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create improvement/degradation indicators for a route compared to reference.
        
        Args:
            route_analysis: Analysis of route to evaluate
            reference_analysis: Reference route analysis for comparison
            
        Returns:
            Dictionary containing indicators for each criterion
            
        Validates: Requirements 2.2, 2.3, 2.4
        """
        indicators = {}
        
        # Time indicator
        time_diff = route_analysis.time_analysis.estimated_time - reference_analysis.time_analysis.estimated_time
        indicators["time"] = {
            "indicator": self._get_indicator_from_difference(time_diff, self.time_thresholds),
            "difference": time_diff,
            "display_text": self._format_time_difference(time_diff),
            "explanation": self._explain_time_difference(time_diff)
        }
        
        # Cost indicator
        cost_diff = route_analysis.cost_analysis.total_cost - reference_analysis.cost_analysis.total_cost
        indicators["cost"] = {
            "indicator": self._get_indicator_from_difference(cost_diff, self.cost_thresholds),
            "difference": cost_diff,
            "display_text": self._format_cost_difference(cost_diff),
            "explanation": self._explain_cost_difference(cost_diff)
        }
        
        # Stress indicator (lower is better, so flip the difference)
        stress_diff = route_analysis.stress_analysis.overall_stress - reference_analysis.stress_analysis.overall_stress
        indicators["stress"] = {
            "indicator": self._get_indicator_from_difference(stress_diff, self.stress_thresholds),
            "difference": stress_diff,
            "display_text": self._format_stress_difference(stress_diff),
            "explanation": self._explain_stress_difference(stress_diff)
        }
        
        # Reliability indicator (higher is better)
        reliability_diff = route_analysis.reliability_analysis.overall_reliability - reference_analysis.reliability_analysis.overall_reliability
        indicators["reliability"] = {
            "indicator": self._get_indicator_from_difference(reliability_diff, self.reliability_thresholds),
            "difference": reliability_diff,
            "display_text": self._format_reliability_difference(reliability_diff),
            "explanation": self._explain_reliability_difference(reliability_diff)
        }
        
        return indicators
    
    def ensure_consistent_metrics(
        self,
        route_analyses: List[RouteAnalysis]
    ) -> Dict[str, Any]:
        """
        Ensure all route analyses use consistent metrics and units.
        
        Args:
            route_analyses: List of route analyses to validate
            
        Returns:
            Dictionary containing validation results and any inconsistencies found
            
        Validates: Requirements 2.2, 2.3, 2.4
        """
        validation_result = {
            "is_consistent": True,
            "inconsistencies": [],
            "metrics_summary": {},
            "recommendations": []
        }
        
        if not route_analyses:
            return validation_result
        
        # Check time metrics consistency
        time_inconsistencies = self._check_time_metrics_consistency(route_analyses)
        if time_inconsistencies:
            validation_result["is_consistent"] = False
            validation_result["inconsistencies"].extend(time_inconsistencies)
        
        # Check cost metrics consistency
        cost_inconsistencies = self._check_cost_metrics_consistency(route_analyses)
        if cost_inconsistencies:
            validation_result["is_consistent"] = False
            validation_result["inconsistencies"].extend(cost_inconsistencies)
        
        # Check stress metrics consistency
        stress_inconsistencies = self._check_stress_metrics_consistency(route_analyses)
        if stress_inconsistencies:
            validation_result["is_consistent"] = False
            validation_result["inconsistencies"].extend(stress_inconsistencies)
        
        # Check reliability metrics consistency
        reliability_inconsistencies = self._check_reliability_metrics_consistency(route_analyses)
        if reliability_inconsistencies:
            validation_result["is_consistent"] = False
            validation_result["inconsistencies"].extend(reliability_inconsistencies)
        
        # Generate metrics summary
        validation_result["metrics_summary"] = self._generate_metrics_summary(route_analyses)
        
        # Generate recommendations if inconsistencies found
        if not validation_result["is_consistent"]:
            validation_result["recommendations"] = self._generate_consistency_recommendations(
                validation_result["inconsistencies"]
            )
        
        return validation_result
    
    def _create_route_comparison_entry(
        self,
        route: Route,
        analysis: RouteAnalysis,
        reference_analysis: RouteAnalysis,
        route_index: int,
        is_reference: bool
    ) -> Dict[str, Any]:
        """Create a single route entry for the comparison matrix."""
        entry = {
            "route_id": route.id,
            "route_name": f"Route {route_index + 1}",
            "is_reference": is_reference,
            "transportation_modes": [mode.value for mode in route.transportation_modes],
            "metrics": {
                "time": {
                    "value": analysis.time_analysis.estimated_time,
                    "unit": "minutes",
                    "display": f"{analysis.time_analysis.estimated_time} min",
                    "range": f"({analysis.time_analysis.time_range_min}-{analysis.time_analysis.time_range_max} min)",
                    "peak_impact": f"+{analysis.time_analysis.peak_hour_impact} min" if analysis.time_analysis.peak_hour_impact > 0 else "No impact"
                },
                "cost": {
                    "value": analysis.cost_analysis.total_cost,
                    "unit": "dollars",
                    "display": f"${analysis.cost_analysis.total_cost:.2f}",
                    "breakdown": {
                        "fuel": analysis.cost_analysis.fuel_cost,
                        "transit": analysis.cost_analysis.transit_fare,
                        "parking": analysis.cost_analysis.parking_cost,
                        "tolls": analysis.cost_analysis.toll_cost
                    }
                },
                "stress": {
                    "value": analysis.stress_analysis.overall_stress,
                    "unit": "scale_1_10",
                    "display": f"{analysis.stress_analysis.overall_stress}/10",
                    "components": {
                        "traffic": analysis.stress_analysis.traffic_stress,
                        "complexity": analysis.stress_analysis.complexity_stress,
                        "weather": analysis.stress_analysis.weather_stress
                    }
                },
                "reliability": {
                    "value": analysis.reliability_analysis.overall_reliability,
                    "unit": "scale_1_10",
                    "display": f"{analysis.reliability_analysis.overall_reliability}/10",
                    "variance": f"±{analysis.reliability_analysis.historical_variance:.1f} min",
                    "incident_risk": f"{analysis.reliability_analysis.incident_probability:.1%}"
                }
            }
        }
        
        # Add comparison indicators if not reference route
        if not is_reference:
            entry["indicators"] = self.create_improvement_degradation_indicators(analysis, reference_analysis)
        
        return entry
    
    def _generate_comparison_summary(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        reference_index: int
    ) -> str:
        """Generate a summary of the route comparison."""
        if len(routes) < 2:
            return "Only one route available - no comparison possible."
        
        reference_name = f"Route {reference_index + 1}"
        summary_parts = [f"Comparison relative to {reference_name}:"]
        
        # Find routes that are better/worse in each category
        better_routes = {"time": [], "cost": [], "stress": [], "reliability": []}
        
        for i, analysis in enumerate(route_analyses):
            if i == reference_index:
                continue
            
            route_name = f"Route {i + 1}"
            ref_analysis = route_analyses[reference_index]
            
            # Time comparison
            if analysis.time_analysis.estimated_time < ref_analysis.time_analysis.estimated_time - 5:
                time_diff = ref_analysis.time_analysis.estimated_time - analysis.time_analysis.estimated_time
                better_routes["time"].append(f"{route_name} ({time_diff} min faster)")
            
            # Cost comparison
            if analysis.cost_analysis.total_cost < ref_analysis.cost_analysis.total_cost - 1.0:
                cost_diff = ref_analysis.cost_analysis.total_cost - analysis.cost_analysis.total_cost
                better_routes["cost"].append(f"{route_name} (${cost_diff:.2f} cheaper)")
            
            # Stress comparison
            if analysis.stress_analysis.overall_stress < ref_analysis.stress_analysis.overall_stress - 1:
                stress_diff = ref_analysis.stress_analysis.overall_stress - analysis.stress_analysis.overall_stress
                better_routes["stress"].append(f"{route_name} ({stress_diff} points less stressful)")
            
            # Reliability comparison
            if analysis.reliability_analysis.overall_reliability > ref_analysis.reliability_analysis.overall_reliability + 1:
                reliability_diff = analysis.reliability_analysis.overall_reliability - ref_analysis.reliability_analysis.overall_reliability
                better_routes["reliability"].append(f"{route_name} ({reliability_diff} points more reliable)")
        
        # Add summary for each category
        for category, routes_list in better_routes.items():
            if routes_list:
                summary_parts.append(f"• Better {category}: {', '.join(routes_list)}")
        
        if len(summary_parts) == 1:
            summary_parts.append("• No routes significantly outperform the reference route")
        
        return "\n".join(summary_parts)
    
    def _get_criteria_explanations(self) -> Dict[str, str]:
        """Get explanations for each comparison criterion."""
        return {
            "time": "Total estimated travel time including traffic and transit delays",
            "cost": "Total monetary cost including fuel, transit fares, parking, and tolls",
            "stress": "Overall stress level based on traffic, complexity, and weather factors (1=low, 10=high)",
            "reliability": "Predictability of travel time based on historical variance and incident probability (1=unreliable, 10=very reliable)"
        }
    
    def _get_indicator_legend(self) -> Dict[str, Dict[str, str]]:
        """Get legend for comparison indicators."""
        return {
            ComparisonIndicator.MUCH_BETTER.value: {
                "symbol": "↑↑",
                "color": "green",
                "description": "Significantly better"
            },
            ComparisonIndicator.BETTER.value: {
                "symbol": "↑",
                "color": "light_green",
                "description": "Better"
            },
            ComparisonIndicator.SIMILAR.value: {
                "symbol": "≈",
                "color": "gray",
                "description": "Similar"
            },
            ComparisonIndicator.WORSE.value: {
                "symbol": "↓",
                "color": "light_red",
                "description": "Worse"
            },
            ComparisonIndicator.MUCH_WORSE.value: {
                "symbol": "↓↓",
                "color": "red",
                "description": "Significantly worse"
            }
        }
    
    def _get_indicator_from_difference(
        self,
        difference: float,
        thresholds: Dict[str, float]
    ) -> ComparisonIndicator:
        """Get comparison indicator based on difference and thresholds."""
        if difference <= thresholds['much_better']:
            return ComparisonIndicator.MUCH_BETTER
        elif difference <= thresholds['better']:
            return ComparisonIndicator.BETTER
        elif abs(difference) <= thresholds['similar']:
            return ComparisonIndicator.SIMILAR
        elif difference <= thresholds['worse']:
            return ComparisonIndicator.WORSE
        else:
            return ComparisonIndicator.MUCH_WORSE
    
    def _format_time_difference(self, time_diff: float) -> str:
        """Format time difference for display."""
        if abs(time_diff) < 1:
            return "Same time"
        elif time_diff < 0:
            return f"{abs(time_diff):.0f} min faster"
        else:
            return f"{time_diff:.0f} min slower"
    
    def _format_cost_difference(self, cost_diff: float) -> str:
        """Format cost difference for display."""
        if abs(cost_diff) < 0.50:
            return "Same cost"
        elif cost_diff < 0:
            return f"${abs(cost_diff):.2f} cheaper"
        else:
            return f"${cost_diff:.2f} more expensive"
    
    def _format_stress_difference(self, stress_diff: float) -> str:
        """Format stress difference for display."""
        if abs(stress_diff) < 1:
            return "Similar stress"
        elif stress_diff < 0:
            return f"{abs(stress_diff):.0f} points less stressful"
        else:
            return f"{stress_diff:.0f} points more stressful"
    
    def _format_reliability_difference(self, reliability_diff: float) -> str:
        """Format reliability difference for display."""
        if abs(reliability_diff) < 1:
            return "Similar reliability"
        elif reliability_diff > 0:
            return f"{reliability_diff:.0f} points more reliable"
        else:
            return f"{abs(reliability_diff):.0f} points less reliable"
    
    def _explain_time_difference(self, time_diff: float) -> str:
        """Explain what the time difference means."""
        if abs(time_diff) < 5:
            return "Negligible time difference"
        elif time_diff < -15:
            return "Significantly faster - good for tight schedules"
        elif time_diff < 0:
            return "Moderately faster - saves some time"
        elif time_diff > 15:
            return "Much slower - consider if time is flexible"
        else:
            return "Somewhat slower - minor time trade-off"
    
    def _explain_cost_difference(self, cost_diff: float) -> str:
        """Explain what the cost difference means."""
        if abs(cost_diff) < 1.0:
            return "Minimal cost difference"
        elif cost_diff < -3.0:
            return "Significantly cheaper - good budget option"
        elif cost_diff < 0:
            return "Moderately cheaper - saves money"
        elif cost_diff > 5.0:
            return "Much more expensive - consider budget impact"
        else:
            return "Somewhat more expensive - minor cost trade-off"
    
    def _explain_stress_difference(self, stress_diff: float) -> str:
        """Explain what the stress difference means."""
        if abs(stress_diff) < 1:
            return "Similar stress levels"
        elif stress_diff < -2:
            return "Much less stressful - better for relaxation"
        elif stress_diff < 0:
            return "Somewhat less stressful - easier commute"
        elif stress_diff > 2:
            return "Much more stressful - consider mental energy"
        else:
            return "Somewhat more stressful - minor stress increase"
    
    def _explain_reliability_difference(self, reliability_diff: float) -> str:
        """Explain what the reliability difference means."""
        if abs(reliability_diff) < 1:
            return "Similar reliability"
        elif reliability_diff > 2:
            return "Much more reliable - better for important appointments"
        elif reliability_diff > 0:
            return "Somewhat more reliable - more predictable timing"
        elif reliability_diff < -2:
            return "Much less reliable - higher risk of delays"
        else:
            return "Somewhat less reliable - slightly more unpredictable"
    def _format_as_table(self, comparison_data: Dict[str, Any]) -> str:
        """Format comparison data as a table."""
        if not comparison_data["comparison_matrix"]:
            return "No routes to compare"
        
        # Create table header
        lines = []
        lines.append("Route Comparison Table")
        lines.append("=" * 80)
        
        # Header row
        header = f"{'Route':<12} {'Time':<15} {'Cost':<12} {'Stress':<10} {'Reliability':<12} {'Modes':<20}"
        lines.append(header)
        lines.append("-" * 80)
        
        # Data rows
        for entry in comparison_data["comparison_matrix"]:
            route_name = entry["route_name"]
            if entry["is_reference"]:
                route_name += " (ref)"
            
            time_display = entry["metrics"]["time"]["display"]
            cost_display = entry["metrics"]["cost"]["display"]
            stress_display = entry["metrics"]["stress"]["display"]
            reliability_display = entry["metrics"]["reliability"]["display"]
            modes = ", ".join(entry["transportation_modes"][:2])  # Limit to 2 modes
            
            # Add indicators if not reference
            if not entry["is_reference"] and "indicators" in entry:
                indicators = entry["indicators"]
                legend = self._get_indicator_legend()
                
                time_symbol = legend[indicators["time"]["indicator"].value]["symbol"]
                cost_symbol = legend[indicators["cost"]["indicator"].value]["symbol"]
                stress_symbol = legend[indicators["stress"]["indicator"].value]["symbol"]
                reliability_symbol = legend[indicators["reliability"]["indicator"].value]["symbol"]
                
                time_display += f" {time_symbol}"
                cost_display += f" {cost_symbol}"
                stress_display += f" {stress_symbol}"
                reliability_display += f" {reliability_symbol}"
            
            row = f"{route_name:<12} {time_display:<15} {cost_display:<12} {stress_display:<10} {reliability_display:<12} {modes:<20}"
            lines.append(row)
        
        lines.append("-" * 80)
        lines.append(comparison_data["summary"])
        
        return "\n".join(lines)
    
    def _format_as_list(self, comparison_data: Dict[str, Any]) -> str:
        """Format comparison data as a list."""
        if not comparison_data["comparison_matrix"]:
            return "No routes to compare"
        
        lines = []
        lines.append("Route Comparison")
        lines.append("================")
        
        for entry in comparison_data["comparison_matrix"]:
            lines.append(f"\n{entry['route_name']}:")
            if entry["is_reference"]:
                lines.append("  (Reference route)")
            
            lines.append(f"  • Time: {entry['metrics']['time']['display']} {entry['metrics']['time']['range']}")
            lines.append(f"  • Cost: {entry['metrics']['cost']['display']}")
            lines.append(f"  • Stress: {entry['metrics']['stress']['display']}")
            lines.append(f"  • Reliability: {entry['metrics']['reliability']['display']}")
            lines.append(f"  • Modes: {', '.join(entry['transportation_modes'])}")
            
            # Add comparison indicators
            if not entry["is_reference"] and "indicators" in entry:
                lines.append("  Compared to reference:")
                indicators = entry["indicators"]
                for criterion, indicator_data in indicators.items():
                    lines.append(f"    - {criterion.title()}: {indicator_data['display_text']}")
        
        lines.append(f"\n{comparison_data['summary']}")
        
        return "\n".join(lines)
    
    def _format_as_detailed(self, comparison_data: Dict[str, Any]) -> str:
        """Format comparison data with detailed breakdown."""
        if not comparison_data["comparison_matrix"]:
            return "No routes to compare"
        
        lines = []
        lines.append("Detailed Route Comparison")
        lines.append("========================")
        
        # Add criteria explanations
        lines.append("\nCriteria Explanations:")
        for criterion, explanation in comparison_data["criteria_explanations"].items():
            lines.append(f"• {criterion.title()}: {explanation}")
        
        # Add detailed route information
        for entry in comparison_data["comparison_matrix"]:
            lines.append(f"\n{entry['route_name']}:")
            lines.append("-" * (len(entry['route_name']) + 1))
            
            if entry["is_reference"]:
                lines.append("(Reference route for comparison)")
            
            # Time details
            time_metrics = entry["metrics"]["time"]
            lines.append(f"Time: {time_metrics['display']}")
            lines.append(f"  Range: {time_metrics['range']}")
            lines.append(f"  Peak hour impact: {time_metrics['peak_impact']}")
            
            # Cost details
            cost_metrics = entry["metrics"]["cost"]
            lines.append(f"Cost: {cost_metrics['display']}")
            breakdown = cost_metrics["breakdown"]
            if any(breakdown.values()):
                lines.append("  Breakdown:")
                if breakdown["fuel"] > 0:
                    lines.append(f"    Fuel/Rideshare: ${breakdown['fuel']:.2f}")
                if breakdown["transit"] > 0:
                    lines.append(f"    Transit fare: ${breakdown['transit']:.2f}")
                if breakdown["parking"] > 0:
                    lines.append(f"    Parking: ${breakdown['parking']:.2f}")
                if breakdown["tolls"] > 0:
                    lines.append(f"    Tolls: ${breakdown['tolls']:.2f}")
            
            # Stress details
            stress_metrics = entry["metrics"]["stress"]
            lines.append(f"Stress: {stress_metrics['display']}")
            components = stress_metrics["components"]
            lines.append("  Components:")
            lines.append(f"    Traffic: {components['traffic']}/10")
            lines.append(f"    Complexity: {components['complexity']}/10")
            lines.append(f"    Weather: {components['weather']}/10")
            
            # Reliability details
            reliability_metrics = entry["metrics"]["reliability"]
            lines.append(f"Reliability: {reliability_metrics['display']}")
            lines.append(f"  Time variance: {reliability_metrics['variance']}")
            lines.append(f"  Incident risk: {reliability_metrics['incident_risk']}")
            
            # Transportation modes
            lines.append(f"Transportation: {', '.join(entry['transportation_modes'])}")
            
            # Comparison indicators
            if not entry["is_reference"] and "indicators" in entry:
                lines.append("\nComparison to reference:")
                indicators = entry["indicators"]
                for criterion, indicator_data in indicators.items():
                    symbol = self._get_indicator_legend()[indicator_data["indicator"].value]["symbol"]
                    lines.append(f"  {criterion.title()}: {indicator_data['display_text']} {symbol}")
                    lines.append(f"    {indicator_data['explanation']}")
        
        lines.append(f"\n{comparison_data['summary']}")
        
        return "\n".join(lines)
    
    def _identify_route_tradeoffs(
        self,
        routes: List[Route],
        route_analyses: List[RouteAnalysis],
        standout_routes: Dict[str, int]
    ) -> List[Dict[str, Any]]:
        """Identify trade-offs between routes."""
        trade_offs = []
        
        # Check if different routes excel in different areas
        unique_standouts = set(standout_routes.values())
        
        if len(unique_standouts) > 1:
            # Time vs Cost trade-off
            fastest_idx = standout_routes["fastest"]
            cheapest_idx = standout_routes["cheapest"]
            
            if fastest_idx != cheapest_idx:
                fastest_cost = route_analyses[fastest_idx].cost_analysis.total_cost
                cheapest_time = route_analyses[cheapest_idx].time_analysis.estimated_time
                fastest_time = route_analyses[fastest_idx].time_analysis.estimated_time
                cheapest_cost = route_analyses[cheapest_idx].cost_analysis.total_cost
                
                time_saved = cheapest_time - fastest_time
                cost_difference = fastest_cost - cheapest_cost
                
                if time_saved > 10 and cost_difference > 2.0:
                    trade_offs.append({
                        "type": "time_vs_cost",
                        "description": f"Route {fastest_idx + 1} saves {time_saved:.0f} minutes but costs ${cost_difference:.2f} more than Route {cheapest_idx + 1}",
                        "routes_involved": [fastest_idx + 1, cheapest_idx + 1],
                        "magnitude": "high" if time_saved > 20 or cost_difference > 5.0 else "medium"
                    })
            
            # Stress vs Time trade-off
            fastest_idx = standout_routes["fastest"]
            least_stressful_idx = standout_routes["least_stressful"]
            
            if fastest_idx != least_stressful_idx:
                fastest_stress = route_analyses[fastest_idx].stress_analysis.overall_stress
                least_stressful_time = route_analyses[least_stressful_idx].time_analysis.estimated_time
                fastest_time = route_analyses[fastest_idx].time_analysis.estimated_time
                least_stressful_stress = route_analyses[least_stressful_idx].stress_analysis.overall_stress
                
                time_saved = least_stressful_time - fastest_time
                stress_difference = fastest_stress - least_stressful_stress
                
                if time_saved > 10 and stress_difference > 2:
                    trade_offs.append({
                        "type": "time_vs_stress",
                        "description": f"Route {fastest_idx + 1} saves {time_saved:.0f} minutes but is {stress_difference:.0f} points more stressful than Route {least_stressful_idx + 1}",
                        "routes_involved": [fastest_idx + 1, least_stressful_idx + 1],
                        "magnitude": "high" if time_saved > 20 or stress_difference > 3 else "medium"
                    })
            
            # Reliability vs Cost trade-off
            most_reliable_idx = standout_routes["most_reliable"]
            cheapest_idx = standout_routes["cheapest"]
            
            if most_reliable_idx != cheapest_idx:
                reliable_cost = route_analyses[most_reliable_idx].cost_analysis.total_cost
                cheapest_reliability = route_analyses[cheapest_idx].reliability_analysis.overall_reliability
                reliable_reliability = route_analyses[most_reliable_idx].reliability_analysis.overall_reliability
                cheapest_cost = route_analyses[cheapest_idx].cost_analysis.total_cost
                
                reliability_gain = reliable_reliability - cheapest_reliability
                cost_difference = reliable_cost - cheapest_cost
                
                if reliability_gain > 2 and cost_difference > 2.0:
                    trade_offs.append({
                        "type": "reliability_vs_cost",
                        "description": f"Route {most_reliable_idx + 1} is {reliability_gain:.0f} points more reliable but costs ${cost_difference:.2f} more than Route {cheapest_idx + 1}",
                        "routes_involved": [most_reliable_idx + 1, cheapest_idx + 1],
                        "magnitude": "high" if reliability_gain > 3 or cost_difference > 5.0 else "medium"
                    })
        
        return trade_offs
    
    def _generate_differences_summary(
        self,
        significant_differences: List[Dict[str, Any]],
        trade_offs: List[Dict[str, Any]]
    ) -> str:
        """Generate a summary of key differences and trade-offs."""
        if not significant_differences and not trade_offs:
            return "Routes are very similar across all criteria - choice comes down to personal preference."
        
        summary_parts = []
        
        if significant_differences:
            summary_parts.append("Key differences:")
            for diff in significant_differences:
                summary_parts.append(f"• {diff['description']} ({diff['impact']} impact)")
        
        if trade_offs:
            summary_parts.append("Main trade-offs:")
            for trade_off in trade_offs:
                summary_parts.append(f"• {trade_off['description']}")
        
        return "\n".join(summary_parts)
    
    def _check_time_metrics_consistency(self, route_analyses: List[RouteAnalysis]) -> List[Dict[str, str]]:
        """Check consistency of time metrics across analyses."""
        inconsistencies = []
        
        for i, analysis in enumerate(route_analyses):
            # Check if time range is logical
            if analysis.time_analysis.time_range_min >= analysis.time_analysis.time_range_max:
                inconsistencies.append({
                    "route_index": i,
                    "category": "time",
                    "issue": "time_range_invalid",
                    "description": f"Route {i + 1}: minimum time ({analysis.time_analysis.time_range_min}) >= maximum time ({analysis.time_analysis.time_range_max})"
                })
            
            # Check if estimated time is within range
            if not (analysis.time_analysis.time_range_min <= analysis.time_analysis.estimated_time <= analysis.time_analysis.time_range_max):
                inconsistencies.append({
                    "route_index": i,
                    "category": "time",
                    "issue": "estimated_time_outside_range",
                    "description": f"Route {i + 1}: estimated time ({analysis.time_analysis.estimated_time}) outside of range ({analysis.time_analysis.time_range_min}-{analysis.time_analysis.time_range_max})"
                })
        
        return inconsistencies
    
    def _check_cost_metrics_consistency(self, route_analyses: List[RouteAnalysis]) -> List[Dict[str, str]]:
        """Check consistency of cost metrics across analyses."""
        inconsistencies = []
        
        for i, analysis in enumerate(route_analyses):
            # Check if total cost matches breakdown
            breakdown_total = (analysis.cost_analysis.fuel_cost + 
                             analysis.cost_analysis.transit_fare + 
                             analysis.cost_analysis.parking_cost + 
                             analysis.cost_analysis.toll_cost)
            
            if abs(breakdown_total - analysis.cost_analysis.total_cost) > 0.01:
                inconsistencies.append({
                    "route_index": i,
                    "category": "cost",
                    "issue": "total_cost_mismatch",
                    "description": f"Route {i + 1}: total cost ({analysis.cost_analysis.total_cost:.2f}) doesn't match breakdown sum ({breakdown_total:.2f})"
                })
            
            # Check for negative costs
            if analysis.cost_analysis.total_cost < 0:
                inconsistencies.append({
                    "route_index": i,
                    "category": "cost",
                    "issue": "negative_cost",
                    "description": f"Route {i + 1}: negative total cost ({analysis.cost_analysis.total_cost:.2f})"
                })
        
        return inconsistencies
    
    def _check_stress_metrics_consistency(self, route_analyses: List[RouteAnalysis]) -> List[Dict[str, str]]:
        """Check consistency of stress metrics across analyses."""
        inconsistencies = []
        
        for i, analysis in enumerate(route_analyses):
            # Check if stress values are within valid range (1-10)
            stress_values = [
                ("overall", analysis.stress_analysis.overall_stress),
                ("traffic", analysis.stress_analysis.traffic_stress),
                ("complexity", analysis.stress_analysis.complexity_stress),
                ("weather", analysis.stress_analysis.weather_stress)
            ]
            
            for stress_type, value in stress_values:
                if not (1 <= value <= 10):
                    inconsistencies.append({
                        "route_index": i,
                        "category": "stress",
                        "issue": "stress_out_of_range",
                        "description": f"Route {i + 1}: {stress_type} stress ({value}) outside valid range (1-10)"
                    })
        
        return inconsistencies
    
    def _check_reliability_metrics_consistency(self, route_analyses: List[RouteAnalysis]) -> List[Dict[str, str]]:
        """Check consistency of reliability metrics across analyses."""
        inconsistencies = []
        
        for i, analysis in enumerate(route_analyses):
            # Check if reliability score is within valid range (1-10)
            if not (1 <= analysis.reliability_analysis.overall_reliability <= 10):
                inconsistencies.append({
                    "route_index": i,
                    "category": "reliability",
                    "issue": "reliability_out_of_range",
                    "description": f"Route {i + 1}: reliability score ({analysis.reliability_analysis.overall_reliability}) outside valid range (1-10)"
                })
            
            # Check if incident probability is within valid range (0-1)
            if not (0 <= analysis.reliability_analysis.incident_probability <= 1):
                inconsistencies.append({
                    "route_index": i,
                    "category": "reliability",
                    "issue": "incident_probability_out_of_range",
                    "description": f"Route {i + 1}: incident probability ({analysis.reliability_analysis.incident_probability}) outside valid range (0-1)"
                })
            
            # Check if service reliability is within valid range (0-1)
            if not (0 <= analysis.reliability_analysis.service_reliability <= 1):
                inconsistencies.append({
                    "route_index": i,
                    "category": "reliability",
                    "issue": "service_reliability_out_of_range",
                    "description": f"Route {i + 1}: service reliability ({analysis.reliability_analysis.service_reliability}) outside valid range (0-1)"
                })
        
        return inconsistencies
    
    def _generate_metrics_summary(self, route_analyses: List[RouteAnalysis]) -> Dict[str, Any]:
        """Generate a summary of metrics across all routes."""
        if not route_analyses:
            return {}
        
        times = [analysis.time_analysis.estimated_time for analysis in route_analyses]
        costs = [analysis.cost_analysis.total_cost for analysis in route_analyses]
        stress_levels = [analysis.stress_analysis.overall_stress for analysis in route_analyses]
        reliability_scores = [analysis.reliability_analysis.overall_reliability for analysis in route_analyses]
        
        return {
            "time": {
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
                "range": max(times) - min(times),
                "unit": "minutes"
            },
            "cost": {
                "min": min(costs),
                "max": max(costs),
                "avg": sum(costs) / len(costs),
                "range": max(costs) - min(costs),
                "unit": "dollars"
            },
            "stress": {
                "min": min(stress_levels),
                "max": max(stress_levels),
                "avg": sum(stress_levels) / len(stress_levels),
                "range": max(stress_levels) - min(stress_levels),
                "unit": "scale_1_10"
            },
            "reliability": {
                "min": min(reliability_scores),
                "max": max(reliability_scores),
                "avg": sum(reliability_scores) / len(reliability_scores),
                "range": max(reliability_scores) - min(reliability_scores),
                "unit": "scale_1_10"
            }
        }
    
    def _generate_consistency_recommendations(self, inconsistencies: List[Dict[str, str]]) -> List[str]:
        """Generate recommendations for fixing consistency issues."""
        recommendations = []
        
        # Group inconsistencies by type
        issue_types = {}
        for inconsistency in inconsistencies:
            issue_type = inconsistency["issue"]
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(inconsistency)
        
        # Generate recommendations for each issue type
        for issue_type, issues in issue_types.items():
            if issue_type == "time_range_invalid":
                recommendations.append("Fix time range calculations - ensure minimum time < maximum time")
            elif issue_type == "estimated_time_outside_range":
                recommendations.append("Ensure estimated time falls within the calculated time range")
            elif issue_type == "total_cost_mismatch":
                recommendations.append("Verify cost breakdown calculations match total cost")
            elif issue_type == "negative_cost":
                recommendations.append("Check cost calculations - costs should not be negative")
            elif issue_type.endswith("_out_of_range"):
                recommendations.append(f"Validate {issue_type.replace('_out_of_range', '')} values are within expected ranges")
        
        return recommendations