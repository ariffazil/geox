/**
 * LogTrackViewer.js — Interactive well log track renderer.
 * DITEMPA BUKAN DIBERI
 *
 * Renders GR, RHOB, NPHI, RT panels on an HTML5 Canvas element.
 * Receives render payload from geox_render_log_track MCP tool via postMessage.
 *
 * Usage:
 *   const viewer = new LogTrackViewer(canvasElement, { width: 400, height: 800 });
 *   viewer.render(renderPayload);
 *
 * renderPayload shape (from geox_render_log_track):
 *   {
 *     render_type: "log_track",
 *     depth: [float, ...],
 *     depth_unit: "m",
 *     n_samples: number,
 *     tracks: [{
 *       mnemonic: "GR",
 *       unit: "gAPI",
 *       display_range: [0, 150],
 *       fill_color: "#7CFC00",
 *       log_scale: false,
 *       width_px: 80,
 *       normalised: [0.0–1.0, ...]
 *     }, ...],
 *     claim_tag: "CLAIM",
 *     vault_receipt: { hash: "...", timestamp: "..." }
 *   }
 */

class LogTrackViewer {
  /**
   * @param {HTMLCanvasElement} canvas
   * @param {{ width?: number, height?: number, depthTrackWidth?: number }} options
   */
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.width = options.width || canvas.width || 600;
    this.height = options.height || canvas.height || 800;
    this.depthTrackWidth = options.depthTrackWidth || 60;
    this.headerHeight = 40;
    this.footerHeight = 20;
    this.payload = null;

    canvas.width = this.width;
    canvas.height = this.height;

    // Listen for MCP postMessage updates
    window.addEventListener("message", (event) => {
      if (
        event.data &&
        event.data.render_type === "log_track" &&
        event.data.tracks
      ) {
        this.render(event.data);
      }
    });
  }

  /**
   * Render a log track payload onto the canvas.
   * @param {object} payload — geox_render_log_track output
   */
  render(payload) {
    this.payload = payload;
    const ctx = this.ctx;
    const tracks = payload.tracks || [];
    const depth = payload.depth || [];
    const n = depth.length;

    if (n === 0 || tracks.length === 0) {
      this._renderEmpty("No data");
      return;
    }

    ctx.clearRect(0, 0, this.width, this.height);
    this._renderBackground();
    this._renderHeader(payload);

    const plotHeight = this.height - this.headerHeight - this.footerHeight;
    const trackX0 = this.depthTrackWidth;
    let xCursor = trackX0;

    // Depth axis
    this._renderDepthTrack(depth, payload.depth_unit || "m", plotHeight);

    // Curve tracks
    for (const track of tracks) {
      const tw = track.width_px || 80;
      this._renderCurveTrack(track, xCursor, plotHeight, n);
      xCursor += tw;
    }

    this._renderFooter(payload);
  }

  _renderBackground() {
    const ctx = this.ctx;
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, this.width, this.height);
  }

  _renderHeader(payload) {
    const ctx = this.ctx;
    ctx.fillStyle = "#16213e";
    ctx.fillRect(0, 0, this.width, this.headerHeight);
    ctx.fillStyle = "#e0e0e0";
    ctx.font = "bold 13px monospace";
    const claimTag = payload.claim_tag || "UNKNOWN";
    const hash = payload.vault_receipt ? payload.vault_receipt.hash : "—";
    ctx.fillText(`GEOX Log Track | ${claimTag} | VAULT:${hash}`, 8, 26);
  }

  _renderDepthTrack(depth, unit, plotHeight) {
    const ctx = this.ctx;
    const x = 0;
    const y0 = this.headerHeight;
    const dMin = depth[0];
    const dMax = depth[depth.length - 1];

    ctx.fillStyle = "#0f3460";
    ctx.fillRect(x, y0, this.depthTrackWidth, plotHeight);

    ctx.fillStyle = "#a0a0c0";
    ctx.font = "10px monospace";
    ctx.textAlign = "center";
    ctx.fillText(`MD`, this.depthTrackWidth / 2, y0 + 14);
    ctx.fillText(`(${unit})`, this.depthTrackWidth / 2, y0 + 26);

    const nTicks = 10;
    for (let i = 0; i <= nTicks; i++) {
      const frac = i / nTicks;
      const d = dMin + frac * (dMax - dMin);
      const yPx = y0 + frac * plotHeight;
      ctx.fillStyle = "#6060a0";
      ctx.fillRect(x + this.depthTrackWidth - 8, yPx - 0.5, 8, 1);
      ctx.fillStyle = "#a0a0c0";
      ctx.fillText(d.toFixed(0), this.depthTrackWidth / 2, yPx + 4);
    }
    ctx.textAlign = "left";
  }

  _renderCurveTrack(track, xStart, plotHeight, n) {
    const ctx = this.ctx;
    const y0 = this.headerHeight;
    const tw = track.width_px || 80;
    const mnem = track.mnemonic;
    const norm = track.normalised;
    const color = track.fill_color || "#ffffff";

    // Track background
    ctx.fillStyle = "#0d0d1a";
    ctx.fillRect(xStart, y0, tw, plotHeight);
    ctx.strokeStyle = "#333355";
    ctx.strokeRect(xStart, y0, tw, plotHeight);

    // Track header
    ctx.fillStyle = "#16213e";
    ctx.fillRect(xStart, y0, tw, 22);
    ctx.fillStyle = color;
    ctx.font = "bold 11px monospace";
    ctx.fillText(mnem, xStart + 4, y0 + 14);

    if (!norm || norm.length === 0) return;

    // Draw curve as filled area from left wall
    ctx.beginPath();
    ctx.moveTo(xStart, y0 + 22);

    for (let i = 0; i < Math.min(norm.length, n); i++) {
      const v = norm[i];
      const yPx = y0 + 22 + (i / (n - 1)) * (plotHeight - 22);
      const xPx = v != null ? xStart + v * tw : xStart;
      if (i === 0) ctx.moveTo(xPx, yPx);
      else ctx.lineTo(xPx, yPx);
    }

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  _renderFooter(payload) {
    const ctx = this.ctx;
    const y = this.height - this.footerHeight;
    ctx.fillStyle = "#16213e";
    ctx.fillRect(0, y, this.width, this.footerHeight);
    ctx.fillStyle = "#606080";
    ctx.font = "10px monospace";
    const ts = payload.vault_receipt ? payload.vault_receipt.timestamp : "";
    ctx.fillText(`VAULT999 | ${ts} | DITEMPA BUKAN DIBERI`, 8, y + 14);
  }

  _renderEmpty(msg) {
    const ctx = this.ctx;
    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, this.width, this.height);
    ctx.fillStyle = "#606080";
    ctx.font = "14px monospace";
    ctx.fillText(msg, 20, this.height / 2);
  }
}

// Export for both module and browser global usage
if (typeof module !== "undefined" && module.exports) {
  module.exports = LogTrackViewer;
} else {
  window.LogTrackViewer = LogTrackViewer;
}
