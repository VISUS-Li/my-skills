/**
 * Timeline editor — preview (composition / MP4 / Studio) + waveform + scrub/zoom/edit.
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
    const beats = data.beats || [];
    const microEvents = (data.micro_events || []).slice(0, 500);
    const media = data.media || {};
    const preview = data.preview || {};

    const mp4Src = media.render_mp4 ? mediaUrl(media.render_mp4) : "";
    const voSrc = media.vo_wav ? mediaUrl(media.vo_wav) : "";
    const compositionUrl = preview.composition_embed_url || `/api/preview/composition/${segment}/index.html`;
    const studioUrl = preview.studio_url || null;

    const state = {
      totalSec,
      pxPerSec: 40,
      currentTime: 0,
      playing: false,
      selectedBeatId: selectedBeatId || null,
      drag: null,
      previewMode: defaultPreviewMode(media, preview),
      studioUrl,
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
            <div class="tl-studio-actions">
              <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-studio-start" ${preview.studio_running ? "disabled" : ""}>启动 Studio</button>
              <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-studio-stop" ${preview.studio_running ? "" : "disabled"}>停止 Studio</button>
            </div>
          </details>
          <div class="tl-preview-stage" id="tl-preview-stage">
            <iframe id="tl-preview-composition" class="tl-preview-iframe hidden" title="HyperFrames 合成预览" sandbox="allow-scripts allow-same-origin"></iframe>
            <iframe id="tl-preview-studio" class="tl-preview-iframe hidden" title="HyperFrames Studio" sandbox="allow-scripts allow-same-origin allow-popups"></iframe>
            <video id="tl-preview-video" class="tl-preview-video hidden" playsinline preload="metadata"></video>
            <audio id="tl-master-audio" class="hidden" preload="auto"></audio>
            <div id="tl-preview-audio-only" class="tl-preview-audio-only hidden">
              <p class="metric">口播预览 · 使用播放按钮或拖拽下方波形</p>
            </div>
            <div id="tl-preview-empty" class="tl-preview-placeholder hidden"><span>暂无预览媒体</span></div>
          </div>
          <div class="tl-transport">
            <button type="button" class="btn btn-secondary btn-icon" id="tl-btn-start" title="回到开头">⏮</button>
            <button type="button" class="btn btn-primary btn-icon" id="tl-btn-play" title="播放/暂停">▶</button>
            <span id="tl-time-display" class="tl-time-display">${formatTime(0)} / ${formatTime(totalSec)}</span>
            <label class="tl-zoom-label">缩放
              <input type="range" id="tl-zoom-slider" min="${MIN_PX_PER_SEC}" max="${MAX_PX_PER_SEC}" step="1" value="${state.pxPerSec}" />
            </label>
            <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-fit">适应</button>
            <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-zoom-out">−</button>
            <button type="button" class="btn btn-secondary btn-compact" id="tl-btn-zoom-in">+</button>
          </div>
          <p id="tl-preview-hint" class="metric tl-preview-hint"></p>
        </div>
        <div class="card card-no-accent tl-tracks-card">
          <p class="metric">波形=口播 · 灰=计划 · 蓝=实测 · 橙=微事件 · 播放时仅一路音频（合成页画面静音，口播走波形轨）</p>
          <div class="tl-scroll" id="tl-scroll">
            <div class="tl-scroll-inner" id="tl-scroll-inner">
              <div class="tl-waveform-row" id="tl-waveform-row" style="width:${state.totalSec * state.pxPerSec}px">
                <div class="tl-track-label">波形</div>
                <div id="tl-waveform" class="tl-waveform"></div>
              </div>
            </div>
          </div>
          <div class="tl-scroll tl-scroll-tracks" id="tl-scroll-tracks">
            <div class="tl-scroll-inner" id="tl-scroll-tracks-inner"></div>
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
      </div>`;

    const scrollEl = host.querySelector("#tl-scroll-tracks");
    const innerEl = host.querySelector("#tl-scroll-tracks-inner");
    const waveformRow = host.querySelector("#tl-waveform-row");
    const waveformEl = host.querySelector("#tl-waveform");
    const waveformScroll = host.querySelector("#tl-scroll");
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

    let wavesurfer = null;
    let syncingWave = false;
    let waveformVoSrc = "";
    let lastCompSeekMs = 0;
    let lastAutoScrollMs = 0;

    function updatePlayheadUI(t) {
      state.currentTime = clamp(t, 0, state.totalSec);
      const playhead = innerEl?.querySelector("#tl-playhead");
      if (playhead) playhead.style.left = `${secToPx(state.currentTime)}px`;
      timeDisplay.textContent = `${formatTime(state.currentTime)} / ${formatTime(state.totalSec)}`;
      innerEl?.querySelectorAll(".tl-block:not(.planned)").forEach(el => {
        const start = parseFloat(el.dataset.start || "0");
        const dur = parseFloat(el.dataset.dur || "0");
        el.classList.toggle("tl-block-active", state.currentTime >= start && state.currentTime < start + dur);
      });
    }

    function syncCompositionVisual(t) {
      if (state.previewMode !== "composition" || !state.playing) return;
      const now = performance.now();
      if (now - lastCompSeekMs < 80) return;
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

    function updatePreviewHint() {
      const hints = {
        composition: "合成页画面 + 波形口播（合成内音频已静音）· 拖拽蓝条改时长后请「重建合成」",
        mp4: "成片 MP4 自带音轨 · 波形仅作参考",
        audio: "口播 WAV · 播放按钮或波形轨控制",
        studio: "Studio 热重载 · 画面静音 · 口播与 playhead 走波形轨",
      };
      hintEl.textContent = hints[state.previewMode] || "";
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
      } else if (state.previewMode === "mp4" && mp4Src) {
        video.classList.remove("hidden");
        if (video.src !== mp4Src) video.src = mp4Src;
      } else if (state.previewMode === "audio" && voSrc) {
        audioOnlyEl.classList.remove("hidden");
        if (masterAudio.src !== voSrc) masterAudio.src = voSrc;
      } else if (state.previewMode === "studio") {
        if (state.studioUrl) {
          studioIframe.classList.remove("hidden");
          studioIframe.src = `${state.studioUrl}/?v=${Date.now()}`;
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
      const x = secToPx(t);
      [scrollEl, waveformScroll].forEach(el => {
        if (!el) return;
        const pad = el.clientWidth * 0.25;
        if (x < el.scrollLeft + pad || x > el.scrollLeft + el.clientWidth - pad) {
          el.scrollLeft = Math.max(0, x - el.clientWidth * 0.35);
        }
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

    function setCurrentTime(t, { fromMedia = false } = {}) {
      updatePlayheadUI(t);
      if (fromMedia || state.playing) return;
      if (state.previewMode === "composition") {
        seekComposition(state.currentTime, { pause: true });
      }
      const m = masterEl();
      if (m && Math.abs(m.currentTime - state.currentTime) > 0.05) {
        m.currentTime = state.currentTime;
      }
      syncWaveform();
    }

    function renderTracks() {
      const width = secToPx(state.totalSec);
      if (waveformRow) waveformRow.style.width = `${width}px`;

      const plannedBlocks = beats.map(b => {
        const pStart = plannedStart(b);
        const pDur = plannedDur(b);
        return `<div class="tl-block planned" style="left:${secToPx(pStart)}px;width:${Math.max(secToPx(pDur), 2)}px" title="planned ${b.beat_id}"></div>`;
      }).join("");
      const actualBlocks = beats.map(b => {
        const start = beatStart(b);
        const dur = beatDur(b);
        const sel = state.selectedBeatId === b.beat_id ? " selected" : "";
        return `<div class="tl-block${sel}" data-beat="${b.beat_id}" data-start="${start}" data-dur="${dur}"
          style="left:${secToPx(start)}px;width:${Math.max(secToPx(dur), 4)}px" title="${b.beat_id} ${dur.toFixed(2)}s">${b.beat_id}</div>`;
      }).join("");
      const micro = microEvents.map(ev => {
        const t = Number(ev.t || 0);
        const eid = ev.id || ev.event_id || "";
        return `<span class="tl-micro" data-event="${eid}" data-t="${t}" style="left:${secToPx(t)}px" title="${eid} @ ${t}s"></span>`;
      }).join("");

      innerEl.innerHTML = `
        ${buildRulerTicks(state.totalSec, state.pxPerSec)}
        <div class="tl-track tl-track-planned" style="width:${width}px"><div class="tl-track-label">计划</div>${plannedBlocks}</div>
        <div class="tl-track tl-track-beats" style="width:${width}px"><div class="tl-track-label">实测</div>${actualBlocks}</div>
        <div class="tl-track tl-track-micro" style="width:${width}px"><div class="tl-track-label">微事件</div>${micro}</div>
        <div class="tl-playhead" id="tl-playhead" style="left:${secToPx(state.currentTime)}px"></div>`;

      bindTrackEvents();
      if (state.playing) updatePlayheadUI(state.currentTime);
      else setCurrentTime(state.currentTime);
      initOrUpdateWaveform();
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

    function initOrUpdateWaveform() {
      if (!voSrc || !global.WaveSurfer || !waveformEl || !masterAudio) return;

      if (!wavesurfer || waveformVoSrc !== voSrc) {
        if (wavesurfer) {
          try { wavesurfer.destroy(); } catch { /* ignore */ }
          wavesurfer = null;
        }
        masterAudio.src = voSrc;
        waveformVoSrc = voSrc;
        wavesurfer = global.WaveSurfer.create({
          container: waveformEl,
          media: masterAudio,
          height: 56,
          waveColor: "rgba(10, 132, 255, 0.35)",
          progressColor: "rgba(10, 132, 255, 0.85)",
          cursorColor: "#ff453a",
          barWidth: 2,
          barGap: 1,
          minPxPerSec: state.pxPerSec,
          fillParent: false,
          width: secToPx(state.totalSec),
          interact: true,
          hideScrollbar: true,
        });
        bindWaveformEvents();
        if (active) active.wavesurfer = wavesurfer;
        return;
      }

      try {
        if (typeof wavesurfer.zoom === "function") {
          wavesurfer.zoom(state.pxPerSec);
        } else {
          wavesurfer.setOptions?.({ minPxPerSec: state.pxPerSec, width: secToPx(state.totalSec) });
        }
      } catch { /* ignore */ }
    }

    function fitZoom() {
      if (!scrollEl) return;
      const w = Math.max(scrollEl.clientWidth - 48, 200);
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
      return masterAudio.play().catch(() => toast("无法播放口播"));
    }

    function togglePlay() {
      if (state.previewMode === "composition") {
        muteIframeMedia(compIframe);
        if (!voSrc) {
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
        if (!voSrc) {
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

      if (voSrc && masterAudio) {
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
        studioIframe.src = `${state.studioUrl}/?v=${Date.now()}`;
      } else if (state.previewMode === "mp4" && mp4Src) {
        video.src = `${mp4Src}${mp4Src.includes("?") ? "&" : "?"}v=${Date.now()}`;
      }
      toast("预览已刷新");
    }

    function onDocMove(ev) {
      if (!active?.drag) return;
      const d = active.drag;
      const innerRect = innerEl.getBoundingClientRect();
      const xInInner = ev.clientX - innerRect.left + scrollEl.scrollLeft;

      if (d.type === "beat-resize") {
        const newDur = Math.max(0.2, pxToSec(xInInner - secToPx(d.startSec)));
        d.newDur = newDur;
        d.block.style.width = `${Math.max(secToPx(newDur), 4)}px`;
      } else if (d.type === "micro-drag") {
        const newT = clamp(pxToSec(xInInner), 0, state.totalSec);
        d.newT = newT;
        d.el.style.left = `${secToPx(newT)}px`;
      } else if (d.type === "playhead") {
        setCurrentTime(pxToSec(xInInner));
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
          await api(`/timing/beats/${d.beatId}?segment=${segment}`, {
            method: "PATCH",
            body: JSON.stringify({ duration_sec: d.newDur, locked: true }),
          });
          toast(`${d.beatId} → ${d.newDur.toFixed(2)}s · 请重建合成以更新画面`);
          if (onRefresh) await onRefresh();
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
        renderTracks();
      }
    }

    function bindTrackEvents() {
      innerEl.querySelectorAll(".tl-block:not(.planned)").forEach(block => {
        block.addEventListener("mousedown", (ev) => {
          const beatId = block.dataset.beat;
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
          if (onBeatSelect) onBeatSelect(beatId);
          ev.preventDefault();
        });
        block.addEventListener("dblclick", (ev) => {
          if (onBeatOpen) onBeatOpen(block.dataset.beat);
          ev.preventDefault();
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
        const innerRect = innerEl.getBoundingClientRect();
        const xInInner = ev.clientX - innerRect.left + scrollEl.scrollLeft;
        setCurrentTime(pxToSec(xInInner));
        active.drag = { type: "playhead" };
        document.body.classList.add("tl-dragging");
        ev.preventDefault();
      });
    }

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
      waveformScroll.scrollLeft = 0;
      pauseAll();
    });
    zoomSlider.addEventListener("input", () => setZoom(parseFloat(zoomSlider.value)));
    host.querySelector("#tl-btn-fit").addEventListener("click", fitZoom);
    host.querySelector("#tl-btn-zoom-in").addEventListener("click", () => setZoom(state.pxPerSec * ZOOM_STEP));
    host.querySelector("#tl-btn-zoom-out").addEventListener("click", () => setZoom(state.pxPerSec / ZOOM_STEP));
    host.querySelector("#tl-btn-reload-preview").addEventListener("click", reloadPreview);

    let scrollSync = false;
    scrollEl.addEventListener("scroll", () => {
      if (scrollSync) return;
      scrollSync = true;
      waveformScroll.scrollLeft = scrollEl.scrollLeft;
      scrollSync = false;
    });
    waveformScroll.addEventListener("scroll", () => {
      if (scrollSync) return;
      scrollSync = true;
      scrollEl.scrollLeft = waveformScroll.scrollLeft;
      scrollSync = false;
    });

    scrollEl.addEventListener("wheel", (ev) => {
      if (ev.ctrlKey || ev.metaKey) {
        ev.preventDefault();
        setZoom(state.pxPerSec * (ev.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP));
      }
    }, { passive: false });

    compIframe.addEventListener("load", () => {
      muteIframeMedia(compIframe);
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
        state.studioUrl = res.studio_url || res.url;
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

    active = {
      drag: null,
      wavesurfer,
      onDocMove,
      onDocUp,
      destroy: () => {
        if (active?.wavesurfer) {
          try { active.wavesurfer.destroy(); } catch { /* ignore */ }
        }
        document.removeEventListener("mousemove", onDocMove);
        document.removeEventListener("mouseup", onDocUp);
      },
    };
    document.addEventListener("mousemove", onDocMove);
    document.addEventListener("mouseup", onDocUp);

    applyPreviewMode();
    fitZoom();

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
