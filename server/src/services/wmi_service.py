"""Service for reading hardware information from Windows via PowerShell WMI."""

import logging
import platform
import subprocess
import json
import time
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

_wmi_available = platform.system() == "Windows"
_cache = {}
_cache_ttl = 600


def _get_cached(key: str) -> Optional[Any]:
    """Get cached value if not expired."""
    if key in _cache:
        value, timestamp = _cache[key]
        if time.time() - timestamp < _cache_ttl:
            return value
        del _cache[key]
    return None


def _set_cache(key: str, value: Any) -> None:
    """Cache value with timestamp."""
    _cache[key] = (value, time.time())


def _run_powershell_wmi(wmi_class: str) -> list:
    """Run PowerShell Get-CimInstance command and return results as JSON."""
    if not _wmi_available:
        return []

    # Check cache
    cached = _get_cached(f"wmi_{wmi_class}")
    if cached is not None:
        return cached

    try:
        ps_cmd = f"[Console]::OutputEncoding=[Text.Encoding]::UTF8; Get-CimInstance {wmi_class} | ConvertTo-Json -Depth 3"
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            encoding='utf-8',
            errors='replace',
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            # ConvertTo-Json returns single object or array
            result_data = data if isinstance(data, list) else [data]
            _set_cache(f"wmi_{wmi_class}", result_data)
            return result_data
        return []
    except Exception as e:
        logger.debug(f"[WMI] PowerShell error for {wmi_class}: {e}")
        return []


def _parse_bios_date(date_str: str) -> str:
    """Parse WMI date format /Date(ms)/ to YYYY-MM-DD."""
    if not date_str:
        return "Unknown"
    try:
        if isinstance(date_str, str) and date_str.startswith("/Date("):
            ms = int(re.search(r"/Date\((\d+)\)/", date_str).group(1))
            dt = datetime.fromtimestamp(ms / 1000.0)
            return dt.strftime("%Y-%m-%d")
    except:
        pass
    return str(date_str).strip() or "Unknown"


def _memory_type_name(mem_type: Any) -> str:
    """Map memory type code to name."""
    type_map = {
        26: "DDR4",
        34: "DDR5",
        24: "DDR3",
        25: "DDR3L",
        14: "DDR2",
        13: "DDR",
        5: "SDRAM",
    }
    try:
        code = int(mem_type) if mem_type else 0
        return type_map.get(code, f"Type {code}")
    except:
        return str(mem_type) or "Unknown"


def _form_factor_name(ff: Any) -> str:
    """Map form factor code to name."""
    ff_map = {
        8: "DIMM",
        9: "SODIMM",
        10: "RIMM",
        11: "SRIMM",
        12: "FB-DIMM",
    }
    try:
        code = int(ff) if ff else 0
        return ff_map.get(code, f"FF {code}")
    except:
        return str(ff) or "Unknown"


def get_system_product() -> Dict[str, Any]:
    """Get system product info from Win32_ComputerSystemProduct."""
    try:
        results = _run_powershell_wmi("Win32_ComputerSystemProduct")
        if results and len(results) > 0:
            product = results[0]
            return {
                "manufacturer": str(product.get("Vendor", "Unknown")).strip(),
                "model": str(product.get("Name") or product.get("Version", "Unknown")).strip(),
                "serial_number": str(product.get("IdentifyingNumber", "Unknown")).strip(),
                "uuid": str(product.get("UUID", "Unknown")).strip(),
            }
    except Exception as e:
        logger.debug(f"[WMI] Failed to get system product info: {e}")

    return {}


def get_computer_model() -> Optional[str]:
    """Get computer model from Win32_ComputerSystem."""
    try:
        results = _run_powershell_wmi("Win32_ComputerSystem")
        if results and len(results) > 0:
            model = results[0].get("Model") or results[0].get("Manufacturer")
            if model:
                return str(model).strip()
    except Exception as e:
        logger.debug(f"[WMI] Failed to get computer model: {e}")
    return None


def get_bios_info() -> Dict[str, Any]:
    """Get BIOS information from Win32_BIOS."""
    try:
        results = _run_powershell_wmi("Win32_BIOS")
        if results and len(results) > 0:
            bios = results[0]
            return {
                "manufacturer": str(bios.get("Manufacturer", "Unknown")).strip(),
                "version": str(bios.get("Version", "Unknown")).strip(),
                "release_date": _parse_bios_date(bios.get("ReleaseDate")),
                "serial_number": str(bios.get("SerialNumber", "Unknown")).strip(),
            }
    except Exception as e:
        logger.debug(f"[WMI] Failed to get BIOS info: {e}")

    return {}


def get_motherboard_info() -> Dict[str, Any]:
    """Get motherboard information from Win32_BaseBoard."""
    try:
        results = _run_powershell_wmi("Win32_BaseBoard")
        if results and len(results) > 0:
            board = results[0]
            return {
                "manufacturer": str(board.get("Manufacturer", "Unknown")).strip(),
                "product": str(board.get("Product", "Unknown")).strip(),
                "serial_number": str(board.get("SerialNumber", "Unknown")).strip(),
                "version": str(board.get("Version", "Unknown")).strip(),
            }
    except Exception as e:
        logger.debug(f"[WMI] Failed to get motherboard info: {e}")

    return {}


def get_memory_modules_info() -> Dict[str, Any]:
    """Get detailed memory module information from Win32_PhysicalMemory."""
    try:
        results = _run_powershell_wmi("Win32_PhysicalMemory")

        memory_info = {
            "modules": [],
            "total_capacity_gb": 0,
            "total_slots": len(results) if results else 0
        }

        if results:
            for mem in results:
                capacity_bytes = mem.get("Capacity")
                capacity_gb = int(capacity_bytes) // (1024**3) if capacity_bytes else 0
                speed = mem.get("ConfiguredClockSpeed") or mem.get("Speed") or "Unknown"

                memory_info["modules"].append({
                    "manufacturer": str(mem.get("Manufacturer", "Unknown")).strip(),
                    "capacity_gb": capacity_gb,
                    "speed_mhz": speed,
                    "type": _memory_type_name(mem.get("SMBIOSMemoryType")),
                    "form_factor": _form_factor_name(mem.get("FormFactor")),
                    "part_number": str(mem.get("PartNumber", "Unknown")).strip(),
                    "serial_number": str(mem.get("SerialNumber", "Unknown")).strip(),
                    "bank_label": str(mem.get("BankLabel", "Unknown")).strip(),
                    "device_locator": str(mem.get("DeviceLocator", "Unknown")).strip(),
                })

                memory_info["total_capacity_gb"] += capacity_gb

        return memory_info
    except Exception as e:
        logger.debug(f"[WMI] Failed to get memory info: {e}")
        return {}


def get_disk_drives_info() -> Dict[str, Any]:
    """Get disk drive information from Win32_DiskDrive."""
    try:
        results = _run_powershell_wmi("Win32_DiskDrive")

        disk_info = {"drives": []}

        if results:
            for disk in results:
                size_bytes = disk.get("Size")
                size_gb = int(size_bytes) // (1024**3) if size_bytes else 0

                disk_info["drives"].append({
                    "name": str(disk.get("Name", "Unknown")).strip(),
                    "model": str(disk.get("Model", "Unknown")).strip(),
                    "manufacturer": str(disk.get("Manufacturer", "Unknown")).strip(),
                    "size_gb": size_gb,
                    "interface_type": str(disk.get("InterfaceType", "Unknown")).strip(),
                    "serial_number": str(disk.get("SerialNumber", "Unknown")).strip(),
                    "status": str(disk.get("Status", "Unknown")).strip(),
                    "media_type": str(disk.get("MediaType", "Unknown")).strip(),
                    "firmware_revision": str(disk.get("FirmwareRevision", "Unknown")).strip(),
                })

        return disk_info
    except Exception as e:
        logger.debug(f"[WMI] Failed to get disk info: {e}")
        return {}


def get_hardware_info() -> Dict[str, Any]:
    """Get complete hardware information from WMI."""
    return {
        "system": get_system_product(),
        "model": get_computer_model() or "Unknown",
        "bios": get_bios_info(),
        "motherboard": get_motherboard_info(),
        "memory": get_memory_modules_info(),
        "disks": get_disk_drives_info(),
    }
