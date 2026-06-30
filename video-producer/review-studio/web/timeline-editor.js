/**
 * Review Studio TimelineEditor — composition seek via window.__timelines.
 * WaveSurfer optional fallback when per-beat WAV clips are unavailable.
 */
(function (global) {
  "use strict";

  const MIN_PX_PER_SEC = 4;
  const MAX_PX_PER_SEC = 240;
  const ZOOM_STEP = 1.25;

  let active = null;

  function formatTime(sec) {
    const s = Math.max(0, Number(sec) || 0);
    const m = Math.floor(s / 60);
    const r = s - m * 60;
    return `${m}:${r.toFixed(2).padStart(5, "0")}`;
  }

  function clamp(v, lo, hi) {
    return Math.min(hi, Math.max(lo, v));
  }

  function escShort(s) {
    const t = String(s || "");
    return t.length > 14 ? `${t.slice(0, 12)}…` : t;
  }

  function destroyActive() {
    if (!active) return;
    if (active.wavesurfer) {
      try { active.wavesurfer.destroy(); } catch { /* ignore */ }
    }
    document.removeEventListener("mousemove", active.onDocMove);
    document.removeEventListener("mouseup", active.onDocUp);
    active = null;
  }

  function buildRulerTicks(totalSec, pxPerSec) {
    const width = totalSec * pxPerSec;
    let step = 1;
    if (pxPerSec < 8) step = 10;
    else if (pxPerSec < 20) step = 5;
    else if (pxPerSec < 50) step = 2;
    else if (pxPerSec > 100) step = 0.5;
    const parts = [];
    for (let t = 0; t <= totalSec + 0.001; t += step) {
      const left = t * pxPerSec;
      const major = Math.abs(t % (step * 5)) < 0.001 || step >= 5;
      parts.push(
        `<span class="tl-tick${major ? " major" : ""}" style="left:${left}px" title="${t.toFixed(1)}s">` +
        `${major ? `<span class="tl-tick-label">${formatTime(t)}</span>` : ""}</span>`
      );
    }
    return `<div class="tl-ruler-ticks" style="width:${width}px">${parts.join("")}</div>`;
  }

  function beatStart(b) {
    return Number(b.vo?.start_sec ?? b.start_sec ?? 0);
  }

  function beatDur(b) {
    return Number(b.vo?.duration_sec ?? b.duration_sec ?? b.actual_sec ?? 1);
  }

  function plannedStart(b) {
    return Number(b.start_sec ?? beatStart(b));
  }

  function plannedDur(b) {
    return Number(b.planned_sec ?? b.duration_sec ?? beatDur(b));
  }

  function defaultPreviewMode(media, preview) {
    if (preview?.composition_ready) return "composition";
    if (media?.render_mp4) return "mp4";
    if (media?.vo_wav) return "audio";
    return "audio";
  }

  function escAttr(s) {
    return String(s || "").replace(/[&<>"']/g, ch => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[ch]));
  }

  function parseResolution(raw) {
    if (!raw) return null;
    if (typeof raw === "object") {
      const width = Number(raw.width || raw.w);
      const height = Number(raw.height || raw.h);
      return width > 0 && height > 0 ? { width, height } : null;
    }
    const m = String(raw).match(/(\d+(?:\.\d+)?)\s*[xX\u00d7]\s*(\d+(?:\.\d+)?)/);
    if (!m) return null;
    const width = Number(m[1]);
    const height = Number(m[2]);
    return width > 0 && height > 0 ? { width, height } : null;
  }

  function parseRatio(raw) {
    const text = String(raw || "").trim();
    const pair = text.match(/(\d+(?:\.\d+)?)\s*[:/]\s*(\d+(?:\.\d+)?)/);
    if (pair) {
      const width = Number(pair[1]);
      const height = Number(pair[2]);
      if (width > 0 && height > 0) return { width, height, value: width / height };
    }
    const numeric = Number(text);
    if (numeric > 0) return { width: numeric, height: 1, value: numeric };
    return { width: 16, height: 9, value: 16 / 9 };
  }

  function previewGeometry(ratioRaw, resolutionRaw) {
    const resolution = parseResolution(resolutionRaw);
    if (resolution) {
      return {
        width: Math.round(resolution.width),
        height: Math.round(resolution.height),
        ratioValue: resolution.width / resolution.height,
        ratioLabel: `${Math.round(resolution.width)}:${Math.round(resolution.height)}`,
      };
    }
    const ratio = parseRatio(ratioRaw);
    const baseLongEdge = 1920;
    const width = ratio.value >= 1 ? baseLongEdge : Math.round(baseLongEdge * ratio.value);
    const height = ratio.value >= 1 ? Math.round(baseLongEdge / ratio.value) : baseLongEdge;
    return {
      width,
      height,
      ratioValue: ratio.value,
      ratioLabel: `${ratio.width}:${ratio.height}`,
    };
  }

  function formatApiError(err) {
    const raw = String(err?.message || err || "");
    try {
      const parsed = JSON.parse(raw);
      const detail = parsed.detail;
      if (detail && typeof detail === "object" && detail.hint) {
        return `${detail.message || detail.hint}\n${detail.hint}${detail.expected_path ? `\n路径: ${detail.expected_path}` : ""}`;
      }
      if (typeof detail === "string") return detail;
    } catch { /* ignore */ }
    return raw || "请求失败";
  }

  function mount(host, options) {
    destroyActive();
    const {
      data,
      segment,
      mediaUrl,
      api,
      selectedBeatId,
      onBeatSelect,
      onBeatOpen,
      onRefresh,
      renderBlocked,
      runPreset,
      pollJob,
      toast,
    } = options;

    const totalSec = Math.max(0.5, Number(data.total_sec) || 1);
    let beats = (data.beats || []).map(b => ({ ...b, vo: { ...(b.vo || {}) } }));
    const microEvents = (data.micro_events || []).slice(0, 500);
    const timelineTracks = data.tracks || [];
    const media = data.media || {};
    const preview = data.preview || {};

    const mp4Src = media.render_mp4 ? mediaUrl(media.render_mp4) : "";
    const voSrc = media.vo_wav ? mediaUrl(media.vo_wav) : "";
    const useClipEngine = beats.some(b => b.vo_wav);
    const compositionUrl = preview.composition_embed_url || `/api/preview/composition/${segment}/index.html`;
    const studioEmbedUrl = preview.studio_embed_url
      || (preview.studio_url ? `${preview.studio_url}/#project/${segment}` : null);

    const SPEED_PRESETS = [0.5, 0.75, 1, 1.25, 1.5, 2];

    const geometry = previewGeometry(data.ratio || options.ratio || "16:9", data.resolution || options.resolution);

    const state = {
      totalSec,
      pxPerSec: 40,
      currentTime: 0,
      playing: false,
      selectedBeatId: selectedBeatId || null,
      drag: null,
      previewMode: defaultPreviewMode(media, preview),
      studioUrl: studioEmbedUrl,
      masterPlaybackRate: Number(data.master_playback_rate || 1),
    };

    host.innerHTML = `
      <div class="tl-editor" id="tl-editor-root">
        <div class="tl-preview-panel card card-no-accent">
          <div class="tl-preview-mode-bar">
            <div class="segmented tl-preview-modes" role="tablist">
              <button type="button" class="segmented-btn tl-mode-btn${state.previewMode === "composition" ? " active" : ""}" data-mode="composition" ${preview.composition_ready ? "" : "disabled"}>合成页</button>
              <button type="button" class="segmented-btn tl-mode-btn${state.previewMode === "mp4" ? " active" : ""}" data-mode="mp4" ${mp4Src ? "" : "disabled"}>成片</button>
              <button type="button" class="segmented-btn tl-mode-btn${state.previewMode === "audio" ? " active" : ""}" data-mode="audio" ${voSrc ? "" : "disabled"}>口播</button>
              <button type="button" class="segmented-btn tl-mode-btn${state.previewMode === "studio" ? " active" : ""}" data-mode="studio" ${preview.composition_ready ? "" : "disabled"}>Studio</button>
            </div>
            <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-reload-preview">刷新预览</button>
          </div>
          <details class="tl-studio-details">
            <summary class="metric">Studio 热重载（高级）</summary>
            ${preview.composition_ready
              ? ""
              : `<p class="blocked">合成页尚未生成 — 请先点击下方「重建合成」，或运行「对齐 + 重建画面」</p>`}
            <div class="tl-studio-actions">
              <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-studio-start" ${preview.studio_running || !preview.composition_ready ? "disabled" : ""} title="${preview.composition_ready ? "启动 HyperFrames Studio" : "需先生成 segments/S001/index.html"}">启动 Studio</button>
              <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-studio-stop" ${preview.studio_running ? "" : "disabled"}>停止 Studio</button>
            </div>
          </details>
          <div class="tl-preview-frame" id="tl-preview-frame" data-ratio="${escAttr(geometry.ratioLabel)}" style="--preview-aspect:${geometry.width} / ${geometry.height}; --preview-ratio-value:${geometry.ratioValue}; --preview-source-width:${geometry.width}px; --preview-source-height:${geometry.height}px; --preview-scale:1">
          <div class="tl-preview-stage" id="tl-preview-stage">
            <iframe id="tl-preview-composition" class="tl-preview-iframe tl-preview-composition-iframe hidden" title="HyperFrames 合成预览" sandbox="allow-scripts allow-same-origin"></iframe>
            <iframe id="tl-preview-studio" class="tl-preview-iframe hidden" title="HyperFrames Studio" sandbox="allow-scripts allow-same-origin allow-popups"></iframe>
            <video id="tl-preview-video" class="tl-preview-video hidden" playsinline preload="metadata"></video>
            <audio id="tl-master-audio" class="hidden" preload="auto"></audio>
            <div id="tl-preview-audio-only" class="tl-preview-audio-only hidden">
              <p class="metric">口播预览 · 使用播放按钮或拖拽下方波形</p>
            </div>
            <div id="tl-preview-empty" class="tl-preview-placeholder hidden"><span>暂无预览媒体</span></div>
          </div>
          </div>
          <div class="tl-transport">
            <button type="button" class="btn btn-secondary btn-icon" id="tl-btn-start" title="回到开头">⏮</button>
            <button type="button" class="btn btn-primary btn-icon" id="tl-btn-play" title="播放/暂停">▶</button>
            <span id="tl-time-display" class="tl-time-display">${formatTime(0)} / ${formatTime(totalSec)}</span>
            <label class="tl-speed-label" title="整体播放速度（OpenCut 式 transport）">整体
              <input type="range" id="tl-master-speed" min="0.25" max="2" step="0.05" value="${state.masterPlaybackRate}" />
              <span id="tl-master-speed-val">${state.masterPlaybackRate.toFixed(2)}×</span>
            </label>
            <label class="tl-zoom-label">缩放
              <input type="range" id="tl-zoom-slider" min="${MIN_PX_PER_SEC}" max="${MAX_PX_PER_SEC}" step="1" value="${state.pxPerSec}" />
            </label>
            <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-fit">适应</button>
            <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-zoom-out">−</button>
            <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-zoom-in">+</button>
          </div>
          <p id="tl-preview-hint" class="metric tl-preview-hint"></p>
          <div id="tl-clip-inspector" class="tl-clip-inspector hidden" aria-label="片段属性">
            <div class="tl-inspector-head">
              <strong id="tl-inspector-beat">—</strong>
              <span id="tl-inspector-dur" class="metric"></span>
            </div>
            <div class="tl-inspector-row">
              <label class="tl-speed-label">片段速度
                <input type="range" id="tl-clip-speed" min="0.25" max="2" step="0.05" value="1" />
                <span id="tl-clip-speed-val">1.00×</span>
              </label>
              <div class="tl-speed-presets" id="tl-clip-speed-presets"></div>
            </div>
            <div class="tl-inspector-actions">
              <button type="button" class="btn btn-secondary btn-compact" id="tl-clip-restore">恢复片段</button>
              <button type="button" class="btn btn-secondary btn-compact" id="tl-clip-delete">删除片段</button>
            </div>
          </div>
        </div>
        <div class="card card-no-accent tl-tracks-card">
          <p class="metric">统一时间轴 · 口播波形与片段同轨 · 灰=计划 · 橙=微事件 · 右键片段可调速度</p>
          <div class="tl-scroll" id="tl-scroll">
            <div class="tl-scroll-inner" id="tl-scroll-inner"></div>
          </div>
          <div class="toolbar">
            <button type="button" class="btn btn-primary" id="tl-btn-lint">时长检查</button>
            <button type="button" class="btn btn-secondary" id="tl-btn-build">重建合成</button>
            <button type="button" class="btn btn-secondary" id="tl-btn-align">重新对齐</button>
            <button type="button" class="btn btn-secondary" id="tl-btn-render" ${renderBlocked ? "disabled" : ""}>草稿渲染</button>
          </div>
          ${renderBlocked ? `<p class="blocked">${renderBlocked}</p>` : ""}
          <pre id="timeline-log" class="vo-log"></pre>
        </div>
      </div>
      <div id="tl-context-menu" class="tl-context-menu hidden" role="menu"></div>`;

    const scrollEl = host.querySelector("#tl-scroll");
    const innerEl = host.querySelector("#tl-scroll-inner");
    const previewFrame = host.querySelector("#tl-preview-frame");
    const previewStage = host.querySelector("#tl-preview-stage");
    const compIframe = host.querySelector("#tl-preview-composition");
    const studioIframe = host.querySelector("#tl-preview-studio");
    const video = host.querySelector("#tl-preview-video");
    const masterAudio = host.querySelector("#tl-master-audio");
    const audioOnlyEl = host.querySelector("#tl-preview-audio-only");
    const emptyEl = host.querySelector("#tl-preview-empty");
    const playBtn = host.querySelector("#tl-btn-play");
    const timeDisplay = host.querySelector("#tl-time-display");
    const zoomSlider = host.querySelector("#tl-zoom-slider");
    const logEl = host.querySelector("#timeline-log");
    const hintEl = host.querySelector("#tl-preview-hint");
    const contextMenu = host.querySelector("#tl-context-menu");
    const clipInspector = host.querySelector("#tl-clip-inspector");
    const masterSpeedInput = host.querySelector("#tl-master-speed");
    const masterSpeedVal = host.querySelector("#tl-master-speed-val");
    const clipSpeedInput = host.querySelector("#tl-clip-speed");
    const clipSpeedVal = host.querySelector("#tl-clip-speed-val");
    const clipSpeedPresets = host.querySelector("#tl-clip-speed-presets");

    let wavesurfer = null;
    let syncingWave = false;
    let waveformVoSrc = "";
    let lastCompSeekMs = 0;
    let lastAutoScrollMs = 0;
    let activeUiBeatId = null;
    let persistTimer = null;
    let rebuildVoTimer = null;
    let masterSettingsTimer = null;

    const clampRate = (r) => (
      global.TimelineWaveform?.clampRate
        ? global.TimelineWaveform.clampRate(r)
        : clamp(Number(r) || 1, 0.25, 2)
    );

    function beatById(id) {
      return beats.find(b => b.beat_id === id);
    }

    function ensureBeatEditFields(b) {
      const vo = b.vo || {};
      const wavDur = Number(b.wav_duration_sec || vo.wav_duration_sec || 0);
      if (!b.source_duration_sec && !vo.source_duration_sec) {
        if (wavDur > 0) {
          b.source_duration_sec = wavDur;
        } else {
          const dur = Number(vo.duration_sec || b.actual_sec || b.duration_sec || 0);
          const rate = clampRate(b.playback_rate || vo.playback_rate || 1);
          b.source_duration_sec = dur * rate;
        }
      } else if (wavDur > 0) {
        b.source_duration_sec = Number(b.source_duration_sec || vo.source_duration_sec || wavDur);
      }
      b.playback_rate = clampRate(b.playback_rate ?? vo.playback_rate ?? 1);
      b.disabled = Boolean(b.disabled ?? vo.disabled);
      return b;
    }

    function syncTimelineFromServer() {
      for (const raw of beats) ensureBeatEditFields(raw);
      const fromApi = Number(data.total_sec || 0);
      if (fromApi > 0) {
        state.totalSec = fromApi;
      } else {
        let t = 0;
        for (const b of beats) {
          if (b.disabled) continue;
          t += beatDur(b);
        }
        state.totalSec = Math.max(0.5, round3(t));
      }
      timeDisplay.textContent = `${formatTime(state.currentTime)} / ${formatTime(state.totalSec)}`;
      if (audioEngine) audioEngine.setTotalSec(state.totalSec);
    }

    function recomputeLocalTimeline() {
      let t = 0;
      for (const raw of beats) {
        const b = ensureBeatEditFields(raw);
        const vo = b.vo || {};
        if (b.disabled) {
          vo.start_sec = t;
          vo.duration_sec = 0;
          vo.end_sec = t;
          vo.disabled = true;
          b.vo = vo;
          b.actual_sec = 0;
          continue;
        }
        const currentDur = Number(vo.duration_sec || b.duration_sec || b.actual_sec || 0);
        const src = Number(b.source_duration_sec || vo.source_duration_sec || b.wav_duration_sec || currentDur || 1);
        const rate = clampRate(b.playback_rate);
        const dur = currentDur > 0 ? currentDur : src / rate;
        vo.start_sec = round3(t);
        vo.duration_sec = round3(dur);
        vo.end_sec = round3(t + dur);
        vo.playback_rate = rate;
        vo.source_duration_sec = round3(src);
        vo.disabled = false;
        b.vo = vo;
        b.playback_rate = rate;
        b.source_duration_sec = src;
        b.actual_sec = dur;
        t += dur;
      }
      state.totalSec = Math.max(0.5, round3(t));
      timeDisplay.textContent = `${formatTime(state.currentTime)} / ${formatTime(state.totalSec)}`;
      if (audioEngine) audioEngine.setTotalSec(state.totalSec);
    }

    function round3(n) {
      return Math.round(Number(n) * 1000) / 1000;
    }

    function getEnabledClips() {
      return beats
        .filter(b => !b.disabled && b.vo_wav)
        .map(b => {
          ensureBeatEditFields(b);
          return {
            beat_id: b.beat_id,
            start_sec: beatStart(b),
            duration_sec: beatDur(b),
            playback_rate: clampRate(b.playback_rate),
            wav_duration_sec: Number(b.wav_duration_sec || b.vo?.source_duration_sec || 0) || undefined,
            vo_wav_url: mediaUrl(b.vo_wav),
          };
        })
        .sort((a, b) => a.start_sec - b.start_sec);
    }

    function applyTimelineLocally({ rerender = true } = {}) {
      recomputeLocalTimeline();
      if (rerender) {
        renderTracks();
        updateClipInspector();
      }
      if (audioEngine) {
        audioEngine.setTotalSec(state.totalSec);
        audioEngine.refreshRates();
        void audioEngine.warmupAll?.();
        if (!state.playing) audioEngine.seek(state.currentTime);
      }
    }

    function schedulePersistBeat(beatId, patch) {
      clearTimeout(persistTimer);
      persistTimer = setTimeout(async () => {
        try {
          await api(`/timing/beats/${beatId}?segment=${segment}`, {
            method: "PATCH",
            body: JSON.stringify(patch),
          });
          scheduleRebuildVo();
        } catch (err) {
          toast(String(err.message || err));
        }
      }, 400);
    }

    function schedulePersistMasterRate() {
      clearTimeout(masterSettingsTimer);
      masterSettingsTimer = setTimeout(async () => {
        try {
          await api(`/timeline/settings?segment=${segment}`, {
            method: "PATCH",
            body: JSON.stringify({ master_playback_rate: state.masterPlaybackRate }),
          });
        } catch (err) {
          toast(String(err.message || err));
        }
      }, 350);
    }

    function scheduleRebuildVo() {
      clearTimeout(rebuildVoTimer);
      rebuildVoTimer = setTimeout(async () => {
        try {
          await api(`/timeline/rebuild-vo?segment=${segment}`, { method: "POST" });
          waveformVoSrc = "";
          drawAudioWaveforms();
        } catch { /* optional background rebuild */ }
      }, 1400);
    }

    function setBeatSpeed(beatId, rate, { persist = true } = {}) {
      const b = beatById(beatId);
      if (!b || b.disabled) return;
      ensureBeatEditFields(b);
      b.playback_rate = clampRate(rate);
      applyTimelineLocally();
      if (persist) schedulePersistBeat(beatId, { playback_rate: b.playback_rate, locked: true });
    }

    function setBeatDisabled(beatId, disabled) {
      const b = beatById(beatId);
      if (!b) return;
      b.disabled = disabled;
      applyTimelineLocally();
      schedulePersistBeat(beatId, { disabled, locked: true });
      toast(disabled ? `${beatId} 已从时间轴移除` : `${beatId} 已恢复`);
    }

    let audioEngine = null;
    if (useClipEngine && global.TimelineAudioEngine) {
      audioEngine = new global.TimelineAudioEngine({
        getClips: getEnabledClips,
        getMasterRate: () => state.masterPlaybackRate,
        onTimeUpdate: (t) => {
          if (!state.playing) return;
          updatePlayheadUI(t);
          syncCompositionVisual(t);
          maybeAutoScroll(t);
        },
        onEnded: () => {
          state.playing = false;
          playBtn.textContent = "▶";
        },
      });
      audioEngine.setTotalSec(state.totalSec);
      void audioEngine.warmupAll?.();
    }

    function updatePlayheadUI(t) {
      state.currentTime = clamp(t, 0, state.totalSec);
      const playhead = innerEl?.querySelector("#tl-playhead");
      if (playhead) playhead.style.left = `${timeToPlayheadPx(state.currentTime)}px`;
      timeDisplay.textContent = `${formatTime(state.currentTime)} / ${formatTime(state.totalSec)}`;
      const nextBeatId = activeBeatIdAt(state.currentTime);
      if (nextBeatId === activeUiBeatId) return;
      innerEl?.querySelectorAll(".tl-block-active").forEach(el => el.classList.remove("tl-block-active"));
      if (nextBeatId) queryBeatBlock(nextBeatId)?.classList.add("tl-block-active");
      activeUiBeatId = nextBeatId;
    }

    function syncCompositionVisual(t) {
      if (state.previewMode !== "composition" || !state.playing) return;
      const now = performance.now();
      if (now - lastCompSeekMs < 250) return;
      lastCompSeekMs = now;
      seekComposition(t, { pause: false });
    }

    function maybeAutoScroll(t) {
      const now = performance.now();
      if (now - lastAutoScrollMs < 250) return;
      lastAutoScrollMs = now;
      scrollTimeIntoView(t);
    }

    function onAudioTimeUpdate() {
      if (!state.playing || active?.drag) return;
      if (state.previewMode === "mp4") return;
      if (audioEngine) return;
      const t = masterAudio.currentTime;
      if (Math.abs(t - state.currentTime) < 0.015) return;
      updatePlayheadUI(t);
      syncCompositionVisual(t);
      maybeAutoScroll(t);
    }

    function gsapTimeline() {
      if (state.previewMode !== "composition" || !compIframe) return null;
      try {
        return compIframe.contentWindow?.__timelines?.[segment] || null;
      } catch {
        return null;
      }
    }

    function masterEl() {
      if (state.previewMode === "mp4") return video;
      if (audioEngine) return null;
      if (voSrc && masterAudio) return masterAudio;
      return null;
    }

    function muteIframeMedia(iframe) {
      if (!iframe) return;
      try {
        const doc = iframe.contentDocument;
        if (!doc) return;
        doc.querySelectorAll("audio, video").forEach(el => {
          el.muted = true;
          el.volume = 0;
          el.pause();
        });
      } catch { /* ignore */ }
    }

    function secToPx(sec) {
      return sec * state.pxPerSec;
    }

    function pxToSec(px) {
      return px / state.pxPerSec;
    }

    /** Left gutter for track labels — must match .tl-scroll-inner padding-left. */
    function labelGutterPx() {
      if (!innerEl) return 52;
      const v = parseFloat(getComputedStyle(innerEl).paddingLeft);
      return Number.isFinite(v) ? v : 52;
    }

    /** Playhead / scroll hit-test X: gutter + timeline content pixels. */
    function timeToPlayheadPx(sec) {
      return labelGutterPx() + secToPx(sec);
    }

    function playheadPxToTime(px) {
      return pxToSec(px - labelGutterPx());
    }

    function pointerXInInner(ev) {
      const innerRect = innerEl.getBoundingClientRect();
      return ev.clientX - innerRect.left + scrollEl.scrollLeft;
    }

    function activeBeatIdAt(t) {
      for (const b of beats) {
        if (b.disabled) continue;
        const start = beatStart(b);
        const end = start + beatDur(b);
        if (t >= start && t < end) return b.beat_id;
      }
      return null;
    }

    function queryBeatBlock(beatId) {
      const id = global.CSS?.escape ? global.CSS.escape(String(beatId)) : String(beatId).replace(/"/g, '\\"');
      return innerEl?.querySelector(`.tl-audio-clip[data-beat="${id}"]:not(.tl-block-disabled)`) || null;
    }

    function updatePreviewHint() {
      const hints = {
        composition: "合成页画面 + 分片段口播预览 · 右键片段可调速度/删除 · 整体速度在 transport",
        mp4: "成片 MP4 · 整体速度影响播放 · 片段编辑请切「口播」或「合成页」",
        audio: "分片段口播预览 · 拖拽蓝条右缘 trim · Del 删除选中片段",
        studio: "Studio 画面 + 分片段口播 · 合成内音频静音",
      };
      hintEl.textContent = hints[state.previewMode] || "";
    }

    function updateCompositionScale() {
      if (!previewStage || !previewFrame) return;
      const frameRect = previewFrame.getBoundingClientRect();
      const maxStageHeight = Math.min(global.innerHeight * 0.52, 480);
      const ratioValue = geometry.width / geometry.height;
      const stageWidth = Math.min(frameRect.width || geometry.width, maxStageHeight * ratioValue);
      const stageHeight = stageWidth / ratioValue;
      if (stageWidth > 0 && stageHeight > 0) {
        previewStage.style.width = `${stageWidth}px`;
        previewStage.style.height = `${stageHeight}px`;
      }
      const rect = previewStage.getBoundingClientRect();
      if (!rect.width || !rect.height || !geometry.width || !geometry.height) return;
      const scale = Math.min(rect.width / geometry.width, rect.height / geometry.height);
      previewFrame.style.setProperty("--preview-scale", String(Math.max(0.01, scale)));
    }

    function hideAllPreview() {
      compIframe.classList.add("hidden");
      studioIframe.classList.add("hidden");
      video.classList.add("hidden");
      audioOnlyEl.classList.add("hidden");
      emptyEl.classList.add("hidden");
    }

    function applyPreviewMode() {
      hideAllPreview();
      host.querySelectorAll(".tl-mode-btn").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.mode === state.previewMode);
      });

      if (state.previewMode === "composition" && preview.composition_ready) {
        compIframe.classList.remove("hidden");
        if (!compIframe.src || !compIframe.src.includes("/api/preview/composition/")) {
          compIframe.src = `${compositionUrl}?v=${Date.now()}`;
        }
        updateCompositionScale();
      } else if (state.previewMode === "mp4" && mp4Src) {
        video.classList.remove("hidden");
        if (video.src !== mp4Src) video.src = mp4Src;
      } else if (state.previewMode === "audio" && voSrc) {
        audioOnlyEl.classList.remove("hidden");
        if (masterAudio.src !== voSrc) masterAudio.src = voSrc;
      } else if (state.previewMode === "studio") {
        if (state.studioUrl) {
          studioIframe.classList.remove("hidden");
          const base = state.studioUrl.split("#")[0].replace(/\/?$/, "/");
          studioIframe.src = `${base}?v=${Date.now()}#project/${segment}`;
        } else {
          emptyEl.classList.remove("hidden");
          emptyEl.querySelector("span").textContent = "请展开「Studio 热重载」并点击启动";
        }
      } else {
        emptyEl.classList.remove("hidden");
        emptyEl.querySelector("span").textContent = preview.composition_ready
          ? "选择预览模式"
          : voSrc
            ? "已选口播预览 · 可切换成片/合成页"
            : "暂无口播 · 请先在「口播 & 配音」生成 WAV";
      }
      updatePreviewHint();
      pauseAll();
    }

    function pauseAll() {
      state.playing = false;
      playBtn.textContent = "▶";
      try {
        const tl = gsapTimeline();
        if (tl) tl.pause();
      } catch { /* ignore */ }
      if (video && !video.paused) video.pause();
      if (audioEngine) audioEngine.pause();
      if (masterAudio && !masterAudio.paused) masterAudio.pause();
    }

    function seekComposition(t, { pause = true } = {}) {
      const tl = gsapTimeline();
      if (!tl) return false;
      try {
        tl.time(clamp(t, 0, state.totalSec));
        if (pause) tl.pause();
        return true;
      } catch {
        return false;
      }
    }

    function scrollTimeIntoView(t) {
      const x = timeToPlayheadPx(t);
      if (!scrollEl) return;
      const pad = scrollEl.clientWidth * 0.25;
      if (x < scrollEl.scrollLeft + pad || x > scrollEl.scrollLeft + scrollEl.clientWidth - pad) {
        scrollEl.scrollLeft = Math.max(0, x - scrollEl.clientWidth * 0.35);
      }
    }

    function setCurrentTime(t, { fromMedia = false } = {}) {
      updatePlayheadUI(t);
      if (fromMedia || state.playing) return;
      if (state.previewMode === "composition") {
        seekComposition(state.currentTime, { pause: true });
      }
      if (audioEngine) {
        audioEngine.seek(state.currentTime);
        return;
      }
      const m = masterEl();
      if (m && Math.abs(m.currentTime - state.currentTime) > 0.05) {
        m.currentTime = state.currentTime;
      }
      syncWaveform();
    }

    function renderTracks() {
      const width = secToPx(state.totalSec);

      const plannedBlocks = beats.map(b => {
        const pStart = plannedStart(b);
        const pDur = plannedDur(b);
        return `<div class="tl-block planned" style="left:${secToPx(pStart)}px;width:${Math.max(secToPx(pDur), 2)}px" title="planned ${b.beat_id}"></div>`;
      }).join("");

      const audioBlocks = beats.map(b => {
        if (b.disabled) {
          return `<div class="tl-block tl-block-disabled tl-audio-clip" data-beat="${b.beat_id}" title="${b.beat_id} 已删除（可恢复）">${b.beat_id}</div>`;
        }
        const start = beatStart(b);
        const dur = beatDur(b);
        const sel = state.selectedBeatId === b.beat_id ? " selected" : "";
        const rate = clampRate(b.playback_rate || 1);
        const rateBadge = Math.abs(rate - 1) > 0.01 ? `<span class="tl-rate-badge">${rate.toFixed(2)}×</span>` : "";
        const wavWarn = b.wav_duration_sec && Math.abs(Number(b.source_duration_sec || 0) - Number(b.wav_duration_sec)) > 0.08
          ? " tl-wav-mismatch" : "";
        return `<div class="tl-block tl-audio-clip${sel}${wavWarn}" data-beat="${b.beat_id}" data-start="${start}" data-dur="${dur}"
          style="left:${secToPx(start)}px;width:${Math.max(secToPx(dur), 4)}px" title="${b.beat_id} ${dur.toFixed(2)}s @ ${rate.toFixed(2)}×">
          <canvas class="tl-wav-canvas" data-beat-canvas="${b.beat_id}" height="48"></canvas>
          <span class="tl-clip-label">${b.beat_id}${rateBadge}</span>
        </div>`;
      }).join("");

      const micro = microEvents.map(ev => {
        const t = Number(ev.t || 0);
        const eid = ev.id || ev.event_id || "";
        return `<span class="tl-micro" data-event="${eid}" data-t="${t}" style="left:${secToPx(t)}px" title="${eid} @ ${t}s"></span>`;
      }).join("");

      const trackById = Object.fromEntries(timelineTracks.map(tr => [tr.id, tr]));
      const videoTrack = trackById.V1;
      const assetTrack = trackById.V2;
      const eventTrack = trackById.E1;

      const videoBlocks = (videoTrack?.clips || []).map(c => {
        const w = Math.max(secToPx(Number(c.end) - Number(c.start)), 4);
        return `<div class="tl-block tl-scene-clip" data-beat="${c.beat_id || ""}" data-start="${c.start}" data-dur="${Number(c.end) - Number(c.start)}"
          style="left:${secToPx(c.start)}px;width:${w}px" title="${c.label || c.beat_id}">${escShort(c.label || c.beat_id)}</div>`;
      }).join("");

      const assetBlocks = (assetTrack?.clips || []).map(c => {
        const w = Math.max(secToPx(Number(c.end) - Number(c.start)), 3);
        const cls = c.programmatic ? "tl-asset-clip tl-asset-programmatic" : "tl-asset-clip";
        return `<div class="${cls}" data-asset="${c.id}" style="left:${secToPx(c.start)}px;width:${w}px" title="${c.id} · ${c.role || ""}">${escShort(c.id)}</div>`;
      }).join("");

      const eventBlocks = (eventTrack?.clips || []).map(c => {
        const w = Math.max(secToPx(Number(c.end) - Number(c.start)), 3);
        return `<div class="tl-event-clip" data-event="${c.id}" data-t="${c.start}" style="left:${secToPx(c.start)}px;width:${w}px" title="${c.visual_action || c.id}">${escShort(c.id)}</div>`;
      }).join("");

      innerEl.innerHTML = `
        ${buildRulerTicks(state.totalSec, state.pxPerSec)}
        <div class="tl-track tl-track-planned" style="width:${width}px"><div class="tl-track-label">计划</div>${plannedBlocks}</div>
        <div class="tl-track tl-track-audio" style="width:${width}px"><div class="tl-track-label">口播</div>${audioBlocks}</div>
        ${videoBlocks ? `<div class="tl-track tl-track-video" style="width:${width}px"><div class="tl-track-label">画面</div>${videoBlocks}</div>` : ""}
        ${assetBlocks ? `<div class="tl-track tl-track-assets" style="width:${width}px"><div class="tl-track-label">素材</div>${assetBlocks}</div>` : ""}
        ${eventBlocks ? `<div class="tl-track tl-track-events" style="width:${width}px"><div class="tl-track-label">事件</div>${eventBlocks}</div>` : ""}
        ${!eventBlocks ? `<div class="tl-track tl-track-micro" style="width:${width}px"><div class="tl-track-label">微事件</div>${micro}</div>` : ""}
        <div class="tl-playhead" id="tl-playhead" style="left:${timeToPlayheadPx(state.currentTime)}px"></div>`;

      activeUiBeatId = null;
      bindTrackEvents();
      drawAudioWaveforms();
      if (state.playing) updatePlayheadUI(state.currentTime);
      else setCurrentTime(state.currentTime);
    }

    function drawAudioWaveforms() {
      if (!useClipEngine || !global.TimelineWaveform) return;
      if (state.playing) return;
      innerEl.querySelectorAll("canvas[data-beat-canvas]").forEach(canvas => {
        const beatId = canvas.dataset.beatCanvas;
        const b = beatById(beatId);
        if (!b?.vo_wav) return;
        const block = canvas.closest(".tl-audio-clip");
        const w = Math.max(24, Math.floor(block?.offsetWidth || secToPx(beatDur(b))));
        canvas.width = w;
        canvas.height = 48;
        global.TimelineWaveform.drawClipWaveform(canvas, mediaUrl(b.vo_wav), {
          color: state.selectedBeatId === beatId
            ? "rgba(10, 132, 255, 0.85)"
            : "rgba(10, 132, 255, 0.42)",
        });
      });
    }

    function syncWaveform() {
      if (!wavesurfer || !state.totalSec || state.playing) return;
      syncingWave = true;
      try {
        wavesurfer.setTime(state.currentTime);
      } catch { /* ignore */ }
      syncingWave = false;
    }

    /** Optional WaveSurfer fallback when clip engine is unavailable. */
    function initOrUpdateWaveformFallback() {
      if (!voSrc || !global.WaveSurfer || !innerEl || !masterAudio) return;
      void wavesurfer;
    }

    function bindWaveformEvents() {
      if (!wavesurfer) return;
      wavesurfer.on("interaction", () => {
        if (syncingWave || state.playing) return;
        setCurrentTime(wavesurfer.getCurrentTime());
        scrollTimeIntoView(state.currentTime);
      });
      wavesurfer.on("finish", () => {
        state.playing = false;
        playBtn.textContent = "▶";
      });
    }

    function fitZoom() {
      if (!scrollEl) return;
      const w = Math.max(scrollEl.clientWidth - labelGutterPx() - 8, 200);
      state.pxPerSec = clamp(w / state.totalSec, MIN_PX_PER_SEC, MAX_PX_PER_SEC);
      zoomSlider.value = String(Math.round(state.pxPerSec));
      renderTracks();
    }

    function setZoom(pxPerSec) {
      state.pxPerSec = clamp(pxPerSec, MIN_PX_PER_SEC, MAX_PX_PER_SEC);
      zoomSlider.value = String(Math.round(state.pxPerSec));
      renderTracks();
    }

    function playVo() {
      if (audioEngine) {
        if (state.previewMode === "composition") seekComposition(state.currentTime, { pause: true });
        audioEngine.play(state.currentTime);
        return Promise.resolve();
      }
      return masterAudio.play().catch(() => toast("无法播放口播"));
    }

    function togglePlay() {
      if (state.previewMode === "composition") {
        muteIframeMedia(compIframe);
        if (!useClipEngine && !voSrc) {
          toast("口播 WAV 未就绪");
          return;
        }
        if (state.playing) {
          pauseAll();
          return;
        }
        seekComposition(state.currentTime, { pause: true });
        playVo();
        state.playing = true;
        playBtn.textContent = "⏸";
        return;
      }

      if (state.previewMode === "studio") {
        muteIframeMedia(studioIframe);
        if (!useClipEngine && !voSrc) {
          toast("口播 WAV 未就绪");
          return;
        }
        if (state.playing) {
          pauseAll();
          return;
        }
        playVo();
        state.playing = true;
        playBtn.textContent = "⏸";
        return;
      }

      if (state.previewMode === "mp4" && mp4Src && video) {
        if (state.playing) {
          video.pause();
          state.playing = false;
          playBtn.textContent = "▶";
        } else {
          video.play().catch(() => toast("无法播放成片"));
          state.playing = true;
          playBtn.textContent = "⏸";
        }
        return;
      }

      if ((useClipEngine || voSrc) && (audioEngine || masterAudio)) {
        if (state.playing) {
          pauseAll();
        } else {
          playVo();
          state.playing = true;
          playBtn.textContent = "⏸";
        }
        return;
      }

      toast("无预览媒体");
    }

    function reloadPreview() {
      pauseAll();
      if (state.previewMode === "composition") {
        compIframe.src = `${compositionUrl}?v=${Date.now()}`;
      } else if (state.previewMode === "studio" && state.studioUrl) {
        const base = state.studioUrl.split("#")[0].replace(/\/?$/, "/");
        studioIframe.src = `${base}?v=${Date.now()}#project/${segment}`;
      } else if (state.previewMode === "mp4" && mp4Src) {
        video.src = `${mp4Src}${mp4Src.includes("?") ? "&" : "?"}v=${Date.now()}`;
      }
      toast("预览已刷新");
    }

    function onDocMove(ev) {
      if (!active?.drag) return;
      const d = active.drag;
      const xInInner = pointerXInInner(ev);

      if (d.type === "beat-resize") {
        const newDur = Math.max(0.2, playheadPxToTime(xInInner) - d.startSec);
        d.newDur = newDur;
        d.block.style.width = `${Math.max(secToPx(newDur), 4)}px`;
      } else if (d.type === "micro-drag") {
        const newT = clamp(playheadPxToTime(xInInner), 0, state.totalSec);
        d.newT = newT;
        d.el.style.left = `${secToPx(newT)}px`;
      } else if (d.type === "playhead") {
        setCurrentTime(playheadPxToTime(xInInner));
        scrollTimeIntoView(state.currentTime);
      }
    }

    async function onDocUp() {
      if (!active?.drag) return;
      const d = active.drag;
      active.drag = null;
      document.body.classList.remove("tl-dragging");

      try {
        if (d.type === "beat-resize" && d.newDur != null) {
          const b = beatById(d.beatId);
          if (b && !b.disabled) {
            ensureBeatEditFields(b);
            const vo = b.vo || {};
            vo.duration_sec = round3(d.newDur);
            vo.end_sec = round3(Number(vo.start_sec || b.start_sec || 0) + d.newDur);
            b.vo = vo;
            b.duration_sec = round3(d.newDur);
            b.actual_sec = round3(d.newDur);
            applyTimelineLocally();
            schedulePersistBeat(d.beatId, { duration_sec: d.newDur, locked: true });
            toast(`${d.beatId} → ${d.newDur.toFixed(2)}s（实时预览）· 重建合成以更新画面`);
          }
        } else if (d.type === "micro-drag" && d.newT != null) {
          await api(`/timing/micro/${d.eventId}?segment=${segment}`, {
            method: "PATCH",
            body: JSON.stringify({ t: d.newT }),
          });
          toast(`微事件 ${d.eventId} → ${d.newT.toFixed(2)}s · 请重建合成以更新画面`);
          if (onRefresh) await onRefresh();
        }
      } catch (err) {
        toast(String(err.message || err));
        applyTimelineLocally();
      }
    }

    function hideContextMenu() {
      contextMenu?.classList.add("hidden");
    }

    function showContextMenu(ev, beatId) {
      if (!contextMenu) return;
      ev.preventDefault();
      const b = beatById(beatId);
      if (!b) return;
      state.selectedBeatId = beatId;
      updateClipInspector();
      innerEl?.querySelectorAll(".tl-block.selected").forEach(el => el.classList.remove("selected"));
      innerEl?.querySelector(`[data-beat="${beatId}"]`)?.classList.add("selected");
      if (onBeatSelect) onBeatSelect(beatId);

      const disabled = Boolean(b.disabled);
      const rate = clampRate(b.playback_rate || 1);
      const speedItems = SPEED_PRESETS.map(r =>
        `<button type="button" class="tl-menu-item${Math.abs(r - rate) < 0.01 ? " active" : ""}" data-action="speed" data-rate="${r}">${r}× 速度</button>`
      ).join("");
      contextMenu.innerHTML = `
        <div class="tl-menu-title">${beatId}${disabled ? " · 已删除" : ""}</div>
        ${disabled ? `<button type="button" class="tl-menu-item" data-action="restore">恢复片段</button>` : `
          ${speedItems}
          <button type="button" class="tl-menu-item tl-menu-danger" data-action="delete">删除片段 (Del)</button>
        `}`;
      contextMenu.classList.remove("hidden");
      const pad = 4;
      contextMenu.style.left = `${ev.clientX + pad}px`;
      contextMenu.style.top = `${ev.clientY + pad}px`;
      contextMenu.querySelectorAll("[data-action]").forEach(btn => {
        btn.addEventListener("click", () => {
          const action = btn.dataset.action;
          if (action === "delete") setBeatDisabled(beatId, true);
          if (action === "restore") setBeatDisabled(beatId, false);
          if (action === "speed") setBeatSpeed(beatId, Number(btn.dataset.rate));
          hideContextMenu();
        });
      });
    }

    function updateClipInspector() {
      if (!clipInspector) return;
      const b = state.selectedBeatId ? beatById(state.selectedBeatId) : null;
      if (!b) {
        clipInspector.classList.add("hidden");
        return;
      }
      clipInspector.classList.remove("hidden");
      host.querySelector("#tl-inspector-beat").textContent = b.beat_id + (b.disabled ? " · 已删除" : "");
      const dur = b.disabled ? 0 : beatDur(b);
      host.querySelector("#tl-inspector-dur").textContent = b.disabled
        ? "不在时间轴上"
        : `${dur.toFixed(2)}s · 源 ${Number(b.source_duration_sec || dur).toFixed(2)}s`;
      const rate = clampRate(b.playback_rate || 1);
      clipSpeedInput.value = String(rate);
      clipSpeedVal.textContent = `${rate.toFixed(2)}×`;
      host.querySelector("#tl-clip-delete").classList.toggle("hidden", b.disabled);
      host.querySelector("#tl-clip-restore").classList.toggle("hidden", !b.disabled);
      clipSpeedInput.disabled = b.disabled;
    }

    function bindTrackEvents() {
      innerEl.querySelectorAll(".tl-audio-clip:not(.planned)").forEach(block => {
        block.addEventListener("mousedown", (ev) => {
          if (ev.button !== 0) return;
          const beatId = block.dataset.beat;
          const b = beatById(beatId);
          if (b?.disabled) {
            state.selectedBeatId = beatId;
            updateClipInspector();
            ev.preventDefault();
            return;
          }
          const start = parseFloat(block.dataset.start || "0");
          const dur = parseFloat(block.dataset.dur || "0");
          const rect = block.getBoundingClientRect();
          const onEdge = ev.clientX > rect.right - 10;

          if (onEdge) {
            active.drag = { type: "beat-resize", beatId, startSec: start, block, newDur: dur };
            document.body.classList.add("tl-dragging");
            ev.preventDefault();
            ev.stopPropagation();
            return;
          }

          state.selectedBeatId = beatId;
          innerEl.querySelectorAll(".tl-block.selected").forEach(el => el.classList.remove("selected"));
          block.classList.add("selected");
          setCurrentTime(start);
          scrollTimeIntoView(start);
          updateClipInspector();
          drawAudioWaveforms();
          if (onBeatSelect) onBeatSelect(beatId);
          ev.preventDefault();
        });
        block.addEventListener("contextmenu", (ev) => showContextMenu(ev, block.dataset.beat));
        block.addEventListener("dblclick", (ev) => {
          if (onBeatOpen) onBeatOpen(block.dataset.beat);
          ev.preventDefault();
        });
      });

      innerEl.querySelectorAll(".tl-event-clip, .tl-asset-clip").forEach(el => {
        el.addEventListener("click", (ev) => {
          const t = parseFloat(el.dataset.t || el.style.left) || 0;
          const start = el.dataset.t != null ? parseFloat(el.dataset.t) : pxToSec(parseFloat(el.style.left) || 0);
          setCurrentTime(start);
          scrollTimeIntoView(start);
          ev.stopPropagation();
        });
      });

      innerEl.querySelectorAll(".tl-micro").forEach(el => {
        el.addEventListener("mousedown", (ev) => {
          active.drag = {
            type: "micro-drag",
            eventId: el.dataset.event,
            el,
            newT: parseFloat(el.dataset.t || "0"),
          };
          document.body.classList.add("tl-dragging");
          ev.preventDefault();
          ev.stopPropagation();
        });
      });

      scrollEl.addEventListener("mousedown", (ev) => {
        if (ev.target.closest(".tl-block") || ev.target.closest(".tl-micro")) return;
        if (state.playing) pauseAll();
        hideContextMenu();
        setCurrentTime(playheadPxToTime(pointerXInInner(ev)));
        active.drag = { type: "playhead" };
        document.body.classList.add("tl-dragging");
        ev.preventDefault();
      });
    }

    if (clipSpeedPresets) {
      clipSpeedPresets.innerHTML = SPEED_PRESETS.map(r =>
        `<button type="button" class="btn btn-secondary btn-compact tl-speed-preset" data-rate="${r}">${r}×</button>`
      ).join("");
      clipSpeedPresets.querySelectorAll(".tl-speed-preset").forEach(btn => {
        btn.addEventListener("click", () => {
          if (!state.selectedBeatId) return;
          setBeatSpeed(state.selectedBeatId, Number(btn.dataset.rate));
          updateClipInspector();
        });
      });
    }

    clipSpeedInput?.addEventListener("input", () => {
      if (!state.selectedBeatId) return;
      const rate = clampRate(parseFloat(clipSpeedInput.value));
      clipSpeedVal.textContent = `${rate.toFixed(2)}×`;
      setBeatSpeed(state.selectedBeatId, rate, { persist: false });
    });
    clipSpeedInput?.addEventListener("change", () => {
      if (!state.selectedBeatId) return;
      schedulePersistBeat(state.selectedBeatId, {
        playback_rate: clampRate(parseFloat(clipSpeedInput.value)),
        locked: true,
      });
    });

    masterSpeedInput?.addEventListener("input", () => {
      state.masterPlaybackRate = clampRate(parseFloat(masterSpeedInput.value));
      masterSpeedVal.textContent = `${state.masterPlaybackRate.toFixed(2)}×`;
      if (video) video.playbackRate = state.masterPlaybackRate;
      audioEngine?.refreshRates();
      schedulePersistMasterRate();
    });

    host.querySelector("#tl-clip-delete")?.addEventListener("click", () => {
      if (state.selectedBeatId) setBeatDisabled(state.selectedBeatId, true);
    });
    host.querySelector("#tl-clip-restore")?.addEventListener("click", () => {
      if (state.selectedBeatId) setBeatDisabled(state.selectedBeatId, false);
    });

    function onDocumentClick(ev) {
      if (!contextMenu?.contains(ev.target)) hideContextMenu();
    }

    document.addEventListener("click", onDocumentClick);
    host.addEventListener("keydown", (ev) => {
      if (ev.key === "Delete" && state.selectedBeatId) {
        const b = beatById(state.selectedBeatId);
        if (b && !b.disabled) {
          setBeatDisabled(state.selectedBeatId, true);
          ev.preventDefault();
        }
      }
    });
    host.setAttribute("tabindex", "0");

    host.querySelectorAll(".tl-mode-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        if (btn.disabled) return;
        state.previewMode = btn.dataset.mode;
        applyPreviewMode();
      });
    });

    playBtn.addEventListener("click", togglePlay);
    host.querySelector("#tl-btn-start").addEventListener("click", () => {
      setCurrentTime(0);
      scrollEl.scrollLeft = 0;
      pauseAll();
    });
    zoomSlider.addEventListener("input", () => setZoom(parseFloat(zoomSlider.value)));
    host.querySelector("#tl-btn-fit").addEventListener("click", fitZoom);
    host.querySelector("#tl-btn-zoom-in").addEventListener("click", () => setZoom(state.pxPerSec * ZOOM_STEP));
    host.querySelector("#tl-btn-zoom-out").addEventListener("click", () => setZoom(state.pxPerSec / ZOOM_STEP));
    host.querySelector("#tl-btn-reload-preview").addEventListener("click", reloadPreview);

    scrollEl.addEventListener("wheel", (ev) => {
      if (ev.ctrlKey || ev.metaKey) {
        ev.preventDefault();
        setZoom(state.pxPerSec * (ev.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP));
      }
    }, { passive: false });

    compIframe.addEventListener("load", () => {
      muteIframeMedia(compIframe);
      try {
        const doc = compIframe.contentDocument;
        if (doc?.documentElement) {
          doc.documentElement.style.overflow = "hidden";
          if (doc.body) doc.body.style.overflow = "hidden";
        }
      } catch { /* ignore */ }
      seekComposition(state.currentTime);
    });
    studioIframe.addEventListener("load", () => {
      muteIframeMedia(studioIframe);
    });

    if (video) {
      video.addEventListener("timeupdate", () => {
        if (!active?.drag && state.previewMode === "mp4" && state.playing) {
          updatePlayheadUI(video.currentTime);
          maybeAutoScroll(video.currentTime);
        }
      });
      video.addEventListener("ended", () => { state.playing = false; playBtn.textContent = "▶"; });
    }
    if (masterAudio) {
      masterAudio.addEventListener("timeupdate", onAudioTimeUpdate);
      masterAudio.addEventListener("ended", () => {
        state.playing = false;
        playBtn.textContent = "▶";
      });
    }

    host.querySelector("#tl-btn-studio-start").addEventListener("click", async () => {
      try {
        const res = await api(`/preview/hyperframes/start?segment=${segment}`, { method: "POST" });
        state.studioUrl = res.studio_embed_url || res.studio_url || res.url;
        host.querySelector("#tl-btn-studio-start").disabled = true;
        host.querySelector("#tl-btn-studio-stop").disabled = false;
        toast(res.message || "Studio 已启动");
        if (state.previewMode === "studio") applyPreviewMode();
      } catch (e) {
        toast(formatApiError(e));
      }
    });

    host.querySelector("#tl-btn-studio-stop").addEventListener("click", async () => {
      try {
        await api(`/preview/hyperframes/stop?segment=${segment}`, { method: "POST" });
        state.studioUrl = null;
        host.querySelector("#tl-btn-studio-start").disabled = false;
        host.querySelector("#tl-btn-studio-stop").disabled = true;
        toast("Studio 已停止");
        if (state.previewMode === "studio") applyPreviewMode();
      } catch (e) {
        toast(String(e.message || e));
      }
    });

    host.querySelector("#tl-btn-lint").addEventListener("click", async () => {
      try {
        const job = await runPreset("segment_timing_lint");
        await pollJob(job.id, logEl);
        toast("时长检查完成 · 见下方日志");
      } catch (e) {
        toast(String(e.message || e));
      }
    });
    host.querySelector("#tl-btn-build").addEventListener("click", async () => {
      try {
        await api(`/timeline/rebuild-vo?segment=${segment}`, { method: "POST" });
        waveformVoSrc = "";
        const job = await runPreset("build_composition");
        await pollJob(job.id, logEl);
        reloadPreview();
        if (onRefresh) await onRefresh();
        toast("合成已重建 · 预览已刷新");
      } catch (e) {
        toast(String(e.message));
      }
    });
    host.querySelector("#tl-btn-align").addEventListener("click", () => {
      runPreset("audio_chain").catch(e => toast(e.message));
    });
    host.querySelector("#tl-btn-render").addEventListener("click", async () => {
      try {
        const job = await runPreset("render_draft");
        await pollJob(job.id, logEl);
        if (onRefresh) await onRefresh();
        toast("草稿渲染完成");
      } catch (e) {
        toast(String(e.message));
        if (logEl) logEl.textContent = String(e.message);
      }
    });

    const previewResizeObserver = global.ResizeObserver && previewFrame
      ? new global.ResizeObserver(updateCompositionScale)
      : null;
    previewResizeObserver?.observe(previewFrame);
    global.addEventListener("resize", updateCompositionScale);

    active = {
      drag: null,
      wavesurfer,
      audioEngine,
      onDocMove,
      onDocUp,
      destroy: () => {
        clearTimeout(persistTimer);
        clearTimeout(rebuildVoTimer);
        clearTimeout(masterSettingsTimer);
        audioEngine?.destroy();
        previewResizeObserver?.disconnect();
        global.removeEventListener("resize", updateCompositionScale);
        if (active?.wavesurfer) {
          try { active.wavesurfer.destroy(); } catch { /* ignore */ }
        }
        document.removeEventListener("mousemove", onDocMove);
        document.removeEventListener("mouseup", onDocUp);
        document.removeEventListener("click", onDocumentClick);
      },
    };
    document.addEventListener("mousemove", onDocMove);
    document.addEventListener("mouseup", onDocUp);

    applyPreviewMode();
    updateCompositionScale();
    syncTimelineFromServer();
    fitZoom();
    updateClipInspector();

    return {
      destroy: () => {
        active?.destroy?.();
        destroyActive();
      },
      seek: (t) => setCurrentTime(t),
    };
  }

  global.TimelineEditor = { mount, destroy: destroyActive, formatTime };
})(window);
