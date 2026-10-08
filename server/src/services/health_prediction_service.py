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
        "cpu_temp": {
            "warning": 85,      # Celsius
            "critical": 95,     # Celsius
            "component": "CPU"
        },
        "disk_temp": {
            "warning": 45,      # Celsius
            "critical": 55,     # Celsius
            "component": "Disk Temperature"
        },
        "motherboard_temp": {
            "warning": 80,      # Celsius
            "critical": 90,     # Celsius
            "component": "Motherboard"
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
            sensors: Sensor data dict from LHM in format:
                {hardware_name: {sensor_type: sensor_name: {current, min, max}}}

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
            # Parse LHM hardware data for component-specific temps
            AlertService._check_component_temperatures(sensors, alerts)

            # Legacy: Generic temperature alerts (if structured data exists)
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
    def _check_component_temperatures(sensors: Dict, alerts: Dict) -> None:
        """Check LHM component temperatures (CPU, Disk, Motherboard).

        Parses LHM format: {hardware_name: {sensor_type: sensor_name: {current, min, max}}}
        Looks for Temperature sensors in CPU cores, disk drives, and motherboards.
        """
        if not isinstance(sensors, dict):
            return

        cpu_alerts = []
        disk_alerts = []
        mb_alerts = []

        for hardware_name, hardware_sensors in sensors.items():
            if not isinstance(hardware_sensors, dict):
                continue

            # Categorize by hardware name patterns
            hw_name_lower = hardware_name.lower()
            is_cpu = any(x in hw_name_lower for x in ['cpu', 'core', 'processor', 'intel', 'amd', 'ryzen', 'core i'])
            is_disk = any(x in hw_name_lower for x in ['disk', 'drive', 'storage', 'nvme', 'ssd', 'hdd', 'samsung', 'seagate'])
            is_mb = any(x in hw_name_lower for x in ['motherboard', 'system', 'chipset', 'mainboard', 'z390', 'z490', 'b550'])

            for sensor_key, sensor_data in hardware_sensors.items():
                if not isinstance(sensor_data, dict):
                    continue

                # Only process Temperature sensors
                if "Temperature" not in sensor_key:
                    continue

                current = sensor_data.get("current")
                if current is None:
                    continue

                try:
                    value = float(current)
                    label = f"{hardware_name}: {sensor_key}"

                    if is_cpu:
                        AlertService._check_threshold(value, label, "cpu_temp", cpu_alerts, alerts)
                    elif is_disk:
                        AlertService._check_threshold(value, label, "disk_temp", disk_alerts, alerts)
                    elif is_mb:
                        AlertService._check_threshold(value, label, "motherboard_temp", mb_alerts, alerts)

                except (ValueError, TypeError):
                    continue

        if cpu_alerts:
            alerts["components"]["CPU Temperature"] = {
                "alerts": cpu_alerts,
                "count": len(cpu_alerts)
            }
            alerts["total_alerts"] += len(cpu_alerts)

        if disk_alerts:
            alerts["components"]["Disk Temperature"] = {
                "alerts": disk_alerts,
                "count": len(disk_alerts)
            }
            alerts["total_alerts"] += len(disk_alerts)

        if mb_alerts:
            alerts["components"]["Motherboard Temperature"] = {
                "alerts": mb_alerts,
                "count": len(mb_alerts)
            }
            alerts["total_alerts"] += len(mb_alerts)

    @staticmethod
    def _check_threshold(value: float, label: str, threshold_key: str, alerts_list: list, alerts_dict: dict) -> None:
        """Check if value exceeds threshold and add alert if needed."""
        threshold = AlertService.ALERT_THRESHOLDS.get(threshold_key, {})
        critical = threshold.get("critical")
        warning = threshold.get("warning")

        if critical and value >= critical:
            alerts_list.append({
                "level": "critical",
                "message": f"{label}: {value:.1f}°C (Critical)",
                "sensor": label
            })
            alerts_dict["critical_count"] += 1
        elif warning and value >= warning:
            alerts_list.append({
                "level": "warning",
                "message": f"{label}: {value:.1f}°C (High)",
                "sensor": label
            })

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


