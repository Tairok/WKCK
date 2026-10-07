/**
 * Sensor data service — fetch time-series and metadata from TimescaleDB
 */

import { API } from "../api.js";

export class SensorsService {
  /**
   * Get list of available sensors for an agent
   */
  static async fetchSensorList(agentId, hours = 24) {
    try {
      const response = await API.api(
        `/api/agents/${agentId}/sensors/list?hours=${hours}`
      );
      return response.sensors || [];
    } catch (err) {
      console.error(`[SensorsService] fetchSensorList failed:`, err);
      return [];
    }
  }

  /**
   * Get time-series data for a specific sensor (for charting)
   */
  static async fetchSeries(agentId, group, sensor, hours = 1, maxPoints = 300) {
    try {
      const response = await API.api(
        `/api/agents/${agentId}/sensors/series?group=${encodeURIComponent(
          group
        )}&sensor=${encodeURIComponent(sensor)}&hours=${hours}&max_points=${maxPoints}`
      );
      return response.series || [];
    } catch (err) {
      console.error(`[SensorsService] fetchSeries failed:`, err);
      return [];
    }
  }

  /**
   * Get statistics for a sensor in a time window
   */
  static async fetchStats(agentId, group, sensor, hours = 24) {
    try {
      const response = await API.api(
        `/api/agents/${agentId}/sensors/timescale-stats?group=${encodeURIComponent(
          group
        )}&sensor=${encodeURIComponent(sensor)}&hours=${hours}`
      );
      return response.stats || {};
    } catch (err) {
      console.error(`[SensorsService] fetchStats failed:`, err);
      return {};
    }
  }

  /**
   * Format numeric value with appropriate units
   */
  static formatValue(value, group) {
    if (value === null || value === undefined) return "n/a";

    const num = Number(value);
    if (!Number.isFinite(num)) return "n/a";

    if (group === "temperatures") return `${num.toFixed(1)} °C`;
    if (group === "fans") return `${num.toFixed(0)} RPM`;
    if (group === "voltages") return `${num.toFixed(2)} V`;
    if (group === "clocks") return `${num.toFixed(0)} MHz`;
    if (group === "power") return `${num.toFixed(1)} W`;
    if (group === "disk" || group === "memory") return `${num.toFixed(1)} %`;

    return num.toFixed(2);
  }
}
