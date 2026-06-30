/**
 * OpenCut-inspired clip playback engine for Review Studio timeline.
 * Plays per-beat WAVs with per-clip and master playback rates; timeline clock via rAF.
 */
(function (global) {
  "use strict";

  const MIN_RATE = 0.25;
  const MAX_RATE = 2.0;

  function clamp(v, lo, hi) {
    return Math.min(hi, Math.max(lo, v));
  }

  function clampRate(r) {
    return clamp(Number(r) || 1, MIN_RATE, MAX_RATE);
  }

  class TimelineAudioEngine {
    /**
     * @param {object} opts
     * @param {() => Array<object>} opts.getClips - enabled clips sorted by start
     * @param {() => number} opts.getMasterRate
     * @param {(t: number) => void} [opts.onTimeUpdate]
     * @param {() => void} [opts.onEnded]
     */
    constructor(opts) {
      this.getClips = opts.getClips;
      this.getMasterRate = opts.getMasterRate;
      this.onTimeUpdate = opts.onTimeUpdate || (() => {});
      this.onEnded = opts.onEnded || (() => {});
      this.audio = new Audio();
      this.audio.preload = "auto";
      this.playing = false;
      this.timelineTime = 0;
      this.totalSec = 0;
      this._raf = 0;
      this._lastFrame = 0;
      this._activeClipId = null;
      this._activeUrl = null;
      this.audio.addEventListener("ended", () => this._onClipEnded());
    }

    setTotalSec(sec) {
      this.totalSec = Math.max(0, Number(sec) || 0);
    }

    destroy() {
      this.stop();
      this.audio.src = "";
      this._activeClipId = null;
      this._activeUrl = null;
    }

    findClip(t) {
      const clips = this.getClips();
      for (const c of clips) {
        const start = Number(c.start_sec || 0);
        const end = start + Number(c.duration_sec || 0);
        if (t >= start && t < end - 1e-4) {
          return { clip: c, start, end, localT: t - start };
        }
      }
      return null;
    }

    clipAudioRate(clip) {
      return clampRate(clip.playback_rate || 1) * clampRate(this.getMasterRate());
    }

    _attachClip(hit) {
      if (!hit) return;
      const { clip, localT } = hit;
      const url = clip.vo_wav_url || clip.vo_wav;
      if (!url) return;
      const rate = this.clipAudioRate(clip);
      const srcT = localT * clampRate(clip.playback_rate || 1);
      if (this._activeClipId !== clip.beat_id || this._activeUrl !== url) {
        this._activeClipId = clip.beat_id;
        this._activeUrl = url;
        this.audio.src = url;
      }
      this.audio.playbackRate = rate;
      const target = clamp(srcT, 0, Math.max(0, this.audio.duration || 9999));
      if (Number.isFinite(target) && Math.abs(this.audio.currentTime - target) > 0.04) {
        try { this.audio.currentTime = target; } catch { /* ignore */ }
      }
    }

    _onClipEnded() {
      if (!this.playing) return;
      const hit = this.findClip(this.timelineTime + 0.02);
      if (hit && hit.clip.beat_id !== this._activeClipId) {
        this._attachClip(hit);
        this.audio.play().catch(() => {});
        return;
      }
      const clips = this.getClips();
      const idx = clips.findIndex(c => c.beat_id === this._activeClipId);
      if (idx >= 0 && idx < clips.length - 1) {
        const next = clips[idx + 1];
        this.timelineTime = Number(next.start_sec || 0);
        this._attachClip(this.findClip(this.timelineTime));
        this.audio.play().catch(() => {});
        this.onTimeUpdate(this.timelineTime);
        return;
      }
      this.stop();
      this.onEnded();
    }

    _tick = () => {
      if (!this.playing) return;
      const now = performance.now();
      const dt = (now - this._lastFrame) / 1000;
      this._lastFrame = now;
      const master = clampRate(this.getMasterRate());
      this.timelineTime = clamp(this.timelineTime + dt * master, 0, this.totalSec);

      const hit = this.findClip(this.timelineTime);
      if (!hit) {
        this.stop();
        this.onEnded();
        return;
      }

      this._attachClip(hit);
      if (this.audio.paused) this.audio.play().catch(() => {});

      const clipRate = clampRate(hit.clip.playback_rate || 1);
      const expectedSrc = hit.localT * clipRate;
      if (Number.isFinite(this.audio.duration) && this.audio.duration > 0) {
        const drift = Math.abs(this.audio.currentTime - expectedSrc);
        if (drift > 0.25) {
          try { this.audio.currentTime = expectedSrc; } catch { /* ignore */ }
        }
      }

      this.onTimeUpdate(this.timelineTime);
      this._raf = requestAnimationFrame(this._tick);
    };

    seek(t, { autoplay = false } = {}) {
      this.timelineTime = clamp(t, 0, this.totalSec);
      const hit = this.findClip(this.timelineTime);
      this._attachClip(hit);
      if (this.playing || autoplay) {
        if (hit) this.audio.play().catch(() => {});
      } else {
        this.audio.pause();
      }
      this.onTimeUpdate(this.timelineTime);
    }

    play(fromTime) {
      if (fromTime != null) this.timelineTime = clamp(fromTime, 0, this.totalSec);
      const hit = this.findClip(this.timelineTime);
      if (!hit) {
        this.timelineTime = this.getClips()[0]?.start_sec || 0;
      }
      this.playing = true;
      this._lastFrame = performance.now();
      this._attachClip(this.findClip(this.timelineTime));
      this.audio.play().catch(() => {});
      cancelAnimationFrame(this._raf);
      this._raf = requestAnimationFrame(this._tick);
    }

    pause() {
      this.playing = false;
      cancelAnimationFrame(this._raf);
      this.audio.pause();
    }

    stop() {
      this.pause();
    }

    refreshRates() {
      if (!this.playing) {
        this.seek(this.timelineTime);
        return;
      }
      this.audio.playbackRate = this.clipAudioRate(this.findClip(this.timelineTime)?.clip || {}) || clampRate(this.getMasterRate());
    }
  }

  /** Draw simplified RMS waveform peaks into a canvas for one clip. */
  async function drawClipWaveform(canvas, url, { color = "rgba(10, 132, 255, 0.55)" } = {}) {
    if (!canvas || !url) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    try {
      const res = await fetch(url);
      const buf = await res.arrayBuffer();
      const ctx2 = new (window.AudioContext || window.webkitAudioContext)();
      const audioBuf = await ctx2.decodeAudioData(buf.slice(0));
      await ctx2.close();
      const data = audioBuf.getChannelData(0);
      const step = Math.max(1, Math.floor(data.length / w));
      const mid = h / 2;
      ctx.fillStyle = color;
      for (let x = 0; x < w; x++) {
        let min = 1;
        let max = -1;
        const start = x * step;
        for (let i = 0; i < step && start + i < data.length; i++) {
          const v = data[start + i];
          if (v < min) min = v;
          if (v > max) max = v;
        }
        const amp = Math.max(Math.abs(min), Math.abs(max));
        const barH = Math.max(1, amp * mid * 0.92);
        ctx.fillRect(x, mid - barH, 1, barH * 2);
      }
    } catch {
      ctx.fillStyle = "rgba(118,118,128,0.35)";
      ctx.fillRect(0, h * 0.35, w, h * 0.3);
    }
  }

  const peakCache = new Map();

  function drawClipWaveformCached(canvas, url, opts) {
    const key = url;
    if (peakCache.has(key)) {
      return peakCache.get(key).then(() => drawClipWaveform(canvas, url, opts));
    }
    const p = drawClipWaveform(canvas, url, opts);
    peakCache.set(key, p);
    return p;
  }

  global.TimelineAudioEngine = TimelineAudioEngine;
  global.TimelineWaveform = { drawClipWaveform: drawClipWaveformCached, MIN_RATE, MAX_RATE, clampRate };
})(window);
