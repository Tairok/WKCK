export function renderOverview(agent) {
  const $section = $('[data-view="overview"]');
  if ($section.length === 0) return;

  // Render głównego widoku
  $section.html(`
    <div class="pane-header">
      <h2>Overview</h2>
      <span id="agent-online-state"></span>
    </div>
    <div class="section-grid">
      <article class="panel">
        <h3>Client details</h3>
        <dl id="overview-summary"></dl>
      </article>
      <article class="panel">
        <h3>Capabilities</h3>
        <dl id="agent-capabilities"></dl>
      </article>
      <article class="panel">
        <h3>Last update</h3>
        <dl id="update-summary"></dl>
      </article>
    </div>
  `);

  if (!agent) return;

  // Client details
  $("#overview-summary").html(`
    <dt>ID</dt><dd>${agent.id}</dd>
    <dt>Hostname</dt><dd>${agent.hostname}</dd>
    <dt>Platform</dt><dd>${agent.platform || "unknown"}</dd>
  `);

  // Capabilities
  $("#agent-capabilities").html(
    Object.entries(agent.capabilities || {})
      .map(([k, v]) => `<dt>${k}</dt><dd>${Array.isArray(v) ? v.join(", ") : v}</dd>`)
      .join("")
  );

  // Last update summary
  $("#update-summary").html(`
    <dt>Last seen</dt><dd>${new Date(agent.last_seen * 1000).toLocaleString()}</dd>
    <dt>Last inventory</dt><dd>${agent.last_inventory_at ? new Date(agent.last_inventory_at * 1000).toLocaleString() : "never"}</dd>
    <dt>Last sensors</dt><dd>${agent.last_sensors_at ? new Date(agent.last_sensors_at * 1000).toLocaleString() : "never"}</dd>
  `);
}
