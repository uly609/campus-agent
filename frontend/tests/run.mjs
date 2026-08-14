import fs from "node:fs";

const html = fs.readFileSync(new URL("../index.html", import.meta.url), "utf8");
const app = fs.readFileSync(new URL("../src/App.vue", import.meta.url), "utf8");
if (!html.includes('id="app"')) throw new Error("missing Vue mount point");
for (const text of ["AI 助手", "内容助手", "Agent 技能", "记忆", "评测", "轨迹"]) {
  if (!app.includes(text)) throw new Error(`missing demo surface ${text}`);
}
if (!app.includes("搜索知识社区内容") || !app.includes("加载更多帖子")) {
  throw new Error("post feed must include search and pagination");
}
if (!app.includes('type="file"') || !app.includes("resizeImage")) throw new Error("missing real image upload flow");
if (app.includes("JSON.stringify(attrs")) throw new Error("raw image attributes must not be rendered");
if (!app.includes("openSourceDetail") || !app.includes('role="dialog"')) throw new Error("search results need source details");
if (!app.includes("draftCategories") || !app.includes("自动识别")) throw new Error("post assistant needs multiple campus scenarios");
if (app.includes("|| !draftImage")) throw new Error("post drafting must support text without an image");
if (!app.includes("publishDraft") || !app.includes("发布帖子")) {
  throw new Error("confirmed drafts need an explicit publish action");
}
if (!app.includes("chatMessages") || !app.includes("新对话")) {
  throw new Error("chat must preserve and present a continuous conversation");
}
for (const text of ["AtlasHub", "企业知识社区与智能治理 Agent", "Agent 执行过程", "任务计划", "处理步骤"]) {
  if (!app.includes(text)) throw new Error(`missing xiaolin workbench ${text}`);
}
if (!app.includes("agentProcess") || !app.includes("toolLabel")) {
  throw new Error("xiaolin chat must map planner and tool traces");
}
if (!app.includes("const xiaolinAgentEnabled = ref(false)")) {
  throw new Error("xiaolin chat must default to upstream normal mode");
}
if (!app.includes("is_agent: isAgent") || !app.includes("processInfo: useAgent ?")) {
  throw new Error("normal and Agent modes must use different chat flows");
}
for (const extension of [".xlsx", ".csv", ".pdf"]) {
  if (!app.includes(extension)) throw new Error(`chat attachments must support ${extension}`);
}
if (!app.includes("files.map(({ name, dataUrl })") || !app.includes("chatFiles.value.push")) {
  throw new Error("chat documents must be encoded and sent to the Agent backend");
}
if (!app.includes("xiaolin-agent-toggle") || !app.includes('@keydown="handleChatKeydown"')) {
  throw new Error("xiaolin composer must expose mode switching and upstream keyboard behavior");
}
if (!app.includes("chat-avatar") || !app.includes("xiaolin-header-actions") || !app.includes("xiaolin-history-panel")) {
  throw new Error("chat must expose the branded avatar, header actions, and history drawer");
}
if (!app.includes("normalizeXiaolinTaskResult") || !app.includes('{ status: "success", api_result: result }')) {
  throw new Error("successful XiaoLin task events must not be displayed as failures");
}
if (!app.includes("uniqueCitations")) throw new Error("chat citations must be de-duplicated for display");
if (!app.includes("xiaolinTaskDataMode") || !app.includes("回答使用演示数据") || !app.includes("模型直接回答 · 未检索企业资料")) {
  throw new Error("chat answers must disclose verified, demo, live, and ungrounded data modes");
}
if (!app.includes("runCampusPrompt") || !app.includes("发布统筹") || !app.includes("订单服务消息积压")) {
  throw new Error("enterprise skills need executable demo actions");
}
console.log("frontend tests passed");
