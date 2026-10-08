"""Unit tests for health alerts system."""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.health_prediction_service import AlertService


class TestHealthAlerts(unittest.TestCase):
    """Test suite for AlertService component temperature monitoring."""

    def test_cpu_temperature_warning(self):
        """Test CPU temperature warning alert (85°C threshold)."""
        sensors = {
            "Intel Core i7-10700K": {
                "Temperature: CPU Core #0": {"current": 87.5, "min": 30.0, "max": 100.0},
                "Temperature: CPU Core #1": {"current": 75.0, "min": 30.0, "max": 100.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        self.assertGreater(alerts["total_alerts"], 0)
        self.assertIn("CPU Temperature", alerts["components"])
        cpu_alerts = alerts["components"]["CPU Temperature"]["alerts"]
        self.assertEqual(len(cpu_alerts), 1)
        self.assertEqual(cpu_alerts[0]["level"], "warning")
        self.assertIn("87.5", cpu_alerts[0]["message"])

    def test_cpu_temperature_critical(self):
        """Test CPU temperature critical alert (95°C threshold)."""
        sensors = {
            "AMD Ryzen 9": {
                "Temperature: CPU Core #0": {"current": 96.2, "min": 25.0, "max": 100.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        self.assertEqual(alerts["critical_count"], 1)
        self.assertIn("CPU Temperature", alerts["components"])
        cpu_alerts = alerts["components"]["CPU Temperature"]["alerts"]
        self.assertEqual(cpu_alerts[0]["level"], "critical")

    def test_disk_temperature_warning(self):
        """Test disk temperature warning alert (45°C threshold)."""
        sensors = {
            "Storage - Samsung SSD 860": {
                "Temperature: ST1000DM010": {"current": 47.3, "min": 20.0, "max": 60.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        self.assertGreater(alerts["total_alerts"], 0)
        self.assertIn("Disk Temperature", alerts["components"])
        disk_alerts = alerts["components"]["Disk Temperature"]["alerts"]
        self.assertEqual(len(disk_alerts), 1)
        self.assertEqual(disk_alerts[0]["level"], "warning")

    def test_disk_temperature_critical(self):
        """Test disk temperature critical alert (55°C threshold)."""
        sensors = {
            "HDD Samsung 1TB": {
                "Temperature: HDD1": {"current": 58.0, "min": 20.0, "max": 60.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        self.assertEqual(alerts["critical_count"], 1)
        disk_alerts = alerts["components"]["Disk Temperature"]["alerts"]
        self.assertEqual(disk_alerts[0]["level"], "critical")

    def test_motherboard_temperature_warning(self):
        """Test motherboard temperature warning alert (80°C threshold)."""
        sensors = {
            "Z490 Motherboard": {
                "Temperature: System": {"current": 82.1, "min": 25.0, "max": 95.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        self.assertGreater(alerts["total_alerts"], 0)
        self.assertIn("Motherboard Temperature", alerts["components"])
        mb_alerts = alerts["components"]["Motherboard Temperature"]["alerts"]
        self.assertEqual(mb_alerts[0]["level"], "warning")

    def test_motherboard_temperature_critical(self):
        """Test motherboard temperature critical alert (90°C threshold)."""
        sensors = {
            "B550 Mainboard": {
                "Temperature: Chipset": {"current": 91.5, "min": 25.0, "max": 95.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        self.assertEqual(alerts["critical_count"], 1)
        mb_alerts = alerts["components"]["Motherboard Temperature"]["alerts"]
        self.assertEqual(mb_alerts[0]["level"], "critical")

    def test_multiple_temperature_alerts(self):
        """Test multiple component temperature alerts simultaneously."""
        sensors = {
            "Intel i5": {
                "Temperature: CPU Core #0": {"current": 88.0, "min": 30.0, "max": 100.0},
                "Temperature: CPU Core #1": {"current": 86.5, "min": 30.0, "max": 100.0},
            },
            "Samsung SSD 970 EVO": {
                "Temperature: SSD": {"current": 52.0, "min": 20.0, "max": 60.0},
            },
            "ASUS ROG Strix Z390": {
                "Temperature: Chipset": {"current": 85.0, "min": 25.0, "max": 95.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        self.assertGreaterEqual(alerts["total_alerts"], 3)
        self.assertIn("CPU Temperature", alerts["components"])
        self.assertIn("Disk Temperature", alerts["components"])
        self.assertIn("Motherboard Temperature", alerts["components"])

    def test_no_temperature_alerts_healthy(self):
        """Test no alerts when all temperatures are healthy."""
        sensors = {
            "Intel Core i7": {
                "Temperature: CPU Core #0": {"current": 45.0, "min": 30.0, "max": 100.0},
                "Temperature: CPU Core #1": {"current": 42.5, "min": 30.0, "max": 100.0},
            },
            "Storage": {
                "Temperature: HDD": {"current": 35.0, "min": 20.0, "max": 60.0},
            },
            "Mainboard": {
                "Temperature: System": {"current": 65.0, "min": 25.0, "max": 95.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        self.assertEqual(alerts["total_alerts"], 0)
        self.assertEqual(alerts["critical_count"], 0)
        self.assertEqual(len(alerts["components"]), 0)

    def test_non_temperature_sensors_ignored(self):
        """Test that non-temperature sensors don't trigger temperature alerts."""
        sensors = {
            "CPU": {
                "Fan: CPU Fan": {"current": 2500, "min": 0, "max": 5000},
                "Voltage: CPU Voltage": {"current": 1.35, "min": 1.0, "max": 1.5},
                "Temperature: CPU Core #0": {"current": 87.0, "min": 30.0, "max": 100.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        # Should only have 1 alert for temp, not for fan or voltage
        cpu_alerts = alerts["components"].get("CPU Temperature", {}).get("alerts", [])
        self.assertEqual(len(cpu_alerts), 1)
        self.assertIn("87.0", cpu_alerts[0]["message"])

    def test_invalid_sensor_data_handled(self):
        """Test that invalid sensor data doesn't break alerts."""
        sensors = {
            "CPU": {
                "Temperature: CPU Core #0": {"current": 85.0, "min": 30.0, "max": 100.0},
                "Temperature: CPU Core #1": None,  # Invalid
                "Temperature: CPU Core #2": {"current": "invalid"},  # Invalid type
                "Temperature: CPU Core #3": {},  # Missing current
            }
        }

        alerts = AlertService.get_alerts(sensors)

        # Should only process valid sensor
        cpu_alerts = alerts["components"].get("CPU Temperature", {}).get("alerts", [])
        self.assertEqual(len(cpu_alerts), 1)

    def test_response_structure(self):
        """Test that alert response has correct structure."""
        sensors = {
            "CPU": {
                "Temperature: CPU": {"current": 90.0, "min": 30.0, "max": 100.0},
            }
        }

        alerts = AlertService.get_alerts(sensors)

        # Verify required fields
        self.assertIn("timestamp", alerts)
        self.assertIn("components", alerts)
        self.assertIn("total_alerts", alerts)
        self.assertIn("critical_count", alerts)

        # Verify component structure
        for component_name, component_data in alerts["components"].items():
            self.assertIn("alerts", component_data)
            self.assertIn("count", component_data)
            for alert in component_data["alerts"]:
                self.assertIn("level", alert)
                self.assertIn("message", alert)
                self.assertIn("sensor", alert)


class TestAlertThresholds(unittest.TestCase):
    """Test alert threshold values."""

    def test_cpu_thresholds_defined(self):
        """Verify CPU temperature thresholds are defined."""
        thresholds = AlertService.ALERT_THRESHOLDS["cpu_temp"]
        self.assertIn("warning", thresholds)
        self.assertIn("critical", thresholds)
        self.assertLess(thresholds["warning"], thresholds["critical"])

    def test_disk_thresholds_defined(self):
        """Verify disk temperature thresholds are defined."""
        thresholds = AlertService.ALERT_THRESHOLDS["disk_temp"]
        self.assertIn("warning", thresholds)
        self.assertIn("critical", thresholds)
        self.assertLess(thresholds["warning"], thresholds["critical"])

    def test_motherboard_thresholds_defined(self):
        """Verify motherboard temperature thresholds are defined."""
        thresholds = AlertService.ALERT_THRESHOLDS["motherboard_temp"]
        self.assertIn("warning", thresholds)
        self.assertIn("critical", thresholds)
        self.assertLess(thresholds["warning"], thresholds["critical"])

    def test_threshold_values_reasonable(self):
        """Verify threshold values are within reasonable ranges."""
        cpu = AlertService.ALERT_THRESHOLDS["cpu_temp"]
        disk = AlertService.ALERT_THRESHOLDS["disk_temp"]
        mb = AlertService.ALERT_THRESHOLDS["motherboard_temp"]

        # CPU: 85-95°C
        self.assertGreaterEqual(cpu["warning"], 80)
        self.assertLess(cpu["warning"], 100)
        self.assertGreater(cpu["critical"], cpu["warning"])

        # Disk: 45-55°C
        self.assertGreaterEqual(disk["warning"], 40)
        self.assertLess(disk["warning"], 60)
        self.assertGreater(disk["critical"], disk["warning"])

        # Motherboard: 80-90°C
        self.assertGreaterEqual(mb["warning"], 70)
        self.assertLess(mb["warning"], 100)
        self.assertGreater(mb["critical"], mb["warning"])


if __name__ == "__main__":
    unittest.main()
