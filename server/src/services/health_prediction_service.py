import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service for hardware component alerts based on sensor data.
    
    Provides simple threshold-based alerts for each component.
    Placeholder for future AI-based failure prediction model.
    """
    
    # Alert thresholds for different components
    # These are simple rule-based thresholds
    ALERT_THRESHOLDS = {
        "temperatures": {
            "warning": 80,      # Celsius
            "critical": 95,     # Celsius
            "component": "CPU/Thermal"
        },
        "fans": {
            "warning_low": 1000,    # RPM - too slow
            "critical_low": 500,    # RPM - critical
            "warning_high": 6000,   # RPM - too fast
            "component": "Cooling System"
        },
        "power": {
            "warning_low": 11.5,    # Volts
            "critical_low": 11.0,   # Volts
            "component": "Power Supply"
        },
        "disk": {
            "warning": 80,          # % usage
            "critical": 95,         # % usage
            "component": "Storage"
        },
        "memory": {
            "warning": 80,          # % usage
            "critical": 95,         # % usage
            "component": "RAM"
        }
    }
    
    @staticmethod
    def get_alerts(sensors: Dict) -> Dict:
        """Generate alerts based on sensor data.
        
        Args:
            sensors: Sensor data dict with keys like 'temperatures', 'fans', etc.
            
        Returns:
            Dict with alerts per component
        """
        alerts = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "total_alerts": 0,
            "critical_count": 0
        }
        
        try:
            # Temperature alerts
            alerts = AlertService._check_temperatures(sensors, alerts)
            
            # Fan speed alerts
            alerts = AlertService._check_fans(sensors, alerts)
            
            # Power alerts
            alerts = AlertService._check_power(sensors, alerts)
            
            # Disk usage alerts
            alerts = AlertService._check_disk(sensors, alerts)
            
            # Memory usage alerts
            alerts = AlertService._check_memory(sensors, alerts)
            
        except Exception as e:
            logger.error(f"Error generating alerts: {e}")
        
        return alerts
    
    @staticmethod
    def _check_temperatures(sensors: Dict, alerts: Dict) -> Dict:
        """Check temperature sensors for alerts."""
        temps = sensors.get("temperatures", {})
        if not temps:
            return alerts
        
        component_alerts = []
        for sensor_name, sensor_data in temps.items():
            if not isinstance(sensor_data, dict):
                continue
            
            current = sensor_data.get("current")
            if current is None:
                continue
            
            try:
                value = float(current)
                label = sensor_data.get("label", sensor_name)
                
                if value >= AlertService.ALERT_THRESHOLDS["temperatures"]["critical"]:
                    component_alerts.append({
                        "level": "critical",
                        "message": f"{label}: {value:.1f}°C (Critical)",
                        "sensor": label
                    })
                    alerts["critical_count"] += 1
                elif value >= AlertService.ALERT_THRESHOLDS["temperatures"]["warning"]:
                    component_alerts.append({
                        "level": "warning",
                        "message": f"{label}: {value:.1f}°C (High)",
                        "sensor": label
                    })
            except (ValueError, TypeError):
                continue
        
        if component_alerts:
            alerts["components"]["Thermal"] = {
                "alerts": component_alerts,
                "count": len(component_alerts)
            }
            alerts["total_alerts"] += len(component_alerts)
        
        return alerts
    
    @staticmethod
    def _check_fans(sensors: Dict, alerts: Dict) -> Dict:
        """Check fan speed sensors for alerts."""
        fans = sensors.get("fans", {})
        if not fans:
            return alerts
        
        component_alerts = []
        for sensor_name, sensor_data in fans.items():
            if not isinstance(sensor_data, dict):
                continue
            
            current = sensor_data.get("current")
            if current is None:
                continue
            
            try:
                value = float(current)
                label = sensor_data.get("label", sensor_name)
                
                if value > 0 and value < AlertService.ALERT_THRESHOLDS["fans"]["critical_low"]:
                    component_alerts.append({
                        "level": "critical",
                        "message": f"{label}: {value:.0f} RPM (Critical - Fan Failure)",
                        "sensor": label
                    })
                    alerts["critical_count"] += 1
                elif value > 0 and value < AlertService.ALERT_THRESHOLDS["fans"]["warning_low"]:
                    component_alerts.append({
                        "level": "warning",
                        "message": f"{label}: {value:.0f} RPM (Low Speed)",
                        "sensor": label
                    })
                elif value > AlertService.ALERT_THRESHOLDS["fans"]["warning_high"]:
                    component_alerts.append({
                        "level": "warning",
                        "message": f"{label}: {value:.0f} RPM (High Speed)",
                        "sensor": label
                    })
            except (ValueError, TypeError):
                continue
        
        if component_alerts:
            alerts["components"]["Cooling System"] = {
                "alerts": component_alerts,
                "count": len(component_alerts)
            }
            alerts["total_alerts"] += len(component_alerts)
        
        return alerts
    
    @staticmethod
    def _check_power(sensors: Dict, alerts: Dict) -> Dict:
        """Check power supply voltage for alerts."""
        power = sensors.get("power", {})
        if not power:
            return alerts
        
        component_alerts = []
        for sensor_name, sensor_data in power.items():
            if not isinstance(sensor_data, dict):
                continue
            
            current = sensor_data.get("current")
            if current is None:
                continue
            
            try:
                value = float(current)
                label = sensor_data.get("label", sensor_name)
                
                if value < AlertService.ALERT_THRESHOLDS["power"]["critical_low"]:
                    component_alerts.append({
                        "level": "critical",
                        "message": f"{label}: {value:.2f}V (Critical - Power Loss)",
                        "sensor": label
                    })
                    alerts["critical_count"] += 1
                elif value < AlertService.ALERT_THRESHOLDS["power"]["warning_low"]:
                    component_alerts.append({
                        "level": "warning",
                        "message": f"{label}: {value:.2f}V (Low Voltage)",
                        "sensor": label
                    })
            except (ValueError, TypeError):
                continue
        
        if component_alerts:
            alerts["components"]["Power Supply"] = {
                "alerts": component_alerts,
                "count": len(component_alerts)
            }
            alerts["total_alerts"] += len(component_alerts)
        
        return alerts
    
    @staticmethod
    def _check_disk(sensors: Dict, alerts: Dict) -> Dict:
        """Check disk usage for alerts."""
        disk = sensors.get("disk", {})
        if not disk:
            return alerts
        
        component_alerts = []
        for sensor_name, sensor_data in disk.items():
            if not isinstance(sensor_data, dict):
                continue
            
            current = sensor_data.get("current")
            if current is None:
                continue
            
            try:
                value = float(current)
                label = sensor_data.get("label", sensor_name)
                
                if value >= AlertService.ALERT_THRESHOLDS["disk"]["critical"]:
                    component_alerts.append({
                        "level": "critical",
                        "message": f"{label}: {value:.1f}% Full (Critical)",
                        "sensor": label
                    })
                    alerts["critical_count"] += 1
                elif value >= AlertService.ALERT_THRESHOLDS["disk"]["warning"]:
                    component_alerts.append({
                        "level": "warning",
                        "message": f"{label}: {value:.1f}% Full",
                        "sensor": label
                    })
            except (ValueError, TypeError):
                continue
        
        if component_alerts:
            alerts["components"]["Storage"] = {
                "alerts": component_alerts,
                "count": len(component_alerts)
            }
            alerts["total_alerts"] += len(component_alerts)
        
        return alerts
    
    @staticmethod
    def _check_memory(sensors: Dict, alerts: Dict) -> Dict:
        """Check memory usage for alerts."""
        memory = sensors.get("memory", {})
        if not memory:
            return alerts
        
        component_alerts = []
        for sensor_name, sensor_data in memory.items():
            if not isinstance(sensor_data, dict):
                continue
            
            current = sensor_data.get("current")
            if current is None:
                continue
            
            try:
                value = float(current)
                label = sensor_data.get("label", sensor_name)
                
                if value >= AlertService.ALERT_THRESHOLDS["memory"]["critical"]:
                    component_alerts.append({
                        "level": "critical",
                        "message": f"{label}: {value:.1f}% Used (Critical)",
                        "sensor": label
                    })
                    alerts["critical_count"] += 1
                elif value >= AlertService.ALERT_THRESHOLDS["memory"]["warning"]:
                    component_alerts.append({
                        "level": "warning",
                        "message": f"{label}: {value:.1f}% Used",
                        "sensor": label
                    })
            except (ValueError, TypeError):
                continue
        
        if component_alerts:
            alerts["components"]["RAM"] = {
                "alerts": component_alerts,
                "count": len(component_alerts)
            }
            alerts["total_alerts"] += len(component_alerts)
        
        return alerts


