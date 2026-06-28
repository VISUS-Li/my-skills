const API = "/api";
let currentSegment = "S001";
let activeView = "pipeline";
let selectedStageId = "script";
let selectedBeatId = null;
let timelineData = null;
let dragState = null;
let activeEditors = {};
let lightboxZoom = 1;

const TABS = [
  { view: "pipeline", icon: "🎬", label: "流程" },
  { view: "script", icon: "📝", label: "文案" },
  { view: "beats", icon: "🎯", label: "Beats" },
  { view: "audio", icon: "🎙️", label: "音频" },
  { view: "assets", icon: "🖼️", label: "资产" },
  { view: "timeline", icon: "⏱️", label: "时间轴" },
  { view: "preview", icon: "▶️", label: "预览" },
  { view: "stage", icon: "📦", label: "阶段" },
  { view: "queue", icon: "📋", label: "待办" },
  { view: "jobs", icon: "⚙️", label: "任务" },
  { view: "qc", icon: "✅", label: "质检" },
  { view: "history", icon: "📜", label: "历史" },
];

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

function statusBadge(s) {
  return `<span class="${statusClass(s)}">${esc(statusZh(s))}</span>`;
}

function mediaUrl(path) {
  if (!path) return "";
  return `/api/media/${String(path).split(/[/\\]/).filter(Boolean).map(encodeURIComponent).join("/")}`;
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
  const close = () => {
    lb?.classList.add("hidden");
    backdrop?.classList.add("hidden");
    document.getElementById("lightbox-content").innerHTML = "";
    lightboxZoom = 1;
  };
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

window.openAssetLightbox = async (path, title) => {
  const lb = document.getElementById("asset-lightbox");
  const backdrop = document.getElementById("lightbox-backdrop");
  const content = document.getElementById("lightbox-content");
  const url = mediaUrl(path);
  document.getElementById("lightbox-title").textContent = title || path;
  lightboxZoom = 1;
  content.style.transform = "scale(1)";
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

function assetThumb(path, assetId) {
  const url = mediaUrl(path);
  return `<div class="asset-thumb" onclick="openAssetLightbox('${escAttr(path)}','${escAttr(assetId)}')" title="点击放大">
    <img src="${url}" alt="${esc(assetId)}" loading="lazy" onerror="assetThumbFallback(this,'${escAttr(path)}')" />
    <span class="zoom-hint">🔍 放大</span>
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

function statusClass(status) {
  return `status ${status || "draft"}`;
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
    audio: renderAudio,
    assets: renderAssets,
    timeline: renderTimeline,
    preview: renderPreview,
    stage: renderStageDetail,
    queue: renderQueue,
    jobs: renderJobs,
    qc: renderQc,
    history: renderHistory,
  };
  if (map[activeView]) await map[activeView]();
}

async function runPreset(name, extra = "") {
  const url = `/jobs/preset/${name}?segment=${currentSegment}${extra}`;
  const res = await fetch(`${API}${url}`, { method: "POST" });
  const data = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(data));
  toast(`任务 ${name}：${data.job.status === "queued" ? "已排队" : data.job.status}`);
  pollJob(data.job.id);
  return data.job;
}

async function pollJob(jobId, logEl) {
  for (let i = 0; i < 120; i++) {
    await new Promise(r => setTimeout(r, 1000));
    const { job } = await api(`/jobs/${jobId}`);
    if (logEl) logEl.textContent = `[${job.status}] ${job.label || job.script}\n${job.stdout_tail || ""}\n${job.stderr_tail || ""}`;
    if (job.status === "completed" || job.status === "failed") {
      toast(`任务${job.status === "completed" ? "完成" : "失败"}`);
      if (job.status === "completed") await refreshActiveView();
      return job;
    }
  }
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
      <p class="metric">共 <strong>${beats.length}</strong> 条 · 详细编辑请前往「Beats」· 改口播后请到「音频」跑对齐链</p>
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

// --- Beats ---
async function renderBeats() {
  const { beats } = await api(`/beats?segment=${currentSegment}`);
  document.getElementById("beats").innerHTML = pageWrap("Beats 口播", `${currentSegment} · 逐条编辑、试听与 TTS`, tableWrap(`<thead><tr>
    <th>Beat</th><th>口播</th><th>计划</th><th>实测</th><th>偏差</th><th>CPS</th><th>状态</th><th>操作</th>
  </tr></thead><tbody>${beats.map(b => {
    const cps = b.vo?.cps ?? (b.char_count && b.actual_sec ? (Number(b.char_count)/Number(b.actual_sec)).toFixed(1) : "-");
    const drift = b.drift_sec != null ? `${b.drift_sec > 0 ? "+" : ""}${b.drift_sec}s` : "-";
    return `<tr>
      <td><a href="#" onclick="openBeatDetail('${b.beat_id}');return false">${b.beat_id}</a></td>
      <td><textarea id="n-${b.beat_id}" class="beat-text" rows="2">${esc(b.narration || "")}</textarea></td>
      <td>${b.planned_sec ?? b.duration_sec ?? "-"}s</td>
      <td>${b.actual_sec ?? "-"}s</td>
      <td>${drift}</td>
      <td><span class="${statusClass(b.cps_band)}">${cps}</span></td>
      <td>${statusBadge(b.review_status)}</td>
      <td>
        <button class="btn btn-secondary btn-compact" onclick="saveBeat('${b.beat_id}')">保存</button>
        <button class="btn btn-secondary btn-compact" onclick="regenBeatTts('${b.beat_id}')">配音</button>
        ${b.vo_wav ? `<audio controls src="${mediaUrl(b.vo_wav)}"></audio>` : ""}
      </td>
    </tr>`;
  }).join("")}</tbody>`));
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
    ${beat.vo_wav ? `<audio controls src="${mediaUrl(beat.vo_wav)}"></audio>` : ""}
    <p><strong>微事件 (${(beat.micro_events || []).length})</strong></p>
    <ul>${micro || "<li>无</li>"}</ul>
    <div class="toolbar">
      <button class="btn btn-primary" onclick="saveBeatFromDrawer('${beatId}')">保存口播</button>
      <button class="btn btn-secondary" onclick="regenBeatTts('${beatId}')">重生成 TTS</button>
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

window.regenBeatTts = async (beatId) => {
  await fetch(`${API}/jobs/preset/indextts_beats?segment=${currentSegment}&beats=${beatId}`, { method: "POST" })
    .then(r => r.json())
    .then(d => { toast(`配音任务：${statusZh(d.job?.status)}`); pollJob(d.job.id); });
};

// --- Audio Lab ---
async function renderAudio() {
  const summary = await api(`/audio/summary?segment=${currentSegment}`);
  const tts = summary.tts || {};
  const driftRows = (summary.drift_beats || []).slice(0, 20).map(b =>
    `<tr><td>${b.beat_id}</td><td>${b.planned_sec}s</td><td>${b.duration_sec}s</td>
    <td>${b.drift_sec > 0 ? "+" : ""}${b.drift_sec}s</td>
    <td><span class="${statusClass(b.cps_band)}">${b.cps}</span></td></tr>`
  ).join("");
  document.getElementById("audio").innerHTML = pageWrap("音频实验室", "IndexTTS 配音与时长对齐", `
    <div class="card card-no-accent">
      <div class="card-icon-title"><span class="emoji">🎙️</span><h3>连接与时长</h3></div>
      <p class="metric">IndexTTS · <strong>${tts.available ? "在线" : "离线"}</strong> ${esc(tts.base_url || tts.reason || "")}</p>
      <p class="metric">计划总长 <strong>${summary.planned_total_sec}s</strong> · 实测 <strong>${summary.actual_total_sec}s</strong> · 偏差 <strong>${summary.drift_total_sec}s</strong></p>
      <div class="toolbar">
        <button class="btn btn-primary" onclick="runPreset('audio_chain_tts').catch(e=>toast(e.message))">完整链：配音→对齐</button>
        <button class="btn btn-secondary" onclick="runPreset('audio_chain').catch(e=>toast(e.message))">仅对齐（不配音）</button>
        <button class="btn btn-secondary" onclick="runPreset('audio_chain_build').catch(e=>toast(e.message))">对齐 + 重建画面</button>
        <button class="btn btn-secondary" onclick="runPreset('measure_vo').catch(e=>toast(e.message))">测量时长</button>
        <button class="btn btn-secondary" onclick="runPreset('build_micro_timing').catch(e=>toast(e.message))">微事件对齐</button>
      </div>
      <pre id="audio-log"></pre>
    </div>
    <div class="card card-no-accent" style="margin-top:20px">
      <h3>时长偏差 Beats（${(summary.drift_beats || []).length}）</h3>
      ${tableWrap(`<thead><tr><th>Beat</th><th>计划</th><th>实测</th><th>偏差</th><th>CPS</th></tr></thead>
      <tbody>${driftRows || "<tr><td colspan=5>无明显偏差</td></tr>"}</tbody>`)}
    </div>`);
}

// --- Assets ---
async function renderAssets() {
  const { assets } = await api(`/assets?segment=${currentSegment}`);
  const visual = assets.filter(a => /\.(svg|png|jpe?g|webp|gif)$/i.test(a.path_or_url || ""));
  document.getElementById("assets").innerHTML = pageWrap("视觉资产", `${currentSegment} · 共 ${visual.length} 项 · 点击缩略图放大`, `<div class="asset-grid">${visual.map(a => `
    <article class="card asset-card card-no-accent">
      ${assetThumb(a.path_or_url, a.asset_id)}
      <h3>${a.asset_id}</h3>
      ${statusBadge(a.review_status || "review")}
      <div class="toolbar">
        <button class="btn btn-primary btn-compact" onclick="reviewAsset('${a.asset_id}','approved')">通过</button>
        <button class="btn btn-secondary btn-compact" onclick="rejectAsset('${a.asset_id}')">驳回</button>
        <button class="btn btn-secondary btn-compact" onclick="openAssetLightbox('${escAttr(a.path_or_url)}','${escAttr(a.asset_id)}')">放大</button>
        <button class="btn btn-secondary btn-compact" onclick="enqueueAsset('${a.asset_id}')">加入待办</button>
      </div>
    </article>`).join("") || `<div class="card card-no-accent"><p class="metric">暂无视觉资产</p></div>`}</div>`);
}

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
  await renderPreview();
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

// --- Timeline Editor ---
async function renderTimeline() {
  timelineData = await api(`/timeline?segment=${currentSegment}`);
  const total = Number(timelineData.total_sec || 211);
  const blocks = (timelineData.beats || []).map(b => {
    const start = Number(b.vo?.start_sec ?? b.start_sec ?? 0);
    const dur = Number(b.vo?.duration_sec ?? b.duration_sec ?? 1);
    const planned = Number(b.planned_sec ?? b.duration_sec ?? dur);
    const pStart = Number(b.start_sec ?? start);
    return `
      <div class="tl-block planned" style="left:${(pStart / total) * 100}%;width:${Math.max((planned / total) * 100, 0.3)}%" title="planned ${b.beat_id}"></div>
      <div class="tl-block${selectedBeatId === b.beat_id ? " selected" : ""}" data-beat="${b.beat_id}" data-start="${start}" data-dur="${dur}"
        style="left:${(start / total) * 100}%;width:${Math.max((dur / total) * 100, 0.5)}%" title="${b.beat_id} ${dur}s">${b.beat_id}</div>`;
  }).join("");
  const micro = (timelineData.micro_events || []).slice(0, 200).map(ev =>
    `<span class="tl-micro" data-event="${ev.id}" data-t="${ev.t}" style="left:${(Number(ev.t || 0) / total) * 100}%" title="${ev.id} @ ${ev.t}s"></span>`
  ).join("");
  document.getElementById("timeline").innerHTML = pageWrap("时间轴", `${currentSegment} · ${total.toFixed(1)} 秒 · 灰条计划 / 蓝条实测`, `
    <div class="card card-no-accent">
      <p class="metric">拖拽蓝条右边缘调整时长；点击橙点修改微事件时间。</p>
      <div class="tl-ruler" id="tl-ruler">${blocks}${micro}<div class="tl-playhead" id="tl-playhead" style="left:0"></div></div>
      <div class="toolbar">
        <button class="btn btn-primary" onclick="runPreset('segment_timing_lint').catch(e=>toast(e.message))">时长检查</button>
        <button class="btn btn-secondary" onclick="runPreset('build_composition').catch(e=>toast(e.message))">重建合成</button>
        <button class="btn btn-secondary" onclick="runPreset('audio_chain').catch(e=>toast(e.message))">重新对齐</button>
      </div>
      <pre id="timeline-log"></pre>
    </div>`);
  bindTimelineDrag(total);
  document.querySelectorAll(".tl-micro").forEach(el => {
    el.addEventListener("click", () => {
      const t = prompt(`微事件 ${el.dataset.event} 新时间（秒）：`, el.dataset.t);
      if (t == null) return;
      api(`/timing/micro/${el.dataset.event}?segment=${currentSegment}`, { method: "PATCH", body: JSON.stringify({ t: parseFloat(t) }) })
        .then(() => { toast("微事件时间已更新"); renderTimeline(); });
    });
  });
}

function bindTimelineDrag(total) {
  const ruler = document.getElementById("tl-ruler");
  if (!ruler) return;
  ruler.querySelectorAll(".tl-block:not(.planned)").forEach(block => {
    block.addEventListener("mousedown", (ev) => {
      if (ev.offsetX < block.offsetWidth - 8) {
        openBeatDetail(block.dataset.beat);
        return;
      }
      dragState = { beatId: block.dataset.beat, startX: ev.clientX, origDur: parseFloat(block.dataset.dur), total, block };
      ev.preventDefault();
    });
  });
  document.onmousemove = (ev) => {
    if (!dragState) return;
    const dx = ev.clientX - dragState.startX;
    const rulerW = document.getElementById("tl-ruler")?.offsetWidth || 1;
    const dSec = (dx / rulerW) * dragState.total;
    const newDur = Math.max(0.2, dragState.origDur + dSec);
    dragState.block.style.width = `${Math.max((newDur / dragState.total) * 100, 0.5)}%`;
    dragState.newDur = newDur;
  };
  document.onmouseup = async () => {
    if (!dragState || dragState.newDur == null) { dragState = null; return; }
    const { beatId, newDur } = dragState;
    dragState = null;
    try {
      await api(`/timing/beats/${beatId}?segment=${currentSegment}`, {
        method: "PATCH",
        body: JSON.stringify({ duration_sec: newDur, locked: true }),
      });
      toast(`${beatId} → ${newDur.toFixed(2)}s`);
      await renderTimeline();
    } catch (e) { toast(String(e.message)); }
  };
}

// --- Preview ---
async function renderPreview() {
  const project = await api("/project");
  const blocked = project.render_blocked;
  const mp4 = `segments/${currentSegment}/render.mp4`;
  document.getElementById("preview").innerHTML = pageWrap("视频预览", `${currentSegment} 草稿渲染`, `
    <div class="card card-no-accent">
      <video controls src="${mediaUrl(mp4)}"></video>
      <div class="toolbar">
        <button class="btn btn-primary" id="render-btn" ${blocked ? "disabled" : ""} onclick="runDraftRender()">草稿渲染</button>
        <button class="btn btn-secondary" onclick="runPreset('build_composition').catch(e=>toast(e.message))">重建合成页</button>
      </div>
      ${blocked ? `<p class="blocked">${esc(blocked)}</p>` : ""}
      <pre id="job-log"></pre>
    </div>`);
}

window.runDraftRender = async () => {
  const log = document.getElementById("job-log");
  try {
    const job = await runPreset("render_draft");
    await pollJob(job.id, log);
  } catch (e) {
    toast(String(e.message));
    if (log) log.textContent = String(e.message);
  }
};

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
      if (data.type === "job_progress") renderJobs();
    };
  } catch (_) { /* optional */ }
})();
