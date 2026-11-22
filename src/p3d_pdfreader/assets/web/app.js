/* P3D PDF Reader Web - Oberflaeche. Alle Daten, Bilder und Ausgaben kommen vom Python-Server (core unveraendert). */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const store = {
  get(key, def) { try { const v = localStorage.getItem("p3dpr." + key); return v === null ? def : JSON.parse(v); } catch { return def; } },
  set(key, val) { try { localStorage.setItem("p3dpr." + key, JSON.stringify(val)); } catch { /* ohne Speicher weiter */ } },
};
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// ---- Offline-Bericht (Variante 1, web/report.py): Daten und Seitenbilder stehen in der HTML-Datei -------------
const OFFLINE = window.P3D_OFFLINE || null;
// Funktionen, die den Server brauchen - im Offline-Bericht ausgeblendet
const SERVER_CMDS = new Set(["scan", "upload", "pipes", "clear", "bulk", "redline", "review", "exportXlsx", "exportCsv",
  "openPdf", "report"]);
function offlineGet(path) {
  const m = path.match(/^files\/(\d+)\/(tags|pages)$/);
  if (m) return m[2] === "tags" ? OFFLINE.tags[m[1]] || [] : OFFLINE.pages[m[1]] || [];
  if (path === "files") return OFFLINE.files;
  if (path === "tags") return OFFLINE.all_tags;
  if (path === "info") return OFFLINE.info;
  if (path === "scan") return { running: false, finished: true, total: 0, done: 0, current: "", error: "" };
  throw new Error("Im Offline-Bericht nicht verfügbar");
}

// ---- Server ------------------------------------------------------------------------------------------------
async function api(path, options = {}) {
  if (OFFLINE) throw new Error("Im Offline-Bericht nicht verfügbar – dafür die Web-Version oder die Desktop-App nutzen");
  const res = await fetch("/api/" + path, { credentials: "same-origin", ...options });
  if (!res.ok) {
    let msg = res.status + " " + res.statusText;
    try { msg = (await res.json()).error || msg; } catch { /* kein JSON */ }
    throw new Error(msg);
  }
  return res;
}
const getJson = async path => OFFLINE ? offlineGet(path) : (await api(path)).json();
const postJson = async (path, data) => (await api(path, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data || {}) })).json();

async function download(path, data, label) {
  status(label + " wird erstellt …");
  const res = await api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data || {}) });
  const cd = res.headers.get("Content-Disposition") || "";
  const m = cd.match(/filename\*=UTF-8''([^;]+)/) || cd.match(/filename="([^"]+)"/);
  const name = m ? decodeURIComponent(m[1]) : "download";
  const blob = await res.blob();
  const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: name });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 30000);
  status(`${label}: ${name} heruntergeladen.`);
}

function status(text, right) {
  $("#status").textContent = text;
  if (right !== undefined) $("#statusRight").textContent = right;
}

// ---- Tabelle (virtuell gescrollt, Spaltenfilter, Sortierung, Mehrfachauswahl) -------------------------------
class Table {
  constructor(el, opts) {
    this.el = el; this.o = opts; this.cols = opts.columns; this.rows = []; this.view = [];
    this.filters = {}; this.globalFilter = ""; this.extraFilter = null; this.sort = null;
    this.sel = new Set(); this.anchor = null; this.current = null;
    this.rowH = 22;
    el.tabIndex = 0;
    el.innerHTML = `<div class="t-head"><div class="t-hrow"></div><div class="t-frow"></div></div><div class="t-body"></div>`;
    this.head = $(".t-hrow", el); this.frow = $(".t-frow", el); this.body = $(".t-body", el);
    const tpl = this.cols.map(c => (c.width || 100) + "px").join(" ");
    const total = this.cols.reduce((s, c) => s + (c.width || 100), 0);
    for (const r of [this.head, this.frow]) { r.style.gridTemplateColumns = tpl; r.style.width = total + "px"; }
    this.tpl = tpl; this.total = total;
    this.body.style.width = total + "px";
    this.cols.forEach((c, i) => {
      const h = document.createElement("div");
      h.textContent = c.label; h.title = c.title || c.label;
      h.onclick = () => this.toggleSort(i);
      this.head.appendChild(h);
      const f = document.createElement("div");
      const inp = Object.assign(document.createElement("input"), { type: "search", placeholder: "Filter" });
      inp.oninput = () => { this.filters[c.key] = inp.value.trim().toLowerCase(); this.refresh(); };
      f.appendChild(inp); this.frow.appendChild(f);
    });
    el.addEventListener("scroll", () => this.paint());
    this.body.addEventListener("mousedown", e => {
      const div = e.target.closest(".t-row");
      if (div) { e.preventDefault(); el.focus(); this.click(+div.dataset.i, e); }
    });
    this.body.addEventListener("dblclick", e => {
      const div = e.target.closest(".t-row");
      if (!div) return;
      const cell = e.target.closest(".t-row > div"), c = this.cols[[...div.children].indexOf(cell)];
      if (c && c.edit && this.o.onEdit) this.editCell(this.view[+div.dataset.i], c, cell);
      else if (this.o.onActivate) this.o.onActivate(this.view[+div.dataset.i]);
    });
    el.addEventListener("keydown", e => this.key(e));
    new ResizeObserver(() => this.paint()).observe(el);
  }
  setRows(rows, keepSelection = true) {
    const keyOf = this.o.key || (r => r);
    const old = keepSelection ? new Set([...this.sel].map(keyOf)) : new Set();
    const cur = keepSelection && this.current ? keyOf(this.current) : null;
    this.rows = rows;
    this.sel = new Set(rows.filter(r => old.has(keyOf(r))));
    this.current = cur === null ? null : rows.find(r => keyOf(r) === cur) || null;
    this.refresh();
  }
  value(row, c) { return c.get ? c.get(row) : row[c.key]; }
  text(row, c) { const v = this.value(row, c); return c.fmt ? c.fmt(v, row) : (v ?? ""); }
  refresh() {
    const g = this.globalFilter;
    let v = this.rows.filter(r => {
      if (this.extraFilter && !this.extraFilter(r)) return false;
      for (const c of this.cols) {
        const f = this.filters[c.key];
        if (f && !String(this.text(r, c)).toLowerCase().includes(f)) return false;
      }
      return !g || this.cols.some(c => String(this.text(r, c)).toLowerCase().includes(g));
    });
    if (this.sort) {
      const c = this.cols[this.sort.i], d = this.sort.dir;
      v = v.slice().sort((a, b) => {
        const x = this.value(a, c), y = this.value(b, c);
        const r = (typeof x === "number" && typeof y === "number") ? x - y
          : String(x ?? "").localeCompare(String(y ?? ""), "de", { numeric: true, sensitivity: "base" });
        return r * d;
      });
    }
    this.view = v;
    $$(".sort", this.head).forEach(s => s.remove());
    if (this.sort) this.head.children[this.sort.i].insertAdjacentHTML("beforeend", `<span class="sort">${this.sort.dir > 0 ? "▲" : "▼"}</span>`);
    this.body.style.height = Math.max(v.length * this.rowH, 1) + "px";
    this.paint();
    this.o.onView && this.o.onView(this);
  }
  toggleSort(i) {
    if (!this.sort || this.sort.i !== i) this.sort = { i, dir: 1 };
    else if (this.sort.dir === 1) this.sort.dir = -1;
    else this.sort = null;
    this.refresh();
  }
  resetFilters() {
    this.filters = {}; this.globalFilter = ""; this.sort = null;
    $$("input", this.frow).forEach(i => (i.value = ""));
    this.refresh();
  }
  paint() {
    const top = this.el.scrollTop, h = this.el.clientHeight;
    const headH = this.head.parentElement.offsetHeight;
    const first = Math.max(0, Math.floor((top - headH) / this.rowH) - 5);
    const last = Math.min(this.view.length, Math.ceil((top + h) / this.rowH) + 5);
    let html = "";
    for (let i = first; i < last; i++) {
      const r = this.view[i];
      const cls = ["t-row", this.o.rowClass ? this.o.rowClass(r) : "", this.sel.has(r) ? "sel" : ""].join(" ");
      html += `<div class="${cls}" data-i="${i}" style="top:${i * this.rowH}px;grid-template-columns:${this.tpl};width:${this.total}px">` +
        this.cols.map(c => `<div class="${c.num ? "num" : ""}" title="${esc(this.text(r, c))}">${esc(this.text(r, c))}</div>`).join("") + "</div>";
    }
    this.body.innerHTML = html || (this.rows.length ? "" : `<div class="t-empty">${esc(this.o.empty || "Keine Daten")}</div>`);
  }
  // Zelle bearbeiten (Doppelklick auf eine Spalte mit ``edit``): Auswahlliste oder Textfeld, Enter/Verlassen = uebernehmen
  editCell(row, c, cell) {
    const old = String(this.value(row, c) ?? "");
    const ed = c.options ? document.createElement("select") : document.createElement("input");
    if (c.options) ed.innerHTML = c.options.map(v => `<option ${v === old ? "selected" : ""}>${esc(v)}</option>`).join("");
    else ed.value = old;
    ed.className = "t-editor";
    cell.textContent = ""; cell.appendChild(ed);
    ed.addEventListener("mousedown", e => e.stopPropagation());
    let done = false;
    const finish = save => {
      if (done) return; done = true;
      const v = ed.value;
      if (save && v !== old) this.o.onEdit(row, c, v);
      this.paint(); this.el.focus();
    };
    ed.addEventListener("keydown", e => {
      e.stopPropagation();
      if (e.key === "Enter") finish(true); else if (e.key === "Escape") finish(false);
    });
    ed.addEventListener("blur", () => finish(true));
    if (c.options) ed.addEventListener("change", () => finish(true));
    ed.focus();
  }
  paintSel() {      // nur Markierung umschalten - Zeilen bleiben erhalten (Doppelklick funktioniert)
    $$(".t-row", this.body).forEach(div => div.classList.toggle("sel", this.sel.has(this.view[+div.dataset.i])));
  }
  click(i, e) {
    const r = this.view[i];
    const again = this.current === r && this.sel.size === 1 && this.sel.has(r);
    if (e.shiftKey && this.anchor !== null && this.o.multi) {
      const a = this.view.indexOf(this.anchor);
      if (!e.ctrlKey) this.sel.clear();
      for (let k = Math.min(a, i); k <= Math.max(a, i); k++) this.sel.add(this.view[k]);
    } else if ((e.ctrlKey || e.metaKey) && this.o.multi) {
      this.sel.has(r) ? this.sel.delete(r) : this.sel.add(r);
      this.anchor = r;
    } else {
      this.sel = new Set([r]); this.anchor = r;
    }
    this.current = r;
    this.paintSel();
    this.o.onSelect && this.o.onSelect(r, again);
  }
  key(e) {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp" || !this.view.length) return;
    e.preventDefault();
    let i = this.view.indexOf(this.current);
    i = Math.max(0, Math.min(this.view.length - 1, i < 0 ? 0 : i + (e.key === "ArrowDown" ? 1 : -1)));
    const r = this.view[i];
    this.sel = new Set([r]); this.anchor = r; this.current = r;
    const y = i * this.rowH, headH = this.head.parentElement.offsetHeight;
    if (y < this.el.scrollTop) this.el.scrollTop = y;
    else if (y + this.rowH + headH > this.el.scrollTop + this.el.clientHeight) this.el.scrollTop = y + this.rowH + headH - this.el.clientHeight;
    this.paint();
    this.o.onSelect && this.o.onSelect(r, false);
  }
  selectAll() { this.sel = new Set(this.view); this.paintSel(); }
  selected() { return this.view.filter(r => this.sel.has(r)); }
  select(r) {
    this.sel = new Set([r]); this.current = r; this.anchor = r;
    const i = this.view.indexOf(r);
    if (i >= 0) this.el.scrollTop = Math.max(0, i * this.rowH - this.el.clientHeight / 2);
    this.paint();
  }
}

// ---- PDF-Viewer: Seite als Bild vom Server, scharfer Ausschnitt bei jedem Zoom neu gerendert -------------------
const BASE_PIXELS = 2400;

class Viewer {
  constructor(root) {
    this.root = root;
    root.innerHTML = `<div class="v-stage"><img class="v-base" alt=""><img class="v-detail" alt="">
      <svg class="v-svg" xmlns="http://www.w3.org/2000/svg"></svg></div><div class="v-badges"></div>
      <div class="v-info"></div><div class="v-empty">Keine PDF gewählt</div>`;
    this.stage = $(".v-stage", root); this.base = $(".v-base", root); this.detail = $(".v-detail", root);
    this.svg = $(".v-svg", root); this.badges = $(".v-badges", root); this.info = $(".v-info", root); this.empty = $(".v-empty", root);
    this.file = null; this.pages = []; this.page = -1; this.s = 1; this.tx = 0; this.ty = 0; this.rot = 0;
    this.dups = []; this.marks = null; this.seq = 0; this.onPage = null; this.mono = false;
    this.found = []; this.faulty = [];   // alle gefundenen Tags gruen, fehlerhafte rot umrandet (je Tag [[Seite, Rechteck]])
    this.stage.style.display = "none";
    this.bindMouse();
    new ResizeObserver(() => this.file && this.apply()).observe(root);
  }
  async open(file) {
    if (this.file && file && this.file.id === file.id) return;
    this.file = file; this.page = -1; this.marks = null; this.info.textContent = "";
    if (!file) { this.stage.style.display = "none"; this.empty.style.display = ""; this.badges.innerHTML = ""; return; }
    this.empty.textContent = "PDF wird geladen …";
    this.pages = await getJson(`files/${file.id}/pages`);
    if (this.file !== file) return;
    this.empty.style.display = "none"; this.stage.style.display = "";
    this.setPage(0);
  }
  get size() { return this.pages[this.page] || [1, 1]; }
  setPage(n, fit = true) {
    if (!this.file || n < 0 || n >= this.pages.length) return;
    if (n !== this.page) {
      this.page = n;
      const [w, h] = this.size;
      this.stage.style.width = w + "px"; this.stage.style.height = h + "px";
      this.svg.setAttribute("viewBox", `0 0 ${w} ${h}`); this.svg.setAttribute("width", w); this.svg.setAttribute("height", h);
      this.base.style.width = w + "px"; this.base.style.height = h + "px";
      this.loadBase();
      this.detail.removeAttribute("src"); this.detail.style.display = "none";
      this.draw();
      this.onPage && this.onPage(n, this.pages.length);
    }
    if (fit) this.fit();
  }
  monoArg() { return this.mono ? "&mono=1" : ""; }
  loadBase() {
    const [w, h] = this.size;
    if (OFFLINE) {             // Bild aus dem Bericht; Schwarz-Weiss nur als Anzeige-Filter
      this.base.src = (OFFLINE.images[this.file.id] || [])[this.page] || "";
      this.base.style.filter = this.mono ? "grayscale(1) contrast(1.8)" : "";
      return;
    }
    this.base.src = `/api/files/${this.file.id}/render?page=${this.page}&zoom=${(BASE_PIXELS / Math.max(w, h)).toFixed(4)}${this.monoArg()}`;
  }
  // Monochrom: Seite schwarz auf weiss (nur Ansicht); Zoom, Drehung und Markierungen bleiben
  setMono(on) {
    if (this.mono === !!on) return;
    this.mono = !!on;
    if (!this.file || this.page < 0) return;
    this.loadBase();
    this.detail.style.display = "none";
    this.renderDetail();
  }
  // Transformation: Bildschirm = T + R(rot) * s * Seite
  rotVec(x, y) {
    switch (this.rot) { case 90: return [-y, x]; case 180: return [-x, -y]; case 270: return [y, -x]; default: return [x, y]; }
  }
  toScreen(px, py) { const [x, y] = this.rotVec(px * this.s, py * this.s); return [this.tx + x, this.ty + y]; }
  toPage(sx, sy) {
    const x = (sx - this.tx) / this.s, y = (sy - this.ty) / this.s;
    switch (this.rot) { case 90: return [y, -x]; case 180: return [-x, -y]; case 270: return [-y, x]; default: return [x, y]; }
  }
  apply() {
    this.stage.style.transform = `translate(${this.tx}px,${this.ty}px) rotate(${this.rot}deg) scale(${this.s})`;
    this.placeBadges();
    clearTimeout(this.timer);
    this.timer = setTimeout(() => this.renderDetail(), 180);
  }
  centerOn(px, py) {
    const [x, y] = this.rotVec(px * this.s, py * this.s);
    this.tx = this.root.clientWidth / 2 - x; this.ty = this.root.clientHeight / 2 - y;
    this.apply();
  }
  fit() {
    if (!this.file) return;
    const [w, h] = this.size, turned = this.rot % 180 !== 0;
    const cw = this.root.clientWidth, ch = this.root.clientHeight;
    this.s = 0.98 * Math.min(cw / (turned ? h : w), ch / (turned ? w : h));
    this.centerOn(w / 2, h / 2);
  }
  zoomAt(f, sx, sy) {
    const s = Math.max(0.02, Math.min(40, this.s * f)); f = s / this.s;
    this.tx = sx - (sx - this.tx) * f; this.ty = sy - (sy - this.ty) * f; this.s = s;
    this.apply();
  }
  zoom(f) { this.zoomAt(f, this.root.clientWidth / 2, this.root.clientHeight / 2); }
  zoomRect(r) {
    const pad = 90, turned = this.rot % 180 !== 0;
    const rw = r[2] - r[0] + 2 * pad, rh = r[3] - r[1] + 2 * pad;
    const cw = this.root.clientWidth, ch = this.root.clientHeight;
    this.s = Math.min(cw / (turned ? rh : rw), ch / (turned ? rw : rh));
    this.centerOn((r[0] + r[2]) / 2, (r[1] + r[3]) / 2);
  }
  rotate() {
    const c = this.toPage(this.root.clientWidth / 2, this.root.clientHeight / 2);
    this.rot = (this.rot + 90) % 360;
    this.centerOn(c[0], c[1]);
  }
  async renderDetail() {
    if (!this.file || this.page < 0 || OFFLINE) return;     // offline: nur das Seitenbild aus dem Bericht
    const [w, h] = this.size, dpr = window.devicePixelRatio || 1;
    const zoom = this.s * dpr, baseZoom = BASE_PIXELS / Math.max(w, h);
    if (zoom <= baseZoom * 1.05) { this.detail.style.display = "none"; return; }
    const cw = this.root.clientWidth, ch = this.root.clientHeight;
    const pts = [[0, 0], [cw, 0], [0, ch], [cw, ch]].map(p => this.toPage(p[0], p[1]));
    const x0 = Math.max(0, Math.min(...pts.map(p => p[0]))), y0 = Math.max(0, Math.min(...pts.map(p => p[1])));
    const x1 = Math.min(w, Math.max(...pts.map(p => p[0]))), y1 = Math.min(h, Math.max(...pts.map(p => p[1])));
    if (x1 <= x0 || y1 <= y0) return;
    const seq = ++this.seq, id = this.file.id, page = this.page;
    const url = `/api/files/${id}/render?page=${page}&zoom=${zoom.toFixed(3)}&x0=${x0.toFixed(1)}&y0=${y0.toFixed(1)}&x1=${x1.toFixed(1)}&y1=${y1.toFixed(1)}${this.monoArg()}`;
    const img = new Image();
    img.onload = () => {
      if (seq !== this.seq || !this.file || this.file.id !== id || this.page !== page) return;
      Object.assign(this.detail.style, { left: x0 + "px", top: y0 + "px", width: (x1 - x0) + "px", height: (y1 - y0) + "px", display: "" });
      this.detail.src = img.src;
    };
    img.src = url;
  }
  bindMouse() {
    const r = this.root;
    r.addEventListener("wheel", e => {
      e.preventDefault();
      const b = r.getBoundingClientRect();
      this.zoomAt(Math.pow(1.0015, -e.deltaY), e.clientX - b.left, e.clientY - b.top);
    }, { passive: false });
    let drag = null;
    r.addEventListener("pointerdown", e => {
      if (e.button !== 0) return;
      drag = { x: e.clientX, y: e.clientY, tx: this.tx, ty: this.ty };
      r.setPointerCapture(e.pointerId); r.classList.add("drag");
    });
    r.addEventListener("pointermove", e => {
      if (!drag) return;
      this.tx = drag.tx + e.clientX - drag.x; this.ty = drag.ty + e.clientY - drag.y; this.apply();
    });
    const end = () => { drag = null; r.classList.remove("drag"); };
    r.addEventListener("pointerup", end); r.addEventListener("pointercancel", end);
    r.addEventListener("dblclick", () => this.fit());
  }
  // Markierungen: gelb = doppelte Tags dieser Seite, Rahmen + Nummer = Fundstellen des gewaehlten Tags
  setDuplicates(groups) { this.dups = groups; this.draw(); }
  setMarks(marks) { this.marks = marks; this.draw(); }
  draw() {
    const pad = 3;
    let html = "";
    for (const hits of this.dups) for (const [p, r] of hits) if (p === this.page)
      html += `<rect class="v-dup" x="${r[0] - pad}" y="${r[1] - pad}" width="${r[2] - r[0] + 2 * pad}" height="${r[3] - r[1] + 2 * pad}"/>`;
    for (const [groups, cls] of [[this.found, ""], [this.faulty, " bad"]])
      for (const hits of groups) for (const [p, r] of hits) if (p === this.page)
        html += `<rect class="v-found${cls}" x="${r[0] - pad}" y="${r[1] - pad}" width="${r[2] - r[0] + 2 * pad}" height="${r[3] - r[1] + 2 * pad}"/>`;
    if (this.marks) this.marks.hits.forEach(([p, r], i) => {
      if (p !== this.page) return;
      html += `<rect class="v-mark ${i === this.marks.focus ? "focus" : ""}" x="${r[0] - pad - 1}" y="${r[1] - pad - 1}" width="${r[2] - r[0] + 2 * pad + 2}" height="${r[3] - r[1] + 2 * pad + 2}"/>`;
    });
    this.svg.innerHTML = html;
    this.placeBadges();
  }
  placeBadges() {
    if (!this.marks || this.marks.hits.length < 2) { this.badges.innerHTML = ""; return; }
    let html = "";
    this.marks.hits.forEach(([p, r], i) => {
      if (p !== this.page) return;
      const [x, y] = this.toScreen(r[2] + 6, r[1] - 6);
      html += `<div class="v-badge ${i === this.marks.focus ? "focus" : ""}" style="left:${x + 10}px;top:${y - 4}px">${i + 1}</div>`;
    });
    this.badges.innerHTML = html;
  }
  setInfo(text) { this.info.textContent = text || ""; }
}

// ---- Anwendung --------------------------------------------------------------------------------------------------
const state = { files: [], file: null, tags: [], allTags: null, dupsOnly: false, nav: null, scanTimer: null };

const fileCols = [
  { key: "drawing_no", label: "Zeichnungsnr.", width: 210, get: r => r.drawing_no || r.name },
  { key: "created", label: "Erstellt (PDF)", width: 112 },
  { key: "author", label: "Ersteller", width: 90 },
  { key: "checked", label: "Checked", width: 80 },
  { key: "revision", label: "Rev", width: 40 },
  { key: "revision_date", label: "Rev-Datum", width: 86 },
  { key: "revision_text", label: "Rev-Text", width: 160 },
  { key: "plot_user", label: "Plot-Benutzer", width: 90 },
  { key: "tags", label: "Anzahl Tags", width: 76, num: true },
  { key: "duplicates", label: "Doppelt", width: 60, num: true },
  { key: "pages", label: "Seiten", width: 52, num: true },
  { key: "name", label: "PDF", width: 240 },
  { key: "origin", label: "Quelle", width: 70, fmt: v => v === "upload" ? "Upload" : "Server" },
  { key: "error", label: "Fehler", width: 160 },
];
// Audit-/Review-Spalten wie der Bearbeiten-Modus der Desktop-App (core/review_store.py); Auswahllisten kommen vom
// Server bzw. aus dem Bericht (info.review_values / info.change_values). Doppelklick in die Zelle = bearbeiten.
const AUDIT_EDIT = ["Review", "Änderung", "Neuer Wert", "Bemerkung", "WPO"];
const auditCols = () => [
  ...AUDIT_EDIT.map(f => ({ key: "a:" + f, label: f, width: f === "Bemerkung" ? 180 : f === "Review" ? 150 : 120,
    get: r => (r.audit || {})[f] || "", edit: f,
    options: f === "Review" ? state.reviewValues : f === "Änderung" ? state.changeValues : null,
    title: `${f} – Doppelklick zum Bearbeiten` })),
  { key: "a:Datum", label: "Datum", width: 120, get: r => (r.audit || {}).Datum || "" },
  { key: "a:User", label: "User", width: 90, get: r => (r.audit || {}).User || "" },
];
state.reviewValues = ["", "Offen", "OK", "Korrektur erforderlich", "Klärung", "Nicht relevant"];
state.changeValues = ["", "Keine", "Tag ändern", "Tag ergänzen", "Tag löschen", "Position prüfen", "Doppelten Tag auflösen"];
state.reviewFaulty = ["Korrektur erforderlich"];
state.pending = {};             // fileId -> {"Typ|Tag": {type, tag, fields: {Feld: Wert}}} (noch nicht gespeichert)
const tagCols = [
  { key: "type", label: "Typ", width: 120 },
  { key: "tag", label: "Tag", width: 200 },
  { key: "count", label: "Anzahl", width: 60, num: true },
  { key: "pages", label: "Seiten", width: 90 },
  ...auditCols(),
];
const allCols = [
  { key: "drawing_no", label: "Zeichnungsnr.", width: 220, get: r => r.drawing_no || r.pdf },
  { key: "type", label: "Typ", width: 120 },
  { key: "tag", label: "Tag", width: 200 },
  { key: "count", label: "Anzahl", width: 60, num: true },
  { key: "pages", label: "Seiten", width: 90 },
  ...auditCols().map(c => ({ ...c, edit: undefined, title: c.label })),
  { key: "pdf", label: "PDF", width: 280 },
];
const isFaulty = r => state.reviewFaulty.includes((r.audit || {}).Review || "");

const tblFiles = new Table($("#tblFiles"), {
  columns: fileCols, multi: true, key: r => r.id, empty: "Noch keine PDFs eingelesen – „Quellordner scannen“ oder „PDFs hochladen“.",
  rowClass: r => r.error ? "err" : "", onSelect: r => openFile(r), onView: () => updateNote(),
});
const tblTags = new Table($("#tblTags"), {
  columns: tagCols, key: r => r.type + "|" + r.tag, empty: "Keine Tags",
  rowClass: r => [r.duplicate ? "dup" : "", isFaulty(r) ? "err" : ""].join(" "), onSelect: (r, again) => selectTag(r, again),
  onView: () => updateNote(), onEdit: (r, c, v) => editAudit(r, c.edit, v),
});
const tblAll = new Table($("#tblAll"), {
  columns: allCols, key: r => r.file + "|" + r.type + "|" + r.tag, empty: "Keine Tags",
  rowClass: r => r.duplicate ? "dup" : "", onActivate: r => gotoTag(r.file, r.type, r.tag),
});
const dupFilter = r => !state.dupsOnly || r.duplicate;
tblTags.extraFilter = dupFilter; tblAll.extraFilter = dupFilter;

const viewer = new Viewer($("#viewer"));
function setMono(on) {
  viewer.setMono(on);
  $("#monoBtn").classList.toggle("on", viewer.mono);
  store.set("monochrome", viewer.mono);
}
setMono(store.get("monochrome", false));
viewer.onPage = (n, total) => { $("#pageLabel").textContent = `Seite ${n + 1} / ${total}`; };

function updateNote() {
  $("#pidNote").textContent = `${tblFiles.view.length} / ${state.files.length} PDFs · ${tblTags.view.length} / ${state.tags.length} Tags`;
}

async function loadFiles() {
  state.files = await getJson("files");
  tblFiles.setRows(state.files);
  state.allTags = null;
  if ($("#sheet-all").classList.contains("active")) loadAllTags();
  const dups = state.files.reduce((s, f) => s + f.duplicates, 0);
  status(`${state.files.length} PDFs eingelesen.`, `${state.files.reduce((s, f) => s + f.tags, 0)} Tags · ${dups} doppelt`);
}

async function loadAllTags() {
  if (state.allTags) return;
  state.allTags = await getJson("tags");
  tblAll.setRows(state.allTags);
}

async function openFile(file) {
  if (!file || (state.file && state.file.id === file.id)) return;
  if (!OFFLINE && state.file && state.pending[state.file.id]) await saveAudit(true);   // Wechsel = speichern
  state.file = file; state.nav = null;
  $("#tagsTitle").textContent = `Tags: ${file.drawing_no || file.name}`;
  $("#viewerTitle").textContent = `PDF-Viewer: ${file.name}`;
  viewer.setMarks(null); viewer.setInfo("");
  state.tags = await getJson(`files/${file.id}/tags`);
  if (state.file !== file) return;
  tblTags.setRows(state.tags, false);
  viewer.dups = state.tags.filter(t => t.duplicate).map(t => t.hits);
  markReviewInViewer();
  await viewer.open(file);
  viewer.draw();
}

// ---- Audit / Review-Spalten bearbeiten und speichern ----------------------------------------------------------
function markReviewInViewer() {       // wie Desktop: "Korrektur erforderlich" rot umrandet, alle anderen gruen
  viewer.found = state.tags.filter(t => !isFaulty(t)).map(t => t.hits);
  viewer.faulty = state.tags.filter(isFaulty).map(t => t.hits);
  viewer.draw();
}
function auditUser() {
  let user = store.get("user", "");
  if (!user) {
    user = (window.prompt("Name oder Kürzel für die Spalte „User“ (wird auf diesem PC gemerkt):", "") || "").trim();
    if (user) store.set("user", user);
  }
  return user;
}
const pendingCount = () => Object.values(state.pending).reduce((s, p) => s + Object.keys(p).length, 0);
function editAudit(row, field, value) {
  const user = auditUser();
  row.audit = row.audit || {};
  row.audit[field] = value;
  const now = new Date(), pad = n => String(n).padStart(2, "0");
  row.audit.Datum = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
  row.audit.User = user;
  const fid = state.file.id, k = row.type + "|" + row.tag;
  const p = (state.pending[fid] = state.pending[fid] || {});
  (p[k] = p[k] || { type: row.type, tag: row.tag, fields: {} }).fields[field] = value;
  if (OFFLINE) offlineRemember();
  state.allTags = null;                                       // Blatt "Alle Tags" neu aufbauen
  tblTags.refresh(); markReviewInViewer();
  status(OFFLINE ? `Audit gemerkt (in diesem Browser). „Review speichern“ speichert die Ergebnisse als CSV/Excel-Datei.`
    : `${pendingCount()} ungespeicherte Audit-Änderung(en) – „Review speichern“ oder Strg+S.`);
}
async function saveAudit(silent = false) {
  if (OFFLINE) return exportAuditCsv();
  const ids = Object.keys(state.pending);
  if (!ids.length) { if (!silent) status("Keine ungespeicherten Audit-Änderungen."); return; }
  let n = 0;
  for (const id of ids) {
    const changes = [];
    for (const e of Object.values(state.pending[id])) for (const [field, value] of Object.entries(e.fields)) changes.push({ type: e.type, tag: e.tag, field, value });
    const res = await postJson("audit", { id: +id, changes, user: store.get("user", "") });
    n += res.saved;
    delete state.pending[id];
    if (state.file && state.file.id === +id) { state.tags = res.tags; tblTags.setRows(state.tags); markReviewInViewer(); }
  }
  state.allTags = null;
  status(`Audit gespeichert: ${n} Feld(er) – auf dem Server wie „Review speichern“ der Desktop-App (data\\reviews). Redline und Review-Excel enthalten die Einträge.`);
}
window.addEventListener("beforeunload", e => { if (!OFFLINE && pendingCount()) { e.preventDefault(); e.returnValue = ""; } });

// Offline-Bericht: Eintraege im Browser merken (localStorage, je Bericht) und als CSV speichern
const offlineKey = () => OFFLINE && `audit.${OFFLINE.info.created}.${OFFLINE.info.title}`;
function offlineRemember() {
  const all = {};
  for (const [fid, tags] of Object.entries(OFFLINE.tags)) for (const t of tags)
    if (t.audit && AUDIT_EDIT.some(f => t.audit[f])) (all[fid] = all[fid] || {})[t.type + "|" + t.tag] = t.audit;
  store.set(offlineKey(), all);
}
function offlineRestore() {
  const saved = store.get(offlineKey(), {});
  let n = 0;
  for (const [fid, entries] of Object.entries(saved)) for (const t of OFFLINE.tags[fid] || []) {
    const a = entries[t.type + "|" + t.tag];
    if (a) { t.audit = { ...(t.audit || {}), ...a }; n++; }
  }
  const byKey = {};
  for (const [fid, tags] of Object.entries(OFFLINE.tags)) for (const t of tags) byKey[fid + "|" + t.type + "|" + t.tag] = t.audit;
  for (const r of OFFLINE.all_tags) { const a = byKey[r.file + "|" + r.type + "|" + r.tag]; if (a) r.audit = a; }
  return n;
}
function exportAuditCsv() {
  const head = ["PDF", "Zeichnungsnr.", "Typ", "Tag", "Anzahl", "Seiten", "Doppelt", ...AUDIT_EDIT, "Datum", "User"];
  const q = v => { const s = String(v ?? ""); return /[;"\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
  const lines = [head.join(";")];
  const files = Object.fromEntries(OFFLINE.files.map(f => [f.id, f]));
  for (const [fid, tags] of Object.entries(OFFLINE.tags)) for (const t of tags) {
    const a = t.audit || {}, f = files[fid] || {};
    lines.push([f.name, f.drawing_no, t.type, t.tag, t.count, t.pages, t.duplicate ? "Ja" : "", ...AUDIT_EDIT.map(x => a[x]), a.Datum, a.User].map(q).join(";"));
  }
  const name = `${OFFLINE.info.title}_Audit_${new Date().toISOString().slice(0, 19).replace(/[T:]/g, "-")}.csv`;
  const url = URL.createObjectURL(new Blob(["﻿" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: name });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
  status(`Audit-Ergebnisse gespeichert: ${name} (alle Tags aller PDFs, öffnet in Excel).`);
}

// Fundstellen-Navigation wie in der Desktop-App
function selectTag(tag, again) {
  if (again && state.nav && state.nav.tag === tag) return step(1);
  state.nav = { tag, focus: tag.hits.length === 1 ? 0 : null };
  showNav();
}
function step(dir) {
  if (!state.nav) {
    const t = tblTags.current || tblTags.view[0];
    if (!t) return;
    tblTags.select(t);
    state.nav = { tag: t, focus: null };
  }
  const n = state.nav.tag.hits.length;
  let f = state.nav.focus;
  if (n === 1) f = 0;
  else if (f === null) f = dir > 0 ? 0 : n - 1;
  else { f += dir; if (f < 0 || f >= n) f = null; }
  state.nav.focus = f;
  showNav();
}
function showNav() {
  const { tag, focus } = state.nav, hits = tag.hits, n = hits.length;
  const pages = [...new Set(hits.map(h => h[0]))];
  viewer.setMarks({ hits, focus });
  if (focus === null) {
    viewer.setPage(tag.page, true);
    const on = hits.filter(h => h[0] === tag.page).length;
    const more = pages.length > 1 ? ` · auch auf Seite ${pages.filter(p => p !== tag.page).map(p => p + 1).join(", ")}` : "";
    viewer.setInfo(`${tag.tag}: ${on} Fundstelle(n) auf dieser Seite${more} – F3 / erneuter Klick: nächste`);
  } else {
    const [p, r] = hits[focus];
    viewer.setPage(p, false);
    viewer.zoomRect(r);
    viewer.setInfo((n > 1 ? `${tag.tag}: Fundstelle ${focus + 1} / ${n}` : tag.tag) + (pages.length > 1 ? ` · Seite ${p + 1}` : ""));
  }
}

async function gotoTag(fileId, type, tagName) {
  showSheet("pid");
  const f = state.files.find(x => x.id === fileId);
  if (!f) return;
  tblFiles.select(f);
  await openFile(f);
  const t = state.tags.find(x => x.type === type && x.tag === tagName);
  if (t) { if (!tblTags.view.includes(t)) tblTags.resetFilters(); tblTags.select(t); selectTag(t, false); }
}

function showSheet(name) {
  $$(".sheet-tab").forEach(b => b.classList.toggle("active", b.dataset.sheet === name));
  $$(".sheet").forEach(s => s.classList.toggle("active", s.id === "sheet-" + name));
  if (name === "all") loadAllTags().catch(e => status("Fehler: " + e.message));
}

// Auswahl fuer Redline/Review: gefilterte Tag-Tabelle (wie Desktop: "Es gilt der Tabellenfilter")
function filteredKeys() {
  const filtered = tblTags.view.length !== state.tags.length;
  return filtered ? tblTags.view.map(t => [t.type, t.tag]) : null;
}
function needFile() {
  if (!state.file) { status("Bitte zuerst eine PDF in der Dateiliste wählen."); return false; }
  return true;
}

// ---- Dialoge --------------------------------------------------------------------------------------------------
function modal(html) { $("#modal").innerHTML = html; $("#modalBack").classList.add("open"); return $("#modal"); }
function closeModal() { $("#modalBack").classList.remove("open"); }

async function scanDialog() {
  const info = await getJson("info");
  const remembered = store.get("scanSources", null);
  const rows = info.sources.map(s => `<label><input type="checkbox" value="${s.index}" ${s.exists ? "" : "disabled"}
      ${s.exists && (!remembered || remembered.includes(s.path)) ? "checked" : ""}>
      <span class="${s.exists ? "" : "bad"}">${s.exists ? "✓" : "✗"} ${esc(s.path)}</span></label>`).join("");
  const m = modal(`<h2>Quellordner scannen</h2>
    <div class="section">Quellordner auf dem Server</div>
    ${rows || `<div class="note">Keine Quellordner eingerichtet. Sie werden auf dem Server in <code>config\\paths.json</code>
      (Desktop-Tool: Einstellungen › Pfade) oder beim Start mit <code>--source</code> festgelegt. Hochladen geht immer.</div>`}
    <div class="progress"><div id="scanBar"></div></div><div class="note" id="scanText"></div>
    <div class="buttons"><button class="btn" id="scanClose">Schließen</button>
      <button class="btn" id="scanCancel" disabled>Abbrechen</button>
      <button class="btn primary" id="scanStart" ${rows ? "" : "disabled"}>Scannen</button></div>`);
  $("#scanClose", m).onclick = closeModal;
  $("#scanCancel", m).onclick = () => postJson("cancel");
  $("#scanStart", m).onclick = async () => {
    const boxes = $$("input:checked", m);
    store.set("scanSources", boxes.map(b => info.sources[+b.value].path));
    try { await postJson("scan", { sources: boxes.map(b => +b.value), pipes: !!state.pipes }); } catch (e) { $("#scanText").textContent = e.message; return; }
    $("#scanStart", m).disabled = true; $("#scanCancel", m).disabled = false;
    pollScan();
  };
}

async function pollScan() {
  clearTimeout(state.scanTimer);
  let st;
  try { st = await getJson("scan"); } catch (e) { status("Fehler: " + e.message); return; }
  const bar = $("#scanBar"), text = $("#scanText");
  const pct = st.total ? Math.round(100 * st.done / st.total) : 0;
  if (bar) bar.style.width = pct + "%";
  const line = st.finished ? `Fertig: ${st.done} von ${st.total} PDFs eingelesen.${st.error ? " Fehler: " + st.error : ""}`
    : `${st.done} / ${st.total || "…"} – ${st.current}`;
  if (text) text.textContent = line;
  status("Scan: " + line);
  if (!state.lastScanRefresh || Date.now() - state.lastScanRefresh > 1500 || st.finished) {
    state.lastScanRefresh = Date.now();
    await loadFiles();
  }
  if (st.running) state.scanTimer = setTimeout(pollScan, 500);
  else {
    const c = $("#scanCancel"), s = $("#scanStart");
    if (c) c.disabled = true; if (s) s.disabled = false;
    status(line);
  }
}

async function uploadFiles(list) {
  const files = [...list].filter(f => f.name.toLowerCase().endsWith(".pdf"));
  if (!files.length) { status("Keine PDF-Dateien gewählt."); return; }
  let i = 0;
  for (const f of files) {
    status(`Hochladen ${++i} / ${files.length}: ${f.name} …`);
    try {
      await api("upload", { method: "POST", headers: { "X-File-Name": encodeURIComponent(f.name), "X-Pipes": state.pipes ? "1" : "0", "Content-Type": "application/pdf" }, body: f });
    } catch (e) { status(`${f.name}: ${e.message}`); }
  }
  await loadFiles();
  status(`${files.length} PDF(s) hochgeladen und eingelesen.`);
}

function bulkDialog() {
  const marked = tblFiles.selected();
  const o = store.get("bulk", { scope: "marked", redline: true, review_each: false, review_total: true });
  const m = modal(`<h2>Review Auswahl / Bulk</h2>
    <div class="section">PDFs</div>
    <label><input type="radio" name="scope" value="marked" ${o.scope === "marked" ? "checked" : ""} ${marked.length ? "" : "disabled"}> Markierte PDFs (${marked.length})</label>
    <label><input type="radio" name="scope" value="all" ${o.scope === "all" || !marked.length ? "checked" : ""}> Alle eingelesenen PDFs (${state.files.length})</label>
    <div class="section">Ausgaben</div>
    <label><input type="checkbox" id="bRed" ${o.redline ? "checked" : ""}> Redline-PDF je PDF</label>
    <label><input type="checkbox" id="bEach" ${o.review_each ? "checked" : ""}> Review-Excel je PDF</label>
    <label><input type="checkbox" id="bTotal" ${o.review_total ? "checked" : ""}> Review-Excel gesamt</label>
    <div class="note">Ergebnis: ZIP-Datei mit Unterordner <code>Review_&lt;Zeitstempel&gt;</code> als Download. Die Original-PDFs bleiben unverändert.</div>
    <div class="buttons"><button class="btn" id="bClose">Abbrechen</button><button class="btn primary" id="bGo">Erstellen</button></div>`);
  $("#bClose", m).onclick = closeModal;
  $("#bGo", m).onclick = async () => {
    const scope = $("input[name=scope]:checked", m).value;
    const opts = { redline: $("#bRed", m).checked, review_each: $("#bEach", m).checked, review_total: $("#bTotal", m).checked };
    store.set("bulk", { scope, ...opts });
    if (!opts.redline && !opts.review_each && !opts.review_total) return;
    const ids = scope === "marked" ? marked.map(f => f.id) : null;
    closeModal();
    await run(() => download("bulk", { ids, options: opts }, "Review Bulk"));
  };
}

function reportDialog() {
  const marked = tblFiles.selected().filter(f => !f.error);
  const o = store.get("report", { scope: "marked", redline: true, review: true });
  const pagesOf = list => list.reduce((s, f) => s + Math.max(f.pages || 1, 1), 0);
  const m = modal(`<h2>Offline-HTML-Bericht</h2>
    <div class="note">Eine HTML-Datei ohne Server: Tabellen, Filter, Viewer, Fundstellen-Navigation und Audit-Spalten.
      Weitergeben per Mail, Freigabe oder SharePoint; öffnen im Browser (Edge, Chrome).</div>
    <div class="section">PDFs</div>
    <label><input type="radio" name="rscope" value="marked" ${o.scope === "marked" && marked.length ? "checked" : ""} ${marked.length ? "" : "disabled"}> Markierte PDFs (${marked.length})</label>
    <label><input type="radio" name="rscope" value="all" ${o.scope === "all" || !marked.length ? "checked" : ""}> Alle eingelesenen PDFs (${state.files.length})</label>
    <div class="section">Im Bericht enthalten</div>
    <label><input type="checkbox" id="rRed" ${o.redline ? "checked" : ""}> Redline-PDF je PDF (macht die Datei etwa so groß wie die PDFs)</label>
    <label><input type="checkbox" id="rRev" ${o.review ? "checked" : ""}> Review-Excel je PDF</label>
    <div class="note" id="rSize"></div>
    <div class="buttons"><button class="btn" id="rClose">Abbrechen</button><button class="btn primary" id="rGo">Erstellen</button></div>`);
  const chosen = () => $("input[name=rscope]:checked", m).value === "marked" ? marked : state.files.filter(f => !f.error);
  const size = () => {
    const n = pagesOf(chosen());
    $("#rSize", m).textContent = `${chosen().length} PDF(s), ${n} Seite(n): ca. ${Math.max(1, Math.round(n * 0.7))} MB ohne Redline.` +
      (n > 150 ? " Sehr große Datei – besser markierte PDFs wählen." : "");
  };
  $$("input", m).forEach(i => (i.onchange = size)); size();
  $("#rClose", m).onclick = closeModal;
  $("#rGo", m).onclick = async () => {
    const scope = $("input[name=rscope]:checked", m).value, redline = $("#rRed", m).checked, review = $("#rRev", m).checked;
    store.set("report", { scope, redline, review });
    const ids = scope === "marked" ? marked.map(f => f.id) : null;
    closeModal();
    await run(() => download("report", { ids, redline, review }, "Offline-Bericht"));
  };
}

function helpDialog() {
  const m = modal(`<h2>Kurzanleitung</h2>
    <div class="section">Einlesen</div><div class="note">„Quellordner scannen“ liest die Ordner, die auf dem Server eingerichtet sind.
      „PDFs hochladen“ (oder PDFs ins Fenster ziehen) liest PDFs von diesem PC.</div>
    <div class="section">Prüfen</div><div class="note">PDF wählen, dann Tag anklicken oder mit den Pfeiltasten wählen. Bei mehreren
      Fundstellen zeigt der erste Klick die ganze Seite mit nummerierten Rahmen; jeder weitere Klick oder F3 springt zur nächsten,
      Umschalt+F3 zurück. Doppelte Tags sind gelb. Mausrad zoomt, Ziehen verschiebt, Doppelklick zeigt die ganze Seite.</div>
    <div class="section">Ausgaben</div><div class="note">Redline-PDF, Review-Excel und Export kommen als Download. Es gilt der
      Filter der Tag-Tabelle (z. B. „Nur doppelte“).</div>
    <div class="buttons"><button class="btn primary" id="hClose">OK</button></div>`);
  $("#hClose", m).onclick = closeModal;
}

// ---- Befehle --------------------------------------------------------------------------------------------------
async function run(fn) {
  try { await fn(); } catch (e) { status("Fehler: " + e.message); }
}
const commands = {
  scan: () => run(scanDialog),
  upload: () => $("#fileInput").click(),
  pipes: () => {
    state.pipes = !state.pipes; store.set("pipes", state.pipes);
    $$("[data-cmd=pipes]").forEach(b => b.classList.toggle("on", state.pipes));
    status(state.pipes ? "Rohrleitungsnummern werden beim nächsten Scan/Upload mit eingelesen." : "Rohrleitungsnummern: aus.");
  },
  clear: () => run(async () => { await postJson("clear"); state.file = null; state.tags = []; tblTags.setRows([]); await viewer.open(null); await loadFiles(); }),
  prev: () => step(-1),
  next: () => step(1),
  dups: () => {
    state.dupsOnly = !state.dupsOnly;
    $$("[data-cmd=dups]").forEach(b => b.classList.toggle("on", state.dupsOnly));
    tblTags.refresh(); tblAll.refresh();
  },
  reset: () => {
    if (state.dupsOnly) commands.dups();
    $("#pidFilter").value = ""; $("#allFilter").value = "";
    tblFiles.resetFilters(); tblTags.resetFilters(); tblAll.resetFilters();
  },
  bulk: () => state.files.length ? bulkDialog() : status("Noch keine PDFs eingelesen."),
  redline: () => needFile() && run(() => download("redline", { id: state.file.id, tags: filteredKeys() }, "Redline-PDF")),
  review: () => needFile() && run(() => {
    const keys = filteredKeys();
    return download("review", { ids: [state.file.id], tags: keys ? { [state.file.id]: keys } : null }, "Review-Excel");
  }),
  exportXlsx: () => state.files.length ? run(() => download("export", { format: "xlsx" }, "Export Excel")) : status("Noch keine PDFs eingelesen."),
  exportCsv: () => state.files.length ? run(() => download("export", { format: "csv" }, "Export CSV")) : status("Noch keine PDFs eingelesen."),
  help: helpDialog,
  selectAll: () => tblFiles.selectAll(),
  fit: () => viewer.fit(),
  zoomIn: () => viewer.zoom(1.4),
  zoomOut: () => viewer.zoom(1 / 1.4),
  rotate: () => viewer.rotate(),
  mono: () => setMono(!viewer.mono),
  saveAudit: () => run(() => saveAudit()),
  report: () => state.files.length ? reportDialog() : status("Noch keine PDFs eingelesen."),
  pagePrev: () => viewer.setPage(viewer.page - 1),
  pageNext: () => viewer.setPage(viewer.page + 1),
  openPdf: () => needFile() && window.open(`/api/files/${state.file.id}/pdf`, "_blank", "noopener"),
};

// Offline-Bericht: Redline-PDF, Review-Excel und Export-Excel sind beim Erstellen eingebettet worden (alle Tags)
function saveEmbedded(blob, label) {
  if (!blob) { status(`${label} ist in diesem Bericht nicht enthalten.`); return; }
  const a = Object.assign(document.createElement("a"), { href: blob.uri, download: blob.name });
  document.body.appendChild(a); a.click(); a.remove();
  const note = tblTags.view.length !== state.tags.length ? " (enthält alle Tags – der Tabellenfilter wirkt im Bericht nicht)" : "";
  status(`${label}: ${blob.name} gespeichert${note}.`);
}
if (OFFLINE) {
  const dl = OFFLINE.downloads || {}, per = id => (dl.per_file || {})[id] || {};
  Object.assign(commands, {
    redline: () => needFile() && saveEmbedded(per(state.file.id).redline, "Redline-PDF"),
    review: () => needFile() && saveEmbedded(per(state.file.id).review, "Review-Excel"),
    exportXlsx: () => saveEmbedded(dl.export, "Export Excel"),
    bulk: () => saveEmbedded(dl.review_total, "Review-Excel gesamt"),
  });
  const available = { redline: true, review: true, exportXlsx: !!dl.export, bulk: !!dl.review_total };
  for (const [cmd, ok] of Object.entries(available)) if (ok) SERVER_CMDS.delete(cmd);
}

document.addEventListener("click", e => {
  const b = e.target.closest("[data-cmd]");
  if (b) commands[b.dataset.cmd]();
  const t = e.target.closest(".sheet-tab");
  if (t) showSheet(t.dataset.sheet);
});
document.addEventListener("keydown", e => {
  if (e.key === "F3") { e.preventDefault(); step(e.shiftKey ? -1 : 1); }
  else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); commands.saveAudit(); }
  else if (e.key === "F5") { e.preventDefault(); if (!OFFLINE) commands.scan(); }
  else if (e.key === "Escape") closeModal();
});
$("#fileInput").onchange = e => { uploadFiles(e.target.files); e.target.value = ""; };
$("#pidFilter").oninput = e => { const v = e.target.value.trim().toLowerCase(); tblFiles.globalFilter = v; tblTags.globalFilter = v; tblFiles.refresh(); tblTags.refresh(); };
$("#allFilter").oninput = e => { tblAll.globalFilter = e.target.value.trim().toLowerCase(); tblAll.refresh(); };

// PDFs ins Fenster ziehen = hochladen
let dragDepth = 0;
window.addEventListener("dragenter", e => { if (!OFFLINE && [...e.dataTransfer.types].includes("Files")) { dragDepth++; $("#dropHint").classList.add("open"); } });
window.addEventListener("dragleave", () => { if (--dragDepth <= 0) { dragDepth = 0; $("#dropHint").classList.remove("open"); } });
window.addEventListener("dragover", e => e.preventDefault());
window.addEventListener("drop", e => { e.preventDefault(); if (OFFLINE) return; dragDepth = 0; $("#dropHint").classList.remove("open"); uploadFiles(e.dataTransfer.files); });

// Trennlinien ziehen (Breite/Hoehe wird gemerkt)
function splitter(el, cssVar, host, horizontal) {
  const saved = store.get(cssVar, null);
  if (saved) host.style.setProperty(cssVar, saved);
  el.addEventListener("pointerdown", e => {
    el.setPointerCapture(e.pointerId);
    const move = ev => {
      const b = host.getBoundingClientRect();
      const pct = horizontal ? (ev.clientY - b.top) / b.height : (ev.clientX - b.left) / b.width;
      const v = Math.round(Math.max(0.15, Math.min(0.85, pct)) * 1000) / 10 + "%";
      host.style.setProperty(cssVar, v); store.set(cssVar, v);
    };
    const up = () => { el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up); viewer.file && viewer.fit(); };
    el.addEventListener("pointermove", move); el.addEventListener("pointerup", up);
  });
}
splitter($("[data-split=main]"), "--left-w", $("#pidLayout"), false);
splitter($("[data-split=left]"), "--files-h", $(".pid-left"), true);

(async () => {
  state.pipes = !!store.get("pipes", false);
  $$("[data-cmd=pipes]").forEach(b => b.classList.toggle("on", state.pipes));
  if (OFFLINE) {               // Server-Funktionen ausblenden, leere Menueband-Gruppen ebenso
    $$("[data-cmd]").forEach(b => { if (SERVER_CMDS.has(b.dataset.cmd)) b.style.display = "none"; });
    $$(".ribbon .group").forEach(g => { if (!$$("[data-cmd]", g).some(b => b.style.display !== "none")) g.style.display = "none"; });
    $$("[title]").forEach(b => { if (b.dataset.cmd === "bulk") b.title = "Review-Excel über alle PDFs des Berichts speichern"; });
  }
  if (OFFLINE) offlineRestore();          // im Bericht schon erfasste Audit-Eintraege (dieser Browser)
  try {
    const info = await getJson("info");
    for (const [k, list] of [["review_values", state.reviewValues], ["change_values", state.changeValues], ["review_faulty", state.reviewFaulty]])
      if (Array.isArray(info[k])) list.splice(0, list.length, ...info[k]);
    $("#topInfo").textContent = OFFLINE ? `Offline-Bericht „${info.title}“ · erstellt ${info.created} · Version ${info.version}`
      : `Version ${info.version} · Server ${location.host}`;
    document.title = OFFLINE ? `${info.title} – P3D PDF Reader` : `P3D PDF Reader ${info.version}`;
    await loadFiles();
    if (OFFLINE) { status(`Offline-Bericht: ${state.files.length} PDFs. Zoom bis zur Bildauflösung (${info.max_px} px).`); return; }
    const st = await getJson("scan");
    if (st.running) pollScan();
  } catch (e) { status("Server nicht erreichbar: " + e.message); }
})();
