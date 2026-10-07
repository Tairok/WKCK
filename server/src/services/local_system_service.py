"""Service for reading local system information and hardware data using psutil."""

import logging
import platform
from typing import Dict, Any, Optional
from datetime import datetime

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)


class LocalSystemService:
    """Collect hardware and system information from local computer using psutil."""

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get basic system information.

        Returns:
            Dict with hostname, OS, platform, architecture, uptime, etc.
        """
        if not psutil:
            return {"error": "psutil not installed"}

        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = (datetime.now() - boot_time).total_seconds()

            return {
                "hostname": platform.node(),
                "os": platform.system(),
                "platform": platform.platform(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "uptime_seconds": int(uptime_seconds),
                "boot_time": boot_time.isoformat(),
                "processor_count": psutil.cpu_count(logical=False),
                "thread_count": psutil.cpu_count(logical=True),
            }
        except Exception as e:
            logger.error(f"[LOCAL_SYSTEM] Failed to get system info: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information.

        Returns:
            Dict with CPU model, cores, frequency, and current usage
        """
        if not psutil:
            return {"error": "psutil not installed"}

        try:
            cpu_freq = psutil.cpu_freq()
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Try to get CPU model from platform
            cpu_model = platform.processor() or "Unknown"

            return {
                "model": cpu_model,
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "frequency_mhz": cpu_freq.current if cpu_freq else None,
                "frequency_max_mhz": cpu_freq.max if cpu_freq else None,
                "frequency_min_mhz": cpu_freq.min if cpu_freq else None,
                "usage_percent": cpu_percent,
            }
        except Exception as e:
            logger.error(f"[LOCAL_SYSTEM] Failed to get CPU info: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get memory (RAM) information.

        Returns:
            Dict with total, used, available, swap memory in bytes and percentages
        """
        if not psutil:
            return {"error": "psutil not installed"}

        try:
            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "ram": {
                    "total_bytes": vm.total,
                    "used_bytes": vm.used,
                    "available_bytes": vm.available,
                    "percent": vm.percent,
                },
                "swap": {
                    "total_bytes": swap.total,
                    "used_bytes": swap.used,
                    "free_bytes": swap.free,
                    "percent": swap.percent,
                }
            }
        except Exception as e:
            logger.error(f"[LOCAL_SYSTEM] Failed to get memory info: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """Get disk/partition information.

        Returns:
            Dict with disk partitions and usage info
        """
        if not psutil:
            return {"error": "psutil not installed"}

        try:
            disks = {}

            for partition in psutil.disk_partitions():
                if partition.fstype == '':  # Skip special partitions
                    continue

                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks[partition.device] = {
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total_bytes": usage.total,
                        "used_bytes": usage.used,
                        "free_bytes": usage.free,
                        "percent": usage.percent,
                    }
                except (PermissionError, OSError):
                    pass  # Skip inaccessible disks

            return disks if disks else {"info": "No disk information available"}
        except Exception as e:
            logger.error(f"[LOCAL_SYSTEM] Failed to get disk info: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """Get network interface information.

        Returns:
            Dict with network interfaces and their stats
        """
        if not psutil:
            return {"error": "psutil not installed"}

        try:
            interfaces = {}

            for name, addrs in psutil.net_if_addrs().items():
                interfaces[name] = {
                    "addresses": []
                }
                for addr in addrs:
                    interfaces[name]["addresses"].append({
                        "family": addr.family.name if hasattr(addr.family, 'name') else str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                    })

            # Add network stats
            net_stats = psutil.net_io_counters()
            interfaces["__stats__"] = {
                "bytes_sent": net_stats.bytes_sent,
                "bytes_recv": net_stats.bytes_recv,
                "packets_sent": net_stats.packets_sent,
                "packets_recv": net_stats.packets_recv,
                "errors_in": net_stats.errin,
                "errors_out": net_stats.errout,
            }

            return interfaces
        except Exception as e:
            logger.error(f"[LOCAL_SYSTEM] Failed to get network info: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_battery_info() -> Optional[Dict[str, Any]]:
        """Get battery information if available.

        Returns:
            Dict with battery status or None if not available
        """
        if not psutil:
            return None

        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": battery.percent,
                    "is_plugged_in": battery.power_plugged,
                    "time_left_seconds": battery.secsleft if hasattr(battery, 'secsleft') else None,
                }
            return None
        except Exception as e:
            logger.debug(f"[LOCAL_SYSTEM] Battery info not available: {e}")
            return None

    @staticmethod
    def get_sensor_data() -> Dict[str, Any]:
        """Get current sensor readings (temperatures, fans, etc.).

        Returns:
            Dict with sensor readings in OpenHardwareMonitor-like format
        """
        if not psutil:
            return {"error": "psutil not installed"}

        sensors = {}

        # CPU temperatures (if available)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, readings in temps.items():
                    group_key = f"Temperatures: {name}"
                    sensors[group_key] = {}
                    for reading in readings:
                        sensor_key = f"Temp: {reading.label}" if reading.label else f"Temp {name}"
                        sensors[group_key][sensor_key] = {
                            "current": reading.current,
                            "min": reading.high if hasattr(reading, 'high') else None,
                            "max": reading.critical if hasattr(reading, 'critical') else None,
                        }
        except Exception as e:
            logger.debug(f"[LOCAL_SYSTEM] Temperature sensors not available: {e}")

        # Fan speeds (if available)
        try:
            fans = psutil.sensors_fans()
            if fans:
                for name, readings in fans.items():
                    group_key = f"Fans: {name}"
                    sensors[group_key] = {}
                    for reading in readings:
                        sensor_key = f"RPM: {reading.label}" if reading.label else f"Fan {name}"
                        sensors[group_key][sensor_key] = {
                            "current": reading.current,
                            "min": None,
                            "max": None,
                        }
        except Exception as e:
            logger.debug(f"[LOCAL_SYSTEM] Fan sensors not available: {e}")

        # Usage-based sensors (CPU, memory, disk)
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            vm = psutil.virtual_memory()

            sensors["System Usage"] = {
                "CPU Usage (%)": {
                    "current": cpu_percent,
                    "min": 0,
                    "max": 100,
                },
                "Memory Usage (%)": {
                    "current": vm.percent,
                    "min": 0,
                    "max": 100,
                }
            }

            # Disk usage for each partition
            disks = {}
            for partition in psutil.disk_partitions():
                if partition.fstype == '':
                    continue
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_name = partition.mountpoint.split('/')[-1] or partition.device.split('/')[-1]
                    disks[f"Disk Usage: {disk_name}"] = {
                        "current": usage.percent,
                        "min": 0,
                        "max": 100,
                    }
                except (PermissionError, OSError):
                    pass

            if disks:
                sensors["Disk Usage"] = disks

        except Exception as e:
            logger.error(f"[LOCAL_SYSTEM] Failed to get usage sensors: {e}")

        return sensors

    @staticmethod
    def get_inventory() -> Dict[str, Any]:
        """Get complete hardware inventory.

        Returns:
            Dict with system, CPU, memory, disk, network and battery info
        """
        inventory = {
            "timestamp": datetime.now().isoformat(),
            "system": LocalSystemService.get_system_info(),
            "cpu": LocalSystemService.get_cpu_info(),
            "memory": LocalSystemService.get_memory_info(),
            "disks": LocalSystemService.get_disk_info(),
            "network": LocalSystemService.get_network_info(),
        }

        battery = LocalSystemService.get_battery_info()
        if battery:
            inventory["battery"] = battery

        return inventory
