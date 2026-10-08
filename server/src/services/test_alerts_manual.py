#!/usr/bin/env python3
"""Manual alert generation for testing - create artificial alerts without hardware."""

import sys
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from health_prediction_service import AlertService
from sqlite_storage import get_storage
from config import Config


def create_test_alerts(severity="warning", components=None):
    """Create artificial test alerts.

    Args:
        severity: "warning" or "critical"
        components: list of ["cpu", "disk", "motherboard"] or None for all
    """
    if components is None:
        components = ["cpu", "disk", "motherboard"]

    # Create dummy sensor data with high temps to trigger alerts
    dummy_sensors = {}

    if "cpu" in components:
        if severity == "critical":
            temp = 96.0  # Critical threshold is 95
        else:
            temp = 87.0  # Warning threshold is 85

        dummy_sensors["Intel Core i7-10700K"] = {
            f"Temperature: CPU Core #0": {"current": temp, "min": 30.0, "max": 100.0},
            f"Temperature: CPU Core #1": {"current": temp - 1, "min": 30.0, "max": 100.0},
        }

    if "disk" in components:
        if severity == "critical":
            temp = 58.0  # Critical threshold is 55
        else:
            temp = 48.0  # Warning threshold is 45

        dummy_sensors["Samsung SSD 970 EVO"] = {
            f"Temperature: SSD": {"current": temp, "min": 20.0, "max": 60.0},
        }

    if "motherboard" in components:
        if severity == "critical":
            temp = 92.0  # Critical threshold is 90
        else:
            temp = 82.0  # Warning threshold is 80

        dummy_sensors["ASUS ROG Strix Z390"] = {
            f"Temperature: Chipset": {"current": temp, "min": 25.0, "max": 95.0},
        }

    print("\n" + "="*60)
    print(f"🧪 Creating {severity.upper()} test alerts...")
    print("="*60)

    # Generate alerts from dummy sensor data
    alerts = AlertService.get_alerts(dummy_sensors)

    print(f"\n✓ Alerts generated:")
    print(f"  - Total alerts: {alerts['total_alerts']}")
    print(f"  - Critical alerts: {alerts['critical_count']}")
    print(f"  - Timestamp: {alerts['timestamp']}\n")

    # Display alert details
    for component_name, component_data in alerts.get("components", {}).items():
        print(f"\n📊 {component_name}:")
        for alert in component_data.get("alerts", []):
            level_icon = "🔴" if alert["level"] == "critical" else "🟡"
            print(f"  {level_icon} [{alert['level'].upper()}] {alert['message']}")
            print(f"     Sensor: {alert['sensor']}")

    # Store in database
    print("\n" + "-"*60)
    print("💾 Storing alerts in database...")

    try:
        db_path = Path(Config.BASE_PATH) / "data" / "sensors.db"
        storage = get_storage(str(db_path))
        count = storage.store_alerts_batch("localhost", alerts)
        print(f"✓ Stored {count} alerts in {db_path}")
    except Exception as e:
        print(f"✗ Failed to store alerts: {e}")
        return False

    print("\n" + "="*60)
    print("✅ Test alerts created successfully!")
    print("="*60)
    print("\n💡 Check the Health tab in browser - refresh page if needed")
    print("   Alerts should appear with timestamps\n")

    return True


def show_usage():
    """Show usage instructions."""
    print("\n" + "="*60)
    print("📋 Manual Alert Generator")
    print("="*60)
    print("\nUsage: python services/test_alerts_manual.py [OPTIONS]\n")
    print("Options:")
    print("  python services/test_alerts_manual.py")
    print("    → Create WARNING level alerts for all components (CPU, Disk, Motherboard)\n")
    print("  python services/test_alerts_manual.py critical")
    print("    → Create CRITICAL level alerts for all components\n")
    print("  python services/test_alerts_manual.py warning cpu disk")
    print("    → Create WARNING level alerts for CPU and Disk only\n")
    print("  python services/test_alerts_manual.py critical motherboard")
    print("    → Create CRITICAL level alert for Motherboard only\n")
    print("Examples:")
    print("  cd server/src")
    print("  python services/test_alerts_manual.py")
    print("  python services/test_alerts_manual.py critical")
    print("  python services/test_alerts_manual.py warning cpu motherboard\n")
    print("="*60 + "\n")


def main():
    """Main entry point."""
    show_usage()

    # Parse arguments
    severity = "warning"  # default
    components = None  # default: all

    if len(sys.argv) > 1:
        severity = sys.argv[1].lower()

        if severity not in ["warning", "critical"]:
            print(f"✗ Invalid severity: {severity}")
            print("  Valid options: warning, critical\n")
            return False

        # Remaining args are component filters
        if len(sys.argv) > 2:
            components = [c.lower() for c in sys.argv[2:]]
            valid_components = ["cpu", "disk", "motherboard"]

            for comp in components:
                if comp not in valid_components:
                    print(f"✗ Invalid component: {comp}")
                    print(f"  Valid options: {', '.join(valid_components)}\n")
                    return False

    return create_test_alerts(severity=severity, components=components)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
