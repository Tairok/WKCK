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
  const wmi = inventory.wmi || {};
  const system_hw = inventory.system_hw || {};
  const bios = inventory.bios || {};
  const wmi_memory = wmi.memory || {};
  const wmi_disks = wmi.disks || {};

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

    ${system_hw?.model ? `<article class="panel"><h3>System Hardware</h3><dl id="system-hw-info"></dl></article>` : ''}

    ${bios?.manufacturer ? `<article class="panel"><h3>BIOS</h3><dl id="bios-info"></dl></article>` : ''}

    ${motherboard ? `<article class="panel"><h3>Motherboard</h3><dl id="motherboard-info"></dl></article>` : ''}

    ${wmi_memory?.modules?.length > 0 ? `
    <article class="panel">
      <h3>Memory Modules</h3>
      <table style="font-size: 0.9em;">
        <thead>
          <tr>
            <th>Slot</th>
            <th>Manufacturer</th>
            <th>Capacity</th>
            <th>Type</th>
            <th>Speed</th>
            <th>Part Number</th>
          </tr>
        </thead>
        <tbody id="memory-modules-table"></tbody>
      </table>
    </article>` : ''}

    ${wmi_disks?.drives?.length > 0 ? `
    <article class="panel">
      <h3>Physical Disks</h3>
      <table style="font-size: 0.9em;">
        <thead>
          <tr>
            <th>Model</th>
            <th>Size</th>
            <th>Serial</th>
            <th>Interface</th>
            <th>Media</th>
          </tr>
        </thead>
        <tbody id="physical-disks-table"></tbody>
      </table>
    </article>` : ''}

    <article class="panel">
      <h3>Storage Partitions</h3>
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

  // System Hardware
  if (system_hw?.model) {
    $("#system-hw-info").html(`
      <dt>Manufacturer</dt><dd>${system_hw.manufacturer || '-'}</dd>
      <dt>Model</dt><dd>${system_hw.model || '-'}</dd>
      <dt>Serial</dt><dd>${system_hw.serial_number || '-'}</dd>
      <dt>UUID</dt><dd>${system_hw.uuid || '-'}</dd>
    `);
  }

  // BIOS
  if (bios?.manufacturer) {
    $("#bios-info").html(`
      <dt>Manufacturer</dt><dd>${bios.manufacturer || '-'}</dd>
      <dt>Version</dt><dd>${bios.version || '-'}</dd>
      <dt>Release Date</dt><dd>${bios.release_date || '-'}</dd>
      <dt>Serial</dt><dd>${bios.serial_number || '-'}</dd>
    `);
  }

  // Motherboard
  if (motherboard) {
    $("#motherboard-info").html(`
      <dt>Manufacturer</dt><dd>${motherboard.manufacturer || '-'}</dd>
      <dt>Model</dt><dd>${motherboard.product || motherboard.model || '-'}</dd>
      <dt>Version</dt><dd>${motherboard.version || '-'}</dd>
      <dt>Serial</dt><dd>${motherboard.serial_number || '-'}</dd>
    `);
  }

  // Memory Modules
  if (wmi_memory?.modules?.length > 0) {
    $("#memory-modules-table").html(
      wmi_memory.modules.map((m, idx) => `
        <tr>
          <td>${m.device_locator || m.bank_label || `Slot ${idx + 1}`}</td>
          <td>${m.manufacturer || '-'}</td>
          <td>${m.capacity_gb} GB</td>
          <td>${m.type || '-'}</td>
          <td>${m.speed_mhz}${typeof m.speed_mhz === 'number' ? ' MHz' : ''}</td>
          <td>${m.part_number || '-'}</td>
        </tr>
      `).join("")
    );
  }

  // Physical Disks
  if (wmi_disks?.drives?.length > 0) {
    $("#physical-disks-table").html(
      wmi_disks.drives.map(d => `
        <tr>
          <td>${d.model || '-'}</td>
          <td>${d.size_gb} GB</td>
          <td>${d.serial_number || '-'}</td>
          <td>${d.interface_type || '-'}</td>
          <td>${d.media_type || '-'}</td>
        </tr>
      `).join("")
    );
  }

  // DISKS (Partitions)
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
