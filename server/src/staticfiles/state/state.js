export const state = {
  agent: null,
  logs: [],
  activeTab: "overview",
  sensorHistory: [],  // Array of {timestamp, sensors} objects

  setAgent(agentId)
  {
    this.agent = agentId;
  },
  
  getAgent() 
  {
    return this.agent;
  },
  
  addSensorReading(timestamp, sensors) {
    if (!this.sensorHistory) {
      this.sensorHistory = [];
    }
    
    this.sensorHistory.push({
      timestamp,
      sensors
    });
    
    // Keep only last 200 readings
    if (this.sensorHistory.length > 200) {
      this.sensorHistory.shift();
    }
  },
  
  getSensorHistory() {
    return this.sensorHistory || [];
  }

};

