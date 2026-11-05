const $ = (s, el = document) => el.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let MODES = {};
const cards = new Map();   // video id -> {el, sig}

async function api(path, opts = {}) {
  const r = await fetch(path, opts);
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.error || r.statusText);
  return body;
}
const post = (path, data) => api(path, {method: "POST", headers: {"Content-Type": "application/json"},
  body: JSON.stringify(data || {})});

async function loadModes() {
  MODES = await api("/api/status");
  const b = (name, m, label) => `<span class="badge ${m}">${name}: ${m === "mock" ? "MOCK (" + label + ")" : "LIVE"}</span>`;
  $("#modes").innerHTML = b("OpusClip", MODES.opusclip, "local FFmpeg cuts, not AI clips") +
    b("Publishing", MODES.publisher, "nothing is posted");
}

$("#checkBtn").onclick = async () => {
  $("#checkOut").textContent = "Checking…";
  try {
    const r = await api("/api/check");
    const line = (n, x) => x.mode === "mock" ? `${n}: MOCK (no credentials)` : x.ok
      ? `${n}: OK${x.plan ? " · plan " + x.plan : ""}${x.platforms ? " · " + Object.entries(x.platforms).map(([k, v]) => `${PLAT[k]}: ${v}`).join(", ") : ""}`
      : `${n}: FAILED · ${x.detail}`;
    $("#checkOut").textContent = line("OpusClip", r.opusclip) + "\n" + line("Upload-Post", r.publisher);
  } catch (e) { $("#checkOut").textContent = "Error: " + e.message; }
};

$("#newProject").addEventListener("submit", async e => {
  e.preventDefault();
  const fd = new FormData(e.target);
  if (!fd.get("file")?.name) fd.delete("file");
  $("#projectMsg").textContent = "Submitting…";
  try { const r = await api("/api/projects", {method: "POST", body: fd});
    $("#projectMsg").textContent = `Project #${r.id} submitted (${r.mode.toUpperCase()}).`; e.target.reset();
    loadProjects();
  } catch (err) { $("#projectMsg").textContent = "Error: " + err.message; }
});

async function loadProjects() {
  const projects = await api("/api/projects");
  projSig = projectsSig(projects);
  $("#projects").innerHTML = projects.length ? projects.map(p => `
    <div class="projhead"><strong>Project #${p.id}</strong>
      <span class="badge ${p.opus_mode}">${p.opus_mode.toUpperCase()}</span>
      <span class="badge ${p.status === "failed" ? "bad" : p.status === "ready" ? "ok" : "warn"}">${esc(p.status)}</span>
      <small>${esc(p.source_url || "uploaded file")}</small></div>
    ${p.error ? `<div class="err">${esc(p.error)}</div>` : ""}
    <div class="clips">${p.clips.map(c => `
      <div class="clip">
        ${c.url ? `<video src="${c.url}" controls preload="metadata"></video>` : "<p>(no file)</p>"}
        <p><strong>${esc(c.title)}</strong> ${c.is_mock ? '<span class="badge mock">MOCK</span>' : ""}
          ${c.source_kind === "opus_render" ? '<span class="badge warn" title="Downloaded from OpusClip; may already have OpusClip captions burned in. Clear the subtitles box if they double up.">OpusClip render</span>' : ""}
          ${c.source_kind === "raw_cut" ? '<span class="badge ok" title="Cut from your original file at OpusClip\'s timestamps; no overlays.">clean cut</span>' : ""}</p>
        ${c.subtitles ? "<p><small>Timed subtitles ready from transcript</small></p>" : ""}
        <p>${c.start_s ?? "?"}s – ${c.end_s ?? "?"}s ${c.score != null ? "· score " + c.score : ""}</p>
        <button data-clip="${c.id}" ${c.selected ? "disabled" : ""}>${c.selected ? "Selected" : "Use this clip"}</button>
      </div>`).join("")}</div>`).join("") : "<p><small>No projects yet.</small></p>";
  return projects;
}
$("#projects").addEventListener("click", async e => {
  const id = e.target.dataset.clip; if (!id) return;
  e.target.disabled = true;
  try { await post(`/api/clips/${id}/select`); await loadProjects(); await loadVideos(); }
  catch (err) { alert(err.message); e.target.disabled = false; }
});

function stateBadge(v) {
  if (v.approval_valid) return ["APPROVED", "ok"];
  if (v.render_status === "rendering") return ["RENDERING…", "warn"];
  if (v.render_status === "failed") return ["RENDER FAILED", "bad"];
  if (v.render_status === "rendered") return ["NEEDS APPROVAL", "warn"];
  return ["DRAFT", "warn"];
}
const PUB_LABEL = {submitting: ["Submitting…", "warn"], pending: ["Pending provider confirmation", "warn"],
  published: ["Published (provider confirmed)", "ok"], failed: ["Failed", "bad"],
  needs_action: ["NOT live: action needed", "bad"], mock_published: ["MOCK: not posted", "mock"]};
const PLAT = {instagram: "Instagram Reels", tiktok: "TikTok", youtube: "YouTube Shorts"};

function fillCard(el, v, full) {
  $("h3", el).textContent = `Video #${v.id} · ${v.clip?.title || ""}`;
  const [t, cls] = stateBadge(v); const s = $(".state", el); s.textContent = t; s.className = "badge state " + cls;
  if (full) {
    el.querySelectorAll("[data-f]").forEach(i => i.value = v[i.dataset.f] ?? "");
    if (v.clip?.url && $(".clipPrev", el).getAttribute("src") !== v.clip.url) $(".clipPrev", el).src = v.clip.url;
    renderDrafts(el, v);
  }
  const rp = $(".reactPrev", el);
  if (v.reaction_url && rp.getAttribute("src") !== v.reaction_url) { rp.src = v.reaction_url; rp.hidden = false; }
  const op = $(".outPrev", el);
  if (v.output_url && v.render_status === "rendered") {
    if (op.getAttribute("src") !== v.output_url) { op.src = v.output_url; }
    op.hidden = false;
  } else op.hidden = v.render_status !== "rendered";
  $(".renderErr", el).textContent = v.render_error || "";
  $(".render", el).disabled = v.render_status === "rendering";
  $(".approve", el).disabled = v.render_status !== "rendered" || v.approval_valid;
  $(".unapprove", el).disabled = !v.approved;
  $(".pub", el).disabled = !v.approval_valid;
  $(".pub", el).textContent = MODES.publisher === "mock" ? "Publish (MOCK, nothing is posted)" : "Publish approved video";
  $(".pubs tbody", el).innerHTML = v.publications.length ? v.publications.map(p => {
    const [lbl, c] = PUB_LABEL[p.status] || [p.status, "warn"];
    return `<tr><td>${PLAT[p.platform] || p.platform}</td><td><span class="badge ${c}">${esc(lbl)}</span></td>
      <td>${p.post_url ? `<a href="${esc(p.post_url)}" target="_blank" rel="noopener">${esc(p.post_url)}</a><br>` : ""}
      ${p.provider_post_id ? "id " + esc(p.provider_post_id) + "<br>" : ""}${esc(p.error || "")}
      <small>${esc(p.provider)} · ${esc(p.updated_at)} UTC</small></td></tr>`; }).join("")
    : `<tr><td colspan="3"><small>Not published anywhere yet.</small></td></tr>`;
  updateCounts(el);
}
function updateCounts(el) {
  el.querySelectorAll(".count").forEach(c => {
    const f = $(`[data-f="${c.dataset.for}"]`, el); c.textContent = `${f.value.length}/${f.maxLength}`; });
}
function renderDrafts(el, v) {
  const d = v.drafts || {}; const box = $(".draftOpts", el);
  if (!d.note) { box.innerHTML = ""; return; }
  const sect = (kind, field, arr) => arr?.length ? `<div class="kind">${kind}: click to use</div>` +
    arr.map(x => `<button class="opt" data-target="${field}">${esc(x)}</button>`).join("") : "";
  box.innerHTML = `<small>${esc(d.note)}</small>` + sect("Hooks", "hook", d.hooks) +
    sect("Titles", "title", d.titles) + sect("Captions", "caption", d.captions);
}

function collect(el) {
  const o = {}; el.querySelectorAll("[data-f]").forEach(i => o[i.dataset.f] = i.value); return o;
}
function wire(el, id) {
  const msg = t => $(".vmsg", el).textContent = t;
  const act = async (fn) => { try { const v = await fn(); if (v && v.id) { fillCard(el, v, false); cards.get(id).sig = sig(v); } }
    catch (e) { msg("Error: " + e.message); } };
  el.addEventListener("input", e => { if (e.target.dataset.f) { cards.get(id).dirty = true; updateCounts(el); } });
  $(".save", el).onclick = () => act(async () => { const v = await post(`/api/videos/${id}`, collect(el));
    cards.get(id).dirty = false; msg("Saved. Any approval was reset."); return v; });
  $(".drafts", el).onclick = () => act(async () => {
    await post(`/api/videos/${id}`, collect(el)); cards.get(id).dirty = false;
    const v = await post(`/api/videos/${id}/drafts`); renderDrafts(el, v); msg(""); return v; });
  $(".draftOpts", el).onclick = e => { const t = e.target.dataset.target; if (!t) return;
    $(`[data-f="${t}"]`, el).value = e.target.textContent; cards.get(id).dirty = true; updateCounts(el);
    msg("Draft copied in. Edit it, then Save text."); };
  $(".reaction", el).onchange = e => act(async () => { const fd = new FormData(); fd.append("file", e.target.files[0]);
    msg("Uploading reaction…"); const v = await api(`/api/videos/${id}/reaction`, {method: "POST", body: fd});
    msg("Reaction uploaded. Re-render to include it."); return v; });
  $(".render", el).onclick = () => act(async () => { await post(`/api/videos/${id}`, collect(el));
    cards.get(id).dirty = false; msg("Rendering with FFmpeg…"); return post(`/api/videos/${id}/render`); });
  $(".approve", el).onclick = () => act(async () => {
    if (cards.get(id).dirty) throw new Error("Save your text edits first, then approve.");
    const v = await post(`/api/videos/${id}/approve`, {video_reviewed: $(".okVideo", el).checked,
      captions_reviewed: $(".okCaps", el).checked}); msg("Approved."); return v; });
  $(".unapprove", el).onclick = () => act(() => post(`/api/videos/${id}/unapprove`));
  $(".pub", el).onclick = () => act(async () => {
    const platforms = [...el.querySelectorAll(".publish input:checked")].map(i => i.value);
    const live = MODES.publisher === "live";
    if (live && !confirm(`Publish publicly to: ${platforms.map(p => PLAT[p]).join(", ")}?`)) return null;
    const r = await post(`/api/videos/${id}/publish`, {platforms});
    msg((r.submitted.length ? "Submitted: " + r.submitted.join(", ") + ". " : "") +
      Object.entries(r.skipped).map(([p, w]) => `${p}: ${w}`).join("; ")); return r.video; });
  $(".refresh", el).onclick = () => act(() => post(`/api/videos/${id}/refresh`));
}
const sig = v => JSON.stringify([v.render_status, v.render_error, v.output_sha256, v.approved, v.approval_valid,
  v.reaction_file, v.publications]);

async function loadVideos() {
  const videos = await api("/api/videos");
  for (const v of videos) {
    let c = cards.get(v.id);
    if (!c) {
      const el = $("#videoTpl").content.firstElementChild.cloneNode(true);
      $("#videos").prepend(el); c = {el, sig: null, dirty: false}; cards.set(v.id, c);
      wire(el, v.id); fillCard(el, v, true); c.sig = sig(v);
    } else if (c.sig !== sig(v)) { fillCard(c.el, v, false); c.sig = sig(v); }
  }
  return videos;
}

let projSig = "";
const projectsSig = ps => JSON.stringify(ps.map(p => [p.id, p.status, p.error, p.clips.map(c => [c.id, c.selected])]));
async function loadProjectsIfChanged() {
  const ps = await api("/api/projects"); const sg = projectsSig(ps);
  if (sg !== projSig) { projSig = sg; await loadProjects(); }
}
let tickN = 0;
async function tick() {
  try {
    await loadProjectsIfChanged();
    const videos = await loadVideos();
    if (++tickN % 12 === 0)   // ~30 s: ask Upload-Post about live posts still pending
      for (const v of videos.filter(v => v.publications.some(p => p.status === "pending" && !p.is_mock)))
        await post(`/api/videos/${v.id}/refresh`);
  }   // cards only redraw when their status changes
  catch (e) { console.error(e); }
}
(async () => { await loadModes(); await loadProjects(); await loadVideos(); setInterval(tick, 2500); })();
