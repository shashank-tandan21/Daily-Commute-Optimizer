"""Tests for transparency and explanation features."""

import pytest
from datetime import datetime, timedelta
from commute_optimizer.services.decision_making import DecisionMakingEngine
from commute_optimizer.models import (
    Route, RouteAnalysis, PreferenceProfile, TransportationMode,
    TimeAnalysis, CostAnalysis, StressAnalysis, ReliabilityAnalysis,
    TradeoffSummary, Location, RouteSegment
)


@pytest.fixture
def decision_engine():
    """Create a decision making engine for testing."""
    return DecisionMakingEngine()


@pytest.fixture
def sample_routes_and_analyses():
    """Create sample routes and analyses for testing."""
    # Create sample locations
    origin = Location(latitude=37.7749, longitude=-122.4194, address="San Francisco, CA")
    destination = Location(latitude=37.7849, longitude=-122.4094, address="San Francisco, CA")
    
    # Create sample route segments
    segment1 = RouteSegment(
        mode=TransportationMode.DRIVING,
        start_location=origin,
        end_location=destination,
        distance=5.0,
        duration=20,
        instructions="Drive north"
    )
    
    segment2 = RouteSegment(
        mode=TransportationMode.PUBLIC_TRANSIT,
        start_location=origin,
        end_location=destination,
        distance=6.0,
        duration=35,
        instructions="Take bus"
    )
    
    # Create sample routes
    departure_time = datetime.now()
    
    route1 = Route(
        id="route_1",
        segments=[segment1],
        total_distance=5.0,
        estimated_time=20,
        estimated_cost=8.50,
        stress_level=6,
        reliability_score=8,
        transportation_modes=[TransportationMode.DRIVING],
        departure_time=departure_time,
        arrival_time=departure_time + timedelta(minutes=20),
        instructions=["Drive north"]
    )
    
    route2 = Route(
        id="route_2",
        segments=[segment2],
        total_distance=6.0,
        estimated_time=35,
        estimated_cost=3.25,
        stress_level=3,
        reliability_score=6,
        transportation_modes=[TransportationMode.PUBLIC_TRANSIT],
        departure_time=departure_time,
        arrival_time=departure_time + timedelta(minutes=35),
        instructions=["Take bus north"]
    )
    
    # Create sample analyses
    analysis1 = RouteAnalysis(
        route_id="route_1",
        timestamp=datetime.now(),
        time_analysis=TimeAnalysis(
            estimated_time=20,
            time_range_min=18,
            time_range_max=25,
            peak_hour_impact=5
        ),
        cost_analysis=CostAnalysis(
            fuel_cost=6.00,
            transit_fare=0.00,
            parking_cost=2.50,
            toll_cost=0.00,
            total_cost=8.50
        ),
        stress_analysis=StressAnalysis(
            traffic_stress=7,
            complexity_stress=4,
            weather_stress=5,
            overall_stress=6
        ),
        reliability_analysis=ReliabilityAnalysis(
            historical_variance=5.0,
            incident_probability=0.15,
            weather_impact=0.2,
            service_reliability=0.9,
            overall_reliability=8
        ),
        tradeoff_summary=TradeoffSummary(
            strengths=["Fast", "Direct"],
            weaknesses=["Expensive", "Stressful"],
            when_to_choose=["When time is critical"],
            when_not_to_choose=["When budget is tight"],
            compared_to_alternatives=[]
        )
    )
    
    analysis2 = RouteAnalysis(
        route_id="route_2",
        timestamp=datetime.now(),
        time_analysis=TimeAnalysis(
            estimated_time=35,
            time_range_min=30,
            time_range_max=45,
            peak_hour_impact=10
        ),
        cost_analysis=CostAnalysis(
            fuel_cost=0.00,
            transit_fare=3.25,
            parking_cost=0.00,
            toll_cost=0.00,
            total_cost=3.25
        ),
        stress_analysis=StressAnalysis(
            traffic_stress=2,
            complexity_stress=4,
            weather_stress=3,
            overall_stress=3
        ),
        reliability_analysis=ReliabilityAnalysis(
            historical_variance=8.0,
            incident_probability=0.25,
            weather_impact=0.3,
            service_reliability=0.7,
            overall_reliability=6
        ),
        tradeoff_summary=TradeoffSummary(
            strengths=["Affordable", "Low stress"],
            weaknesses=["Slower", "Less reliable"],
            when_to_choose=["When budget matters"],
            when_not_to_choose=["When time is critical"],
            compared_to_alternatives=[]
        )
    )
    
    return [route1, route2], [analysis1, analysis2]


@pytest.fixture
def sample_preferences():
    """Create sample user preferences."""
    return PreferenceProfile(
        name="Balanced",
        time_weight=30,
        cost_weight=25,
        comfort_weight=25,
        reliability_weight=20
    )


class TestTransparencyFeatures:
    """Test transparency and explanation features."""
    
    def test_generate_tradeoff_explanation_templates(self, decision_engine, sample_routes_and_analyses):
        """Test generation of trade-off explanation templates."""
        routes, analyses = sample_routes_and_analyses
        
        templates = decision_engine.generate_tradeoff_explanation_templates(routes, analyses)
        
        # Should have templates for both routes
        assert len(templates["templates"]) == 2
        
        # Each template should have required components
        for template in templates["templates"]:
            assert "route_id" in template
            assert "route_name" in template
            assert "strengths" in template
            assert "weaknesses" in template
            assert "trade_offs" in template
            assert "when_to_choose" in template
            assert "when_not_to_choose" in template
            assert "comparison_highlights" in template
        
        # Should have overall summary and guidance
        assert "summary" in templates
        assert "decision_guidance" in templates
        assert isinstance(templates["decision_guidance"], list)
    
    def test_make_decision_factors_visible(self, decision_engine, sample_routes_and_analyses, sample_preferences):
        """Test making decision factors visible."""
        routes, analyses = sample_routes_and_analyses
        
        factors = decision_engine.make_decision_factors_visible(
            routes, analyses, sample_preferences
        )
        
        # Should have all required components
        assert "preference_weights" in factors
        assert "scoring_breakdown" in factors
        assert "context_factors" in factors
        assert "route_comparisons" in factors
        assert "decision_logic" in factors
        assert "uncertainty_factors" in factors
        assert "assumptions" in factors
        
        # Preference weights should match input
        assert factors["preference_weights"]["time_weight"] == 30
        assert factors["preference_weights"]["cost_weight"] == 25
        
        # Should have scoring breakdown for each route
        assert len(factors["scoring_breakdown"]) == 2
        
        for breakdown in factors["scoring_breakdown"]:
            assert "route_id" in breakdown
            assert "total_score" in breakdown
            assert "component_scores" in breakdown
            assert "score_explanation" in breakdown
    
    def test_identify_when_not_to_choose_with_alternatives(self, decision_engine, sample_routes_and_analyses):
        """Test identification of when not to choose a route with alternatives."""
        routes, analyses = sample_routes_and_analyses
        route, analysis = routes[0], analyses[0]
        alternatives = [(routes[1], analyses[1])]
        
        warnings = decision_engine.identify_when_not_to_choose(route, analysis, alternatives)
        
        # Should have warnings
        assert len(warnings) > 0
        assert isinstance(warnings, list)
        
        # Should include comparative warnings since alternatives are provided
        # The expensive route should have budget-related warnings
        budget_warnings = [w for w in warnings if "budget" in w.lower() or "cost" in w.lower()]
        assert len(budget_warnings) > 0


class TestLanguageFiltering:
    """Test language filtering and compliance features."""
    
    def test_validate_language_compliance_with_violations(self, decision_engine):
        """Test language validation with violations."""
        text_with_violations = "This is the best route and optimal choice for your commute."
        
        result = decision_engine.validate_language_compliance(text_with_violations)
        
        # Should not be compliant
        assert not result["is_compliant"]
        
        # Should have violations
        assert len(result["violations"]) > 0
        assert len(result["forbidden_terms_found"]) > 0
        
        # Should have suggestions
        assert len(result["suggestions"]) > 0
    
    def test_validate_language_compliance_without_violations(self, decision_engine):
        """Test language validation without violations."""
        compliant_text = "This route scores highest based on your preferences because it balances time and cost effectively."
        
        result = decision_engine.validate_language_compliance(compliant_text)
        
        # Should be compliant
        assert result["is_compliant"]
        
        # Should have no violations
        assert len(result["violations"]) == 0
        assert len(result["forbidden_terms_found"]) == 0
    
    def test_filter_and_correct_language(self, decision_engine):
        """Test language filtering and correction."""
        problematic_text = "This is the best route for you."
        
        result = decision_engine.filter_and_correct_language(problematic_text)
        
        # Should have made changes
        assert len(result["changes_made"]) > 0
        
        # Corrected text should be different
        assert result["corrected_text"] != result["original_text"]
        
        # Should not contain the original forbidden term
        assert "best" not in result["corrected_text"].lower()
    
    def test_generate_compliant_recommendation_text(self, decision_engine, sample_routes_and_analyses):
        """Test generation of compliant recommendation text."""
        routes, analyses = sample_routes_and_analyses
        route, analysis = routes[0], analyses[0]
        alternatives = [(routes[1], analyses[1])]
        
        reasoning = "This route is fastest and most reliable."
        
        compliant_text = decision_engine.generate_compliant_recommendation_text(
            route, analysis, reasoning, alternatives
        )
        
        # Should not contain forbidden terms without explanation
        forbidden_terms = ["best", "optimal", "perfect", "ideal"]
        for term in forbidden_terms:
            if term in compliant_text.lower():
                # If term appears, it should have explanation nearby
                assert decision_engine._has_nearby_explanation(compliant_text, term)
        
        # Should contain explanation-based language
        assert "based on" in compliant_text.lower() or "because" in compliant_text.lower()
        
        # Should contain transparency elements
        assert "consider alternatives" in compliant_text.lower() or "when not to" in compliant_text.lower()
    
    def test_forbidden_terms_detection(self, decision_engine):
        """Test detection of forbidden terms."""
        test_cases = [
            ("This is the best route", True),
            ("This is the optimal solution", True),
            ("This route is recommended", True),
            ("This route scores highest based on your preferences", False),
            ("This route is suitable given your priorities", False)
        ]
        
        for text, should_have_violations in test_cases:
            violations = decision_engine._check_forbidden_terms(text)
            
            if should_have_violations:
                assert len(violations) > 0, f"Expected violations for: {text}"
            else:
                assert len(violations) == 0, f"Unexpected violations for: {text}"
    
    def test_superlatives_without_explanation_detection(self, decision_engine):
        """Test detection of superlatives without explanation."""
        test_cases = [
            ("This is the fastest route", True),
            ("This is the fastest route compared to alternatives", False),
            ("This route is cheapest", True),
            ("This route is cheapest among the options", False)
        ]
        
        for text, should_have_violations in test_cases:
            violations = decision_engine._check_superlatives_without_explanation(text)
            
            if should_have_violations:
                assert len(violations) > 0, f"Expected violations for: {text}"
            else:
                assert len(violations) == 0, f"Unexpected violations for: {text}"


class TestExplanationGeneration:
    """Test explanation generation methods."""
    
    def test_route_strengths_identification(self, decision_engine, sample_routes_and_analyses):
        """Test identification of route strengths."""
        routes, analyses = sample_routes_and_analyses
        route, analysis = routes[0], analyses[0]  # Faster but more expensive route
        
        strengths = decision_engine._identify_route_strengths(route, analysis, routes, analyses)
        
        # Should identify that this route is faster
        assert len(strengths) > 0
        time_strengths = [s for s in strengths if "fast" in s.lower() or "time" in s.lower()]
        assert len(time_strengths) > 0
    
    def test_route_weaknesses_identification(self, decision_engine, sample_routes_and_analyses):
        """Test identification of route weaknesses."""
        routes, analyses = sample_routes_and_analyses
        route, analysis = routes[0], analyses[0]  # More expensive route
        
        weaknesses = decision_engine._identify_route_weaknesses(route, analysis, routes, analyses)
        
        # Should identify cost as a weakness
        assert len(weaknesses) > 0
        cost_weaknesses = [w for w in weaknesses if "cost" in w.lower() or "expensive" in w.lower()]
        assert len(cost_weaknesses) > 0
    
    def test_when_to_choose_guidance(self, decision_engine, sample_routes_and_analyses):
        """Test generation of when-to-choose guidance."""
        routes, analyses = sample_routes_and_analyses
        route, analysis = routes[0], analyses[0]  # Fast route
        
        guidance = decision_engine._generate_when_to_choose_guidance(route, analysis)
        
        # Should have guidance
        assert len(guidance) > 0
        
        # Should include time-related guidance for the fast route
        time_guidance = [g for g in guidance if "time" in g.lower() or "quick" in g.lower()]
        assert len(time_guidance) > 0