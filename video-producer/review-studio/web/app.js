const API = "/api";
let currentSegment = "S001";
let activeView = "pipeline";
let selectedStageId = "script";
let selectedBeatId = null;
let timelineData = null;
let timelineEditorHandle = null;
let activeEditors = {};
let lightboxZoom = 1;
let beatsTtsPollTimer = null;
let activeBeatsTts = null;
let lastTtsProgress = { status: "idle" };

const TABS = [
  { view: "pipeline", icon: "🎬", label: "流程" },
  { view: "script", icon: "📝", label: "文案" },
  { view: "beats", icon: "🎙️", label: "口播 & 配音" },
  { view: "assets", icon: "🖼️", label: "资产" },
  { view: "timeline", icon: "⏱️", label: "时间轴" },
  { view: "stage", icon: "📦", label: "阶段" },
  { view: "queue", icon: "📋", label: "待办" },
  { view: "jobs", icon: "⚙️", label: "任务" },
  { view: "qc", icon: "✅", label: "质检" },
  { view: "history", icon: "📜", label: "历史" },
];

const ASSET_IMAGE_RE = /\.(svg|png|jpe?g|webp|gif)$/i;
const ASSET_VIDEO_RE = /\.(mp4|webm|mov|m4v)$/i;
const ASSET_PREVIEW_RE = /\.(svg|png|jpe?g|webp|gif|mp4|webm|mov|m4v)$/i;

const STATUS_ZH = {
  draft: "草稿",
  review: "待审核",
  approved: "已通过",
  locked: "已锁定",
  "needs-revision": "需修改",
  rejected: "已驳回",
  stale: "已过期",
  ok: "正常",
  warn: "注意",
  fail: "异常",
  queued: "排队中",
  running: "运行中",
  completed: "已完成",
  failed: "失败",
  pending: "待处理",
  "in_progress": "进行中",
};

function statusZh(s) {
  return STATUS_ZH[s] || s || "—";
}

function statusClass(status) {
  return `status ${status || "draft"}`;
}

function statusBadge(s) {
  return `<span class="${statusClass(s)}">${esc(statusZh(s))}</span>`;
}

function mediaUrl(path) {
  if (!path) return "";
  return `/api/media/${String(path).split(/[/\\]/).filter(Boolean).map(encodeURIComponent).join("/")}`;
}

let beatPreviewAudio = null;
let beatPreviewBeatId = null;

function ensureBeatPreviewAudio() {
  if (beatPreviewAudio) return beatPreviewAudio;
  beatPreviewAudio = document.createElement("audio");
  beatPreviewAudio.preload = "none";
  beatPreviewAudio.addEventListener("ended", () => {
    document.querySelectorAll(".beat-audio-btn.playing").forEach(btn => btn.classList.remove("playing"));
    beatPreviewBeatId = null;
  });
  beatPreviewAudio.addEventListener("pause", () => {
    document.querySelectorAll(".beat-audio-btn.playing").forEach(btn => btn.classList.remove("playing"));
  });
  document.body.appendChild(beatPreviewAudio);
  return beatPreviewAudio;
}

window.playBeatAudio = (beatId, path) => {
  if (!path) return;
  const audio = ensureBeatPreviewAudio();
  const url = mediaUrl(path);
  if (beatPreviewBeatId === beatId && !audio.paused) {
    audio.pause();
    beatPreviewBeatId = null;
    return;
  }
  document.querySelectorAll(".beat-audio-btn.playing").forEach(btn => btn.classList.remove("playing"));
  if (!audio.paused) audio.pause();
  audio.src = url;
  beatPreviewBeatId = beatId;
  const btn = document.querySelector(`.beat-audio-btn[data-beat="${beatId}"]`);
  audio.play().then(() => {
    if (beatPreviewBeatId === beatId && btn) btn.classList.add("playing");
  }).catch(err => {
    beatPreviewBeatId = null;
    toast(String(err.message || "无法播放音频"));
  });
};

function assetMediaKind(path) {
  if (!path) return null;
  if (ASSET_VIDEO_RE.test(path)) return "video";
  if (ASSET_IMAGE_RE.test(path)) return "image";
  return null;
}

function assetKindLabel(kind) {
  if (kind === "video") return "视频";
  if (kind === "image") return "图片";
  return "媒体";
}

function escAttr(s) {
  return String(s ?? "").replace(/\\/g, "\\\\").replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

function initTabs() {
  const bar = document.getElementById("tab-bar-scroll");
  if (!bar) return;
  bar.innerHTML = TABS.map(t =>
    `<button type="button" data-view="${t.view}" class="tab${t.view === activeView ? " active" : ""}"><span class="tab-icon">${t.icon}</span>${t.label}</button>`
  ).join("");
  bar.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", async () => {
      bar.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
      btn.classList.add("active");
      activeView = btn.dataset.view;
      document.getElementById(activeView)?.classList.add("active");
      await refreshActiveView();
    });
  });
}

function initWorkspaceToggle() {
  const panel = document.getElementById("workspace-panel");
  const btn = document.getElementById("workspace-toggle");
  if (!panel || !btn) return;
  const key = "rs-workspace-collapsed";
  const collapsed = localStorage.getItem(key) === "1";
  panel.classList.toggle("collapsed", collapsed);
  btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
  btn.addEventListener("click", () => {
    const now = panel.classList.toggle("collapsed");
    localStorage.setItem(key, now ? "1" : "0");
    btn.setAttribute("aria-expanded", now ? "false" : "true");
  });
}

function initLightbox() {
  const lb = document.getElementById("asset-lightbox");
  const backdrop = document.getElementById("lightbox-backdrop");
  const content = document.getElementById("lightbox-content");
  function close() {
    lb?.classList.add("hidden");
    backdrop?.classList.add("hidden");
    content?.querySelector("video")?.pause();
    if (content) content.innerHTML = "";
    lightboxZoom = 1;
    setLightboxMediaMode(null);
  }
  document.getElementById("lightbox-close")?.addEventListener("click", close);
  backdrop?.addEventListener("click", close);
  document.getElementById("lightbox-zoom-in")?.addEventListener("click", () => setLightboxZoom(lightboxZoom + 0.25));
  document.getElementById("lightbox-zoom-out")?.addEventListener("click", () => setLightboxZoom(Math.max(0.25, lightboxZoom - 0.25)));
  document.getElementById("lightbox-fit")?.addEventListener("click", () => setLightboxZoom(1));
  document.getElementById("lightbox-fullscreen")?.addEventListener("click", () => {
    const stage = document.getElementById("lightbox-stage");
    if (stage?.requestFullscreen) stage.requestFullscreen();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && lb && !lb.classList.contains("hidden")) close();
  });
}

function setLightboxZoom(z) {
  lightboxZoom = z;
  const el = document.getElementById("lightbox-content");
  if (el) el.style.transform = `scale(${lightboxZoom})`;
}

function setLightboxMediaMode(kind) {
  const isVideo = kind === "video";
  document.querySelectorAll("#lightbox-zoom-out, #lightbox-zoom-in, #lightbox-fit").forEach(el => {
    el.classList.toggle("hidden", isVideo);
  });
}

window.openAssetLightbox = async (path, title) => {
  const lb = document.getElementById("asset-lightbox");
  const backdrop = document.getElementById("lightbox-backdrop");
  const content = document.getElementById("lightbox-content");
  const url = mediaUrl(path);
  const kind = assetMediaKind(path);
  document.getElementById("lightbox-title").textContent = title || path;
  lightboxZoom = 1;
  content.style.transform = "scale(1)";
  setLightboxMediaMode(kind);
  if (kind === "video") {
    content.innerHTML = `<video src="${url}" controls autoplay playsinline preload="metadata" class="lightbox-video"></video>`;
  } else {
    const ext = (path.split(".").pop() || "").toLowerCase();
    if (ext === "svg") {
      try {
        const res = await fetch(url);
        const text = await res.text();
        if (text.trim().startsWith("<") || text.includes("<svg")) {
          content.innerHTML = `<object type="image/svg+xml" data="data:image/svg+xml;charset=utf-8,${encodeURIComponent(text)}"></object>`;
        } else {
          content.innerHTML = `<img src="${url}" alt="${esc(title)}" />`;
        }
      } catch {
        content.innerHTML = `<img src="${url}" alt="${esc(title)}" />`;
      }
    } else {
      content.innerHTML = `<img src="${url}" alt="${esc(title)}" />`;
    }
  }
  lb.classList.remove("hidden");
  backdrop.classList.remove("hidden");
};

window.assetThumbFallback = async function (img, path) {
  try {
    const res = await fetch(mediaUrl(path));
    const ct = res.headers.get("content-type") || "";
    const text = await res.text();
    if (path.endsWith(".svg") || ct.includes("svg") || text.trim().startsWith("<")) {
      img.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(text)}`;
      img.onerror = null;
      return;
    }
    img.alt = "加载失败";
  } catch {
    img.replaceWith(Object.assign(document.createElement("span"), { className: "asset-fallback", textContent: "⚠️ 无法预览" }));
  }
};

function mountEditor(containerId, options) {
  const el = document.getElementById(containerId);
  if (!el || !window.EditorPane) return null;
  if (activeEditors[containerId]) {
    EditorPane.destroy(activeEditors[containerId]);
  }
  const id = EditorPane.create(el, options);
  activeEditors[containerId] = id;
  return id;
}

function editorGetValue(containerId) {
  const eid = activeEditors[containerId];
  return eid ? EditorPane.getValue(eid) : "";
}

function assetThumb(asset) {
  const path = (typeof asset === "string") ? asset : (asset.media_path || asset.path_or_url);
  const assetId = (typeof asset === "string") ? path : (asset.asset_id || path);
  const exists = (typeof asset === "object") ? asset.exists !== false : true;
  const kind = assetMediaKind(path);
  if (!exists || !path) {
    return `<div class="asset-thumb asset-thumb-missing" title="文件尚未生成">
      <span class="asset-fallback">未生成</span>
      <span class="zoom-hint missing">缺失</span>
    </div>`;
  }
  const url = mediaUrl(path);
  const hint = kind === "video" ? "▶ 播放" : "🔍 放大";
  if (kind === "video") {
    return `<div class="asset-thumb asset-thumb-video" onclick="openAssetLightbox('${escAttr(path)}','${escAttr(assetId)}')" title="点击播放">
      <video src="${url}" muted playsinline preload="metadata" class="asset-thumb-video-el"></video>
      <span class="zoom-hint">${hint}</span>
    </div>`;
  }
  return `<div class="asset-thumb" onclick="openAssetLightbox('${escAttr(path)}','${escAttr(assetId)}')" title="点击放大">
    <img src="${url}" alt="${esc(assetId)}" loading="lazy" onerror="assetThumbFallback(this,'${escAttr(path)}')" />
    <span class="zoom-hint">${hint}</span>
  </div>`;
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => el.classList.remove("show"), 3500);
}

function pageWrap(title, subtitle, inner) {
  return `<div class="ios-page">
    <div class="page-header">
      <h2 class="page-title">${title}</h2>
      ${subtitle ? `<p class="page-subtitle">${subtitle}</p>` : ""}
    </div>
    ${inner}
  </div>`;
}

function tableWrap(html) {
  return `<div class="table-wrap"><table>${html}</table></div>`;
}

function setActiveTab(view) {
  if (view === "audio") view = "beats";
  if (view === "preview") view = "timeline";
  activeView = view;
  document.querySelectorAll(".tab").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.getElementById(view)?.classList.add("active");
}

function openSheet() {
  document.getElementById("beat-drawer").classList.remove("hidden");
  document.getElementById("sheet-backdrop")?.classList.remove("hidden");
}

function closeSheet() {
  document.getElementById("beat-drawer").classList.add("hidden");
  document.getElementById("sheet-backdrop")?.classList.add("hidden");
}

async function api(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  if (res.status === 204) return {};
  return res.json();
}

function parseFetchError(data, fallback = "请求失败") {
  if (!data) return fallback;
  if (typeof data === "string") {
    try {
      return parseFetchError(JSON.parse(data), fallback);
    } catch {
      return data || fallback;
    }
  }
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map(item => item.msg || item.message || JSON.stringify(item)).join("；");
  }
  if (data.error) return String(data.error);
  if (data.message) return String(data.message);
  return fallback;
}

function setRefUploadUi(visible, label, pct) {
  const wrap = document.getElementById("ref-upload-status");
  const bar = document.getElementById("ref-upload-bar");
  const lbl = document.getElementById("ref-upload-label");
  const btn = document.getElementById("ref-upload-btn");
  if (wrap) wrap.classList.toggle("hidden", !visible);
  if (lbl) lbl.textContent = label || "处理中…";
  if (bar) {
    bar.style.width = `${Math.max(0, Math.min(100, pct || 0))}%`;
    bar.classList.toggle("indeterminate", visible && (pct == null || pct <= 0));
  }
  if (btn) {
    btn.disabled = visible;
    btn.textContent = visible ? "处理中…" : "上传 WAV / MP3";
  }
}

async function pollRefUpload(uploadId) {
  for (let i = 0; i < 600; i++) {
    await new Promise(r => setTimeout(r, 400));
    const st = await api(`/audio/refs/upload/${uploadId}`);
    setRefUploadUi(true, st.message || statusZh(st.status), st.progress ?? 10);
    if (st.status === "completed") return st;
    if (st.status === "failed") throw new Error(st.error || st.message || "上传失败");
  }
  throw new Error("上传超时，请稍后刷新参考音频库");
}

function bindRefUploadInput() {
  const input = document.getElementById("tts-ref-upload");
  if (!input || input.dataset.bound === "1") return;
  input.dataset.bound = "1";
  input.addEventListener("change", () => {
    if (input.files?.[0]) uploadTtsRef().catch(e => toast(String(e.message || e)));
  });
}

function esc(s) {
  return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
}

async function refreshSegment() {
  try {
    const data = await api("/segments");
    currentSegment = data.default || data.segments?.[0] || "S001";
    const sel = document.getElementById("segment-select");
    if (sel) {
      sel.innerHTML = (data.segments || [currentSegment]).map(s =>
        `<option value="${s}" ${s === currentSegment ? "selected" : ""}>${s}</option>`
      ).join("");
    }
  } catch {
    currentSegment = "S001";
  }
}

function renderWorkspaceControls(workspace) {
  const ws = workspace || {};
  document.getElementById("workspace-input").value = ws.workspace_root || "";
  const select = document.getElementById("project-select");
  const currentPath = ws.current_project?.path || "";
  const options = new Map();
  for (const p of ws.projects || []) options.set(p.path, p);
  for (const p of ws.recent_projects || []) options.set(p.path, p);
  select.innerHTML = [...options.values()].map(p => {
    const label = `${p.title || p.name} (${p.current_stage || "-"})`;
    return `<option value="${p.path}" ${p.path === currentPath ? "selected" : ""}>${label}</option>`;
  }).join("") || `<option value="">— 未发现项目 —</option>`;
  if (currentPath) document.getElementById("project-path-input").value = currentPath;
}

async function loadWorkspace() {
  const data = await api("/workspace");
  renderWorkspaceControls(data);
  return data;
}

async function pickDirectory(title) {
  const res = await fetch(`${API}/dialog/pick-directory?title=${encodeURIComponent(title)}`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  if (data.cancelled || !data.path) return null;
  return data.path;
}

async function browseWorkspace() {
  try {
    const path = await pickDirectory("选择工作区根目录");
    if (!path) return;
    document.getElementById("workspace-input").value = path;
    await setWorkspaceRoot();
  } catch (err) { toast(String(err.message || err)); }
}

async function browseProject() {
  try {
    const path = await pickDirectory("选择视频项目目录");
    if (!path) return;
    document.getElementById("project-path-input").value = path;
    await switchProject(path);
  } catch (err) { toast(String(err.message || err)); }
}

async function setWorkspaceRoot() {
  const path = document.getElementById("workspace-input").value.trim();
  if (!path) return toast("请输入工作区根目录");
  const data = await api("/workspace/root", { method: "PUT", body: JSON.stringify({ path, scan_depth: 2 }) });
  renderWorkspaceControls(data);
  toast(`已扫描 ${data.projects?.length || 0} 个项目`);
  await afterProjectChange();
}

async function scanWorkspace() {
  const data = await api("/workspace/scan", { method: "POST" });
  renderWorkspaceControls(data);
  toast(`扫描完成：${data.projects?.length || 0} 个项目`);
}

async function switchProject(path) {
  if (!path) return toast("请选择或输入项目路径");
  await api("/project/switch", { method: "POST", body: JSON.stringify({ path }) });
  toast("项目已切换");
  await afterProjectChange();
}

async function afterProjectChange() {
  await loadWorkspace();
  await refreshSegment();
  await loadProjectMeta();
  await refreshActiveView();
}

async function loadProjectMeta() {
  const data = await api("/project");
  renderWorkspaceControls(data.workspace);
  if (data.needs_project) {
    document.getElementById("project-meta").textContent = "请先设置工作区并选择项目";
    document.getElementById("pipeline").innerHTML = pageWrap("制作流程", "设置工作区后即可开始", `<div class="card card-no-accent"><p class="metric">在上方展开「工作区」，输入路径并扫描，再选择项目。</p></div>`);
    return data;
  }
  const title = data.video?.title || data.root;
  const stage = data.current_stage || "-";
  const blocked = data.render_blocked ? ` · 渲染阻塞` : "";
  document.getElementById("project-meta").textContent = `${title} · ${currentSegment} · 阶段：${stage}${blocked}`;
  return data;
}

async function refreshActiveView() {
  const map = {
    pipeline: renderPipeline,
    script: renderScript,
    beats: renderBeats,
    audio: renderBeats,
    assets: renderAssets,
    timeline: renderTimeline,
    preview: renderTimeline,
    stage: renderStageDetail,
    queue: renderQueue,
    jobs: renderJobs,
    qc: renderQc,
    history: renderHistory,
  };
  if (map[activeView]) await map[activeView]();
}

async function ensureTtsOnline() {
  const health = await api("/tts/health");
  if (!health.available) {
    const detail = health.reason || health.base_url || "IndexTTS 不可用";
    throw new Error(`IndexTTS 离线：${detail}`);
  }
  return health;
}

function isTtsPreset(name) {
  return /indextts|audio_chain_tts/.test(name);
}

function isTtsForceRedub() {
  return document.getElementById("tts-force-redub")?.checked ?? false;
}

function bindTtsForceRedubCheckbox() {
  const el = document.getElementById("tts-force-redub");
  if (!el) return;
  el.checked = localStorage.getItem("rs-tts-force-redub") === "1";
  el.onchange = () => localStorage.setItem("rs-tts-force-redub", el.checked ? "1" : "0");
}

function ttsProgressPercent(prog) {
  if (!prog || prog.status === "idle") return 0;
  if (typeof prog.percent === "number" && !Number.isNaN(prog.percent)) {
    return Math.min(100, Math.max(0, Math.round(prog.percent)));
  }
  const total = Number(prog.total || 0);
  const done = Number(prog.done || 0);
  if (total > 0) return Math.min(100, Math.round((done / total) * 100));
  return prog.status === "completed" ? 100 : 0;
}

function ttsProgressLabel(prog) {
  if (!prog || prog.status === "idle") return "配音进度：空闲";
  const pct = ttsProgressPercent(prog);
  const beatPart = prog.total
    ? `${prog.done ?? 0}/${prog.total}`
    : `${pct}%`;
  const phase = prog.phase && prog.phase !== "generating" ? ` · ${prog.phase}` : "";
  const cur = prog.current_beat ? ` · ${prog.current_beat}` : "";
  const msg = prog.message ? ` · ${prog.message}` : "";
  return `配音进度：${beatPart}${phase}${cur}${msg} (${statusZh(prog.status)})`;
}

async function runPreset(name, extra = "") {
  if (isTtsPreset(name)) await ensureTtsOnline();
  let forceExtra = "";
  if (isTtsPreset(name) && isTtsForceRedub()) {
    forceExtra = "&force_tts=true";
  }
  const url = `/jobs/preset/${name}?segment=${currentSegment}${forceExtra}${extra}`;
  const res = await fetch(`${API}${url}`, { method: "POST" });
  const data = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(data));
  toast(`任务 ${name}：${data.job.status === "queued" ? "已排队" : data.job.status}`);
  const logEl = document.getElementById("vo-log")
    || document.getElementById("timeline-log")
    || document.getElementById("job-log");
  const isTts = isTtsPreset(name);
  pollJob(data.job.id, logEl, { isTts });
  if (isTts) startBeatsTtsTracking(data.job.id, null);
  return data.job;
}

function formatTtsProgress(prog) {
  if (!prog || prog.status === "idle") return "";
  if (prog.phase === "lint" && prog.lint_score != null) {
    const issues = (prog.lint_issues || []).slice(0, 3).map(i => i.message || i).join("; ");
    return `[时长质检] ${prog.lint_score}/${prog.lint_fail_under ?? 80}${issues ? ` · ${issues}` : ""} (${statusZh(prog.status)})`;
  }
  if (prog.message) return `[配音进度] ${prog.message} (${prog.percent ?? 0}% · ${statusZh(prog.status)})`;
  const cur = prog.current_beat ? ` · 当前 ${prog.current_beat}` : "";
  const err = prog.error ? `\n错误：${prog.error}` : "";
  return `[配音进度] ${prog.done ?? 0}/${prog.total ?? "?"}${cur} (${statusZh(prog.status)})${err}`;
}

async function pollJob(jobId, logEl, options = {}) {
  const intervalMs = options.isTts ? 500 : 1000;
  const maxSec = options.maxSec ?? (options.isTts ? 900 : 120);
  const maxIter = Math.ceil((maxSec * 1000) / intervalMs);
  for (let i = 0; i < maxIter; i++) {
    await new Promise(r => setTimeout(r, intervalMs));
    const { job } = await api(`/jobs/${jobId}`);
    let progressLine = "";
    if (options.isTts) {
      try {
        const prog = await api("/tts/progress");
        progressLine = formatTtsProgress(prog);
        updateTtsProgressBar(prog);
        updateBeatsTtsCells(prog);
        lastTtsProgress = prog;
      } catch { /* optional */ }
    }
    if (logEl) {
      logEl.textContent = `[${job.status}] ${job.label || job.script}\n${progressLine}\n${job.stdout_tail || ""}\n${job.stderr_tail || ""}`.trim();
    }
    if (job.status === "completed" || job.status === "failed") {
      toast(`任务${job.status === "completed" ? "完成" : "失败"}`);
      if (options.isTts) {
        try {
          const prog = await api("/tts/progress");
          updateTtsProgressBar(prog);
          updateBeatsTtsCells(prog);
          lastTtsProgress = prog;
        } catch { /* optional */ }
      }
      stopBeatsTtsTracking(false);
      if (job.status === "completed") await refreshActiveView();
      return job;
    }
  }
  toast("任务轮询超时，请到「任务」页查看");
}

function updateTtsProgressBar(prog) {
  const bar = document.getElementById("tts-progress-bar");
  const label = document.getElementById("tts-progress-label");
  if (!bar || !label) return;
  if (!prog || prog.status === "idle") {
    bar.style.width = "0%";
    label.textContent = "配音进度：空闲";
    return;
  }
  const pct = ttsProgressPercent(prog);
  bar.style.width = `${pct}%`;
  label.textContent = ttsProgressLabel(prog);
}

function initCollapsiblePanel(toggleId, panelId, storageKey, defaultCollapsed = false) {
  const toggle = document.getElementById(toggleId);
  const panel = document.getElementById(panelId);
  if (!toggle || !panel) return;
  const collapsed = localStorage.getItem(storageKey) === "1" || (localStorage.getItem(storageKey) === null && defaultCollapsed);
  panel.classList.toggle("collapsed", collapsed);
  toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
  toggle.onclick = () => {
    const now = panel.classList.toggle("collapsed");
    localStorage.setItem(storageKey, now ? "1" : "0");
    toggle.setAttribute("aria-expanded", now ? "false" : "true");
  };
}

function formatRefDate(iso) {
  if (!iso) return "—";
  return String(iso).slice(0, 19).replace("T", " ");
}

function beatTtsStatusHtml(beatId, prog) {
  if (!prog || prog.status === "idle") {
    return `<span class="tts-beat-idle">—</span>`;
  }
  const bs = prog.beat_status?.[beatId];
  const completed = prog.completed_beats || [];
  if (bs === "running" || (prog.status === "running" && prog.current_beat === beatId)) {
    return `<span class="status running tts-beat-status">生成中</span>`;
  }
  if (bs === "failed" || (prog.status === "failed" && prog.current_beat === beatId)) {
    return `<span class="status failed tts-beat-status">失败</span>`;
  }
  if (bs === "done" || completed.includes(beatId)) {
    return `<span class="status completed tts-beat-status">已完成</span>`;
  }
  if (bs === "pending" && prog.status === "running") {
    return `<span class="status queued tts-beat-status">排队</span>`;
  }
  if (prog.status === "running" && Array.isArray(prog.beats) && prog.beats.includes(beatId)) {
    return `<span class="status queued tts-beat-status">排队</span>`;
  }
  if (prog.status === "completed" && Array.isArray(prog.beats) && prog.beats.includes(beatId)) {
    return `<span class="status completed tts-beat-status">已完成</span>`;
  }
  return `<span class="tts-beat-idle">—</span>`;
}

function updateBeatsTtsCells(prog) {
  lastTtsProgress = prog || { status: "idle" };
  document.querySelectorAll("[data-tts-beat]").forEach(el => {
    const beatId = el.dataset.ttsBeat;
    el.innerHTML = beatTtsStatusHtml(beatId, lastTtsProgress);
    const drawerEl = document.getElementById(`drawer-tts-st-${beatId}`);
    if (drawerEl) drawerEl.innerHTML = beatTtsStatusHtml(beatId, lastTtsProgress);
  });
  updateTtsProgressBar(prog);
}

function stopBeatsTtsTracking(refresh = false) {
  if (beatsTtsPollTimer) {
    clearInterval(beatsTtsPollTimer);
    beatsTtsPollTimer = null;
  }
  activeBeatsTts = null;
  if (refresh && activeView === "beats") renderBeats();
}

function startBeatsTtsTracking(jobId, beatIds) {
  activeBeatsTts = { jobId, beatIds };
  if (beatsTtsPollTimer) clearInterval(beatsTtsPollTimer);
  beatsTtsPollTimer = setInterval(async () => {
    try {
      const prog = await api("/tts/progress");
      updateBeatsTtsCells(prog);
      updateTtsProgressBar(prog);
      if (activeBeatsTts?.jobId) {
        const { job } = await api(`/jobs/${activeBeatsTts.jobId}`);
        if (job.status === "completed" || job.status === "failed") {
          stopBeatsTtsTracking(true);
        }
      } else if (prog.status === "completed" || prog.status === "failed") {
        stopBeatsTtsTracking(true);
      }
    } catch { /* optional */ }
  }, 500);
}

function renderRefLibraryRows(refs) {
  const items = refs.refs || [];
  if (!items.length) {
    return `<tr><td colspan="5">暂无参考音频，请上传 WAV 文件</td></tr>`;
  }
  return items.map(r => `
    <tr class="ref-row${r.selected ? " ref-row-selected" : ""}">
      <td>${r.selected ? `<span class="status approved">当前</span>` : ""} ${esc(r.label || r.name)} <span class="ref-format">${(r.format || "wav").toUpperCase()}</span></td>
      <td>${Math.round((r.size_bytes || 0) / 1024)} KB</td>
      <td>${formatRefDate(r.uploaded_at)}</td>
      <td><audio controls preload="none" src="${mediaUrl(r.path)}" class="ref-audio-player"></audio></td>
      <td>
        <div class="toolbar ref-toolbar">
          ${r.selected ? "" : `<button class="btn btn-primary btn-compact" onclick="selectTtsRef('${escAttr(r.path)}')">选用</button>`}
          <button class="btn btn-secondary btn-compact" onclick="deleteTtsRef('${escAttr(r.path)}','${escAttr(r.name)}')">删除</button>
        </div>
      </td>
    </tr>`).join("");
}

// --- Pipeline ---
async function renderPipeline() {
  const { stages } = await api("/stages");
  const approved = stages.filter(s => s.status === "approved" || s.status === "locked").length;
  const blocked = stages.filter(s => s.blocked_by?.length).length;
  const hero = `<div class="hero-stats">
    <div class="stat-hero accent-blue"><span class="stat-icon">🎬</span><div class="stat-value">${stages.length}</div><div class="stat-label">总阶段数</div></div>
    <div class="stat-hero accent-green"><span class="stat-icon">✅</span><div class="stat-value">${approved}</div><div class="stat-label">已通过</div></div>
    <div class="stat-hero accent-orange"><span class="stat-icon">⏸️</span><div class="stat-value">${blocked}</div><div class="stat-label">阻塞中</div></div>
    <div class="stat-hero accent-purple"><span class="stat-icon">📍</span><div class="stat-value">${currentSegment}</div><div class="stat-label">当前段落</div></div>
  </div>`;
  const cards = `<div class="grid">${stages.map(s => `
    <article class="card clickable card-no-accent" onclick="openStage('${s.id}')">
      <div class="card-icon-title"><span class="emoji">📦</span><h3>${esc(s.label || s.id)}</h3></div>
      ${statusBadge(s.status)}
      <p class="metric">产物进度 <strong>${s.required_ready ?? 0} / ${s.required_count ?? 0}</strong></p>
      ${s.blocked_by?.length ? `<p class="blocked">阻塞：${s.blocked_by.map(b => `${b.stage}（${statusZh(b.status)}）`).join("、")}</p>` : ""}
      <div class="toolbar">
        <button class="btn btn-primary btn-compact" onclick="event.stopPropagation(); approveStage('${s.id}')">通过</button>
        <button class="btn btn-secondary btn-compact" onclick="event.stopPropagation(); setStage('${s.id}','needs-revision')">驳回</button>
      </div>
    </article>`).join("")}</div>`;
  document.getElementById("pipeline").innerHTML = pageWrap("制作流程", `${stages.length} 个阶段 · 点击卡片进入详情`, hero + cards);
}

window.openStage = async (stageId) => {
  selectedStageId = stageId;
  activeView = "stage";
  setActiveTab("stage");
  await renderStageDetail();
};

async function approveStage(stageId) {
  await api(`/stages/${stageId}/status`, { method: "POST", body: JSON.stringify({ status: "approved", note: "UI approve" }) });
  toast(`已通过：${stageId}`);
  await renderPipeline();
}

async function setStage(stageId, status) {
  await api(`/stages/${stageId}/status`, { method: "POST", body: JSON.stringify({ status, note: "UI update" }) });
  toast(`${stageId} → ${status}`);
  await renderPipeline();
}

// --- Script Lab ---
async function renderScript() {
  let vo = { path: "script/voiceover.md", content: "" };
  try { vo = await api("/script/voiceover"); } catch { /* empty */ }
  const { beats } = await api(`/beats?segment=${currentSegment}`);
  document.getElementById("script").innerHTML = pageWrap("文案脚本", "口播全文编辑 · 支持 Markdown 分栏预览", `
    <div class="card editor-full card-no-accent">
      <div class="card-icon-title"><span class="emoji">📝</span><h3>口播全文</h3></div>
      <p class="metric">修改后请点击编辑器内「保存口播」</p>
      <div id="voiceover-editor-host" class="editor-host"></div>
    </div>
    <div class="card card-no-accent" style="margin-top:20px">
      <div class="card-icon-title"><span class="emoji">🎯</span><h3>Beats 概览</h3></div>
      <p class="metric">共 <strong>${beats.length}</strong> 条 · 逐条编辑请前往「口播 & 配音」</p>
      ${tableWrap(`<thead><tr><th>Beat</th><th>口播</th><th>计划</th><th>实测</th></tr></thead>
        <tbody>${beats.slice(0, 15).map(b => `<tr>
          <td>${b.beat_id}</td>
          <td>${esc((b.narration || "").slice(0, 48))}${(b.narration || "").length > 48 ? "…" : ""}</td>
          <td>${b.planned_sec ?? "-"}s</td>
          <td>${b.actual_sec ?? "-"}s</td>
        </tr>`).join("")}${beats.length > 15 ? `<tr><td colspan="4">…还有 ${beats.length - 15} 条</td></tr>` : ""}
        </tbody>`)}
    </div>`);
  mountEditor("voiceover-editor-host", {
    id: "voiceover-ed",
    path: vo.path,
    value: vo.content,
    height: "min(78vh, 720px)",
    defaultMode: "split",
    saveLabel: "保存口播",
    onSave: async (content) => {
      await api("/script/voiceover", { method: "PUT", body: JSON.stringify({ content, note: "Script Lab edit" }) });
      toast("口播已保存，下游产物已标记过期");
    },
  });
}

window.saveVoiceover = async () => {
  const content = editorGetValue("voiceover-editor-host");
  await api("/script/voiceover", { method: "PUT", body: JSON.stringify({ content, note: "Script Lab edit" }) });
  toast("口播已保存");
};

// --- 口播 & 配音（Beats + Audio 合并） ---
function beatNeedsAttention(b) {
  const drift = Math.abs(Number(b.drift_sec || 0));
  return drift > 0.3 || b.cps_band === "warn" || b.cps_band === "fail";
}

function renderBeatTableRows(beats, prog) {
  return beats.map(b => {
    const cps = b.vo?.cps ?? (b.char_count && b.actual_sec ? (Number(b.char_count) / Number(b.actual_sec)).toFixed(1) : "-");
    const drift = b.drift_sec != null ? `${b.drift_sec > 0 ? "+" : ""}${b.drift_sec}s` : "-";
    const driftClass = beatNeedsAttention(b) ? "beat-row-attention" : "";
    return `<tr class="${driftClass}" data-beat-row="${b.beat_id}">
      <td><a href="#" onclick="openBeatDetail('${b.beat_id}');return false">${b.beat_id}</a></td>
      <td><textarea id="n-${b.beat_id}" class="beat-text beat-text-main" rows="3">${esc(b.narration || "")}</textarea></td>
      <td>${b.planned_sec ?? b.duration_sec ?? "-"}s</td>
      <td>${b.actual_sec ?? "-"}s</td>
      <td>${drift}</td>
      <td><span class="${statusClass(b.cps_band)}">${cps}</span></td>
      <td>${statusBadge(b.review_status)}</td>
      <td data-tts-beat="${b.beat_id}">${beatTtsStatusHtml(b.beat_id, prog)}</td>
      <td class="beat-audio-cell">${b.vo_wav
        ? `<button type="button" class="btn btn-secondary btn-compact beat-audio-btn" data-beat="${b.beat_id}" title="试听 ${b.beat_id}" onclick="playBeatAudio('${b.beat_id}','${escAttr(b.vo_wav)}')">▶</button>`
        : `<span class="tts-beat-idle">—</span>`}</td>
      <td class="col-actions">
        <div class="beat-actions">
        <button class="btn btn-secondary btn-compact" onclick="saveBeat('${b.beat_id}')">保存</button>
        <button class="btn btn-secondary btn-compact" onclick="regenBeatTts('${b.beat_id}', true)">配音+对齐</button>
        <button class="btn btn-secondary btn-compact" onclick="regenBeatTts('${b.beat_id}', false)">仅配音</button>
        </div>
      </td>
    </tr>`;
  }).join("");
}

async function renderBeats() {
  let prog = lastTtsProgress;
  try {
    prog = await api("/tts/progress");
    lastTtsProgress = prog;
  } catch { /* optional */ }

  const summary = await api(`/audio/summary?segment=${currentSegment}`);
  const { beats } = await api(`/beats?segment=${currentSegment}`);
  const tts = summary.tts || {};
  let cfg = {};
  try {
    cfg = (await api("/tts/config")).config || {};
  } catch {
    cfg = {};
  }
  const refs = summary.refs || { refs: [], selected_path: "" };
  const defaults = cfg.defaults || {};
  const selectedRef = refs.selected_path || cfg.voice_reference?.path || "";
  const attentionCount = beats.filter(beatNeedsAttention).length;

  const selectedRefName = (selectedRef || "").split("/").pop() || "未设置";
  const settingsHint = `${selectedRefName} · ${cfg.base_url || "未配置"}`;

  document.getElementById("beats").innerHTML = pageWrap(
    "口播 & 配音",
    `${currentSegment} · ${beats.length} 条 beat · 编辑口播、IndexTTS 配音与时长对齐`,
    `
    <div class="card card-no-accent vo-summary-card">
      <div class="vo-summary-metrics">
        <p class="metric">IndexTTS · <strong>${tts.available ? "在线" : "离线"}</strong> ${esc(tts.base_url || tts.reason || "")}</p>
        <p class="metric">参考音 · <strong>${tts.reference_exists ? "已就绪" : "缺失"}</strong> ${esc(tts.reference_path || selectedRef || "未设置")}</p>
        <p class="metric">计划总长 <strong>${summary.planned_total_sec}s</strong> · 实测 <strong>${summary.actual_total_sec}s</strong> · 偏差 <strong>${summary.drift_total_sec}s</strong>${attentionCount ? ` · <strong>${attentionCount}</strong> 条需关注` : ""}</p>
      </div>
      <div class="tts-progress-wrap">
        <p id="tts-progress-label" class="metric">配音进度：空闲</p>
        <div class="tts-progress-track"><div id="tts-progress-bar" class="tts-progress-bar"></div></div>
      </div>
      <div class="vo-chain-row">
        <div class="toolbar vo-chain-toolbar">
          <button class="btn btn-primary" onclick="runPreset('audio_chain_tts').catch(e=>toast(e.message))">完整链：配音→对齐</button>
          <button class="btn btn-secondary" onclick="runPreset('indextts_segment').catch(e=>toast(e.message))">仅整段配音</button>
          <button class="btn btn-secondary" onclick="runPreset('audio_chain').catch(e=>toast(e.message))">仅对齐（不配音）</button>
          <button class="btn btn-secondary" onclick="runPreset('audio_chain_build').catch(e=>toast(e.message))">对齐 + 重建画面</button>
          <button class="btn btn-secondary" onclick="runPreset('measure_vo').catch(e=>toast(e.message))">测量时长</button>
          <button class="btn btn-secondary" onclick="runPreset('build_micro_timing').catch(e=>toast(e.message))">微事件对齐</button>
          <button class="btn btn-secondary" onclick="checkTtsHealth().catch(e=>toast(e.message))">检测 IndexTTS</button>
        </div>
        <label class="tts-force-label" title="勾选后覆盖已有 WAV；不勾选则跳过已生成的 beat，从中断处继续">
          <input type="checkbox" id="tts-force-redub" />
          重新配音（覆盖已有音频）
        </label>
      </div>
      <pre id="vo-log" class="vo-log"></pre>
    </div>
    <div class="card card-no-accent vo-settings-card">
      <button type="button" id="vo-settings-toggle" class="collapse-header" aria-expanded="false">
        <span class="toggle-icon">▼</span>
        <span class="emoji">⚙️</span>
        <span>配音设置</span>
        <span class="collapse-hint">${esc(settingsHint)}</span>
      </button>
      <div id="vo-settings-panel" class="collapse-panel collapsed vo-settings-panel">
        <section class="vo-settings-section">
          <div class="card-icon-title"><span class="emoji">🎧</span><h3>参考音频库</h3></div>
          <p class="metric">共 <strong>${(refs.refs || []).length}</strong> 条 · WAV / MP3 · 当前 <strong>${esc(selectedRefName)}</strong></p>
          ${tableWrap(`<thead><tr><th>名称</th><th>大小</th><th>上传</th><th>试听</th><th>操作</th></tr></thead>
            <tbody>${renderRefLibraryRows(refs)}</tbody>`)}
          <div id="ref-upload-status" class="ref-upload-status hidden">
            <p id="ref-upload-label" class="metric">准备上传…</p>
            <div class="tts-progress-track"><div id="ref-upload-bar" class="tts-progress-bar indeterminate"></div></div>
          </div>
          <div class="toolbar">
            <input id="tts-ref-upload" class="ios-input ref-upload-input" type="file" accept=".wav,.mp3,audio/wav,audio/mpeg,audio/mp3" />
            <button type="button" id="ref-upload-btn" class="btn btn-primary" onclick="uploadTtsRef().catch(e=>toast(e.message))">上传</button>
          </div>
        </section>
        <section class="vo-settings-section vo-settings-section-divider">
          <div class="card-icon-title"><span class="emoji">🔧</span><h3>IndexTTS 配置</h3></div>
          <div class="ios-group">
            <div class="group-caption">服务地址</div>
            <div class="ios-group-body">
              <div class="field-row field-row-stack">
                <label class="field-label" for="tts-base-url">Gradio 地址</label>
                <input id="tts-base-url" class="ios-input" type="url" placeholder="http://10.0.221.33:37191/" value="${escAttr(cfg.base_url || "")}" />
              </div>
            </div>
          </div>
          <div class="ios-group" style="margin-top:12px">
            <div class="group-caption">生成参数</div>
            <div class="ios-group-body">
              <div class="field-row">
                <label class="field-label" for="tts-emo-weight">情感权重</label>
                <input id="tts-emo-weight" class="ios-input" type="number" step="0.05" min="0" max="1" value="${defaults.emo_weight ?? 0.65}" />
              </div>
              <div class="field-divider"></div>
              <div class="field-row">
                <label class="field-label" for="tts-temperature">Temperature</label>
                <input id="tts-temperature" class="ios-input" type="number" step="0.05" min="0" max="2" value="${defaults.temperature ?? 0.8}" />
              </div>
              <div class="field-divider"></div>
              <div class="field-row">
                <label class="field-label" for="tts-top-p">Top P</label>
                <input id="tts-top-p" class="ios-input" type="number" step="0.05" min="0" max="1" value="${defaults.top_p ?? 0.8}" />
              </div>
            </div>
          </div>
          <div class="toolbar">
            <button class="btn btn-primary" onclick="saveTtsConfig().catch(e=>toast(e.message))">保存配置</button>
            <button class="btn btn-secondary" onclick="checkTtsHealth().catch(e=>toast(e.message))">检测连接</button>
          </div>
        </section>
      </div>
    </div>
    <div class="card card-no-accent vo-main-card">
      <div class="beats-filter-bar">
        <label class="beats-filter-label">
          <input type="checkbox" id="beats-filter-attention" onchange="toggleBeatsFilter()" />
          仅显示需关注（偏差 &gt;0.3s 或 CPS 异常）
        </label>
        <span id="beats-filter-count" class="metric"></span>
      </div>
      <div class="beats-table-wrap">
        ${tableWrap(`<thead><tr>
          <th class="col-beat-id">Beat</th><th class="col-narration">口播</th><th class="col-metric">计划</th><th class="col-metric">实测</th><th class="col-metric">偏差</th><th class="col-metric">CPS</th><th class="col-status">状态</th><th class="col-status">配音</th><th class="col-audio">音频</th><th class="col-actions">操作</th>
        </tr></thead><tbody id="beats-table-body">${renderBeatTableRows(beats, prog)}</tbody>`)}
      </div>
    </div>`
  );

  window.__beatsAllRows = beats;
  initCollapsiblePanel("vo-settings-toggle", "vo-settings-panel", "rs-vo-settings-collapsed", true);
  bindTtsForceRedubCheckbox();
  bindRefUploadInput();
  updateTtsProgressBar(summary.progress || prog);
  updateBeatsTtsCells(prog);
  updateBeatsFilterCount();
}

window.toggleBeatsFilter = () => {
  const onlyAttention = document.getElementById("beats-filter-attention")?.checked;
  const beats = window.__beatsAllRows || [];
  document.querySelectorAll("[data-beat-row]").forEach(row => {
    const beatId = row.dataset.beatRow;
    const beat = beats.find(b => b.beat_id === beatId);
    if (!beat) return;
    row.style.display = onlyAttention && !beatNeedsAttention(beat) ? "none" : "";
  });
  updateBeatsFilterCount();
};

function updateBeatsFilterCount() {
  const el = document.getElementById("beats-filter-count");
  if (!el) return;
  const beats = window.__beatsAllRows || [];
  const onlyAttention = document.getElementById("beats-filter-attention")?.checked;
  const visible = onlyAttention ? beats.filter(beatNeedsAttention).length : beats.length;
  el.textContent = `显示 ${visible} / ${beats.length} 条`;
}

window.openBeatDetail = async (beatId) => {
  selectedBeatId = beatId;
  const beat = await api(`/beats/${beatId}?segment=${currentSegment}`);
  document.getElementById("beat-drawer-title").textContent = beatId;
  const micro = (beat.micro_events || []).map(ev =>
    `<li>${ev.id} @ ${ev.t}s — ${esc((ev.visual_action || "").slice(0, 60))}</li>`
  ).join("");
  document.getElementById("beat-drawer-body").innerHTML = `
    <p><strong>口播</strong></p>
    <textarea id="drawer-narration" class="beat-text" rows="4">${esc(beat.narration || "")}</textarea>
    <p class="metric">计划 ${beat.planned_sec ?? "-"}s · 实测 ${beat.vo?.duration_sec ?? "-"}s · CPS ${beat.vo?.cps ?? "-"}</p>
    <p class="metric">Claim ${esc(beat.claim_ids || "-")} · 动作 ${esc(beat.semantic_action || "-")}</p>
    ${beat.vo_wav ? `<button type="button" class="btn btn-secondary btn-compact beat-audio-btn" data-beat="${beatId}" onclick="playBeatAudio('${beatId}','${escAttr(beat.vo_wav)}')">▶ 试听</button>` : ""}
    <p style="margin-top:12px"><strong>IndexTTS 配音状态</strong></p>
    <div id="drawer-tts-st-${beatId}" class="beat-drawer-tts">${beatTtsStatusHtml(beatId, lastTtsProgress)}</div>
    <p><strong>微事件 (${(beat.micro_events || []).length})</strong></p>
    <ul>${micro || "<li>无</li>"}</ul>
    <div class="toolbar">
      <button class="btn btn-primary" onclick="saveBeatFromDrawer('${beatId}')">保存口播</button>
      <button class="btn btn-secondary" onclick="regenBeatTts('${beatId}', true)">配音+对齐</button>
      <button class="btn btn-secondary" onclick="regenBeatTts('${beatId}', false)">仅配音</button>
    </div>
    <div class="ios-group" style="margin-top:16px">
      <div class="group-caption">手动时长</div>
      <div class="ios-group-body">
        <div class="field-row field-row-stack">
          <label class="field-label" for="drawer-duration">时长（秒）</label>
          <input id="drawer-duration" class="ios-input" type="number" step="0.01" value="${beat.vo?.duration_sec ?? ""}" />
        </div>
        <div class="field-divider"></div>
        <div class="field-row">
          <label class="field-label" for="drawer-locked">锁定时长</label>
          <input id="drawer-locked" type="checkbox" ${beat.vo?.locked ? "checked" : ""} style="width:22px;height:22px;accent-color:var(--accent)" />
        </div>
      </div>
    </div>
    <div class="toolbar">
      <button class="btn btn-secondary" onclick="patchBeatDuration('${beatId}')">应用手动时长</button>
    </div>`;
  openSheet();
};

window.saveBeatFromDrawer = async (beatId) => {
  const narration = document.getElementById("drawer-narration").value;
  await api(`/beats/${beatId}?segment=${currentSegment}`, { method: "PATCH", body: JSON.stringify({ narration }) });
  toast(`${beatId} 已保存`);
  await renderBeats();
};

window.patchBeatDuration = async (beatId) => {
  const duration = parseFloat(document.getElementById("drawer-duration").value);
  const locked = document.getElementById("drawer-locked").checked;
  await api(`/timing/beats/${beatId}?segment=${currentSegment}`, {
    method: "PATCH",
    body: JSON.stringify({ duration_sec: duration, locked }),
  });
  toast(`${beatId} 时长已更新`);
  await renderTimeline();
};

async function saveBeat(beatId) {
  const narration = document.getElementById(`n-${beatId}`).value;
  await api(`/beats/${beatId}?segment=${currentSegment}`, { method: "PATCH", body: JSON.stringify({ narration }) });
  toast(`${beatId} 已保存 · 下游已过期`);
  await renderBeats();
}

window.regenBeatTts = async (beatId, align = true) => {
  try {
    await ensureTtsOnline();
  } catch (err) {
    toast(String(err.message || err));
    return;
  }
  const preset = align ? "indextts_beats_align" : "indextts_beats";
  await fetch(`${API}/jobs/preset/${preset}?segment=${currentSegment}&beats=${beatId}`, { method: "POST" })
    .then(r => r.json())
    .then(d => {
      if (d.detail) throw new Error(typeof d.detail === "string" ? d.detail : JSON.stringify(d.detail));
      toast(`${beatId} 配音任务：${statusZh(d.job?.status)}`);
      const logEl = document.getElementById("vo-log");
      pollJob(d.job.id, logEl, { isTts: true });
      startBeatsTtsTracking(d.job.id, [beatId]);
      const drawerSt = document.getElementById(`drawer-tts-st-${beatId}`);
      if (drawerSt) drawerSt.innerHTML = beatTtsStatusHtml(beatId, { status: "running", current_beat: beatId, beat_status: { [beatId]: "running" } });
    })
    .catch(e => toast(String(e.message || e)));
};

// --- Audio helpers (sidebar in 口播 & 配音) ---
window.selectTtsRef = async (path) => {
  await api("/audio/refs/select", { method: "PUT", body: JSON.stringify({ path }) });
  toast(`已选用：${path.split("/").pop()}`);
  await renderBeats();
};

window.deleteTtsRef = async (path, name) => {
  if (!confirm(`确定删除参考音频「${name}」？`)) return;
  const q = new URLSearchParams({ path });
  const res = await fetch(`${API}/audio/refs?${q}`, { method: "DELETE" });
  const data = await res.json();
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data));
  toast(`已删除：${name}`);
  await renderBeats();
};

window.saveTtsConfig = async () => {
  const baseUrl = document.getElementById("tts-base-url")?.value.trim();
  const body = {
    base_url: baseUrl,
    webui_url: baseUrl,
    defaults: {
      emo_weight: parseFloat(document.getElementById("tts-emo-weight")?.value || "0.65"),
      temperature: parseFloat(document.getElementById("tts-temperature")?.value || "0.8"),
      top_p: parseFloat(document.getElementById("tts-top-p")?.value || "0.8"),
    },
  };
  const res = await api("/tts/config", { method: "PUT", body: JSON.stringify(body) });
  toast(`配置已保存 · IndexTTS ${res.health?.available ? "在线" : "离线"}`);
  await renderBeats();
};

window.uploadTtsRef = async () => {
  const input = document.getElementById("tts-ref-upload");
  const file = input?.files?.[0];
  if (!file) throw new Error("请先选择 WAV 或 MP3 文件");
  const lower = file.name.toLowerCase();
  if (!lower.endsWith(".wav") && !lower.endsWith(".mp3")) {
    throw new Error("仅支持 .wav 和 .mp3 文件");
  }
  const form = new FormData();
  form.append("file", file, file.name);
  setRefUploadUi(true, "正在上传…", 8);
  let res;
  try {
    res = await fetch(`${API}/audio/refs/upload?select=true`, { method: "POST", body: form });
  } catch (err) {
    setRefUploadUi(false);
    throw err;
  }
  let data = {};
  try {
    data = await res.json();
  } catch {
    data = {};
  }
  if (!res.ok) {
    setRefUploadUi(false);
    throw new Error(parseFetchError(data, `上传失败 (${res.status})`));
  }
  setRefUploadUi(true, "已接收，准备转码…", 15);
  const finalState = await pollRefUpload(data.upload_id);
  setRefUploadUi(false);
  toast(`已上传：${finalState.result?.path || file.name}`);
  if (input) input.value = "";
  await renderBeats();
};

window.checkTtsHealth = async () => {
  const health = await api("/tts/health");
  toast(`IndexTTS ${health.available ? "在线" : "离线"} · ${health.base_url || health.reason || ""}`);
  await renderBeats();
};

// --- Assets ---
async function renderAssets() {
  const { assets } = await api(`/assets?segment=${currentSegment}`);
  const visual = assets.filter(a => ASSET_PREVIEW_RE.test(a.path_or_url || ""));
  const missing = visual.filter(a => !a.exists).length;
  const videoCount = visual.filter(a => assetMediaKind(a.path_or_url || a.media_path) === "video").length;
  const subtitle = `${currentSegment} · 共 ${visual.length} 项${videoCount ? `（${videoCount} 视频）` : ""}${missing ? ` · ${missing} 项未生成` : ""} · 点击缩略图预览`;
  document.getElementById("assets").innerHTML = pageWrap("媒体资产", subtitle, `${missing ? `<div class="card card-no-accent asset-missing-banner"><p class="metric">有 ${missing} 个资产在 manifest 中已登记但磁盘上尚无文件。请生成 <code>segments/${currentSegment}/assets/</code> 下对应文件后刷新，或运行 <code>python scripts/review_sync.py &lt;project&gt;</code> 同步。</p></div>` : ""}<div class="asset-grid">${visual.map(a => {
    const path = a.media_path || a.path_or_url || "";
    const kind = assetMediaKind(path || a.path_or_url || "");
    const previewLabel = kind === "video" ? "播放" : "放大";
    return `
    <article class="card asset-card card-no-accent${a.exists ? "" : " asset-card-missing"}">
      ${assetThumb(a)}
      <h3>${a.asset_id}</h3>
      ${kind ? `<span class="status draft asset-kind-badge">${assetKindLabel(kind)}</span>` : ""}
      ${a.exists ? "" : `<span class="status draft">未生成</span>`}
      ${statusBadge(a.review_status || "review")}
      <p class="metric asset-path">${esc(a.path_or_url || "")}</p>
      <div class="toolbar">
        <button class="btn btn-primary btn-compact" onclick="reviewAsset('${a.asset_id}','approved')" ${a.exists ? "" : "disabled title=\"请先生成文件\""}>通过</button>
        <button class="btn btn-secondary btn-compact" onclick="rejectAsset('${a.asset_id}')">驳回</button>
        <button class="btn btn-secondary btn-compact" onclick="openAssetLightbox('${escAttr(path)}','${escAttr(a.asset_id)}')" ${a.exists ? "" : "disabled"}>${previewLabel}</button>
        <button class="btn btn-secondary btn-compact" onclick="openAssetFolder('${escAttr(path || a.path_or_url)}')">打开目录</button>
        <button class="btn btn-secondary btn-compact" onclick="enqueueAsset('${a.asset_id}')">加入待办</button>
      </div>
    </article>`;
  }).join("") || `<div class="card card-no-accent"><p class="metric">暂无媒体资产</p></div>`}</div>`);
}

window.openAssetFolder = async (path) => {
  if (!path) return toast("无可用路径");
  try {
    const res = await api("/dialog/reveal-path", { method: "POST", body: JSON.stringify({ path }) });
    toast(res.selected ? "已在文件管理器中定位文件" : "已在文件管理器中打开目录");
  } catch (err) {
    toast(String(err.message || err));
  }
};

async function reviewAsset(assetId, status) {
  await api(`/assets/${assetId}/review`, { method: "POST", body: JSON.stringify({ status, note: "UI review" }) });
  toast(`${assetId} → ${status}`);
  await renderAssets();
  await loadProjectMeta();
}

async function rejectAsset(assetId) {
  const note = prompt("驳回原因：", "视觉问题") || "已驳回";
  await api(`/assets/${assetId}/review`, { method: "POST", body: JSON.stringify({ status: "rejected", note }) });
  toast(`${assetId} 已驳回`);
  await renderAssets();
  await renderTimeline();
  await loadProjectMeta();
}

async function enqueueAsset(assetId) {
  await api("/regen-queue", {
    method: "POST",
    body: JSON.stringify({
      target_artifact_id: `asset:${assetId}`,
      action: "regenerate_svg",
      reason: "Rejected in Review Studio",
      commands_suggested: [
        `edit segments/${currentSegment}/assets/${assetId}.svg`,
        `python scripts/build_${currentSegment.toLowerCase()}_composition.py`,
      ],
    }),
  });
  toast(`${assetId} 已加入待办`);
  await renderQueue();
}

// --- Timeline Editor (preview + zoom + scrub) ---
async function renderTimeline() {
  if (timelineEditorHandle) {
    timelineEditorHandle.destroy();
    timelineEditorHandle = null;
  }
  timelineData = await api(`/timeline?segment=${currentSegment}`);
  let project = { render_blocked: null };
  try {
    project = await api("/project");
  } catch { /* optional */ }
  const total = Number(timelineData.total_sec || 211);
  document.getElementById("timeline").innerHTML = pageWrap(
    "时间轴",
    `${currentSegment} · ${total.toFixed(1)} 秒 · 预览与编辑（OpenCut 式 transport + 缩放）`,
    `<div id="timeline-editor-host"></div>`
  );
  const host = document.getElementById("timeline-editor-host");
  if (!host || !window.TimelineEditor) {
    if (host) host.innerHTML = `<p class="metric">时间轴编辑器加载失败</p>`;
    return;
  }
  timelineEditorHandle = TimelineEditor.mount(host, {
    data: timelineData,
    segment: currentSegment,
    mediaUrl,
    api,
    selectedBeatId,
    onBeatSelect: (beatId) => {
      selectedBeatId = beatId;
    },
    onBeatOpen: (beatId) => openBeatDetail(beatId),
    onRefresh: renderTimeline,
    renderBlocked: project.render_blocked ? String(project.render_blocked) : "",
    runPreset,
    pollJob,
    toast,
  });
}

// --- Stage Detail ---
async function renderStageDetail() {
  const { stages } = await api("/stages");
  const stage = stages.find(s => s.id === selectedStageId) || stages[0];
  if (stage) selectedStageId = stage.id;
  const { artifacts } = await api(`/stages/${selectedStageId}/artifacts?segment=${currentSegment}`);
  const stageOpts = stages.map(s => `<option value="${s.id}" ${s.id === selectedStageId ? "selected" : ""}>${s.label || s.id}</option>`).join("");
  const artRows = artifacts.map(a => `
    <tr>
      <td>${a.required ? "✓" : ""}</td>
      <td>${esc(a.path)}</td>
      <td>${a.exists ? "有" : "缺失"}</td>
      <td>${statusBadge(a.review_status)}</td>
      <td>${a.exists ? `<button class="btn btn-secondary btn-compact" onclick="editArtifact('${a.path.replace(/'/g, "\\'")}')">编辑</button>` : ""}</td>
    </tr>`).join("");
  document.getElementById("stage").innerHTML = pageWrap("阶段详情", "逐阶段产物查看与编辑", `
    <div class="card card-no-accent">
      <div class="ios-group-body" style="background:transparent;box-shadow:none;margin-bottom:16px">
        <div class="field-row">
          <label class="field-label" for="stage-select">选择阶段</label>
          <select id="stage-select" class="ios-select" onchange="selectedStageId=this.value;renderStageDetail()">${stageOpts}</select>
        </div>
      </div>
      <p>${statusBadge(stage?.status)}</p>
      <div class="toolbar">
        <button class="btn btn-primary btn-compact" onclick="approveStage('${selectedStageId}')">通过</button>
        <button class="btn btn-secondary btn-compact" onclick="validateStage('${selectedStageId}')">运行校验</button>
      </div>
      ${tableWrap(`<thead><tr><th>必需</th><th>产物路径</th><th>存在</th><th>审核</th><th></th></tr></thead>
      <tbody>${artRows}</tbody>`)}
      <div id="artifact-editor" class="editor-host"></div>
    </div>`);
}

window.validateStage = async (stageId) => {
  const res = await api(`/stages/${stageId}/validate?segment=${currentSegment}`, { method: "POST" });
  toast(res.skipped ? "此阶段无校验脚本" : `已启动 ${res.jobs?.length || 0} 个校验任务`);
  await renderJobs();
};

window.editArtifact = async (path) => {
  const data = await api(`/artifacts/${path}`);
  if (data.content == null) return toast("二进制文件请在资源管理器中打开");
  const host = document.getElementById("artifact-editor");
  host.innerHTML = `<div id="artifact-editor-pane"></div>`;
  mountEditor("artifact-editor-pane", {
    id: `art-${path}`,
    path,
    value: data.content,
    height: "min(72vh, 680px)",
    defaultMode: "split",
    saveLabel: "保存产物",
    onSave: async (content) => {
      await api(`/artifacts/${path}?segment=${currentSegment}`, { method: "PUT", body: JSON.stringify({ content, note: "阶段编辑器" }) });
      toast("已保存 · 下游已过期");
      await renderStageDetail();
    },
  });
  host.scrollIntoView({ behavior: "smooth", block: "nearest" });
};

window.saveArtifact = async (path) => {
  const content = editorGetValue("artifact-editor-pane");
  await api(`/artifacts/${path}?segment=${currentSegment}`, { method: "PUT", body: JSON.stringify({ content, note: "阶段编辑器" }) });
  toast("已保存 · 下游已过期");
  await renderStageDetail();
};

// --- Queue / Jobs / QC / History ---
async function renderQueue() {
  const data = await api("/regen-queue");
  const items = data.items || [];
  document.getElementById("queue").innerHTML = pageWrap("重生待办", "Agent 待处理任务队列", `<div class="card card-no-accent">
    ${tableWrap(`<thead><tr><th>编号</th><th>目标</th><th>动作</th><th>状态</th><th>原因</th></tr></thead>
    <tbody>${items.map(i => `<tr>
      <td>${i.id}</td><td>${i.target_artifact_id}</td><td>${i.action || ""}</td><td>${statusZh(i.status)}</td><td>${esc(i.reason || "")}</td>
    </tr>`).join("") || "<tr><td colspan=5>暂无待办</td></tr>"}
    </tbody>`)}
  </div>`);
}

async function renderJobs() {
  const { jobs } = await api("/jobs?limit=30");
  document.getElementById("jobs").innerHTML = pageWrap("后台任务", "脚本执行与日志", `<div class="card card-no-accent">
    ${tableWrap(`<thead><tr><th>任务</th><th>状态</th><th>退出码</th><th>创建时间</th></tr></thead>
    <tbody>${jobs.map(j => `<tr class="job-${j.status}">
      <td>${esc(j.label || j.script)}</td><td>${statusZh(j.status)}</td><td>${j.exit_code ?? "-"}</td><td>${(j.created_at || "").slice(0, 19)}</td>
    </tr>`).join("") || "<tr><td colspan=4>暂无任务</td></tr>"}
    </tbody>`)}
    ${jobs[0] ? `<pre>${esc(jobs[0].stdout_tail || jobs[0].stderr_tail || "")}</pre>` : ""}
  </div>`);
}

async function renderQc() {
  const files = [
    `segments/${currentSegment}/timing_qc_report.md`,
    "edit/aesthetic_report.md",
    "edit/qc_report.md",
  ];
  const parts = await Promise.all(files.map(async f => {
    try {
      const res = await fetch(`/api/media/${f}`);
      if (!res.ok) return "";
      const text = await res.text();
      return `<div class="card"><h3>${f}</h3><pre>${esc(text.slice(0, 4000))}</pre></div>`;
    } catch { return ""; }
  }));
  document.getElementById("qc").innerHTML = pageWrap("质量检查", "时长 / 美学 / 综合 QC 报告", `<div class="grid">${parts.join("")}</div>`);
}

async function renderHistory() {
  const { events } = await api("/history?limit=50");
  document.getElementById("history").innerHTML = pageWrap("操作历史", "人工与 Agent 审计日志", `<div class="card card-no-accent"><pre>${esc(JSON.stringify(events, null, 2))}</pre></div>`);
}

// --- Init ---
document.getElementById("workspace-browse-btn").addEventListener("click", browseWorkspace);
document.getElementById("workspace-scan-btn").addEventListener("click", async () => {
  const path = document.getElementById("workspace-input").value.trim();
  if (path) await setWorkspaceRoot();
  else await scanWorkspace();
});
document.getElementById("project-select").addEventListener("change", async (ev) => {
  if (ev.target.value) await switchProject(ev.target.value);
});
document.getElementById("project-browse-btn").addEventListener("click", browseProject);
document.getElementById("project-open-btn").addEventListener("click", async () => {
  await switchProject(document.getElementById("project-path-input").value.trim());
});
document.getElementById("segment-select")?.addEventListener("change", async (ev) => {
  currentSegment = ev.target.value;
  await loadProjectMeta();
  await refreshActiveView();
});
document.getElementById("beat-drawer-close")?.addEventListener("click", closeSheet);
document.getElementById("sheet-backdrop")?.addEventListener("click", closeSheet);

(async function init() {
  initTabs();
  initWorkspaceToggle();
  initLightbox();
  await loadWorkspace();
  await refreshSegment();
  await loadProjectMeta();
  if (!document.getElementById("project-meta").textContent.startsWith("请先")) {
    await renderPipeline();
  }
  try {
    const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/events`);
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === "project_switched") afterProjectChange();
      if (data.type === "registry_updated" || data.type === "state_updated") loadProjectMeta();
      if (data.type === "job_progress") {
        renderJobs();
        api("/tts/progress").then(prog => {
          updateTtsProgressBar(prog);
          updateBeatsTtsCells(prog);
        }).catch(() => {});
      }
    };
  } catch (_) { /* optional */ }
})();
