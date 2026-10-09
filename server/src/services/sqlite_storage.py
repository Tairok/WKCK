"""SQLite storage for health alerts."""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class SQLiteSensorStorage:
    """Store health alerts in SQLite database."""

    def __init__(self, db_path: str = "sensors.db"):
        """Initialize SQLite storage.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        self._init_db()
        logger.info(f"[SQLITE] Initialized at {self.db_path}")

    def _init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    component TEXT NOT NULL,
                    level TEXT NOT NULL,
                    sensor TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_agent_timestamp
                ON alerts(agent_id, timestamp DESC)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_level
                ON alerts(agent_id, level, timestamp DESC)
            """)

            conn.commit()

    def store_alert(self, agent_id: str, component: str, level: str, sensor: str,
                   message: str, timestamp: Optional[str] = None) -> bool:
        """Store a single alert.

        Args:
            agent_id: Agent identifier
            component: Component name (e.g., "CPU Temperature")
            level: Alert level ("warning" or "critical")
            sensor: Sensor identifier
            message: Alert message
            timestamp: ISO timestamp (defaults to now)

        Returns:
            True if successful
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO alerts
                    (agent_id, component, level, sensor, message, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (agent_id, component, level, sensor, message, timestamp))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[SQLITE] Failed to store alert: {e}")
            return False

    def store_alerts_batch(self, agent_id: str, alerts_dict: Dict[str, Any],
                          timestamp: Optional[str] = None) -> int:
        """Store multiple alerts from AlertService output.

        Args:
            agent_id: Agent identifier
            alerts_dict: Dict from AlertService.get_alerts() with 'components' key
            timestamp: ISO timestamp (defaults to now)

        Returns:
            Number of alerts stored
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()

        count = 0
        try:
            components = alerts_dict.get("components", {})

            with sqlite3.connect(self.db_path) as conn:
                for component_name, component_data in components.items():
                    alerts_list = component_data.get("alerts", [])

                    for alert in alerts_list:
                        try:
                            conn.execute("""
                                INSERT INTO alerts
                                (agent_id, component, level, sensor, message, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                agent_id,
                                component_name,
                                alert.get("level", "info"),
                                alert.get("sensor", "unknown"),
                                alert.get("message", ""),
                                timestamp
                            ))
                            count += 1
                        except Exception as e:
                            logger.debug(f"[SQLITE] Failed to store individual alert: {e}")
                            continue

                conn.commit()

            logger.debug(f"[SQLITE] Stored {count} alerts for {agent_id}")
        except Exception as e:
            logger.error(f"[SQLITE] Failed to store alerts batch: {e}")

        return count

    def get_latest_alerts(self, agent_id: str, hours: int = 1) -> Dict[str, Any]:
        """Get latest alerts.

        Args:
            agent_id: Agent identifier
            hours: Look back N hours

        Returns:
            Dict with alert summary and components
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                cursor = conn.execute("""
                    SELECT * FROM alerts
                    WHERE agent_id = ?
                    AND datetime(timestamp) > datetime('now', '-' || ? || ' hours')
                    ORDER BY timestamp DESC
                    LIMIT 100
                """, (agent_id, hours))

                alerts_by_component = {}
                total_alerts = 0
                critical_count = 0

                for row in cursor:
                    component = row["component"]
                    total_alerts += 1
                    if row["level"] == "critical":
                        critical_count += 1

                    if component not in alerts_by_component:
                        alerts_by_component[component] = {
                            "alerts": [],
                            "count": 0
                        }

                    alerts_by_component[component]["alerts"].append({
                        "level": row["level"],
                        "message": row["message"],
                        "sensor": row["sensor"],
                        "timestamp": row["timestamp"]
                    })
                    alerts_by_component[component]["count"] += 1

                return {
                    "components": alerts_by_component,
                    "total_alerts": total_alerts,
                    "critical_count": critical_count,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"[SQLITE] Failed to get latest alerts: {e}")
            return {
                "components": {},
                "total_alerts": 0,
                "critical_count": 0,
                "timestamp": datetime.now().isoformat()
            }

    def get_alert_history(self, agent_id: str, component: Optional[str] = None,
                         level: Optional[str] = None, hours: int = 24,
                         limit: int = 100) -> List[Dict]:
        """Get alert history.

        Args:
            agent_id: Agent identifier
            component: Optional component filter
            level: Optional level filter ("warning", "critical")
            hours: Look back N hours
            limit: Max results

        Returns:
            List of alerts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = """
                    SELECT * FROM alerts
                    WHERE agent_id = ?
                    AND datetime(timestamp) > datetime('now', '-' || ? || ' hours')
                """
                params = [agent_id, hours]

                if component:
                    query += " AND component = ?"
                    params.append(component)

                if level:
                    query += " AND level = ?"
                    params.append(level)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cursor = conn.execute(query, params)

                results = []
                for row in cursor:
                    results.append({
                        "component": row["component"],
                        "level": row["level"],
                        "sensor": row["sensor"],
                        "message": row["message"],
                        "timestamp": row["timestamp"]
                    })

                return results
        except Exception as e:
            logger.error(f"[SQLITE] Failed to get alert history: {e}")
            return []


# Global instance
_storage = None


def get_storage(db_path: str = "sensors.db") -> SQLiteSensorStorage:
    """Get or create global storage instance."""
    global _storage
    if _storage is None:
        _storage = SQLiteSensorStorage(db_path)
    return _storage
