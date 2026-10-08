/**
 * Sensor data service — fetch time-series and metadata from TimescaleDB
 */

import { API } from "../api.js";

export class SensorsService {
  /**
   * Get list of available sensors (live from hardware)
   */
  static async fetchSensorList(agentId, hours = 24) {
    try {
      const response = await API.api("/api/sensors/latest");
      if (response?.sensors) {
        const sensors = [];
        Object.entries(response.sensors).forEach(([group, groupSensors]) => {
          Object.entries(groupSensors).forEach(([sensorName, sensorData]) => {
            sensors.push({
              group,
              name: sensorName,
              value: sensorData.current,
              min: sensorData.min,
              max: sensorData.max
            });
          });
        });
        return sensors;
      }
      return [];
    } catch (err) {
      console.error(`[SensorsService] fetchSensorList failed:`, err);
      return [];
    }
  }

  /**
   * Get time-series data for a specific sensor (live value)
   */
  static async fetchSeries(agentId, group, sensor, hours = 1, maxPoints = 300) {
    try {
      const response = await API.api("/api/sensors/latest");
      if (response?.sensors?.[group]?.[sensor]) {
        const sensorData = response.sensors[group][sensor];
        return [{
          timestamp: new Date().toISOString(),
          value: sensorData.current || 0
        }];
      }
      return [];
    } catch (err) {
      console.error(`[SensorsService] fetchSeries failed:`, err);
      return [];
    }
  }

  /**
   * Get statistics for a sensor (current value stats)
   */
  static async fetchStats(agentId, group, sensor, hours = 24) {
    try {
      const response = await API.api("/api/sensors/latest");
      if (response?.sensors?.[group]?.[sensor]) {
        const sensorData = response.sensors[group][sensor];
        return {
          current: sensorData.current,
          min: sensorData.min,
          max: sensorData.max
        };
      }
      return {};
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
