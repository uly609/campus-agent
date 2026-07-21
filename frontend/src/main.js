const API = location.hostname === "localhost" ? "http://localhost:8000" : "";
let currentDraftId = "";

function show(view) {
  document.querySelectorAll(".view").forEach((el) => el.classList.toggle("active", el.id === view));
  document.querySelectorAll(".sidebar button").forEach((el) => el.classList.toggle("active", el.dataset.view === view));
}

async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function card(title, body, meta = "") {
  return `<article class="card"><h3>${escapeHtml(title)}</h3><p>${escapeHtml(body)}</p><small>${escapeHtml(meta)}</small></article>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char]));
}

async function loadPosts() {
  const posts = await api("/api/v1/posts");
  document.querySelector("#post-list").innerHTML = posts.slice(0, 12).map((post) => card(post.title, post.body, `${post.category} · ${post.location || "校园"}`)).join("");
}

async function sendChat() {
  const message = document.querySelector("#chat-input").value;
  const out = document.querySelector("#chat-output");
  out.textContent = "运行中...";
  const result = await api("/api/v1/chat", { method: "POST", body: JSON.stringify({ session_id: "ui-session", user_id: "demo-user", message }) });
  const citations = result.citations.map((item, index) => `<div class="citation">[${index + 1}] ${escapeHtml(item.title)} · ${escapeHtml(item.source_id)}</div>`).join("");
  const nodes = result.trace.filter((item) => item.event === "node_finished").map((item) => item.node).join(" → ");
  out.innerHTML = `<p>${escapeHtml(result.answer.answer)}</p>${citations}<pre>${escapeHtml(nodes)}</pre>`;
}

async function runSearch() {
  const query = document.querySelector("#search-input").value;
  const data = await api("/api/v1/posts/search", { method: "POST", body: JSON.stringify({ query, image_attributes: { category: "校园卡", color: "蓝色", location_hints: ["南门"] }, top_k: 8 }) });
  document.querySelector("#search-results").innerHTML = data.results.map((item) => card(item.title, item.excerpt, `${item.metadata.retrieval} · ${item.metadata.explanation}`)).join("");
}

async function createDraft() {
  const intent = document.querySelector("#draft-intent").value;
  const data = await api("/api/v1/posts/draft", { method: "POST", body: JSON.stringify({ intent, image_url: "synthetic-card-library-blue.png" }) });
  currentDraftId = data.draft.draft_id;
  renderDraft(data.draft, data.image_attributes);
}

function renderDraft(draft, attrs = {}) {
  document.querySelector("#draft-box").innerHTML = `<h3>${escapeHtml(draft.title)}</h3><p>${escapeHtml(draft.body)}</p><p>轮次 ${draft.edit_round}/${draft.max_edit_rounds}</p><pre>${escapeHtml(JSON.stringify(attrs, null, 2))}</pre>`;
}

async function editDraft(confirm = false) {
  if (!currentDraftId) await createDraft();
  const feedback = document.querySelector("#draft-feedback").value;
  const data = await api(`/api/v1/posts/draft/${currentDraftId}/feedback`, { method: "POST", body: JSON.stringify({ feedback, confirm }) });
  renderDraft(data.draft);
}

async function loadMemory() {
  const data = await api("/api/v1/memories?user_id=demo-user");
  document.querySelector("#memory-list").innerHTML = data.memories.length ? data.memories.map((m) => card(m.key, m.value, m.memory_type)).join("") : '<div class="panel empty">暂无长期记忆。</div>';
}

async function runEval() {
  const box = document.querySelector("#eval-report");
  box.textContent = "评测运行中...";
  const data = await api("/api/v1/evals/run", { method: "POST" });
  box.innerHTML = `<h3>${escapeHtml(data.run_id)}</h3><pre>${escapeHtml(JSON.stringify(data.metrics, null, 2))}</pre>`;
}

async function loadTrace() {
  const data = await api("/api/v1/traces").catch(() => ({ traces: [] }));
  document.querySelector("#trace-list").innerHTML = `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
}

document.querySelectorAll(".sidebar button").forEach((button) => button.addEventListener("click", () => show(button.dataset.view)));
document.querySelector("#refresh-posts").addEventListener("click", loadPosts);
document.querySelector("#send-chat").addEventListener("click", sendChat);
document.querySelector("#run-search").addEventListener("click", runSearch);
document.querySelector("#create-draft").addEventListener("click", createDraft);
document.querySelector("#edit-draft").addEventListener("click", () => editDraft(false));
document.querySelector("#confirm-draft").addEventListener("click", () => editDraft(true));
document.querySelector("#load-memory").addEventListener("click", loadMemory);
document.querySelector("#run-eval").addEventListener("click", runEval);
document.querySelector("#load-trace").addEventListener("click", loadTrace);
loadPosts().catch((error) => { document.querySelector("#post-list").innerHTML = `<div class="panel empty">${escapeHtml(error.message)}</div>`; });
