#!/usr/bin/env python3
"""
Demonstration of the Condition Monitoring Service.

This script shows how to use the ConditionMonitoringService and 
RecommendationUpdateTrigger to monitor route conditions and trigger
updates when significant changes are detected.

Validates: Requirements 4.3, 4.5
"""

import asyncio
import logging
from datetime import datetime, timedelta

from commute_optimizer.models import Location
from commute_optimizer.services.data_collection import DataCollectionService
from commute_optimizer.services.condition_monitoring import (
    ConditionMonitoringService, RecommendationUpdateTrigger,
    ConditionType, ChangeSignificance
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Demonstrate condition monitoring functionality."""
    logger.info("Starting Condition Monitoring Demo")
    
    # Create sample locations
    home = Location(
        latitude=37.7749,
        longitude=-122.4194,
        address="123 Main St, San Francisco, CA",
        name="Home"
    )
    
    work = Location(
        latitude=37.7849,
        longitude=-122.4094,
        address="456 Oak St, San Francisco, CA",
        name="Work"
    )
    
    # Initialize services
    data_service = DataCollectionService()
    condition_monitor = ConditionMonitoringService(data_service)
    update_trigger = RecommendationUpdateTrigger(condition_monitor)
    
    # Track updates
    route_updates = []
    recommendation_updates = []
    
    def route_update_callback(changes):
        """Handle route updates."""
        logger.info(f"Route update triggered by {len(changes)} changes")
        route_updates.extend(changes)
        for change in changes:
            logger.info(f"  - {change.description}")
    
    def recommendation_update_callback(changes):
        """Handle recommendation updates."""
        logger.info(f"Recommendation update triggered by {len(changes)} changes")
        recommendation_updates.extend(changes)
        for change in changes:
            logger.info(f"  - {change.description}")
    
    # Register callbacks
    update_trigger.register_route_update_callback(route_update_callback)
    update_trigger.register_recommendation_update_callback(recommendation_update_callback)
    
    # Add monitoring target
    condition_monitor.add_monitoring_target(
        target_id="home_to_work",
        origin=home,
        destination=work,
        conditions={ConditionType.TRAFFIC, ConditionType.WEATHER, ConditionType.TRANSIT}
    )
    
    logger.info("Added monitoring target: home_to_work")
    
    # Show initial status
    status = condition_monitor.get_monitoring_status()
    logger.info(f"Monitoring status: {status['total_targets']} targets, "
                f"{len(status['targets'][0]['monitoring_conditions'])} conditions")
    
    # First check - establishes baseline
    logger.info("Performing initial condition check (establishes baseline)...")
    changes = await condition_monitor.check_conditions_now("home_to_work")
    logger.info(f"Initial check detected {len(changes)} changes (expected: 0)")
    
    # Wait a moment
    await asyncio.sleep(1)
    
    # Second check - should detect changes due to mock data variation
    logger.info("Performing second condition check...")
    changes = await condition_monitor.check_conditions_now("home_to_work")
    logger.info(f"Second check detected {len(changes)} changes")
    
    if changes:
        logger.info("Detected changes:")
        for change in changes:
            logger.info(f"  - {change.condition_type.value}: {change.description}")
            logger.info(f"    Significance: {change.significance.value}")
    
    # Show change history
    history = condition_monitor.get_change_history()
    logger.info(f"Total changes in history: {len(history)}")
    
    # Show trigger status
    trigger_status = update_trigger.get_trigger_status()
    logger.info(f"Update triggers configured: {trigger_status['update_triggers']}")
    logger.info(f"Callbacks registered: {trigger_status['registered_callbacks']}")
    
    # Demonstrate threshold configuration
    logger.info("Configuring update triggers...")
    update_trigger.set_update_trigger_threshold(ChangeSignificance.MINOR, True)
    logger.info("Enabled updates for minor changes")
    
    # Third check with more sensitive triggers
    logger.info("Performing third condition check with sensitive triggers...")
    changes = await condition_monitor.check_conditions_now("home_to_work")
    logger.info(f"Third check detected {len(changes)} changes")
    
    # Show final statistics
    logger.info(f"Total route updates triggered: {len(route_updates)}")
    logger.info(f"Total recommendation updates triggered: {len(recommendation_updates)}")
    
    # Demonstrate monitoring multiple targets
    logger.info("Adding second monitoring target...")
    
    shopping = Location(
        latitude=37.7649,
        longitude=-122.4294,
        address="789 Pine St, San Francisco, CA",
        name="Shopping Center"
    )
    
    condition_monitor.add_monitoring_target(
        target_id="home_to_shopping",
        origin=home,
        destination=shopping,
        conditions={ConditionType.TRAFFIC, ConditionType.PARKING}
    )
    
    # Check all targets
    logger.info("Checking conditions for all targets...")
    all_changes = await condition_monitor.check_conditions_now()
    logger.info(f"All targets check detected {len(all_changes)} total changes")
    
    # Final status
    final_status = condition_monitor.get_monitoring_status()
    logger.info(f"Final status: {final_status['total_targets']} targets monitored")
    
    logger.info("Condition Monitoring Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())