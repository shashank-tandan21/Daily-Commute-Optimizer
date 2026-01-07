"""
Streamlit Web UI for the Daily Commute Optimizer.

Run with: streamlit run web_ui.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, time
import json

from commute_optimizer.app import CommuteOptimizerApp
from commute_optimizer.models import Location, UserPreferences, PreferenceProfile, NotificationSettings


def main():
    st.set_page_config(
        page_title="Daily Commute Optimizer",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🚗 Daily Commute Optimizer")
    st.markdown("Compare multiple commute options with transparent trade-off analysis")
    
    # Initialize the app
    if 'app' not in st.session_state:
        st.session_state.app = CommuteOptimizerApp()
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Trip Details")
        
        # Location inputs
        origin_address = st.text_input(
            "From (Origin)",
            value="Seattle, WA",
            help="Enter your starting location"
        )
        
        destination_address = st.text_input(
            "To (Destination)", 
            value="Bellevue, WA",
            help="Enter your destination"
        )
        
        # Departure time
        st.subheader("Departure Time")
        use_now = st.checkbox("Leave now", value=True)
        
        if not use_now:
            departure_time_input = st.time_input(
                "Departure time",
                value=time(8, 30),
                help="When do you want to leave?"
            )
            departure_datetime = datetime.combine(datetime.now().date(), departure_time_input)
        else:
            departure_datetime = datetime.now()
        
        st.divider()
        
        # Preferences
        st.header("Your Priorities")
        st.markdown("Adjust the sliders to match your priorities (must sum to 100%)")
        
        time_weight = st.slider("Time Priority", 0, 100, 40, 5, help="How important is minimizing travel time?")
        cost_weight = st.slider("Cost Priority", 0, 100, 20, 5, help="How important is minimizing cost?")
        comfort_weight = st.slider("Comfort Priority", 0, 100, 20, 5, help="How important is minimizing stress?")
        reliability_weight = st.slider("Reliability Priority", 0, 100, 20, 5, help="How important is predictable timing?")
        
        total_weight = time_weight + cost_weight + comfort_weight + reliability_weight
        
        if total_weight != 100:
            st.error(f"⚠️ Weights must sum to 100% (currently {total_weight}%)")
            st.stop()
        else:
            st.success(f"✅ Weights sum to 100%")
        
        st.divider()
        
        # Transportation preferences
        st.subheader("Transportation Options")
        preferred_modes = st.multiselect(
            "Preferred modes",
            ["driving", "public_transit", "walking", "cycling", "rideshare"],
            default=["driving", "public_transit", "walking"],
            help="Select your preferred transportation methods"
        )
        
        max_walking_distance = st.slider(
            "Max walking distance (km)",
            0.5, 5.0, 2.0, 0.5,
            help="Maximum distance you're willing to walk"
        )
        
        # Optimize button
        st.divider()
        optimize_button = st.button("🔍 Find Routes", type="primary", use_container_width=True)
    
    # Main content area
    if optimize_button:
        if not origin_address or not destination_address:
            st.error("Please enter both origin and destination addresses.")
            st.stop()
        
        with st.spinner("Finding the best routes for you..."):
            try:
                # Create locations
                origin = Location(
                    latitude=47.6062,  # Mock coordinates for demo
                    longitude=-122.3321,
                    address=origin_address
                )
                destination = Location(
                    latitude=47.6101,  # Mock coordinates for demo  
                    longitude=-122.2015,
                    address=destination_address
                )
                
                # Create user preferences
                preferences = UserPreferences(
                    user_id="web_user",
                    preference_profiles=[
                        PreferenceProfile(
                            name="current",
                            time_weight=time_weight,
                            cost_weight=cost_weight,
                            comfort_weight=comfort_weight,
                            reliability_weight=reliability_weight,
                            preferred_modes=preferred_modes,
                            max_walking_distance=max_walking_distance
                        )
                    ],
                    default_profile="current",
                    saved_locations=[],  # Empty list for web users
                    notification_settings=NotificationSettings()  # Default notification settings
                )
                
                # Optimize commute
                result = st.session_state.app.optimize_commute(
                    origin=origin,
                    destination=destination,
                    departure_time=departure_datetime,
                    user_preferences=preferences
                )
                
                # Display results
                display_results(result)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.error("Please try again with different inputs.")


def display_results(result):
    """Display the optimization results in a user-friendly format."""
    
    routes = result.get('routes', [])
    recommendation = result.get('recommendation', {})
    
    if not routes:
        st.warning("No routes found for your trip. Please try different locations.")
        return
    
    st.success(f"✅ Found {len(routes)} route options!")
    
    # Recommendation section
    st.header("🎯 Recommended Route")
    
    if recommendation and 'recommended_route' in recommendation:
        rec_route = recommendation['recommended_route']
        rec_reasoning = recommendation.get('reasoning', 'No reasoning provided')
        rec_confidence = recommendation.get('confidence', 0)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**Why this route:** {rec_reasoning}")
        
        with col2:
            confidence_color = "green" if rec_confidence > 0.7 else "orange" if rec_confidence > 0.4 else "red"
            st.markdown(f"**Confidence:** :{confidence_color}[{rec_confidence:.0%}]")
    
    st.divider()
    
    # Route comparison table
    st.header("📊 All Route Options")
    
    # Create comparison data
    route_data = []
    for i, route in enumerate(routes):
        # Get corresponding analysis
        analysis = None
        for analysis_item in result.get('analyses', []):
            if analysis_item.route_id == route.id:
                analysis = analysis_item
                break
        
        if analysis:
            route_data.append({
                'Route': f"Route {i+1}",
                'Transportation': ' + '.join([mode.value.replace('_', ' ').title() for mode in route.transportation_modes]),
                'Time': f"{route.estimated_time} min",
                'Time Range': f"{analysis.time_analysis.time_range_min}-{analysis.time_analysis.time_range_max} min",
                'Cost': f"${route.estimated_cost:.2f}",
                'Stress Level': f"{analysis.stress_analysis.overall_stress}/10",
                'Reliability': f"{analysis.reliability_analysis.overall_reliability}/10"
            })
    
    if route_data:
        df = pd.DataFrame(route_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Detailed route cards
    st.header("🗺️ Route Details")
    
    for i, route in enumerate(routes):
        # Find corresponding analysis
        analysis = None
        for analysis_item in result.get('analyses', []):
            if analysis_item.route_id == route.id:
                analysis = analysis_item
                break
        
        if not analysis:
            continue
        
        with st.expander(f"Route {i+1}: {' + '.join([mode.value.replace('_', ' ').title() for mode in route.transportation_modes])}", expanded=i==0):
            
            # Route metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Travel Time", f"{route.estimated_time} min", 
                         f"Range: {analysis.time_analysis.time_range_min}-{analysis.time_analysis.time_range_max} min")
            
            with col2:
                st.metric("Total Cost", f"${route.estimated_cost:.2f}")
            
            with col3:
                stress_color = "green" if analysis.stress_analysis.overall_stress <= 4 else "orange" if analysis.stress_analysis.overall_stress <= 7 else "red"
                st.metric("Stress Level", f"{analysis.stress_analysis.overall_stress}/10")
            
            with col4:
                reliability_color = "green" if analysis.reliability_analysis.overall_reliability >= 7 else "orange" if analysis.reliability_analysis.overall_reliability >= 4 else "red"
                st.metric("Reliability", f"{analysis.reliability_analysis.overall_reliability}/10")
            
            # Strengths and weaknesses
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("✅ Strengths")
                strengths = []
                if route.estimated_time <= 30:
                    strengths.append("Quick travel time")
                if route.estimated_cost <= 3.0:
                    strengths.append("Low cost")
                if analysis.stress_analysis.overall_stress <= 4:
                    strengths.append("Low stress journey")
                if analysis.reliability_analysis.overall_reliability >= 8:
                    strengths.append("Highly reliable")
                
                if not strengths:
                    strengths = ["Viable route option"]
                
                for strength in strengths:
                    st.write(f"• {strength}")
            
            with col2:
                st.subheader("❌ When NOT to choose")
                warnings = []
                if route.estimated_time > 60:
                    warnings.append("When you have time constraints")
                if route.estimated_cost > 10.0:
                    warnings.append("When budget is tight")
                if analysis.stress_analysis.overall_stress >= 7:
                    warnings.append("When you're already stressed")
                if analysis.reliability_analysis.overall_reliability <= 5:
                    warnings.append("For critical appointments")
                
                # Add mode-specific warnings
                from commute_optimizer.models import TransportationMode
                if TransportationMode.PUBLIC_TRANSIT in route.transportation_modes:
                    warnings.append("During service disruptions")
                if TransportationMode.CYCLING in route.transportation_modes:
                    warnings.append("In bad weather")
                
                if not warnings:
                    warnings = ["Generally a good option"]
                
                for warning in warnings:
                    st.write(f"• {warning}")
    
    # Trade-off summary
    if len(routes) > 1:
        st.header("⚖️ Trade-off Summary")
        
        comparisons = result.get('comparisons', {})
        if comparisons and 'summary' in comparisons:
            st.info(comparisons['summary'])
        else:
            # Generate simple comparison
            fastest_route = min(routes, key=lambda r: r.estimated_time)
            cheapest_route = min(routes, key=lambda r: r.estimated_cost)
            
            fastest_idx = routes.index(fastest_route) + 1
            cheapest_idx = routes.index(cheapest_route) + 1
            
            if fastest_idx != cheapest_idx:
                st.info(f"Route {fastest_idx} is fastest, Route {cheapest_idx} is cheapest")
            else:
                st.info(f"Route {fastest_idx} is both fastest and cheapest")


if __name__ == "__main__":
    main()