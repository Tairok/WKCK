import { API } from "../api.js";

export const renderHealth = async (agent) => {
  const pane = $('[data-view="health"]');
  if (!pane || pane.length === 0) return;

  pane.find('.panel').html('');

  if (!agent) {
    pane.find('.panel').html('<p>No agent selected</p>');
    return;
  }

  try {
    // Get component alerts from API
    const agent_id = agent.id || agent.agent_id;
    const endpoint = agent_id 
      ? `/api/agents/${agent_id}/health/analysis`
      : `/api/health/analysis`;

    const response = await API.api(endpoint);
    
    if (!response) {
      pane.find('.panel').html('<p>Failed to load alerts</p>');
      return;
    }

    const html = buildAlertsHTML(response);
    pane.find('.panel').html(html);

  } catch (err) {
    console.error("Failed to render health:", err);
    pane.find('.panel').html(`<p>Error: ${err.message}</p>`);
  }
};

function buildAlertsHTML(data) {
  const components = data.components || {};
  const totalAlerts = data.total_alerts || 0;
  const criticalCount = data.critical_count || 0;
  
  // Determine status based on alerts
  let statusColor, statusText;
  if (criticalCount > 0) {
    statusColor = "#721c24";
    statusText = "CRITICAL";
  } else if (totalAlerts > 0) {
    statusColor = "#ffc107";
    statusText = "WARNING";
  } else {
    statusColor = "#28a745";
    statusText = "HEALTHY";
  }

  let html = `
    <div class="alerts-container">
      <div class="alerts-header">
        <div class="alerts-status" style="background-color: ${statusColor}">
          <div class="status-text">${statusText}</div>
          <div class="status-count">${totalAlerts} Alert${totalAlerts !== 1 ? 's' : ''}</div>
        </div>
        <div class="alerts-meta">
          <div class="meta-row">
            <span class="meta-label">Total Alerts:</span>
            <span class="meta-value">${totalAlerts}</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">Critical:</span>
            <span class="meta-value" style="color: ${criticalCount > 0 ? '#dc3545' : '#28a745'}">
              ${criticalCount}
            </span>
          </div>
          <div class="meta-row">
            <span class="meta-label">Last Updated:</span>
            <span class="meta-value">${new Date(data.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
  `;

  // No alerts - show healthy message
  if (totalAlerts === 0) {
    html += `
      <div class="alerts-section">
        <div class="alerts-healthy">
          <p>✅ All components healthy!</p>
          <p>No alerts detected.</p>
        </div>
      </div>
    `;
  } else {
    // Show alerts grouped by component
    Object.entries(components).forEach(([componentName, componentData]) => {
      const alerts = componentData.alerts || [];
      const componentAlertCount = componentData.count || 0;
      
      html += `
        <div class="alerts-section">
          <h3>${componentName} (${componentAlertCount})</h3>
          <div class="component-alerts">
      `;
      
      alerts.forEach((alert) => {
        const levelColors = {
          "critical": "#721c24",
          "warning": "#ffc107",
          "info": "#17a2b8"
        };
        const levelColor = levelColors[alert.level] || "#6c757d";
        
        html += `
          <div class="alert-item" style="border-left: 4px solid ${levelColor}">
            <div class="alert-header">
              <span class="alert-level" style="background-color: ${levelColor}">
                ${alert.level.toUpperCase()}
              </span>
            </div>
            <div class="alert-message">${alert.message}</div>
            <div class="alert-sensor">Sensor: ${alert.sensor}</div>
          </div>
        `;
      });
      
      html += `
          </div>
        </div>
      `;
    });
  }

  html += `
    </div>
  `;
  
  return html;
}
