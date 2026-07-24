<script setup>
import { computed, onMounted, ref } from "vue";
import {
  Activity,
  Bot,
  BookOpen,
  Check,
  ChevronRight,
  CircleAlert,
  FileImage,
  Gauge,
  ImagePlus,
  LayoutList,
  LoaderCircle,
  KeyRound,
  MemoryStick,
  MessageSquareText,
  RefreshCw,
  ServerCog,
  Search,
  Send,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-vue-next";

const views = [
  { id: "feed", label: "帖子", icon: LayoutList },
  { id: "chat", label: "AI 助手", icon: MessageSquareText },
  { id: "search", label: "智能搜索", icon: Search },
  { id: "draft", label: "发帖助手", icon: Sparkles },
  { id: "knowledge", label: "知识库", icon: BookOpen },
  { id: "memory", label: "记忆", icon: MemoryStick },
  { id: "eval", label: "评测", icon: Gauge },
  { id: "trace", label: "轨迹", icon: Activity },
  { id: "platform", label: "模型", icon: ServerCog },
];

const activeView = ref("feed");
const busy = ref("");
const notice = ref(null);
const posts = ref([]);
const chatInput = ref("图书馆今天几点关门？");
const chatResult = ref(null);
const searchInput = ref("南门捡到蓝色校园卡");
const searchResults = ref([]);
const draftIntent = ref("帮我根据图片起草失物招领");
const draftFeedback = ref("正文加一句在图书馆门口发现");
const draft = ref(null);
const draftAttributes = ref(null);
const draftImage = ref("");
const draftImageName = ref("");
const memories = ref([]);
const evalReport = ref(null);
const traces = ref([]);
const knowledgeDocuments = ref([]);
const ingestionJobs = ref([]);
const knowledgeForm = ref({ source_id: "", title: "", body: "", official: true });
const sessions = ref([]);
const activeSessionId = ref("ui-session");
const providers = ref([]);
const providerForm = ref({
  name: "百炼云模型",
  role: "chat",
  tier: "cloud_fallback",
  base_url: "",
  model: "qwen-plus",
  api_key: "",
  enabled: true,
});

const pageTitle = computed(() => views.find((item) => item.id === activeView.value)?.label || "CampusFlow AI");
const draftProgress = computed(() => draft.value ? `${draft.value.edit_round} / ${draft.value.max_edit_rounds}` : "0 / 5");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let message = "请求失败，请稍后重试";
    try {
      const payload = await response.json();
      message = payload.detail?.error_code || payload.detail?.code || payload.detail || message;
    } catch {
      // The friendly fallback above is sufficient for non-JSON gateway errors.
    }
    throw new Error(String(message));
  }
  return response.json();
}

async function run(key, action, success = "") {
  busy.value = key;
  notice.value = null;
  try {
    await action();
    if (success) notice.value = { type: "success", text: success };
  } catch (error) {
    notice.value = { type: "error", text: error instanceof Error ? error.message : "操作失败" };
  } finally {
    busy.value = "";
  }
}

function switchView(id) {
  activeView.value = id;
  notice.value = null;
  if (id === "memory" && !memories.value.length) loadMemory();
  if (id === "eval" && !evalReport.value) loadLatestEval();
  if (id === "trace" && !traces.value.length) loadTrace();
  if (id === "knowledge") loadKnowledge();
  if (id === "platform") loadProviders();
}

async function loadPosts() {
  await run("posts", async () => { posts.value = (await api("/api/v1/posts")).slice(0, 12); });
}

async function sendChat() {
  if (!chatInput.value.trim()) return;
  await run("chat", async () => {
    chatResult.value = await api("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: activeSessionId.value, user_id: "demo-user", message: chatInput.value.trim() }),
    });
    await loadSessions();
  });
}

async function loadSessions() {
  sessions.value = await api("/api/v1/sessions?user_id=demo-user");
}

async function newSession() {
  await run("session-new", async () => {
    const session = await api("/api/v1/sessions", {
      method: "POST",
      body: JSON.stringify({ user_id: "demo-user", title: "新对话" }),
    });
    activeSessionId.value = session.session_id;
    chatResult.value = null;
    await loadSessions();
  });
}

async function deleteSession(sessionId) {
  await run(`session-${sessionId}`, async () => {
    await api(`/api/v1/sessions/${sessionId}?user_id=demo-user`, { method: "DELETE" });
    if (activeSessionId.value === sessionId) {
      activeSessionId.value = "ui-session";
      chatResult.value = null;
    }
    await loadSessions();
  }, "会话已删除");
}

async function runSearch() {
  if (!searchInput.value.trim()) return;
  await run("search", async () => {
    const data = await api("/api/v1/posts/search", {
      method: "POST",
      body: JSON.stringify({ query: searchInput.value.trim(), top_k: 8 }),
    });
    searchResults.value = data.results;
  });
}

async function resizeImage(file) {
  const source = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("图片读取失败"));
    reader.readAsDataURL(file);
  });
  const image = await new Promise((resolve, reject) => {
    const element = new Image();
    element.onload = () => resolve(element);
    element.onerror = () => reject(new Error("图片格式不受支持"));
    element.src = source;
  });
  const scale = Math.min(1, 1280 / Math.max(image.width, image.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(image.width * scale));
  canvas.height = Math.max(1, Math.round(image.height * scale));
  canvas.getContext("2d").drawImage(image, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.86);
}

async function selectDraftImage(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    notice.value = { type: "error", text: "请选择图片文件" };
    return;
  }
  await run("image", async () => {
    draftImage.value = await resizeImage(file);
    draftImageName.value = file.name;
    draft.value = null;
    draftAttributes.value = null;
  });
  event.target.value = "";
}

function clearDraftImage() {
  draftImage.value = "";
  draftImageName.value = "";
  draft.value = null;
  draftAttributes.value = null;
}

async function createDraft() {
  if (!draftImage.value) {
    notice.value = { type: "error", text: "请先选择一张物品图片" };
    return;
  }
  await run("draft", async () => {
    const data = await api("/api/v1/posts/draft", {
      method: "POST",
      body: JSON.stringify({ intent: draftIntent.value.trim(), image_url: draftImage.value }),
    });
    draft.value = data.draft;
    draftAttributes.value = data.image_attributes;
  }, "草稿已生成");
}

async function updateDraft(confirm = false) {
  if (!draft.value) return;
  await run(confirm ? "confirm" : "edit", async () => {
    const data = await api(`/api/v1/posts/draft/${draft.value.draft_id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ feedback: draftFeedback.value.trim(), confirm }),
    });
    draft.value = data.draft;
  }, confirm ? "草稿已确认，尚未发布" : "修改已应用");
}

async function loadMemory() {
  await run("memory", async () => { memories.value = (await api("/api/v1/memories?user_id=demo-user")).memories; });
}

async function deleteMemory(memoryId) {
  await run(`memory-${memoryId}`, async () => {
    await api(`/api/v1/memories/${memoryId}?user_id=demo-user`, { method: "DELETE" });
    memories.value = memories.value.filter((item) => item.memory_id !== memoryId);
  }, "记忆已删除");
}

async function runEval() {
  await run("eval", async () => { evalReport.value = await api("/api/v1/evals/run", { method: "POST" }); }, "评测完成");
}

async function loadLatestEval() {
  await run("eval", async () => { evalReport.value = await api("/api/v1/evals/latest"); });
}

async function loadTrace() {
  await run("trace", async () => { traces.value = (await api("/api/v1/traces")).traces.slice().reverse(); });
}

async function loadKnowledge() {
  await run("knowledge-load", async () => {
    [knowledgeDocuments.value, ingestionJobs.value] = await Promise.all([
      api("/api/v1/knowledge/documents"),
      api("/api/v1/knowledge/jobs"),
    ]);
  });
}

async function selectKnowledgeFile(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  if (!/\.(txt|md|markdown)$/i.test(file.name)) {
    notice.value = { type: "error", text: "当前支持 TXT 和 Markdown 文档" };
    return;
  }
  knowledgeForm.value.title ||= file.name.replace(/\.(txt|md|markdown)$/i, "");
  knowledgeForm.value.source_id ||= `kb-${Date.now()}`;
  knowledgeForm.value.body = await file.text();
  event.target.value = "";
}

async function createKnowledge() {
  if (!knowledgeForm.value.title.trim() || !knowledgeForm.value.body.trim()) return;
  knowledgeForm.value.source_id ||= `kb-${Date.now()}`;
  await run("knowledge-create", async () => {
    await api("/api/v1/knowledge/documents", {
      method: "POST",
      body: JSON.stringify({
        ...knowledgeForm.value,
        source_type: knowledgeForm.value.official ? "official" : "post",
      }),
    });
    knowledgeForm.value = { source_id: "", title: "", body: "", official: true };
    await loadKnowledge();
  }, "文档已进入索引任务");
}

async function deleteKnowledge(sourceId) {
  await run(`knowledge-${sourceId}`, async () => {
    await api(`/api/v1/knowledge/documents/${sourceId}`, { method: "DELETE" });
    await loadKnowledge();
  }, "知识文档已删除");
}

async function retryIngestion(jobId) {
  await run(`job-${jobId}`, async () => {
    await api(`/api/v1/knowledge/jobs/${jobId}/retry`, { method: "POST" });
    await loadKnowledge();
  }, "任务已重新提交");
}

async function loadProviders() {
  await run("providers-load", async () => {
    providers.value = await api("/api/v1/providers");
  });
}

async function createProvider() {
  await run("provider-create", async () => {
    await api("/api/v1/providers", {
      method: "POST",
      body: JSON.stringify(providerForm.value),
    });
    providerForm.value.api_key = "";
    await loadProviders();
  }, "模型配置已加密保存");
}

async function checkProvider(providerId) {
  await run(`provider-${providerId}`, async () => {
    await api(`/api/v1/providers/${providerId}/check`, { method: "POST" });
    await loadProviders();
  });
}

async function deleteProvider(providerId) {
  await run(`provider-${providerId}`, async () => {
    await api(`/api/v1/providers/${providerId}`, { method: "DELETE" });
    await loadProviders();
  }, "模型配置已删除");
}

function metricLabel(key) {
  return ({
    intent_accuracy: "意图准确率",
    retrieval_hit_at_8: "检索命中率",
    retrieval_precision_at_5: "前 5 条精确率",
    retrieval_precision_at_8: "前 8 条精确率",
    retrieval_recall_at_8: "前 8 条召回率",
    retrieval_mrr: "检索排序质量",
    claim_recall: "事实覆盖率",
    citation_coverage: "引用覆盖率",
    citation_groundedness: "引用可靠性",
    must_not_show_rate: "敏感内容泄露率",
    refusal_accuracy: "拒答准确率",
    judge_f1: "相关性判断 F1",
    replan_success_rate: "重新规划成功率",
    tool_success_rate: "工具调用成功率",
    cache_repeat_hit_rate: "重复请求缓存命中率",
    p50_latency_ms: "P50 延迟",
    p95_latency_ms: "P95 延迟",
  })[key] || key.replaceAll("_", " ");
}

function metricValue(key, value) {
  if (key.endsWith("_ms")) return `${Math.round(value)} ms`;
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function categoryLabel(value) {
  return ({ lost_found: "失物招领", question: "校园问答", event: "校园活动", experience: "经验分享" })[value] || value;
}

function retrievalLabel(item) {
  const methods = String(item.metadata?.retrieval || "").toUpperCase();
  if (methods.includes("GRAPH")) return "关键词、语义与知识图谱综合匹配";
  if (methods.includes("VECTOR")) return "关键词与语义综合匹配";
  return "关键词相关内容";
}

function intentLabel(value) {
  return ({
    campus_qa: "校园问答",
    post_search: "帖子搜索",
    post_draft: "发帖草稿",
    memory_manage: "记忆管理",
    greeting: "日常问候",
  })[value] || "Agent 执行";
}

function statusLabel(value) {
  return ({
    queued: "排队中",
    processing: "处理中",
    indexing: "构建索引",
    completed: "已完成",
    ready: "可检索",
    failed: "失败",
    healthy: "可用",
    unchecked: "未检测",
  })[value] || value;
}

function modelVersionLabel(value) {
  if (String(value).includes("configured-real")) return "真实模型运行";
  if (String(value).includes("fake")) return "离线可复现模式";
  return "评测模型已记录";
}

onMounted(async () => {
  await Promise.all([loadPosts(), loadSessions()]);
});
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <button class="brand" type="button" aria-label="CampusFlow AI" @click="switchView('feed')">
        <span class="brand-mark"><Bot :size="22" /></span>
        <span><strong>CampusFlow</strong><small>校园智能体</small></span>
      </button>
      <nav aria-label="主导航">
        <button v-for="item in views" :key="item.id" :class="{ active: activeView === item.id }" type="button" @click="switchView(item.id)">
          <component :is="item.icon" :size="19" />
          <span>{{ item.label }}</span>
        </button>
      </nav>
      <div class="service-status"><span></span><div><strong>服务在线</strong><small>CampusFlow Runtime</small></div></div>
    </aside>

    <main>
      <header class="topbar">
        <div><span class="eyebrow">CAMPUSFLOW</span><h1>{{ pageTitle }}</h1></div>
        <div class="avatar" title="演示用户">CF</div>
      </header>

      <div v-if="notice" :class="['notice', notice.type]" role="status">
        <Check v-if="notice.type === 'success'" :size="18" />
        <CircleAlert v-else :size="18" />
        <span>{{ notice.text }}</span>
        <button type="button" aria-label="关闭提示" @click="notice = null"><X :size="17" /></button>
      </div>

      <section v-if="activeView === 'feed'" class="view">
        <div class="section-head"><div><h2>匿名校园动态</h2><p>最新发布的问答、活动与失物招领</p></div><button class="icon-button" title="刷新帖子" :disabled="busy === 'posts'" @click="loadPosts"><RefreshCw :class="{ spin: busy === 'posts' }" :size="19" /></button></div>
        <div class="post-grid">
          <article v-for="post in posts" :key="post.post_id" class="post-card">
            <div class="post-meta"><span>{{ categoryLabel(post.category) }}</span><time>{{ post.created_at.slice(0, 10) }}</time></div>
            <h3>{{ post.title }}</h3><p>{{ post.body }}</p>
            <footer><span>{{ post.author_alias }}</span><span>{{ post.location || '校园' }}</span></footer>
          </article>
        </div>
      </section>

      <section v-else-if="activeView === 'chat'" class="view chat-view">
        <div class="session-strip">
          <button class="secondary icon-text" :disabled="busy === 'session-new'" @click="newSession"><MessageSquareText :size="17" />新对话</button>
          <button v-for="session in sessions.slice(0, 4)" :key="session.session_id" :class="['session-item', { active: activeSessionId === session.session_id }]" @click="activeSessionId = session.session_id; chatResult = null">
            <span>{{ session.title }}</span>
            <Trash2 :size="14" @click.stop="deleteSession(session.session_id)" />
          </button>
        </div>
        <div class="chat-surface">
          <div v-if="!chatResult && busy !== 'chat'" class="empty-state"><span><Bot :size="26" /></span><h2>问我一个校园问题</h2><p>回答会标注信息来源。</p></div>
          <div v-if="busy === 'chat'" class="loading-state"><LoaderCircle class="spin" :size="25" /><span>正在检索校园知识…</span></div>
          <div v-if="chatResult" class="answer">
            <div class="answer-label"><Sparkles :size="18" /> CampusFlow 回答</div>
            <p>{{ chatResult.answer.answer }}</p>
            <div v-if="chatResult.citations.length" class="sources"><h3>信息来源</h3><div v-for="(citation, index) in chatResult.citations" :key="citation.citation_id" class="source"><span>{{ index + 1 }}</span><div><strong>{{ citation.title }}</strong><small>{{ citation.source_id }}</small></div></div></div>
            <div v-if="chatResult.degraded_mode.length" class="mode-warning"><CircleAlert :size="17" />当前使用演示模型，结果仅供界面体验。</div>
          </div>
        </div>
        <form class="composer" @submit.prevent="sendChat"><input v-model="chatInput" aria-label="校园问题" maxlength="2000" /><button class="primary icon-text" :disabled="busy === 'chat' || !chatInput.trim()"><Send :size="18" />发送</button></form>
      </section>

      <section v-else-if="activeView === 'search'" class="view">
        <form class="searchbar" @submit.prevent="runSearch"><Search :size="20" /><input v-model="searchInput" aria-label="搜索校园内容" /><button class="primary" :disabled="busy === 'search'">搜索</button></form>
        <div v-if="busy === 'search'" class="loading-state"><LoaderCircle class="spin" :size="24" /><span>正在融合检索结果…</span></div>
        <div v-else-if="searchResults.length" class="result-list"><article v-for="item in searchResults" :key="item.evidence_id" class="result-row"><div class="result-icon"><FileImage :size="20" /></div><div><div class="result-title"><h3>{{ item.title }}</h3><span>{{ item.official ? '官方' : '帖子' }}</span></div><p>{{ item.excerpt }}</p><small>{{ retrievalLabel(item) }}</small></div><ChevronRight :size="19" /></article></div>
        <div v-else class="empty-state compact"><Search :size="26" /><h2>搜索校园内容</h2></div>
      </section>

      <section v-else-if="activeView === 'draft'" class="view draft-layout">
        <div class="draft-workspace">
          <div class="section-head"><div><h2>图片发帖</h2><p>草稿确认前不会发布</p></div><span class="round-count">修改 {{ draftProgress }}</span></div>
          <label v-if="!draftImage" class="upload-zone">
            <input type="file" accept="image/jpeg,image/png,image/webp" @change="selectDraftImage" />
            <span><Upload :size="24" /></span><strong>选择物品图片</strong><small>JPG、PNG 或 WebP</small>
          </label>
          <div v-else class="image-preview"><img :src="draftImage" :alt="draftImageName" /><div><ImagePlus :size="18" /><span>{{ draftImageName }}</span></div><button class="icon-button danger" title="移除图片" @click="clearDraftImage"><Trash2 :size="18" /></button></div>
          <label class="field"><span>发帖意图</span><input v-model="draftIntent" maxlength="300" /></label>
          <button class="primary wide icon-text" :disabled="busy === 'draft' || busy === 'image' || !draftImage" @click="createDraft"><LoaderCircle v-if="busy === 'draft'" class="spin" :size="18" /><Sparkles v-else :size="18" />生成草稿</button>
        </div>
        <article class="draft-preview">
          <div v-if="!draft" class="empty-state"><FileImage :size="28" /><h2>草稿预览</h2><p>选择图片后生成内容。</p></div>
          <template v-else>
            <div class="draft-status"><span :class="{ confirmed: draft.confirmed }">{{ draft.confirmed ? '已确认' : '待确认' }}</span><small>AI 识别置信度 {{ Math.round((draftAttributes?.confidence || 0) * 100) }}%</small></div>
            <h2>{{ draft.title }}</h2><p class="draft-body">{{ draft.body }}</p>
            <div class="attribute-list"><span v-if="draftAttributes?.category">{{ draftAttributes.category }}</span><span v-if="draftAttributes?.color">{{ draftAttributes.color }}</span><span v-if="draftAttributes?.material">{{ draftAttributes.material }}</span><span v-for="hint in draftAttributes?.location_hints || []" :key="hint">{{ hint }}</span></div>
            <div class="edit-area"><input v-model="draftFeedback" :disabled="draft.confirmed" /><button class="secondary" :disabled="draft.confirmed || busy === 'edit' || draft.edit_round >= 5" @click="updateDraft(false)">修改</button><button class="primary icon-text" :disabled="draft.confirmed || busy === 'confirm'" @click="updateDraft(true)"><Check :size="18" />确认草稿</button></div>
          </template>
        </article>
      </section>

      <section v-else-if="activeView === 'knowledge'" class="view platform-layout">
        <div class="admin-panel">
          <div class="section-head"><div><h2>添加知识</h2><p>TXT 与 Markdown 将异步切分并写入混合检索</p></div></div>
          <label class="upload-document"><input type="file" accept=".txt,.md,.markdown,text/plain,text/markdown" @change="selectKnowledgeFile" /><Upload :size="20" /><span>选择文档</span></label>
          <label class="field"><span>文档标题</span><input v-model="knowledgeForm.title" maxlength="160" placeholder="例如：图书馆开放时间" /></label>
          <label class="field"><span>来源编号</span><input v-model="knowledgeForm.source_id" maxlength="120" placeholder="留空自动生成" /></label>
          <label class="field"><span>正文内容</span><textarea v-model="knowledgeForm.body" maxlength="200000" placeholder="粘贴学校官方通知或知识内容"></textarea></label>
          <label class="check-field"><input v-model="knowledgeForm.official" type="checkbox" /><span>标记为官方可信来源</span></label>
          <button class="primary wide icon-text" :disabled="busy === 'knowledge-create' || !knowledgeForm.title.trim() || !knowledgeForm.body.trim()" @click="createKnowledge"><BookOpen :size="18" />提交索引</button>
        </div>
        <div class="admin-content">
          <div class="section-head"><div><h2>知识文档</h2><p>{{ knowledgeDocuments.length }} 份文档 · {{ ingestionJobs.length }} 个任务</p></div><button class="icon-button" title="刷新知识库" @click="loadKnowledge"><RefreshCw :class="{ spin: busy === 'knowledge-load' }" :size="18" /></button></div>
          <div v-if="knowledgeDocuments.length" class="document-list">
            <article v-for="document in knowledgeDocuments" :key="document.source_id">
              <div class="document-icon"><BookOpen :size="19" /></div>
              <div><div class="document-title"><h3>{{ document.title }}</h3><span :class="document.status">{{ statusLabel(document.status) }}</span></div><p>{{ document.body }}</p><small>{{ document.source_id }} · {{ document.chunk_count }} 个片段</small></div>
              <button class="icon-button danger" title="删除文档" @click="deleteKnowledge(document.source_id)"><Trash2 :size="17" /></button>
            </article>
          </div>
          <div v-else class="empty-state compact"><BookOpen :size="28" /><h2>暂无知识文档</h2></div>
          <div v-if="ingestionJobs.some((job) => job.status !== 'completed')" class="job-list">
            <h3>最近任务</h3>
            <article v-for="job in ingestionJobs.slice(0, 5)" :key="job.job_id">
              <div><strong>{{ job.source_id }}</strong><small>{{ statusLabel(job.status) }} · 第 {{ job.attempt }} 次</small><div class="progress"><span :style="{ width: `${job.progress}%` }"></span></div></div>
              <button v-if="job.status === 'failed' && job.attempt < job.max_attempts" class="secondary" @click="retryIngestion(job.job_id)">重试</button>
            </article>
          </div>
        </div>
      </section>

      <section v-else-if="activeView === 'memory'" class="view">
        <div class="section-head"><div><h2>长期记忆</h2><p>你可以查看或删除保存的信息</p></div><button class="secondary icon-text" :disabled="busy === 'memory'" @click="loadMemory"><RefreshCw :class="{ spin: busy === 'memory' }" :size="18" />刷新</button></div>
        <div v-if="memories.length" class="memory-list"><article v-for="memory in memories" :key="memory.memory_id"><div><span>{{ memory.memory_type }}</span><h3>{{ memory.key }}</h3><p>{{ memory.value }}</p></div><button class="icon-button danger" title="删除记忆" :disabled="busy === `memory-${memory.memory_id}`" @click="deleteMemory(memory.memory_id)"><Trash2 :size="18" /></button></article></div>
        <div v-else class="empty-state compact"><MemoryStick :size="27" /><h2>暂无长期记忆</h2></div>
      </section>

      <section v-else-if="activeView === 'eval'" class="view">
        <div class="section-head"><div><h2>质量评测</h2><p>意图 80 · 检索 18 · 问答 14</p></div><button class="primary icon-text" :disabled="busy === 'eval'" @click="runEval"><LoaderCircle v-if="busy === 'eval'" class="spin" :size="18" /><Gauge v-else :size="18" />运行评测</button></div>
        <template v-if="evalReport"><div class="run-meta"><span>{{ evalReport.run_id }}</span><small>{{ modelVersionLabel(evalReport.model_version) }}</small></div><div class="metric-grid"><article v-for="(value, key) in evalReport.metrics" :key="key"><small>{{ metricLabel(key) }}</small><strong>{{ metricValue(key, value) }}</strong></article></div></template>
        <div v-else class="empty-state"><Gauge :size="28" /><h2>等待评测</h2></div>
      </section>

      <section v-else-if="activeView === 'trace'" class="view">
        <div class="section-head"><div><h2>执行轨迹</h2><p>最近 50 次 Agent 执行记录</p></div><button class="secondary icon-text" :disabled="busy === 'trace'" @click="loadTrace"><RefreshCw :class="{ spin: busy === 'trace' }" :size="18" />刷新</button></div>
        <div v-if="traces.length" class="trace-list"><article v-for="(trace, index) in traces.slice(0, 20)" :key="trace.request_id || index"><span class="trace-dot"></span><div><strong>{{ intentLabel(trace.intent) }}</strong><small>{{ trace.request_id || trace.trace_id }}</small><p>{{ trace.node || trace.status || '已完成' }}</p></div></article></div>
        <div v-else class="empty-state"><Activity :size="28" /><h2>暂无执行轨迹</h2><p>完成一次聊天后刷新。</p></div>
      </section>

      <section v-else class="view platform-layout">
        <div class="admin-panel">
          <div class="section-head"><div><h2>添加模型</h2><p>密钥加密保存，页面不会再次显示</p></div><KeyRound :size="20" /></div>
          <label class="field"><span>显示名称</span><input v-model="providerForm.name" maxlength="80" /></label>
          <div class="field-row">
            <label class="field"><span>能力</span><select v-model="providerForm.role"><option value="chat">对话</option><option value="embedding">向量</option><option value="vlm">视觉</option></select></label>
            <label class="field"><span>路由层级</span><select v-model="providerForm.tier"><option value="local_primary">本地主节点</option><option value="local_backup">本地备用</option><option value="cloud_fallback">云端降级</option></select></label>
          </div>
          <label class="field"><span>OpenAI 兼容地址</span><input v-model="providerForm.base_url" placeholder="https://.../compatible-mode/v1" /></label>
          <label class="field"><span>模型名称</span><input v-model="providerForm.model" /></label>
          <label class="field"><span>API Key</span><input v-model="providerForm.api_key" type="password" autocomplete="new-password" placeholder="只在保存时提交" /></label>
          <button class="primary wide icon-text" :disabled="busy === 'provider-create' || !providerForm.base_url || !providerForm.model" @click="createProvider"><ServerCog :size="18" />保存配置</button>
        </div>
        <div class="admin-content">
          <div class="section-head"><div><h2>模型路由</h2><p>本地主节点 → 本地备用 → 云端降级</p></div><button class="icon-button" title="刷新模型配置" @click="loadProviders"><RefreshCw :class="{ spin: busy === 'providers-load' }" :size="18" /></button></div>
          <div v-if="providers.length" class="provider-list">
            <article v-for="provider in providers" :key="provider.provider_id">
              <div class="provider-main"><span>{{ provider.role.toUpperCase() }}</span><h3>{{ provider.name }}</h3><p>{{ provider.model }}</p><small>{{ provider.base_url }}</small></div>
              <div class="provider-state"><span :class="provider.last_check_status">{{ statusLabel(provider.last_check_status) }}</span><small>{{ provider.api_key_present ? '密钥已加密' : '未配置密钥' }}</small></div>
              <button class="secondary" :disabled="busy === `provider-${provider.provider_id}`" @click="checkProvider(provider.provider_id)">检测</button>
              <button class="icon-button danger" title="删除模型配置" @click="deleteProvider(provider.provider_id)"><Trash2 :size="17" /></button>
            </article>
          </div>
          <div v-else class="empty-state compact"><ServerCog :size="28" /><h2>尚未添加运行模型</h2><p>未配置时会明确使用离线演示适配器。</p></div>
        </div>
      </section>
    </main>
  </div>
</template>
