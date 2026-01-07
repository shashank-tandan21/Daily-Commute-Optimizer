"""Command-line interface for the Daily Commute Optimizer."""

import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .app import CommuteOptimizerApp
from .models import (
    Location, UserPreferences, PreferenceProfile, SavedLocation,
    NotificationSettings, TransportationMode
)


class CommuteCLI:
    """Command-line interface for testing the Daily Commute Optimizer."""
    
    def __init__(self):
        """Initialize the CLI with the main app."""
        self.app = CommuteOptimizerApp()
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for CLI output."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def run(self):
        """Main CLI entry point."""
        parser = self.create_parser()
        args = parser.parse_args()
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        try:
            # Parse locations
            origin = self.parse_location(args.origin)
            destination = self.parse_location(args.destination)
            
            # Parse departure time
            departure_time = self.parse_departure_time(args.departure_time)
            
            # Create user preferences
            user_preferences = self.create_user_preferences(args)
            
            # Run optimization
            print("🚗 Daily Commute Optimizer")
            print("=" * 50)
            print(f"From: {origin.address}")
            print(f"To: {destination.address}")
            print(f"Departure: {departure_time.strftime('%Y-%m-%d %H:%M')}")
            print()
            
            result = self.app.optimize_commute(
                origin=origin,
                destination=destination,
                departure_time=departure_time,
                user_preferences=user_preferences
            )
            
            # Display results
            self.display_results(result)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1
        
        return 0
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="Daily Commute Optimizer - Compare multiple route options",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s "123 Main St, Seattle, WA" "456 Pine St, Seattle, WA"
  %(prog)s "Home" "Work" --departure-time "08:30"
  %(prog)s "Seattle, WA" "Bellevue, WA" --time-weight 60 --cost-weight 40
            """
        )
        
        # Required arguments
        parser.add_argument(
            'origin',
            help='Origin address or location name'
        )
        parser.add_argument(
            'destination', 
            help='Destination address or location name'
        )
        
        # Optional arguments
        parser.add_argument(
            '--departure-time',
            default='now',
            help='Departure time (HH:MM format or "now", default: now)'
        )
        
        # Preference weights
        parser.add_argument(
            '--time-weight',
            type=int,
            default=40,
            help='Weight for time priority (0-100, default: 40)'
        )
        parser.add_argument(
            '--cost-weight',
            type=int,
            default=20,
            help='Weight for cost priority (0-100, default: 20)'
        )
        parser.add_argument(
            '--comfort-weight',
            type=int,
            default=20,
            help='Weight for comfort priority (0-100, default: 20)'
        )
        parser.add_argument(
            '--reliability-weight',
            type=int,
            default=20,
            help='Weight for reliability priority (0-100, default: 20)'
        )
        
        # Transportation preferences
        parser.add_argument(
            '--preferred-modes',
            nargs='*',
            choices=[mode.value for mode in TransportationMode],
            default=[],
            help='Preferred transportation modes'
        )
        parser.add_argument(
            '--max-walking-distance',
            type=float,
            default=2.0,
            help='Maximum walking distance in kilometers (default: 2.0)'
        )
        
        # Output options
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results in JSON format'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        
        return parser
    
    def parse_location(self, location_str: str) -> Location:
        """Parse a location string into a Location object."""
        # For CLI testing, we'll create mock coordinates
        # In a real implementation, this would geocode the address
        
        # Simple coordinate assignment based on common location names
        coords_map = {
            'home': (47.6062, -122.3321),  # Seattle
            'work': (47.6101, -122.2015),  # Bellevue
            'seattle': (47.6062, -122.3321),
            'bellevue': (47.6101, -122.2015),
            'redmond': (47.6740, -122.1215),
            'tacoma': (47.2529, -122.4443)
        }
        
        location_lower = location_str.lower()
        if location_lower in coords_map:
            lat, lon = coords_map[location_lower]
            return Location(
                latitude=lat,
                longitude=lon,
                address=location_str.title(),
                name=location_str.title()
            )
        
        # Default coordinates for unknown addresses (Seattle area)
        return Location(
            latitude=47.6062 + hash(location_str) % 100 / 1000,  # Small variation
            longitude=-122.3321 + hash(location_str) % 100 / 1000,
            address=location_str,
            name=location_str
        )
    
    def parse_departure_time(self, time_str: str) -> datetime:
        """Parse departure time string into datetime object."""
        if time_str.lower() == 'now':
            return datetime.now()
        
        try:
            # Parse HH:MM format
            time_parts = time_str.split(':')
            if len(time_parts) == 2:
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                
                # Use today's date with specified time
                now = datetime.now()
                departure = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If time has passed today, use tomorrow
                if departure <= now:
                    departure += timedelta(days=1)
                
                return departure
        except ValueError:
            pass
        
        raise ValueError(f"Invalid departure time format: {time_str}. Use HH:MM or 'now'")
    
    def create_user_preferences(self, args) -> UserPreferences:
        """Create UserPreferences from command-line arguments."""
        # Validate weights sum to 100
        total_weight = args.time_weight + args.cost_weight + args.comfort_weight + args.reliability_weight
        if total_weight != 100:
            raise ValueError(f"Preference weights must sum to 100, got {total_weight}")
        
        # Convert preferred modes
        preferred_modes = [TransportationMode(mode) for mode in args.preferred_modes]
        
        # Create preference profile
        profile = PreferenceProfile(
            name="cli_profile",
            time_weight=args.time_weight,
            cost_weight=args.cost_weight,
            comfort_weight=args.comfort_weight,
            reliability_weight=args.reliability_weight,
            max_walking_distance=args.max_walking_distance,
            preferred_modes=preferred_modes,
            avoided_features=[]
        )
        
        # Create user preferences
        return UserPreferences(
            user_id="cli_user",
            preference_profiles=[profile],
            saved_locations=[],
            notification_settings=NotificationSettings(),
            default_profile="cli_profile"
        )
    
    def display_results(self, result: Dict[str, Any]):
        """Display optimization results in a readable format."""
        if 'error' in result:
            print(f"❌ {result['message']}")
            if 'suggestions' in result:
                print("\n💡 Suggestions:")
                for suggestion in result['suggestions']:
                    print(f"  • {suggestion}")
            return
        
        routes = result.get('routes', [])
        analyses = result.get('analyses', [])
        recommendation = result.get('recommendation', {})
        
        if not routes:
            print("❌ No routes found")
            return
        
        print(f"✅ Found {len(routes)} route options:")
        print()
        
        # Display recommendation first
        if recommendation:
            recommended_id = recommendation.get('recommended_route_id')
            print("🎯 RECOMMENDATION")
            print("-" * 30)
            if recommended_id:
                recommended_route = next((r for r in routes if r.id == recommended_id), None)
                if recommended_route:
                    print(f"Route: {self.format_route_summary(recommended_route)}")
            
            if 'reasoning' in recommendation:
                print(f"Why: {recommendation['reasoning']}")
            
            if 'caveats' in recommendation and recommendation['caveats']:
                print("⚠️  Caveats:")
                for caveat in recommendation['caveats']:
                    print(f"  • {caveat}")
            print()
        
        # Display all routes with analysis
        print("📊 ALL ROUTE OPTIONS")
        print("-" * 30)
        
        for i, (route, analysis) in enumerate(zip(routes, analyses), 1):
            print(f"{i}. {self.format_route_summary(route)}")
            print(f"   {self.format_route_analysis(analysis)}")
            
            # Show trade-offs
            if hasattr(analysis, 'tradeoff_summary'):
                tradeoff = analysis.tradeoff_summary
                if tradeoff.strengths:
                    print(f"   ✅ Strengths: {', '.join(tradeoff.strengths[:2])}")
                if tradeoff.weaknesses:
                    print(f"   ⚠️  Weaknesses: {', '.join(tradeoff.weaknesses[:2])}")
                if tradeoff.when_not_to_choose:
                    print(f"   ❌ When NOT to choose: {tradeoff.when_not_to_choose[0]}")
            
            print()
        
        # Display comparison summary
        comparisons = result.get('comparisons', {})
        if comparisons and 'summary' in comparisons:
            print("⚖️  TRADE-OFF SUMMARY")
            print("-" * 30)
            print(comparisons['summary'])
    
    def format_route_summary(self, route) -> str:
        """Format a route into a concise summary."""
        modes = ', '.join(set(mode.value.replace('_', ' ').title() for mode in route.transportation_modes))
        return (f"{modes} • {route.estimated_time} min • "
                f"${route.estimated_cost:.2f} • Stress: {route.stress_level}/10 • "
                f"Reliability: {route.reliability_score}/10")
    
    def format_route_analysis(self, analysis) -> str:
        """Format route analysis into a readable string."""
        time_range = f"{analysis.time_analysis.time_range_min}-{analysis.time_analysis.time_range_max} min"
        cost_breakdown = f"${analysis.cost_analysis.total_cost:.2f}"
        
        return f"Time range: {time_range} • Cost: {cost_breakdown}"


def main():
    """Main entry point for the CLI."""
    cli = CommuteCLI()
    return cli.run()


if __name__ == '__main__':
    exit(main())