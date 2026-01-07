"""Condition Monitoring Service for detecting significant changes and triggering updates."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum

from commute_optimizer.models import Location
from commute_optimizer.services.data_collection import (
    DataCollectionService, TrafficData, TransitData, WeatherData, ParkingData, DataSource
)


class ConditionType(str, Enum):
    """Types of conditions that can be monitored."""
    TRAFFIC = "traffic"
    TRANSIT = "transit"
    WEATHER = "weather"
    PARKING = "parking"


class ChangeSignificance(str, Enum):
    """Significance levels for condition changes."""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


@dataclass
class ConditionThreshold:
    """Threshold configuration for detecting significant changes."""
    condition_type: ConditionType
    metric: str
    minor_threshold: float
    moderate_threshold: float
    major_threshold: float
    critical_threshold: float
    comparison_type: str = "absolute"  # "absolute", "percentage", "categorical"


@dataclass
class ConditionChange:
    """Represents a detected condition change."""
    condition_type: ConditionType
    metric: str
    old_value: Any
    new_value: Any
    change_magnitude: float
    significance: ChangeSignificance
    timestamp: datetime
    location_key: str
    description: str


@dataclass
class MonitoringTarget:
    """Target location/route to monitor."""
    target_id: str
    origin: Location
    destination: Location
    monitoring_conditions: Set[ConditionType]
    last_checked: Optional[datetime] = None
    baseline_data: Optional[Dict[str, Any]] = None


class ConditionMonitoringService:
    """
    Service for monitoring condition changes and triggering recommendation updates.
    
    This service continuously monitors traffic, transit, weather, and parking conditions
    for specified routes and triggers updates when significant changes are detected.
    
    Validates: Requirements 4.3, 4.5
    """
    
    def __init__(self, data_collection_service: DataCollectionService):
        """Initialize the condition monitoring service."""
        self.data_service = data_collection_service
        self.logger = logging.getLogger(__name__)
        
        # Monitoring state
        self._is_monitoring = False
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._monitoring_targets: Dict[str, MonitoringTarget] = {}
        self._update_callbacks: List[Callable[[List[ConditionChange]], None]] = []
        
        # Default thresholds for detecting significant changes
        self._thresholds = self._initialize_default_thresholds()
        
        # Monitoring intervals (seconds)
        self.monitoring_intervals = {
            ConditionType.TRAFFIC: 180,    # 3 minutes
            ConditionType.TRANSIT: 300,    # 5 minutes
            ConditionType.WEATHER: 900,    # 15 minutes
            ConditionType.PARKING: 600     # 10 minutes
        }
        
        # Change history for trend analysis
        self._change_history: List[ConditionChange] = []
        self._max_history_size = 1000
    
    def _initialize_default_thresholds(self) -> List[ConditionThreshold]:
        """Initialize default thresholds for condition change detection."""
        return [
            # Traffic thresholds
            ConditionThreshold(
                condition_type=ConditionType.TRAFFIC,
                metric="delay_minutes",
                minor_threshold=5.0,
                moderate_threshold=10.0,
                major_threshold=20.0,
                critical_threshold=30.0,
                comparison_type="absolute"
            ),
            ConditionThreshold(
                condition_type=ConditionType.TRAFFIC,
                metric="average_speed_kmh",
                minor_threshold=10.0,
                moderate_threshold=20.0,
                major_threshold=30.0,
                critical_threshold=40.0,
                comparison_type="percentage"
            ),
            ConditionThreshold(
                condition_type=ConditionType.TRAFFIC,
                metric="congestion_level",
                minor_threshold=1.0,
                moderate_threshold=2.0,
                major_threshold=3.0,
                critical_threshold=4.0,
                comparison_type="categorical"
            ),
            
            # Transit thresholds
            ConditionThreshold(
                condition_type=ConditionType.TRANSIT,
                metric="delay_minutes",
                minor_threshold=3.0,
                moderate_threshold=8.0,
                major_threshold=15.0,
                critical_threshold=25.0,
                comparison_type="absolute"
            ),
            ConditionThreshold(
                condition_type=ConditionType.TRANSIT,
                metric="service_status",
                minor_threshold=1.0,
                moderate_threshold=2.0,
                major_threshold=3.0,
                critical_threshold=4.0,
                comparison_type="categorical"
            ),
            
            # Weather thresholds
            ConditionThreshold(
                condition_type=ConditionType.WEATHER,
                metric="visibility_km",
                minor_threshold=2.0,
                moderate_threshold=5.0,
                major_threshold=8.0,
                critical_threshold=10.0,
                comparison_type="absolute"
            ),
            ConditionThreshold(
                condition_type=ConditionType.WEATHER,
                metric="precipitation_probability",
                minor_threshold=20.0,
                moderate_threshold=40.0,
                major_threshold=60.0,
                critical_threshold=80.0,
                comparison_type="absolute"
            ),
            ConditionThreshold(
                condition_type=ConditionType.WEATHER,
                metric="condition",
                minor_threshold=1.0,
                moderate_threshold=2.0,
                major_threshold=3.0,
                critical_threshold=4.0,
                comparison_type="categorical"
            ),
            
            # Parking thresholds
            ConditionThreshold(
                condition_type=ConditionType.PARKING,
                metric="availability",
                minor_threshold=1.0,
                moderate_threshold=2.0,
                major_threshold=3.0,
                critical_threshold=4.0,
                comparison_type="categorical"
            ),
            ConditionThreshold(
                condition_type=ConditionType.PARKING,
                metric="average_cost_per_hour",
                minor_threshold=1.0,
                moderate_threshold=3.0,
                major_threshold=5.0,
                critical_threshold=8.0,
                comparison_type="absolute"
            )
        ]
    
    async def start_monitoring(self) -> None:
        """
        Start condition monitoring for all registered targets.
        
        Validates: Requirements 4.3, 4.5
        """
        if self._is_monitoring:
            self.logger.warning("Condition monitoring already running")
            return
        
        self._is_monitoring = True
        self.logger.info("Starting condition monitoring service")
        
        # Start monitoring tasks for each condition type
        for condition_type in ConditionType:
            task_name = f"monitor_{condition_type.value}"
            self._monitoring_tasks[task_name] = asyncio.create_task(
                self._monitor_condition_type(condition_type)
            )
        
        # Start cleanup task for change history
        self._monitoring_tasks['cleanup'] = asyncio.create_task(self._cleanup_change_history())
    
    async def stop_monitoring(self) -> None:
        """Stop condition monitoring."""
        if not self._is_monitoring:
            return
        
        self._is_monitoring = False
        self.logger.info("Stopping condition monitoring service")
        
        # Cancel all monitoring tasks
        for task_name, task in self._monitoring_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    self.logger.debug(f"Cancelled monitoring task: {task_name}")
        
        self._monitoring_tasks.clear()
    
    def add_monitoring_target(
        self,
        target_id: str,
        origin: Location,
        destination: Location,
        conditions: Optional[Set[ConditionType]] = None
    ) -> None:
        """
        Add a route/location to monitor for condition changes.
        
        Args:
            target_id: Unique identifier for the monitoring target
            origin: Starting location
            destination: Ending location
            conditions: Set of condition types to monitor (all if None)
            
        Validates: Requirements 4.3, 4.5
        """
        if conditions is None:
            conditions = set(ConditionType)
        
        target = MonitoringTarget(
            target_id=target_id,
            origin=origin,
            destination=destination,
            monitoring_conditions=conditions,
            last_checked=None,
            baseline_data=None
        )
        
        self._monitoring_targets[target_id] = target
        self.logger.info(f"Added monitoring target: {target_id} ({len(conditions)} conditions)")
    
    def remove_monitoring_target(self, target_id: str) -> bool:
        """
        Remove a monitoring target.
        
        Args:
            target_id: Target identifier to remove
            
        Returns:
            True if target was removed, False if not found
        """
        if target_id in self._monitoring_targets:
            del self._monitoring_targets[target_id]
            self.logger.info(f"Removed monitoring target: {target_id}")
            return True
        return False
    
    def register_update_callback(self, callback: Callable[[List[ConditionChange]], None]) -> None:
        """
        Register a callback function to be called when significant changes are detected.
        
        Args:
            callback: Function to call with list of condition changes
            
        Validates: Requirements 4.3, 4.5
        """
        self._update_callbacks.append(callback)
        self.logger.info(f"Registered update callback: {callback.__name__}")
    
    def unregister_update_callback(self, callback: Callable[[List[ConditionChange]], None]) -> bool:
        """
        Unregister an update callback.
        
        Args:
            callback: Callback function to remove
            
        Returns:
            True if callback was removed, False if not found
        """
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
            self.logger.info(f"Unregistered update callback: {callback.__name__}")
            return True
        return False
    
    async def check_conditions_now(self, target_id: Optional[str] = None) -> List[ConditionChange]:
        """
        Immediately check conditions for a specific target or all targets.
        
        Args:
            target_id: Specific target to check, or None for all targets
            
        Returns:
            List of detected condition changes
            
        Validates: Requirements 4.3, 4.5
        """
        changes = []
        
        if target_id:
            if target_id in self._monitoring_targets:
                target_changes = await self._check_target_conditions(self._monitoring_targets[target_id])
                changes.extend(target_changes)
            else:
                self.logger.warning(f"Monitoring target not found: {target_id}")
        else:
            # Check all targets
            for target in self._monitoring_targets.values():
                target_changes = await self._check_target_conditions(target)
                changes.extend(target_changes)
        
        if changes:
            await self._notify_callbacks(changes)
        
        return changes
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status and statistics.
        
        Returns:
            Dictionary with monitoring status information
        """
        return {
            'is_monitoring': self._is_monitoring,
            'total_targets': len(self._monitoring_targets),
            'active_tasks': len([t for t in self._monitoring_tasks.values() if not t.done()]),
            'registered_callbacks': len(self._update_callbacks),
            'change_history_size': len(self._change_history),
            'targets': [
                {
                    'target_id': target.target_id,
                    'origin': f"{target.origin.latitude:.3f},{target.origin.longitude:.3f}",
                    'destination': f"{target.destination.latitude:.3f},{target.destination.longitude:.3f}",
                    'monitoring_conditions': [c.value for c in target.monitoring_conditions],
                    'last_checked': target.last_checked.isoformat() if target.last_checked else None,
                    'has_baseline': target.baseline_data is not None
                }
                for target in self._monitoring_targets.values()
            ],
            'recent_changes': [
                {
                    'condition_type': change.condition_type.value,
                    'metric': change.metric,
                    'significance': change.significance.value,
                    'timestamp': change.timestamp.isoformat(),
                    'description': change.description
                }
                for change in self._change_history[-10:]  # Last 10 changes
            ]
        }
    
    def get_change_history(
        self,
        condition_type: Optional[ConditionType] = None,
        significance: Optional[ChangeSignificance] = None,
        hours_back: int = 24
    ) -> List[ConditionChange]:
        """
        Get filtered change history.
        
        Args:
            condition_type: Filter by condition type
            significance: Filter by significance level
            hours_back: How many hours back to include
            
        Returns:
            List of filtered condition changes
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        filtered_changes = []
        for change in self._change_history:
            # Time filter
            if change.timestamp < cutoff_time:
                continue
            
            # Condition type filter
            if condition_type and change.condition_type != condition_type:
                continue
            
            # Significance filter
            if significance and change.significance != significance:
                continue
            
            filtered_changes.append(change)
        
        return filtered_changes
    
    async def _monitor_condition_type(self, condition_type: ConditionType) -> None:
        """
        Monitor a specific condition type for all targets.
        
        Args:
            condition_type: Type of condition to monitor
        """
        interval = self.monitoring_intervals[condition_type]
        
        while self._is_monitoring:
            try:
                # Check conditions for all targets that monitor this condition type
                changes = []
                for target in self._monitoring_targets.values():
                    if condition_type in target.monitoring_conditions:
                        target_changes = await self._check_condition_for_target(target, condition_type)
                        changes.extend(target_changes)
                
                # Notify callbacks if changes detected
                if changes:
                    await self._notify_callbacks(changes)
                
                # Wait for next check
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring {condition_type.value}: {e}")
                await asyncio.sleep(interval * 2)  # Wait longer on error
    
    async def _check_target_conditions(self, target: MonitoringTarget) -> List[ConditionChange]:
        """
        Check all monitored conditions for a specific target.
        
        Args:
            target: Monitoring target to check
            
        Returns:
            List of detected condition changes
        """
        changes = []
        
        for condition_type in target.monitoring_conditions:
            condition_changes = await self._check_condition_for_target(target, condition_type)
            changes.extend(condition_changes)
        
        target.last_checked = datetime.now()
        return changes
    
    async def _check_condition_for_target(
        self,
        target: MonitoringTarget,
        condition_type: ConditionType
    ) -> List[ConditionChange]:
        """
        Check a specific condition type for a target.
        
        Args:
            target: Monitoring target
            condition_type: Condition type to check
            
        Returns:
            List of detected condition changes
        """
        changes = []
        location_key = self._generate_location_key(target.origin, target.destination)
        
        try:
            # Collect current data
            current_data = await self._collect_condition_data(target, condition_type)
            
            # Initialize baseline if not set
            if target.baseline_data is None:
                target.baseline_data = {}
            
            baseline_key = condition_type.value
            if baseline_key not in target.baseline_data:
                target.baseline_data[baseline_key] = current_data
                self.logger.debug(f"Set baseline for {target.target_id} {condition_type.value}")
                return changes  # No comparison possible yet
            
            # Compare with baseline
            baseline_data = target.baseline_data[baseline_key]
            condition_changes = self._detect_changes(
                condition_type, baseline_data, current_data, location_key
            )
            
            changes.extend(condition_changes)
            
            # Update baseline with current data for next comparison
            target.baseline_data[baseline_key] = current_data
            
        except Exception as e:
            self.logger.error(f"Error checking {condition_type.value} for {target.target_id}: {e}")
        
        return changes
    
    async def _collect_condition_data(
        self,
        target: MonitoringTarget,
        condition_type: ConditionType
    ) -> Dict[str, Any]:
        """
        Collect current data for a specific condition type.
        
        Args:
            target: Monitoring target
            condition_type: Condition type to collect data for
            
        Returns:
            Dictionary with current condition data
        """
        if condition_type == ConditionType.TRAFFIC:
            traffic_data = await self.data_service.collect_traffic_data(
                target.origin, target.destination
            )
            return asdict(traffic_data)
        
        elif condition_type == ConditionType.TRANSIT:
            transit_data = await self.data_service.collect_transit_data(
                target.origin, target.destination
            )
            return asdict(transit_data)
        
        elif condition_type == ConditionType.WEATHER:
            weather_data = await self.data_service.collect_weather_data(target.origin)
            return asdict(weather_data)
        
        elif condition_type == ConditionType.PARKING:
            parking_data = await self.data_service.collect_parking_data(target.destination)
            return asdict(parking_data)
        
        else:
            return {}
    
    def _detect_changes(
        self,
        condition_type: ConditionType,
        baseline_data: Dict[str, Any],
        current_data: Dict[str, Any],
        location_key: str
    ) -> List[ConditionChange]:
        """
        Detect significant changes between baseline and current data.
        
        Args:
            condition_type: Type of condition being compared
            baseline_data: Previous/baseline data
            current_data: Current data
            location_key: Location identifier
            
        Returns:
            List of detected condition changes
        """
        changes = []
        
        # Get relevant thresholds for this condition type
        relevant_thresholds = [
            t for t in self._thresholds if t.condition_type == condition_type
        ]
        
        for threshold in relevant_thresholds:
            metric = threshold.metric
            
            if metric not in baseline_data or metric not in current_data:
                continue
            
            old_value = baseline_data[metric]
            new_value = current_data[metric]
            
            # Calculate change magnitude and significance
            change_magnitude, significance = self._calculate_change_significance(
                threshold, old_value, new_value
            )
            
            if significance != ChangeSignificance.MINOR or change_magnitude > 0:
                # Create change record
                change = ConditionChange(
                    condition_type=condition_type,
                    metric=metric,
                    old_value=old_value,
                    new_value=new_value,
                    change_magnitude=change_magnitude,
                    significance=significance,
                    timestamp=datetime.now(),
                    location_key=location_key,
                    description=self._generate_change_description(
                        condition_type, metric, old_value, new_value, significance
                    )
                )
                
                changes.append(change)
                
                # Add to history
                self._change_history.append(change)
                
                self.logger.info(f"Detected {significance.value} change: {change.description}")
        
        return changes
    
    def _calculate_change_significance(
        self,
        threshold: ConditionThreshold,
        old_value: Any,
        new_value: Any
    ) -> tuple[float, ChangeSignificance]:
        """
        Calculate the magnitude and significance of a change.
        
        Args:
            threshold: Threshold configuration
            old_value: Previous value
            new_value: Current value
            
        Returns:
            Tuple of (change_magnitude, significance_level)
        """
        if threshold.comparison_type == "absolute":
            change_magnitude = abs(float(new_value) - float(old_value))
        
        elif threshold.comparison_type == "percentage":
            if float(old_value) == 0:
                change_magnitude = float('inf') if float(new_value) != 0 else 0
            else:
                change_magnitude = abs((float(new_value) - float(old_value)) / float(old_value) * 100)
        
        elif threshold.comparison_type == "categorical":
            # For categorical changes, map categories to numeric values
            category_values = self._get_category_values(threshold.condition_type, threshold.metric)
            old_numeric = category_values.get(str(old_value), 0)
            new_numeric = category_values.get(str(new_value), 0)
            change_magnitude = abs(new_numeric - old_numeric)
        
        else:
            change_magnitude = 0
        
        # Determine significance level
        if change_magnitude >= threshold.critical_threshold:
            significance = ChangeSignificance.CRITICAL
        elif change_magnitude >= threshold.major_threshold:
            significance = ChangeSignificance.MAJOR
        elif change_magnitude >= threshold.moderate_threshold:
            significance = ChangeSignificance.MODERATE
        elif change_magnitude >= threshold.minor_threshold:
            significance = ChangeSignificance.MODERATE  # Still worth noting
        else:
            significance = ChangeSignificance.MINOR
        
        return change_magnitude, significance
    
    def _get_category_values(self, condition_type: ConditionType, metric: str) -> Dict[str, int]:
        """
        Get numeric values for categorical metrics.
        
        Args:
            condition_type: Type of condition
            metric: Metric name
            
        Returns:
            Dictionary mapping category names to numeric values
        """
        if condition_type == ConditionType.TRAFFIC and metric == "congestion_level":
            return {
                "light": 1,
                "moderate": 2,
                "heavy": 3,
                "severe": 4
            }
        
        elif condition_type == ConditionType.TRANSIT and metric == "service_status":
            return {
                "normal": 1,
                "minor_delays": 2,
                "delays": 3,
                "major_delays": 4,
                "disrupted": 5,
                "suspended": 6,
                "cancelled": 7
            }
        
        elif condition_type == ConditionType.WEATHER and metric == "condition":
            return {
                "clear": 1,
                "cloudy": 2,
                "light_rain": 3,
                "rain": 4,
                "heavy_rain": 5,
                "snow": 6,
                "heavy_snow": 7,
                "fog": 8,
                "storm": 9,
                "ice": 10
            }
        
        elif condition_type == ConditionType.PARKING and metric == "availability":
            return {
                "abundant": 1,
                "moderate": 2,
                "limited": 3,
                "scarce": 4
            }
        
        return {}
    
    def _generate_change_description(
        self,
        condition_type: ConditionType,
        metric: str,
        old_value: Any,
        new_value: Any,
        significance: ChangeSignificance
    ) -> str:
        """
        Generate a human-readable description of the change.
        
        Args:
            condition_type: Type of condition
            metric: Metric that changed
            old_value: Previous value
            new_value: Current value
            significance: Significance level
            
        Returns:
            Human-readable change description
        """
        condition_name = condition_type.value.replace('_', ' ').title()
        metric_name = metric.replace('_', ' ').title()
        
        if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            if new_value > old_value:
                direction = "increased"
                change_amount = new_value - old_value
            else:
                direction = "decreased"
                change_amount = old_value - new_value
            
            return f"{condition_name} {metric_name} {direction} from {old_value} to {new_value} (change: {change_amount})"
        else:
            return f"{condition_name} {metric_name} changed from {old_value} to {new_value}"
    
    def _generate_location_key(self, origin: Location, destination: Location) -> str:
        """Generate a location key for origin-destination pair."""
        return f"{origin.latitude:.3f},{origin.longitude:.3f}-{destination.latitude:.3f},{destination.longitude:.3f}"
    
    async def _notify_callbacks(self, changes: List[ConditionChange]) -> None:
        """
        Notify all registered callbacks about condition changes.
        
        Args:
            changes: List of condition changes to report
        """
        if not changes:
            return
        
        for callback in self._update_callbacks:
            try:
                # Call callback (may be sync or async)
                if asyncio.iscoroutinefunction(callback):
                    await callback(changes)
                else:
                    callback(changes)
            except Exception as e:
                self.logger.error(f"Error in update callback {callback.__name__}: {e}")
    
    async def _cleanup_change_history(self) -> None:
        """
        Periodically clean up old change history entries.
        """
        while self._is_monitoring:
            try:
                # Remove old entries if history is too large
                if len(self._change_history) > self._max_history_size:
                    # Keep only the most recent entries
                    self._change_history = self._change_history[-self._max_history_size//2:]
                    self.logger.debug(f"Cleaned up change history, kept {len(self._change_history)} entries")
                
                # Wait 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in change history cleanup: {e}")
                await asyncio.sleep(3600)


class RecommendationUpdateTrigger:
    """
    Trigger for updating recommendations based on condition changes.
    
    This class works with the ConditionMonitoringService to trigger
    recommendation updates when significant changes are detected.
    
    Validates: Requirements 4.3, 4.5
    """
    
    def __init__(self, condition_monitor: ConditionMonitoringService):
        """Initialize the recommendation update trigger."""
        self.condition_monitor = condition_monitor
        self.logger = logging.getLogger(__name__)
        
        # Update triggers configuration
        self.update_triggers = {
            ChangeSignificance.CRITICAL: True,   # Always trigger updates
            ChangeSignificance.MAJOR: True,      # Always trigger updates
            ChangeSignificance.MODERATE: True,   # Trigger updates
            ChangeSignificance.MINOR: False      # Don't trigger updates
        }
        
        # Callbacks for different types of updates
        self._route_update_callbacks: List[Callable[[List[ConditionChange]], None]] = []
        self._recommendation_update_callbacks: List[Callable[[List[ConditionChange]], None]] = []
        
        # Register with condition monitor
        self.condition_monitor.register_update_callback(self._handle_condition_changes)
    
    def register_route_update_callback(
        self,
        callback: Callable[[List[ConditionChange]], None]
    ) -> None:
        """
        Register a callback for route updates.
        
        Args:
            callback: Function to call when routes need updating
        """
        self._route_update_callbacks.append(callback)
        self.logger.info(f"Registered route update callback: {callback.__name__}")
    
    def register_recommendation_update_callback(
        self,
        callback: Callable[[List[ConditionChange]], None]
    ) -> None:
        """
        Register a callback for recommendation updates.
        
        Args:
            callback: Function to call when recommendations need updating
        """
        self._recommendation_update_callbacks.append(callback)
        self.logger.info(f"Registered recommendation update callback: {callback.__name__}")
    
    def set_update_trigger_threshold(
        self,
        significance: ChangeSignificance,
        should_trigger: bool
    ) -> None:
        """
        Configure whether a significance level should trigger updates.
        
        Args:
            significance: Significance level to configure
            should_trigger: Whether this level should trigger updates
        """
        self.update_triggers[significance] = should_trigger
        self.logger.info(f"Set update trigger for {significance.value}: {should_trigger}")
    
    async def _handle_condition_changes(self, changes: List[ConditionChange]) -> None:
        """
        Handle condition changes and trigger appropriate updates.
        
        Args:
            changes: List of detected condition changes
        """
        if not changes:
            return
        
        # Filter changes that should trigger updates
        triggering_changes = [
            change for change in changes
            if self.update_triggers.get(change.significance, False)
        ]
        
        if not triggering_changes:
            self.logger.debug(f"No triggering changes among {len(changes)} detected changes")
            return
        
        self.logger.info(f"Triggering updates for {len(triggering_changes)} significant changes")
        
        # Categorize changes by type
        route_affecting_changes = []
        recommendation_affecting_changes = []
        
        for change in triggering_changes:
            # Changes that affect route generation/analysis
            if change.condition_type in [ConditionType.TRAFFIC, ConditionType.TRANSIT]:
                route_affecting_changes.append(change)
            
            # All significant changes affect recommendations
            recommendation_affecting_changes.append(change)
        
        # Trigger route updates if needed
        if route_affecting_changes:
            await self._trigger_route_updates(route_affecting_changes)
        
        # Trigger recommendation updates
        if recommendation_affecting_changes:
            await self._trigger_recommendation_updates(recommendation_affecting_changes)
    
    async def _trigger_route_updates(self, changes: List[ConditionChange]) -> None:
        """
        Trigger route updates based on condition changes.
        
        Args:
            changes: List of changes that affect routes
        """
        self.logger.info(f"Triggering route updates for {len(changes)} changes")
        
        for callback in self._route_update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(changes)
                else:
                    callback(changes)
            except Exception as e:
                self.logger.error(f"Error in route update callback {callback.__name__}: {e}")
    
    async def _trigger_recommendation_updates(self, changes: List[ConditionChange]) -> None:
        """
        Trigger recommendation updates based on condition changes.
        
        Args:
            changes: List of changes that affect recommendations
        """
        self.logger.info(f"Triggering recommendation updates for {len(changes)} changes")
        
        for callback in self._recommendation_update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(changes)
                else:
                    callback(changes)
            except Exception as e:
                self.logger.error(f"Error in recommendation update callback {callback.__name__}: {e}")
    
    def get_trigger_status(self) -> Dict[str, Any]:
        """
        Get current trigger configuration and status.
        
        Returns:
            Dictionary with trigger status information
        """
        return {
            'update_triggers': {
                significance.value: should_trigger
                for significance, should_trigger in self.update_triggers.items()
            },
            'registered_callbacks': {
                'route_updates': len(self._route_update_callbacks),
                'recommendation_updates': len(self._recommendation_update_callbacks)
            },
            'condition_monitor_status': self.condition_monitor.get_monitoring_status()
        }