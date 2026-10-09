"""Rolling time-series store for live sensor readings, used by the charts."""

import logging
import sqlite3
import threading
import time
from contextlib import contextmanager

from config import Config

logger = logging.getLogger(__name__)

PRUNE_INTERVAL_SECONDS = 60
MAX_POINTS = 600

_write_lock = threading.Lock()
_schema_ready = False
_last_prune = 0.0


def _ensure_schema():
    global _schema_ready
    if _schema_ready:
        return
    Config.SENSOR_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(Config.SENSOR_HISTORY_PATH, timeout=5)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sensor_samples (
                sensor_id TEXT NOT NULL,
                ts REAL NOT NULL,
                value REAL NOT NULL,
                PRIMARY KEY (sensor_id, ts)
            ) WITHOUT ROWID
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_samples_ts ON sensor_samples(ts)")
        conn.commit()
    finally:
        conn.close()
    _schema_ready = True


@contextmanager
def _db():
    _ensure_schema()
    conn = sqlite3.connect(Config.SENSOR_HISTORY_PATH, timeout=5)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def sensor_id(hardware: str, key: str) -> str:
    return f"{hardware} / {key}"


def record_samples(sensors: dict) -> int:
    """Store one sample per numeric sensor, all sharing the same timestamp."""
    global _last_prune
    ts = time.time()

    rows = []
    for hardware, group in (sensors or {}).items():
        if not isinstance(group, dict):
            continue
        for key, reading in group.items():
            value = reading.get("current") if isinstance(reading, dict) else reading
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                rows.append((sensor_id(hardware, key), ts, float(value)))

    if not rows:
        return 0

    with _write_lock:
        with _db() as conn:
            conn.executemany("INSERT OR REPLACE INTO sensor_samples (sensor_id, ts, value) VALUES (?, ?, ?)", rows)
            if ts - _last_prune > PRUNE_INTERVAL_SECONDS:
                conn.execute("DELETE FROM sensor_samples WHERE ts < ?", (ts - Config.SENSOR_RETENTION_SECONDS,))
                _last_prune = ts

    return len(rows)


def query_series(window_seconds: int, sensor_ids: list) -> dict:
    """Return time-bucketed averages for the requested sensors over the last window."""
    now = time.time()
    since = now - window_seconds
    bucket = max(1.0, window_seconds / MAX_POINTS)
    placeholders = ",".join("?" for _ in sensor_ids)

    sql = f"""
        SELECT sensor_id, AVG(ts), AVG(value)
        FROM sensor_samples
        WHERE ts >= ? AND sensor_id IN ({placeholders})
        GROUP BY sensor_id, CAST((ts - ?) / ? AS INTEGER)
        ORDER BY sensor_id, AVG(ts)
    """

    series = {sid: {"t": [], "v": []} for sid in sensor_ids}
    with _db() as conn:
        for sid, ts, value in conn.execute(sql, [since, *sensor_ids, since, bucket]):
            series[sid]["t"].append(round(ts, 3))
            series[sid]["v"].append(round(value, 3))

    return {"from": since, "to": now, "bucket_seconds": bucket, "series": series}
