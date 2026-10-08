import { SensorsService } from "../services/sensorsService.js";

// Global state for sensors view
let sensorViewState = {
  rendered: false,
  selectedSensorGroup: null,
  selectedSensor: null,
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
}

function _renderScaffold(agent) {
  const $section = $('[data-view="sensors"]');

  $section.html(`
    <div class="pane-header">
      <h2>Sensors</h2>
      <span>Real-time sensor data</span>
    </div>

    <article class="panel">
      <div id="sensor-groups-table"></div>
    </article>
  `);
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
