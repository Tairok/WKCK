import { SensorsService } from "../services/sensorsService.js";
import { SensorChart } from "./sensorChart.js";

// Global state for sensors view
let sensorViewState = {
  rendered: false,
  timeRange: 1, // hours
  selectedSensorGroup: null,
  selectedSensor: null,
  charts: {}, // {groupName: {sensorName: chart instance}}
};

export function renderSensors(agent) {
  const $section = $('[data-view="sensors"]');
  if ($section.length === 0) return;

  if (!agent) {
    $section.html(`
      <div class="pane-header">
        <h2>Sensors</h2>
        <span>Real-time sensor data</span>
      </div>
      <article class="panel">
        <p class="empty-state">No agent connected</p>
      </article>
    `);
    sensorViewState.rendered = false;
    return;
  }

  // Render once, then update data
  if (!sensorViewState.rendered) {
    _renderScaffold(agent);
    sensorViewState.rendered = true;
  }

  // Update values from current agent data
  _updateSensorValues(agent);

  // Load time-series data for charts
  _loadAndRenderCharts(agent);
}

function _renderScaffold(agent) {
  const $section = $('[data-view="sensors"]');

  $section.html(`
    <div class="pane-header">
      <h2>Sensors</h2>
      <span>Real-time sensor data with historical trends</span>
    </div>

    <div class="sensor-controls">
      <div class="time-range-selector">
        <label>Time Range:</label>
        <button class="range-btn active" data-hours="1">1 h</button>
        <button class="range-btn" data-hours="6">6 h</button>
        <button class="range-btn" data-hours="24">24 h</button>
      </div>
    </div>

    <article class="panel">
      <div id="sensor-groups-table"></div>
    </article>

    <article class="panel">
      <div id="sensor-charts"></div>
    </article>
  `);

  // Attach event listeners for time range buttons
  $(".range-btn").on("click", function () {
    $(".range-btn").removeClass("active");
    $(this).addClass("active");
    sensorViewState.timeRange = parseInt($(this).data("hours"));

    // Reload charts
    const agent = window.state?.getAgent?.();
    if (agent) {
      _loadAndRenderCharts(agent);
    }
  });
}

function _updateSensorValues(agent) {
  const sensors = agent?.sensors || {};
  const keys = Object.keys(sensors || {});

  if (!keys.length) {
    $("#sensor-groups-table").html(
      '<p class="empty-state">No sensor data</p>'
    );
    return;
  }

  const html = keys
    .map((groupName) => _renderSensorGroup(groupName, sensors[groupName]))
    .join("");

  $("#sensor-groups-table").html(html);
}

function _renderSensorGroup(groupName, groupValue) {
  const parsed = _parseSensorGroup(groupValue);
  const title = _capitalize(groupName);

  if (!parsed.length) {
    return `
      <section class="sensor-group">
        <h4>${_escapeHtml(title)}</h4>
        <p class="empty-state">No values</p>
      </section>
    `;
  }

  const rows = parsed
    .map((item) => {
      const formatted = _formatSensorValue(groupName, item.current);
      const min = item.min ? _formatSensorValue(groupName, item.min) : "n/a";
      const max = item.max ? _formatSensorValue(groupName, item.max) : "n/a";

      return `
        <tr>
          <td class="sensor-name">${_escapeHtml(item.label)}</td>
          <td class="sensor-value">${_escapeHtml(formatted)}</td>
          <td class="sensor-stat" style="font-size: 0.9em; color: #98a6b3;">min: ${min}</td>
          <td class="sensor-stat" style="font-size: 0.9em; color: #98a6b3;">max: ${max}</td>
        </tr>
      `;
    })
    .join("");

  return `
    <section class="sensor-group">
      <h4>${_escapeHtml(title)}</h4>
      <table class="sensor-table">
        <thead>
          <tr>
            <th>Sensor</th>
            <th>Current</th>
            <th colspan="2">Range</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </section>
  `;
}

async function _loadAndRenderCharts(agent) {
  const agentId = agent.id || agent.agent_id;
  if (!agentId) return;

  // Get list of available sensors
  const sensors = await SensorsService.fetchSensorList(agentId, 24);

  if (!sensors || sensors.length === 0) {
    $("#sensor-charts").html(
      '<p class="empty-state">No historical data yet. Waiting for sensor readings...</p>'
    );
    return;
  }

  // Group sensors by group name
  const grouped = {};
  sensors.forEach((s) => {
    if (!grouped[s.group]) {
      grouped[s.group] = [];
    }
    grouped[s.group].push(s);
  });

  // Render charts for each group
  let chartsHtml = "";
  const groupNames = Object.keys(grouped).sort();

  for (const groupName of groupNames) {
    const groupSensors = grouped[groupName];
    chartsHtml += `
      <div style="margin-bottom: 30px;">
        <h4 style="margin-bottom: 15px;">${_capitalize(groupName)}</h4>
        <div id="chart-${groupName}" style="background: #171d24; border-radius: 4px; padding: 10px;"></div>
      </div>
    `;
  }

  $("#sensor-charts").html(chartsHtml);

  // Render each chart
  for (const groupName of groupNames) {
    const groupSensors = grouped[groupName];
    const containerId = `chart-${groupName}`;

    try {
      // Fetch series data for all sensors in group
      const allSeries = await Promise.all(
        groupSensors.map((s) =>
          SensorsService.fetchSeries(
            agentId,
            groupName,
            s.name,
            sensorViewState.timeRange,
            200
          )
        )
      );

      // Merge all series (for visualization, we'll show average across all sensors)
      // For now, render the first sensor as main chart
      if (allSeries[0] && allSeries[0].length > 0) {
        const chart = new SensorChart(containerId, {
          width: 700,
          height: 250,
          margin: { top: 20, right: 30, bottom: 40, left: 60 },
        });
        chart.render(allSeries[0]);

        // Store chart instance for potential later use
        if (!sensorViewState.charts[groupName]) {
          sensorViewState.charts[groupName] = {};
        }
        sensorViewState.charts[groupName][groupSensors[0].name] = chart;
      }
    } catch (err) {
      console.error(`[Sensors] Failed to render chart for ${groupName}:`, err);
    }
  }
}

function _parseSensorGroup(groupValue) {
  if (!groupValue || typeof groupValue !== "object") return [];

  return Object.entries(groupValue).map(([rawName, payload]) => {
    const normalizedName = _normalizeSensorName(rawName);
    const first = Array.isArray(payload) ? payload[0] : payload;
    const current = first && typeof first === "object" ? first.current : first;
    const min = first && typeof first === "object" ? first.min : undefined;
    const max = first && typeof first === "object" ? first.max : undefined;

    return {
      label: normalizedName,
      current,
      min,
      max,
    };
  });
}

function _normalizeSensorName(rawName) {
  if (!rawName) return "Unknown";

  const compact = String(rawName)
    .replace(/\s*\/\s*/g, "/")
    .replace(/\s+/g, " ")
    .trim();

  const tail = compact.split("/").pop() || compact;
  return tail.trim();
}

function _formatSensorValue(groupName, value) {
  return SensorsService.formatValue(value, groupName);
}

function _capitalize(value) {
  if (!value) return "Unknown";
  return String(value).charAt(0).toUpperCase() + String(value).slice(1);
}

function _escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
