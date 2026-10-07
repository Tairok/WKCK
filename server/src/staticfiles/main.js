import { bindUI } from "./bindings.js";
import { state } from "./state/state.js";
import {API} from "./api.js";
import { render } from "./renders/render.js";
import { renderSensors } from "./renders/sensors.js";

$(document).ready(() => {
  console.log("App initializing...");
  bindUI();
  refreshAgent();

  // Refresh agent data every 5 seconds
  setInterval(refreshAgent, 5000);

  // Update sensors display every 2 seconds (data is now persisted on server)
  setInterval(updateSensorsDisplay, 2000);
});

const refreshAgent = async () => {
  try {
    const agents = await API.api("/api/agents");
    if (agents.agents?.[0]) state.setAgent(agents.agents?.[0]);
    render();

  } catch (err) {
    console.error("Refresh failed:", err);
  }
};

const updateSensorsDisplay = () => {
  try {
    const agent = state.getAgent();
    if (!agent) return;

    // Only update sensors tab if it's active
    const activeTab = state.activeTab;
    if (activeTab === "sensors") {
      renderSensors(agent);
    }
  } catch (err) {
    // Silently fail
  }
};

