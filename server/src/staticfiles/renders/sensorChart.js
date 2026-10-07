/**
 * Line chart renderer for sensor time-series data
 * Uses plain SVG, no external charting libraries
 */

export class SensorChart {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.options = {
      width: 800,
      height: 300,
      margin: { top: 20, right: 30, bottom: 40, left: 60 },
      lineColor: "#6bb6ff",
      rangeColor: "rgba(107, 182, 255, 0.2)",
      gridColor: "#34404d",
      textColor: "#e7ecf2",
      pointRadius: 3,
      ...options,
    };

    if (!this.container) {
      console.warn(`[SensorChart] Container ${containerId} not found`);
      return;
    }

    this.svg = null;
    this.points = [];
  }

  /**
   * Render chart with data
   * @param {Array} data - Array of {t, avg, min, max} points (t = ISO timestamp)
   */
  render(data) {
    if (!data || data.length === 0) {
      this.container.innerHTML =
        '<div style="color: #98a6b3; padding: 20px; text-align: center;">No data available</div>';
      return;
    }

    this.points = data;
    this._createSVG();
    this._drawGrid();
    this._drawAxes();
    this._drawRange();
    this._drawLine();
    this._drawPoints();
    this._attachHover();
  }

  _createSVG() {
    this.container.innerHTML = "";
    const { width, height } = this.options;
    this.svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    this.svg.setAttribute("width", width);
    this.svg.setAttribute("height", height);
    this.svg.setAttribute("style", "display: block; margin: 0 auto;");
    this.container.appendChild(this.svg);

    this.innerWidth =
      width - this.options.margin.left - this.options.margin.right;
    this.innerHeight =
      height - this.options.margin.top - this.options.margin.bottom;
  }

  _getScales() {
    // Time scale (linear)
    const times = this.points.map((p) => new Date(p.t).getTime());
    const tMin = Math.min(...times);
    const tMax = Math.max(...times);
    const tRange = tMax - tMin || 1;

    // Value scale
    const values = this.points.flatMap((p) => [p.min || p.avg, p.max || p.avg]);
    const vMin = Math.min(...values);
    const vMax = Math.max(...values);
    const vRange = vMax - vMin || 1;

    return {
      xScale: (t) => {
        const x =
          ((new Date(t).getTime() - tMin) / tRange) * this.innerWidth;
        return this.options.margin.left + x;
      },
      yScale: (v) => {
        const y = ((vMax - v) / vRange) * this.innerHeight;
        return this.options.margin.top + y;
      },
      vMin,
      vMax,
    };
  }

  _drawGrid() {
    const { margin } = this.options;
    const scales = this._getScales();

    // Horizontal grid lines
    const ySteps = 5;
    for (let i = 0; i <= ySteps; i++) {
      const v = scales.vMin + (scales.vMax - scales.vMin) * (i / ySteps);
      const y = scales.yScale(v);

      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", margin.left);
      line.setAttribute("x2", margin.left + this.innerWidth);
      line.setAttribute("y1", y);
      line.setAttribute("y2", y);
      line.setAttribute("stroke", this.options.gridColor);
      line.setAttribute("stroke-width", "0.5");
      line.setAttribute("opacity", "0.5");
      this.svg.appendChild(line);
    }
  }

  _drawAxes() {
    const { margin } = this.options;
    const scales = this._getScales();

    // Left axis (values)
    const leftAxis = document.createElementNS("http://www.w3.org/2000/svg", "line");
    leftAxis.setAttribute("x1", margin.left);
    leftAxis.setAttribute("x2", margin.left);
    leftAxis.setAttribute("y1", margin.top);
    leftAxis.setAttribute("y2", margin.top + this.innerHeight);
    leftAxis.setAttribute("stroke", this.options.gridColor);
    leftAxis.setAttribute("stroke-width", "1");
    this.svg.appendChild(leftAxis);

    // Bottom axis (time)
    const bottomAxis = document.createElementNS("http://www.w3.org/2000/svg", "line");
    bottomAxis.setAttribute("x1", margin.left);
    bottomAxis.setAttribute("x2", margin.left + this.innerWidth);
    bottomAxis.setAttribute("y1", margin.top + this.innerHeight);
    bottomAxis.setAttribute("y2", margin.top + this.innerHeight);
    bottomAxis.setAttribute("stroke", this.options.gridColor);
    bottomAxis.setAttribute("stroke-width", "1");
    this.svg.appendChild(bottomAxis);

    // Y-axis labels
    const ySteps = 5;
    for (let i = 0; i <= ySteps; i++) {
      const v = scales.vMin + (scales.vMax - scales.vMin) * (i / ySteps);
      const y = scales.yScale(v);

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", margin.left - 10);
      text.setAttribute("y", y + 5);
      text.setAttribute("text-anchor", "end");
      text.setAttribute("font-size", "12");
      text.setAttribute("fill", this.options.textColor);
      text.setAttribute("opacity", "0.7");
      text.textContent = v.toFixed(1);
      this.svg.appendChild(text);
    }

    // X-axis labels (time)
    const xSteps = 4;
    for (let i = 0; i <= xSteps; i++) {
      const idx = Math.floor((i / xSteps) * (this.points.length - 1));
      const point = this.points[idx];
      const x = scales.xScale(point.t);

      const date = new Date(point.t);
      const timeStr = date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", x);
      text.setAttribute("y", margin.top + this.innerHeight + 20);
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("font-size", "12");
      text.setAttribute("fill", this.options.textColor);
      text.setAttribute("opacity", "0.7");
      text.textContent = timeStr;
      this.svg.appendChild(text);
    }
  }

  _drawRange() {
    // Draw min-max range as area under the line
    const scales = this._getScales();
    const pathData = this.points
      .map((p, i) => {
        const x = scales.xScale(p.t);
        const yMin = scales.yScale(p.max || p.avg); // Inverted: higher value = lower on chart
        const yMax = scales.yScale(p.min || p.avg);
        return i === 0
          ? `M ${x} ${yMin} L ${x} ${yMax}`
          : `L ${x} ${yMin} L ${x} ${yMax}`;
      })
      .join(" ");

    if (pathData) {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", pathData);
      path.setAttribute("stroke", "none");
      path.setAttribute("fill", this.options.rangeColor);
      path.setAttribute("opacity", "0.5");
      this.svg.appendChild(path);
    }
  }

  _drawLine() {
    const scales = this._getScales();
    const pathData = this.points
      .map((p, i) => {
        const x = scales.xScale(p.t);
        const y = scales.yScale(p.avg);
        return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
      })
      .join(" ");

    if (pathData) {
      const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
      line.setAttribute("d", pathData);
      line.setAttribute("stroke", this.options.lineColor);
      line.setAttribute("stroke-width", "2");
      line.setAttribute("fill", "none");
      line.setAttribute("stroke-linecap", "round");
      line.setAttribute("stroke-linejoin", "round");
      this.svg.appendChild(line);
    }
  }

  _drawPoints() {
    const scales = this._getScales();
    this.points.forEach((p) => {
      const x = scales.xScale(p.t);
      const y = scales.yScale(p.avg);

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", x);
      circle.setAttribute("cy", y);
      circle.setAttribute("r", this.options.pointRadius);
      circle.setAttribute("fill", this.options.lineColor);
      circle.setAttribute("data-index", this.points.indexOf(p));
      this.svg.appendChild(circle);
    });
  }

  _attachHover() {
    // Add a crosshair and tooltip on hover
    const scales = this._getScales();
    const { margin } = this.options;

    // Create tooltip element
    const tooltip = document.createElement("div");
    tooltip.style.cssText = `
      position: absolute;
      background: #171d24;
      border: 1px solid #34404d;
      border-radius: 4px;
      padding: 8px;
      font-size: 12px;
      color: #e7ecf2;
      pointer-events: none;
      display: none;
      z-index: 100;
    `;
    this.container.style.position = "relative";
    this.container.appendChild(tooltip);

    // Overlay for mouse tracking
    const overlay = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    overlay.setAttribute("x", margin.left);
    overlay.setAttribute("y", margin.top);
    overlay.setAttribute("width", this.innerWidth);
    overlay.setAttribute("height", this.innerHeight);
    overlay.setAttribute("fill", "transparent");
    overlay.style.cursor = "crosshair";

    overlay.addEventListener("mousemove", (e) => {
      const rect = this.svg.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;

      // Find closest point
      let closestIdx = 0;
      let minDist = Infinity;
      this.points.forEach((p, i) => {
        const x = scales.xScale(p.t);
        const dist = Math.abs(x - mouseX);
        if (dist < minDist) {
          minDist = dist;
          closestIdx = i;
        }
      });

      const p = this.points[closestIdx];
      const x = scales.xScale(p.t);
      const y = scales.yScale(p.avg);

      // Show tooltip
      const date = new Date(p.t);
      const timeStr = date.toLocaleTimeString("en-US");
      tooltip.innerHTML = `
        <div><strong>${timeStr}</strong></div>
        <div>Avg: ${p.avg.toFixed(2)}</div>
        <div>Min: ${(p.min || p.avg).toFixed(2)}</div>
        <div>Max: ${(p.max || p.avg).toFixed(2)}</div>
      `;
      tooltip.style.display = "block";
      tooltip.style.left = `${x + 10}px`;
      tooltip.style.top = `${y - 60}px`;
    });

    overlay.addEventListener("mouseout", () => {
      tooltip.style.display = "none";
    });

    this.svg.appendChild(overlay);
  }
}
