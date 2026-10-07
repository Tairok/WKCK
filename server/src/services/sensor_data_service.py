"""Service for collecting and storing sensor data with TimescaleDB"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


def flatten_sensors_for_timescaledb(sensors: Dict[str, Any], timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
    """Convert sensor data to TimescaleDB format.

    Handles various sensor payload formats:
    - {"group": {"sensor": {"current": 42, "min": 40, "max": 45}}}
    - {"group": {"sensor": [{"current": 42}]}}
    - {"group": {"sensor": 42}}

    Args:
        sensors: Sensor data dict from agent
        timestamp: Optional timestamp (defaults to now)

    Returns:
        List of reading dicts for TimescaleDB
    """
    if not sensors:
        return []

    if not timestamp:
        timestamp = datetime.now().isoformat()

    readings = []

    for group_name, group_data in sensors.items():
        if not isinstance(group_data, dict):
            continue

        for sensor_name, sensor_data in group_data.items():
            try:
                # Extract from various formats
                if isinstance(sensor_data, (int, float)):
                    # Simple value: {"sensor": 42}
                    value = float(sensor_data)
                    readings.append({
                        "timestamp": timestamp,
                        "sensor_group": group_name,
                        "sensor_name": sensor_name,
                        "value": value,
                        "label": sensor_name,
                        "min": None,
                        "max": None
                    })
                elif isinstance(sensor_data, list) and len(sensor_data) > 0:
                    # List format: {"sensor": [{"current": 42}]}
                    item = sensor_data[0]
                    if isinstance(item, dict):
                        current = item.get("current")
                        if current is not None:
                            readings.append({
                                "timestamp": timestamp,
                                "sensor_group": group_name,
                                "sensor_name": sensor_name,
                                "value": float(current),
                                "label": item.get("label", sensor_name),
                                "min": item.get("min"),
                                "max": item.get("max")
                            })
                elif isinstance(sensor_data, dict):
                    # Dict format: {"sensor": {"current": 42, "min": 40, "max": 45}}
                    current = sensor_data.get("current")
                    if current is not None:
                        readings.append({
                            "timestamp": timestamp,
                            "sensor_group": group_name,
                            "sensor_name": sensor_name,
                            "value": float(current),
                            "label": sensor_data.get("label", sensor_name),
                            "min": sensor_data.get("min"),
                            "max": sensor_data.get("max")
                        })
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"[SENSOR_FLATTEN] Skipped {group_name}.{sensor_name}: {e}")
                continue

    return readings


class SensorDataCollector:
    """Collect and store sensor data from agents.
    
    Data is stored in-memory and can be optionally persisted to database/file.
    Provides historical data for trend analysis and AI training.
    """
    
    def __init__(self, max_history: int = 1000):
        """Initialize sensor data collector.
        
        Args:
            max_history: Maximum number of readings to keep per sensor
        """
        self.max_history = max_history
        # Structure: {agent_id: {sensor_group: {sensor_name: [readings]}}}
        self.history = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.last_update = {}
        logger.info(f"[SENSOR_DATA] Initialized with max_history={max_history}")
    
    def collect(self, agent_id: str, sensors: Dict[str, Any], timestamp: Optional[str] = None) -> Dict:
        """Collect sensor data from an agent.
        
        Args:
            agent_id: Agent identifier
            sensors: Sensor data dict (e.g., {'temperatures': {...}, 'fans': {...}})
            timestamp: Optional timestamp, uses current time if not provided
            
        Returns:
            Dict with collected data summary
        """
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        if not sensors:
            return {"collected": 0, "timestamp": timestamp}
        
        collected_count = 0
        
        # Process each sensor group
        for group_name, group_data in sensors.items():
            if not isinstance(group_data, dict):
                continue
            
            # Process each sensor in group
            for sensor_name, sensor_data in group_data.items():
                if not isinstance(sensor_data, dict):
                    continue
                
                current_value = sensor_data.get("current")
                if current_value is None:
                    continue
                
                try:
                    # Store reading
                    reading = {
                        "timestamp": timestamp,
                        "value": float(current_value),
                        "label": sensor_data.get("label", sensor_name),
                        "min": sensor_data.get("min"),
                        "max": sensor_data.get("max"),
                    }
                    
                    # Add to history
                    sensor_history = self.history[agent_id][group_name][sensor_name]
                    sensor_history.append(reading)
                    
                    # Keep only max_history readings
                    if len(sensor_history) > self.max_history:
                        sensor_history.pop(0)
                    
                    collected_count += 1
                    
                except (ValueError, TypeError):
                    continue
        
        self.last_update[agent_id] = timestamp
        
        logger.debug(f"[SENSOR_DATA] Collected {collected_count} readings from {agent_id}")
        
        return {
            "agent_id": agent_id,
            "collected": collected_count,
            "timestamp": timestamp
        }
    
    def get_history(self, agent_id: str, group_name: Optional[str] = None, 
                   sensor_name: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Get historical sensor data.
        
        Args:
            agent_id: Agent identifier
            group_name: Optional specific sensor group (e.g., 'temperatures')
            sensor_name: Optional specific sensor name
            limit: Limit number of returned readings
            
        Returns:
            List of readings
        """
        if agent_id not in self.history:
            return []
        
        agent_history = self.history[agent_id]
        
        if group_name is None:
            # Return all data for agent
            results = []
            for group, group_data in agent_history.items():
                for sensor, readings in group_data.items():
                    results.extend(readings)
            results.sort(key=lambda x: x["timestamp"])
        elif sensor_name is None:
            # Return all data for group
            if group_name not in agent_history:
                return []
            results = []
            for sensor, readings in agent_history[group_name].items():
                results.extend(readings)
            results.sort(key=lambda x: x["timestamp"])
        else:
            # Return specific sensor data
            if group_name not in agent_history:
                return []
            if sensor_name not in agent_history[group_name]:
                return []
            results = agent_history[group_name][sensor_name]
        
        # Apply limit from end
        if limit and len(results) > limit:
            results = results[-limit:]
        
        return results
    
    def get_latest(self, agent_id: str) -> Dict:
        """Get latest reading for all sensors of an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dict with latest readings per sensor
        """
        if agent_id not in self.history:
            return {}
        
        latest = {}
        agent_history = self.history[agent_id]
        
        for group_name, group_data in agent_history.items():
            latest[group_name] = {}
            for sensor_name, readings in group_data.items():
                if readings:
                    latest[group_name][sensor_name] = readings[-1]
        
        return latest
    
    def get_stats(self, agent_id: str, group_name: str, sensor_name: str) -> Dict:
        """Get statistics for a specific sensor.
        
        Args:
            agent_id: Agent identifier
            group_name: Sensor group name
            sensor_name: Sensor name
            
        Returns:
            Dict with min, max, avg, count
        """
        readings = self.get_history(agent_id, group_name, sensor_name)
        
        if not readings:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
                "latest": None
            }
        
        values = [r["value"] for r in readings if isinstance(r.get("value"), (int, float))]
        
        if not values:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
                "latest": None
            }
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "label": readings[-1].get("label"),
            "timestamp": readings[-1].get("timestamp")
        }
    
    def export_to_json(self, agent_id: str, filepath: str) -> bool:
        """Export agent's sensor history to JSON file.
        
        Args:
            agent_id: Agent identifier
            filepath: Path to save JSON file
            
        Returns:
            True if successful
        """
        try:
            history = self.get_history(agent_id)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "agent_id": agent_id,
                    "exported": datetime.now().isoformat(),
                    "readings": history
                }, f, indent=2, default=str)
            
            logger.info(f"[SENSOR_DATA] Exported {len(history)} readings for {agent_id} to {filepath}")
            return True
        except Exception as e:
            logger.error(f"[SENSOR_DATA] Failed to export data: {e}")
            return False
    
    def clear_old_data(self, agent_id: Optional[str] = None, days: int = 7) -> int:
        """Remove old sensor data.
        
        Args:
            agent_id: Optional agent to clear; if None, clears all
            days: Keep data from last N days
            
        Returns:
            Number of readings removed
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=days)
        removed = 0
        
        agents = [agent_id] if agent_id else list(self.history.keys())
        
        for aid in agents:
            if aid not in self.history:
                continue
            
            for group_name in self.history[aid]:
                for sensor_name in self.history[aid][group_name]:
                    readings = self.history[aid][group_name][sensor_name]
                    before_count = len(readings)
                    
                    # Keep only recent readings
                    new_readings = []
                    for reading in readings:
                        try:
                            ts = datetime.fromisoformat(reading["timestamp"])
                            if ts >= cutoff_time:
                                new_readings.append(reading)
                        except (ValueError, TypeError):
                            new_readings.append(reading)  # Keep if can't parse
                    
                    self.history[aid][group_name][sensor_name] = new_readings
                    removed += (before_count - len(new_readings))
        
        logger.info(f"[SENSOR_DATA] Cleared {removed} old readings")
        return removed


# Global instance
_collector = None


def get_collector() -> SensorDataCollector:
    """Get or create global sensor data collector."""
    global _collector
    if _collector is None:
        _collector = SensorDataCollector()
    return _collector
