import { bindUI } from "./bindings.js";
import { state } from "./state/state.js";
import {API} from "./api.js";
import { render } from "./renders/render.js";
import { renderSensors } from "./renders/sensors.js";

$(document).ready(() => {
  console.log("App initializing...");
  bindUI();
  refreshAgent();

  // Refresh live sensor data every 1 second (real-time display)
  setInterval(refreshLiveSensors, 1000);

  // Refresh system info every 10 seconds
  setInterval(refreshSystemInfo, 10000);
});

const refreshSystemInfo = async () => {
  try {
    const sysInfo = await API.api("/api/info");
    const invResponse = await API.api("/api/inventory");

    const agent = {
      agent_id: "localhost",
      hostname: sysInfo?.system?.hostname || "localhost",
      status: "active",
      is_local: true,
      inventory: invResponse?.inventory || {},
    };

    state.setAgent(agent);
    render();
  } catch (err) {
    console.error("System info refresh failed:", err);
  }
};

const refreshLiveSensors = async () => {
  try {
    // Get live sensor data from hardware
    const sensorsResponse = await API.api("/api/sensors/latest");

    if (sensorsResponse?.sensors) {
      // Store current sensors in state with timestamp
      state.addSensorReading(new Date().toISOString(), sensorsResponse.sensors);

      // Update agent with latest sensors
      const agent = state.getAgent();
      if (agent) {
        agent.sensors = sensorsResponse.sensors;

        // Only render if sensors tab is active
        const activeTab = state.activeTab;
        if (activeTab === "sensors") {
          renderSensors(agent);
        }
      }
    }
  } catch (err) {
    console.debug("Live sensor refresh error:", err);
  }
};

const refreshAgent = async () => {
  await refreshSystemInfo();
  await refreshLiveSensors();
};

