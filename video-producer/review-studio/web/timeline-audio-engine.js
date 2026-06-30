/**
 * Clip playback engine — timeline clock derived from audio.currentTime (single authority).
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
    constructor(opts) {
      this.getClips = opts.getClips;
      this.getMasterRate = opts.getMasterRate;
      this.onTimeUpdate = opts.onTimeUpdate || (() => {});
      this.onEnded = opts.onEnded || (() => {});
      this.audio = new Audio();
      this.audio.preload = "auto";
      this._preloadAudio = new Audio();
      this._preloadAudio.preload = "auto";
      this.playing = false;
      this.timelineTime = 0;
      this.totalSec = 0;
      this._raf = 0;
      this._lastFrame = 0;
      this._activeClipId = null;
      this._activeUrl = null;
      this._preloadClipId = null;
      this._preloadUrl = null;
      this._holdingGap = null;
      this._blobUrls = new Map();
      this._warmupPromises = new Map();
      this._warmupGeneration = 0;
      this.audio.addEventListener("ended", () => this._onClipEnded());
      this._preloadAudio.addEventListener("ended", () => this._onClipEnded());
    }

    setTotalSec(sec) {
      this.totalSec = Math.max(0, Number(sec) || 0);
    }

    destroy() {
      this.stop();
      this.audio.src = "";
      this._preloadAudio.src = "";
      this._activeClipId = null;
      this._activeUrl = null;
      this._preloadClipId = null;
      this._preloadUrl = null;
      this._holdingGap = null;
      for (const blobUrl of this._blobUrls.values()) {
        try { URL.revokeObjectURL(blobUrl); } catch { /* ignore */ }
      }
      this._blobUrls.clear();
      this._warmupPromises.clear();
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

    nextClipAfter(t) {
      const clips = this.getClips();
      return clips.find(c => Number(c.start_sec || 0) >= t - 1e-4) || null;
    }

    maxSourceTime(clip) {
      const timelineSrc = Number(clip.duration_sec || 0) * this.clipRate(clip);
      const wavCap = Number(clip.wav_duration_sec) || 0;
      if (wavCap > 0) return Math.min(timelineSrc, wavCap);
      return timelineSrc;
    }

    clipRate(clip) {
      return clampRate(clip?.playback_rate || 1);
    }

    playbackRate(clip) {
      return this.clipRate(clip) * clampRate(this.getMasterRate());
    }

    resolvedUrl(url) {
      return this._blobUrls.get(url) || url;
    }

    async _fetchClipBlob(url, generation) {
      if (!url || this._blobUrls.has(url)) return this._blobUrls.get(url) || url;
      if (this._warmupPromises.has(url)) return this._warmupPromises.get(url);
      const promise = fetch(url)
        .then(res => {
          if (!res.ok) throw new Error(`audio preload failed: ${res.status}`);
          return res.blob();
        })
        .then(blob => {
          if (generation !== this._warmupGeneration) return url;
          const blobUrl = URL.createObjectURL(blob);
          this._blobUrls.set(url, blobUrl);
          return blobUrl;
        })
        .catch(() => url)
        .finally(() => {
          this._warmupPromises.delete(url);
        });
      this._warmupPromises.set(url, promise);
      return promise;
    }

    warmupAll({ concurrency = 3 } = {}) {
      const urls = [...new Set(this.getClips()
        .map(c => c.vo_wav_url || c.vo_wav)
        .filter(Boolean))];
      const generation = ++this._warmupGeneration;
      let idx = 0;
      const workers = Array.from({ length: Math.min(concurrency, urls.length) }, async () => {
        while (idx < urls.length && generation === this._warmupGeneration) {
          const url = urls[idx++];
          await this._fetchClipBlob(url, generation);
        }
      });
      return Promise.allSettled(workers);
    }

    _swapInPreloadedAudio() {
      const old = this.audio;
      this.audio = this._preloadAudio;
      this._preloadAudio = old;
      this._preloadAudio.pause();
      this._preloadAudio.removeAttribute("src");
      this._preloadAudio.load();
      this._preloadClipId = null;
      this._preloadUrl = null;
    }

    globalTimeFromAudio() {
      const clips = this.getClips();
      const clip = clips.find(c => c.beat_id === this._activeClipId);
      if (!clip) return this.timelineTime;
      const start = Number(clip.start_sec || 0);
      const srcT = Number(this.audio.currentTime) || 0;
      return start + srcT / this.clipRate(clip);
    }

    _attachClip(hit, { forceSeek = false } = {}) {
      if (!hit) return;
      const { clip, localT } = hit;
      const originalUrl = clip.vo_wav_url || clip.vo_wav;
      if (!originalUrl) return;
      const url = this.resolvedUrl(originalUrl);
      const rate = this.playbackRate(clip);
      const srcT = localT * this.clipRate(clip);
      const switched = this._activeClipId !== clip.beat_id || this._activeUrl !== url;
      const maxSrc = this.maxSourceTime(clip) || Number(this.audio.duration) || 9999;
      const target = clamp(srcT, 0, Math.max(0, maxSrc));

      const applySeekAndRate = () => {
        this.audio.playbackRate = rate;
        if (switched || forceSeek || Math.abs(this.audio.currentTime - target) > 0.04) {
          try { this.audio.currentTime = target; } catch { /* ignore */ }
        }
        if (this.playing && this.audio.paused) {
          this.audio.play().catch(() => {});
        }
      };

      if (switched) {
        const canUsePreload = this._preloadClipId === clip.beat_id && this._preloadUrl === url;
        if (canUsePreload) {
          this.audio.pause();
          this._swapInPreloadedAudio();
        }
        this._activeClipId = clip.beat_id;
        this._activeUrl = url;
        if (!canUsePreload) {
          this.audio.pause();
          this.audio.src = url;
        }
        if (this.audio.readyState >= 1) {
          applySeekAndRate();
        } else {
          this.audio.addEventListener("loadedmetadata", applySeekAndRate, { once: true });
        }
        return;
      }

      applySeekAndRate();
    }

    _preloadNextClip(currentIdx) {
      const clips = this.getClips();
      if (currentIdx < 0 || currentIdx >= clips.length - 1) return;
      const next = clips[currentIdx + 1];
      const originalUrl = next.vo_wav_url || next.vo_wav;
      const url = this.resolvedUrl(originalUrl);
      if (!url || (this._preloadClipId === next.beat_id && this._preloadUrl === url)) return;
      this._preloadClipId = next.beat_id;
      this._preloadUrl = url;
      this._preloadAudio.pause();
      this._preloadAudio.src = url;
      this._preloadAudio.load();
      if (originalUrl && !this._blobUrls.has(originalUrl)) {
        void this._fetchClipBlob(originalUrl, this._warmupGeneration).then(blobUrl => {
          if (this._preloadClipId !== next.beat_id || this._preloadUrl !== url) return;
          if (!blobUrl || blobUrl === url) return;
          this._preloadUrl = blobUrl;
          this._preloadAudio.src = blobUrl;
          this._preloadAudio.load();
        });
      }
    }

    _scheduleTick() {
      if (this.playing) {
        cancelAnimationFrame(this._raf);
        this._raf = requestAnimationFrame(this._tick);
      }
    }

    _advanceToNext(idx) {
      const clips = this.getClips();
      if (idx >= 0 && idx < clips.length - 1) {
        const next = clips[idx + 1];
        this.timelineTime = Number(next.start_sec || 0);
        this._holdingGap = null;
        this._attachClip(this.findClip(this.timelineTime), { forceSeek: true });
        this.onTimeUpdate(this.timelineTime);
        this._scheduleTick();
        return;
      }
      this.stop();
      this.onEnded();
    }

    _holdUntilNextClip(t) {
      const next = this.nextClipAfter(t);
      if (!next) {
        this.stop();
        this.onEnded();
        return;
      }
      const clips = this.getClips();
      const nextIdx = clips.findIndex(c => c.beat_id === next.beat_id);
      this._activeClipId = null;
      this._activeUrl = null;
      this.audio.pause();
      this.timelineTime = clamp(t, 0, this.totalSec);
      this._holdingGap = { until: Number(next.start_sec || 0), nextIdx };
      this.onTimeUpdate(this.timelineTime);
      this._scheduleTick();
    }

    _onClipEnded() {
      if (!this.playing) return;
      const clips = this.getClips();
      const idx = clips.findIndex(c => c.beat_id === this._activeClipId);
      if (idx < 0) {
        this.stop();
        this.onEnded();
        return;
      }
      const clip = clips[idx];
      const end = Number(clip.start_sec || 0) + Number(clip.duration_sec || 0);
      const t = this.globalTimeFromAudio();
      if (t < end - 0.04) {
        this._holdingGap = { until: end, nextIdx: idx + 1 };
        this.audio.pause();
        this.timelineTime = clamp(t, 0, end);
        this.onTimeUpdate(this.timelineTime);
        this._scheduleTick();
        return;
      }
      this._advanceToNext(idx);
    }

    _tick = () => {
      if (!this.playing) return;
      const now = performance.now();
      const dt = (now - this._lastFrame) / 1000;
      this._lastFrame = now;

      if (this._holdingGap) {
        const master = clampRate(this.getMasterRate());
        this.timelineTime = clamp(this.timelineTime + dt * master, 0, this.totalSec);
        if (this.timelineTime >= this._holdingGap.until - 1e-4) {
          const nextIdx = this._holdingGap.nextIdx;
          this._holdingGap = null;
          if (nextIdx < this.getClips().length) {
            this._advanceToNext(nextIdx - 1);
          } else {
            this.stop();
            this.onEnded();
          }
        }
        this.onTimeUpdate(this.timelineTime);
        this._raf = requestAnimationFrame(this._tick);
        return;
      }

      const clips = this.getClips();
      const idx = clips.findIndex(c => c.beat_id === this._activeClipId);
      const activeClip = idx >= 0 ? clips[idx] : null;
      let t = this.globalTimeFromAudio();

      if (activeClip) {
        const end = Number(activeClip.start_sec || 0) + Number(activeClip.duration_sec || 0);
        const maxSrc = this.maxSourceTime(activeClip);
        const srcT = Number(this.audio.currentTime) || 0;
        if (end - t < 0.45) this._preloadNextClip(idx);

        if (!this.audio.paused && maxSrc > 0 && srcT >= maxSrc - 0.02) {
          this.audio.pause();
          this._advanceToNext(idx);
          return;
        }

        if (t >= end - 0.02) {
          this._advanceToNext(idx);
          return;
        }

        t = clamp(t, Number(activeClip.start_sec || 0), end - 1e-4);
      } else {
        const hit = this.findClip(t);
        if (!hit) {
          const last = clips[clips.length - 1];
          if (last && t >= Number(last.start_sec) + Number(last.duration_sec) - 1e-3) {
            this.stop();
            this.onEnded();
            return;
          }
          t = clamp(t, 0, this.totalSec);
          const retry = this.findClip(t);
          if (!retry) {
            this._holdUntilNextClip(t);
            return;
          }
          this._attachClip(retry, { forceSeek: true });
        } else {
          this._attachClip(hit, { forceSeek: true });
        }
      }

      if (this.audio.paused && !this._holdingGap && activeClip) {
        this.audio.play().catch(() => {});
      }

      this.timelineTime = clamp(t, 0, this.totalSec);
      this.onTimeUpdate(this.timelineTime);
      this._raf = requestAnimationFrame(this._tick);
    };

    seek(t, { autoplay = false } = {}) {
      this._holdingGap = null;
      this.timelineTime = clamp(t, 0, this.totalSec);
      const hit = this.findClip(this.timelineTime);
      this._attachClip(hit, { forceSeek: true });
      if (this.playing || autoplay) {
        if (hit) this.audio.play().catch(() => {});
      } else {
        this.audio.pause();
      }
      this.onTimeUpdate(this.timelineTime);
    }

    play(fromTime) {
      if (fromTime != null) this.timelineTime = clamp(fromTime, 0, this.totalSec);
      let hit = this.findClip(this.timelineTime);
      if (!hit) {
        const first = this.nextClipAfter(this.timelineTime) || this.getClips()[0];
        if (first && Number(first.start_sec || 0) <= this.timelineTime + 1e-4) {
          this.timelineTime = Number(first.start_sec || 0);
        }
        hit = this.findClip(this.timelineTime);
      }
      this._holdingGap = null;
      this.playing = true;
      this._lastFrame = performance.now();
      if (hit) {
        this._attachClip(hit, { forceSeek: true });
      } else {
        this._holdUntilNextClip(this.timelineTime);
      }
      this._scheduleTick();
    }

    pause() {
      this.playing = false;
      this._holdingGap = null;
      cancelAnimationFrame(this._raf);
      this.audio.pause();
    }

    stop() {
      this.pause();
    }

    refreshRates() {
      const hit = this.findClip(this.timelineTime);
      if (hit) this.audio.playbackRate = this.playbackRate(hit.clip);
      if (!this.playing) this.seek(this.timelineTime);
    }
  }

  async function calculatePeaks(url, width) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`waveform fetch failed: ${res.status}`);
    const buf = await res.arrayBuffer();
    const ctx2 = new (window.AudioContext || window.webkitAudioContext)();
    try {
      const audioBuf = await ctx2.decodeAudioData(buf.slice(0));
      const data = audioBuf.getChannelData(0);
      const step = Math.max(1, Math.floor(data.length / width));
      const peaks = new Float32Array(width);
      for (let x = 0; x < width; x++) {
        let min = 1;
        let max = -1;
        const start = x * step;
        for (let i = 0; i < step && start + i < data.length; i++) {
          const v = data[start + i];
          if (v < min) min = v;
          if (v > max) max = v;
        }
        peaks[x] = Math.max(Math.abs(min), Math.abs(max));
      }
      return peaks;
    } finally {
      await ctx2.close();
    }
  }

  function renderPeaks(canvas, peaks, color) {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const w = canvas.width;
    const h = canvas.height;
    const mid = h / 2;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = color;
    for (let x = 0; x < w; x++) {
      const amp = peaks[Math.min(x, peaks.length - 1)] || 0;
      const barH = Math.max(1, amp * mid * 0.92);
      ctx.fillRect(x, mid - barH, 1, barH * 2);
    }
  }

  async function drawClipWaveform(canvas, url, { color = "rgba(10, 132, 255, 0.55)" } = {}) {
    if (!canvas || !url) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    try {
      const peaks = await getPeaks(url, w);
      renderPeaks(canvas, peaks, color);
    } catch {
      ctx.fillStyle = "rgba(118,118,128,0.35)";
      ctx.fillRect(0, h * 0.35, w, h * 0.3);
    }
  }

  const peakCache = new Map();

  function getPeaks(url, width) {
    const key = `${url}::${width}`;
    if (!peakCache.has(key)) peakCache.set(key, calculatePeaks(url, width));
    return peakCache.get(key);
  }

  function drawClipWaveformCached(canvas, url, opts) {
    return drawClipWaveform(canvas, url, opts);
  }

  global.TimelineAudioEngine = TimelineAudioEngine;
  global.TimelineWaveform = { drawClipWaveform: drawClipWaveformCached, MIN_RATE, MAX_RATE, clampRate };
})(window);
