import { renderOverview } from "./overview.js";
import { renderInventory } from "./inventory.js";
import { renderSensors } from "./sensors.js";
import { renderHealth } from "./health.js";
import { LogsService } from "../services/logsService.js";
import { state } from "../state/state.js";

// Re-export log functions for backward compatibility
export const loadServerLogs = (...args) => LogsService.loadServerLogs(...args);
export const loadClientLogs = (...args) => LogsService.loadClientLogs(...args);


// Main render orchestrator (jQuery version)
export function render() {
  const agent_v = state.getAgent();

  // Update header
  $("#host-name").text(agent_v?.hostname || "no agent");
  $("#agent-online-state").text(agent_v?.status || "offline");

  // Render all panes
  renderOverview(agent_v);
  renderInventory(agent_v);
  renderSensors(agent_v);
  renderHealth(agent_v);
  LogsService.render(agent_v);
}
