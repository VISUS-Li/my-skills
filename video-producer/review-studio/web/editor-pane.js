/**
 * 分栏编辑器 — CodeMirror + Markdown/JSON/HTML 预览（类似 VS Code 编辑/预览）
 */
(function (global) {
  const instances = new Map();

  function detectLanguage(path) {
    const p = (path || "").toLowerCase();
    if (p.endsWith(".md")) return "markdown";
    if (p.endsWith(".json") || p.endsWith(".jsonl")) return "json";
    if (p.endsWith(".html") || p.endsWith(".htm")) return "html";
    if (p.endsWith(".csv")) return "csv";
    if (p.endsWith(".py")) return "python";
    return "text";
  }

  function cmMode(lang) {
    if (lang === "markdown") return "markdown";
    if (lang === "json") return { name: "javascript", json: true };
    if (lang === "html") return "htmlmixed";
    if (lang === "python") return "python";
    return "text/plain";
  }

  function renderPreview(lang, text) {
    if (lang === "markdown" && global.marked) {
      try {
        return `<div class="md-preview">${global.marked.parse(text || "")}</div>`;
      } catch (e) {
        return `<pre class="preview-error">${e.message}</pre>`;
      }
    }
    if (lang === "json") {
      try {
        const obj = JSON.parse(text || "{}");
        return `<pre class="json-preview">${escapeHtml(JSON.stringify(obj, null, 2))}</pre>`;
      } catch (e) {
        return `<pre class="preview-error">JSON 解析失败: ${escapeHtml(e.message)}</pre>`;
      }
    }
    if (lang === "csv") {
      const rows = (text || "").trim().split(/\r?\n/).filter(Boolean);
      if (!rows.length) return "<p class='metric'>空文件</p>";
      const cells = rows.map(r => r.split(","));
      const head = cells[0].map(c => `<th>${escapeHtml(c)}</th>`).join("");
      const body = cells.slice(1, 80).map(row =>
        `<tr>${row.map(c => `<td>${escapeHtml(c)}</td>`).join("")}</tr>`
      ).join("");
      return `<div class="table-wrap preview-csv"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    }
    if (lang === "html") {
      const src = "data:text/html;charset=utf-8," + encodeURIComponent(text || "");
      return `<iframe class="preview-iframe" sandbox="allow-same-origin" src="${src}"></iframe>`;
    }
    return `<pre class="plain-preview">${escapeHtml(text || "")}</pre>`;
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  }

  function setViewMode(root, mode) {
    root.dataset.viewMode = mode;
    root.querySelectorAll("[data-view-mode]").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.viewMode === mode);
    });
    const body = root.querySelector(".editor-body");
    body.classList.remove("mode-edit", "mode-split", "mode-preview");
    body.classList.add(`mode-${mode}`);
    const inst = instances.get(root.dataset.editorId);
    if (inst?.cm) setTimeout(() => inst.cm.refresh(), 50);
  }

  function updatePreview(root) {
    const inst = instances.get(root.dataset.editorId);
    if (!inst) return;
    const text = inst.cm ? inst.cm.getValue() : "";
    const pane = root.querySelector(".editor-preview");
    if (pane) pane.innerHTML = renderPreview(inst.lang, text);
  }

  function create(container, options) {
    const id = options.id || `ed-${Date.now()}`;
    const lang = options.lang || detectLanguage(options.path);
    const height = options.height || "min(72vh, 640px)";

    container.innerHTML = `
      <div class="editor-pane" data-editor-id="${id}" data-view-mode="split">
        <div class="editor-toolbar">
          <div class="editor-toolbar-left">
            <span class="editor-badge">${lang.toUpperCase()}</span>
            <span class="editor-path" title="${escapeHtml(options.path || "")}">${escapeHtml(options.path || "未命名")}</span>
          </div>
          <div class="segmented editor-segmented" role="tablist">
            <button type="button" class="segmented-btn active" data-view-mode="edit" role="tab">编辑</button>
            <button type="button" class="segmented-btn" data-view-mode="split" role="tab">分栏</button>
            <button type="button" class="segmented-btn" data-view-mode="preview" role="tab">预览</button>
          </div>
          ${options.saveLabel ? `<button type="button" class="btn btn-primary btn-compact editor-save">${options.saveLabel}</button>` : ""}
        </div>
        <div class="editor-body mode-split" style="--editor-height:${height}">
          <div class="editor-code-wrap"><textarea class="editor-source">${escapeHtml(options.value || "")}</textarea></div>
          <div class="editor-preview-wrap"><div class="editor-preview"></div></div>
        </div>
      </div>`;

    const root = container.querySelector(".editor-pane");
    const textarea = root.querySelector(".editor-source");
    let cm = null;
    if (global.CodeMirror) {
      cm = global.CodeMirror.fromTextArea(textarea, {
        mode: cmMode(lang),
        theme: "material-darker",
        lineNumbers: true,
        lineWrapping: true,
        matchBrackets: true,
        tabSize: 2,
        indentUnit: 2,
      });
      cm.setSize("100%", "100%");
      cm.on("change", () => updatePreview(root));
    }

    instances.set(id, { cm, lang, root, textarea });

    root.querySelectorAll("[data-view-mode]").forEach(btn => {
      btn.addEventListener("click", () => {
        setViewMode(root, btn.dataset.viewMode);
        updatePreview(root);
      });
    });

    const saveBtn = root.querySelector(".editor-save");
    if (saveBtn && options.onSave) {
      saveBtn.addEventListener("click", () => options.onSave(getValue(id)));
    }

    setViewMode(root, options.defaultMode || "split");
    updatePreview(root);
    return id;
  }

  function getValue(id) {
    const inst = instances.get(id);
    if (!inst) return "";
    return inst.cm ? inst.cm.getValue() : inst.textarea?.value || "";
  }

  function destroy(id) {
    const inst = instances.get(id);
    if (inst?.cm) inst.cm.toTextArea();
    instances.delete(id);
  }

  global.EditorPane = { create, getValue, destroy, detectLanguage };
})(window);
