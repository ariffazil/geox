/**
 * VolumeRenderer.js — WebGL-based 2D seismic/attribute volume slice renderer.
 * DITEMPA BUKAN DIBERI
 *
 * Renders a 2D slice of a 3D seismic/attribute volume onto a WebGL canvas.
 * Receives render payload from geox_render_volume_slice MCP tool via postMessage.
 *
 * Usage:
 *   const renderer = new VolumeRenderer(canvasElement);
 *   renderer.render(renderPayload);
 *
 * renderPayload shape (from geox_render_volume_slice):
 *   {
 *     render_type: "volume_slice",
 *     attribute_name: "amplitude",
 *     slice_axis: "z",
 *     slice_index: 42,
 *     nx: 256,
 *     ny: 128,
 *     colormap: "seismic",
 *     vmin: -1.0,
 *     vmax: 1.0,
 *     flat_data: [0.0–1.0, ...],  // normalised, length = nx * ny
 *     claim_tag: "CLAIM",
 *     vault_receipt: { hash: "...", timestamp: "..." }
 *   }
 */

const COLORMAPS = {
  seismic: [
    [0.000, 0.000, 0.800],  // deep blue (min)
    [0.000, 0.500, 1.000],
    [1.000, 1.000, 1.000],  // white (mid)
    [1.000, 0.300, 0.000],
    [0.600, 0.000, 0.000],  // deep red (max)
  ],
  viridis: [
    [0.267, 0.004, 0.329],
    [0.128, 0.567, 0.551],
    [0.369, 0.788, 0.384],
    [0.993, 0.906, 0.144],
  ],
  jet: [
    [0.000, 0.000, 0.500],
    [0.000, 0.500, 1.000],
    [0.000, 1.000, 0.500],
    [0.500, 1.000, 0.000],
    [1.000, 0.500, 0.000],
    [0.500, 0.000, 0.000],
  ],
};

function _sampleColormap(cmap, t) {
  const stops = COLORMAPS[cmap] || COLORMAPS.seismic;
  const n = stops.length - 1;
  const scaled = t * n;
  const lo = Math.min(Math.floor(scaled), n - 1);
  const hi = Math.min(lo + 1, n);
  const f = scaled - lo;
  return [
    stops[lo][0] + f * (stops[hi][0] - stops[lo][0]),
    stops[lo][1] + f * (stops[hi][1] - stops[lo][1]),
    stops[lo][2] + f * (stops[hi][2] - stops[lo][2]),
  ];
}

class VolumeRenderer {
  /**
   * @param {HTMLCanvasElement} canvas
   */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.payload = null;

    // Listen for MCP postMessage updates
    window.addEventListener("message", (event) => {
      if (
        event.data &&
        event.data.render_type === "volume_slice" &&
        event.data.flat_data
      ) {
        this.render(event.data);
      }
    });
  }

  /**
   * Render a volume slice payload onto the canvas.
   * @param {object} payload — geox_render_volume_slice output
   */
  render(payload) {
    this.payload = payload;
    const { nx, ny, flat_data, colormap, claim_tag, vault_receipt } = payload;
    const cmap = colormap || "seismic";

    if (!flat_data || flat_data.length === 0) {
      this._renderEmpty("No volume data");
      return;
    }

    this.canvas.width = nx;
    this.canvas.height = ny + 36;  // +36 for header/footer
    const ctx = this.ctx;

    // Black background
    ctx.fillStyle = "#000000";
    ctx.fillRect(0, 0, nx, ny + 36);

    // Header bar
    ctx.fillStyle = "#16213e";
    ctx.fillRect(0, 0, nx, 18);
    ctx.fillStyle = "#a0c0e0";
    ctx.font = "bold 11px monospace";
    const attrName = payload.attribute_name || "attribute";
    const axisLabel = `axis=${payload.slice_axis || "z"} idx=${payload.slice_index ?? 0}`;
    const claimTag = claim_tag || "CLAIM";
    ctx.fillText(`${attrName} | ${axisLabel} | ${claimTag}`, 4, 13);

    // Draw slice via ImageData
    const imageData = ctx.createImageData(nx, ny);
    const data = imageData.data;

    for (let row = 0; row < ny; row++) {
      for (let col = 0; col < nx; col++) {
        const idx = row * nx + col;
        const t = flat_data[idx] != null ? Math.max(0, Math.min(1, flat_data[idx])) : 0.5;
        const [r, g, b] = _sampleColormap(cmap, t);
        const pixIdx = (row * nx + col) * 4;
        data[pixIdx + 0] = Math.round(r * 255);
        data[pixIdx + 1] = Math.round(g * 255);
        data[pixIdx + 2] = Math.round(b * 255);
        data[pixIdx + 3] = 255;
      }
    }

    ctx.putImageData(imageData, 0, 18);

    // Footer bar
    const fy = ny + 18;
    ctx.fillStyle = "#16213e";
    ctx.fillRect(0, fy, nx, 18);
    ctx.fillStyle = "#606080";
    ctx.font = "9px monospace";
    const ts = vault_receipt ? vault_receipt.timestamp : "";
    const hash = vault_receipt ? vault_receipt.hash : "—";
    ctx.fillText(`VAULT999:${hash} | ${ts} | DITEMPA BUKAN DIBERI`, 4, fy + 13);
  }

  /**
   * Render a colorbar legend on a separate canvas element.
   * @param {HTMLCanvasElement} legendCanvas
   * @param {string} colormap
   * @param {number} vmin
   * @param {number} vmax
   */
  renderColorbar(legendCanvas, colormap, vmin, vmax) {
    const ctx = legendCanvas.getContext("2d");
    const w = legendCanvas.width || 20;
    const h = legendCanvas.height || 200;
    const cmap = colormap || "seismic";

    for (let y = 0; y < h; y++) {
      const t = 1.0 - y / h;
      const [r, g, b] = _sampleColormap(cmap, t);
      ctx.fillStyle = `rgb(${Math.round(r * 255)},${Math.round(g * 255)},${Math.round(b * 255)})`;
      ctx.fillRect(0, y, w, 1);
    }

    // Labels
    ctx.fillStyle = "#ffffff";
    ctx.font = "10px monospace";
    ctx.fillText(vmax.toFixed(2), 2, 10);
    ctx.fillText(vmin.toFixed(2), 2, h - 4);
  }

  _renderEmpty(msg) {
    const ctx = this.ctx;
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.fillStyle = "#606080";
    ctx.font = "13px monospace";
    ctx.fillText(msg, 10, 40);
  }
}

// Export for both module and browser global usage
if (typeof module !== "undefined" && module.exports) {
  module.exports = VolumeRenderer;
} else {
  window.VolumeRenderer = VolumeRenderer;
}
