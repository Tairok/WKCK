export function renderInventory(agent) {
  const $section = $('[data-view="inventory"]');
  if ($section.length === 0) return;

  const inventory = agent?.inventory || {};
  const system = inventory.system || {};
  const cpu = inventory.cpu || {};
  const memory = inventory.memory || {};
  const gpu = inventory.gpu;
  const motherboard = inventory.motherboard;
  const power = inventory.power || {};
  const disks = inventory.disks || [];

  // Render głównego widoku
  $section.html(`
    <div class="pane-header">
      <h2>Inventory</h2>
      <span>Hardware & Storage details</span>
    </div>
    <div class="section-grid">
      <article class="panel">
        <h3>System</h3>
        <dl id="system-info"></dl>
      </article>
      <article class="panel">
        <h3>CPU</h3>
        <dl id="cpu-info"></dl>
      </article>
      <article class="panel">
        <h3>Memory</h3>
        <dl id="memory-info"></dl>
      </article>
    </div>

    ${gpu ? `<article class="panel"><h3>GPU</h3><dl id="gpu-info"></dl></article>` : ''}

    ${motherboard ? `<article class="panel"><h3>Motherboard</h3><dl id="motherboard-info"></dl></article>` : ''}

    <article class="panel">
      <h3>Storage</h3>
      <table>
        <thead>
          <tr>
            <th>Device</th>
            <th>Mount</th>
            <th>FS</th>
            <th>Total</th>
            <th>Used</th>
            <th>Free</th>
          </tr>
        </thead>
        <tbody id="disk-table"></tbody>
      </table>
    </article>
  `);

  // SYSTEM
  $("#system-info").html(
    system.hostname
      ? `
        <dt>Hostname</dt><dd>${system.hostname}</dd>
        <dt>OS</dt><dd>${system.os} ${system.release}</dd>
        <dt>Architecture</dt><dd>${system.architecture?.[0] || 'unknown'}</dd>
        <dt>Processor</dt><dd>${system.processor || 'unknown'}</dd>
      `
      : "<dt>No data</dt><dd>-</dd>"
  );

  // CPU
  $("#cpu-info").html(
    cpu.model
      ? `
        <dt>Model</dt><dd>${cpu.model}</dd>
        <dt>Cores</dt><dd>${cpu.physical_cores} physical / ${cpu.logical_cores} logical</dd>
        <dt>Frequency</dt><dd>${cpu.current_frequency_mhz || '?'} MHz (${cpu.min_frequency_mhz || '?'} - ${cpu.max_frequency_mhz || '?'})</dd>
        <dt>Load</dt><dd>${cpu.load_percent}%</dd>
        ${cpu.ctx_switches ? `<dt>Context Switches</dt><dd>${cpu.ctx_switches}</dd>` : ''}
      `
      : "<dt>No data</dt><dd>-</dd>"
  );

  // MEMORY
  $("#memory-info").html(
    memory.total
      ? `
        <dt>Total</dt><dd>${(memory.total / 1024 / 1024 / 1024).toFixed(2)} GB</dd>
        <dt>Used</dt><dd>${(memory.used / 1024 / 1024 / 1024).toFixed(2)} GB (${memory.percent}%)</dd>
        <dt>Available</dt><dd>${(memory.available / 1024 / 1024 / 1024).toFixed(2)} GB</dd>
        ${memory.swap_total ? `<dt>Swap Total</dt><dd>${(memory.swap_total / 1024 / 1024 / 1024).toFixed(2)} GB</dd>` : ''}
        ${memory.swap_used ? `<dt>Swap Used</dt><dd>${(memory.swap_used / 1024 / 1024 / 1024).toFixed(2)} GB</dd>` : ''}
      `
      : "<dt>No data</dt><dd>-</dd>"
  );

  // GPU
  if (gpu) {
    const $gpuInfo = $("#gpu-info");

    if (Array.isArray(gpu)) {
      $gpuInfo.html(
        gpu
          .map(
            g => `
              <dt>${g.name}</dt>
              <dd>
                ${g.adapter_ram ? `RAM: ${(g.adapter_ram / 1024 / 1024 / 1024).toFixed(2)} GB` : ''}
                ${g.load_percent ? `Load: ${g.load_percent}%` : ''}
                ${g.memory_percent ? `Memory: ${g.memory_percent}%` : ''}
                ${g.temperature ? `Temp: ${g.temperature}°C` : ''}
              </dd>
            `
          )
          .join("")
      );
    }
  }

  // Motherboard
  if (motherboard) {
    $("#motherboard-info").html(`
      <dt>Manufacturer</dt><dd>${motherboard.manufacturer || '-'}</dd>
      <dt>Model</dt><dd>${motherboard.model || '-'}</dd>
      <dt>Version</dt><dd>${motherboard.version || '-'}</dd>
      <dt>Serial</dt><dd>${motherboard.serial_number || '-'}</dd>
    `);
  }

  // DISKS
  $("#disk-table").html(
    disks
      .map(
        d => `
        <tr>
          <td>${d.device}</td>
          <td>${d.mountpoint}</td>
          <td>${d.filesystem}</td>
          <td>${d.total ? (d.total / 1024 / 1024 / 1024).toFixed(1) : '?'} GB</td>
          <td>${d.used ? (d.used / 1024 / 1024 / 1024).toFixed(1) : '?'} GB</td>
          <td>${d.free ? (d.free / 1024 / 1024 / 1024).toFixed(1) : '?'} GB</td>
        </tr>
      `
      )
      .join("")
  );
}
