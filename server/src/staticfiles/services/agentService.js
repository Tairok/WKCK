export function renderAgentList(agent) {
  const $list = $("#agent-list");
  if (!$list.length) return;

  if (!agent) {
    $list.html("<li>No agents</li>");
    return;
  }

  $list.html(`
    <li class="active">${agent.hostname}</li>
  `);
}

export function renderAgentSummary(agent) {
  const $summary = $("#agent-summary");
  if (!$summary.length) return;

  if (!agent) {
    $summary.html("");
    return;
  }

  $summary.html(`
    <dt>Agent</dt><dd>${agent.agent_id || "localhost"}</dd>
    <dt>Status</dt><dd>${agent.status || "active"}</dd>
  `);
}
