import fs from "node:fs";

const html = fs.readFileSync(new URL("../index.html", import.meta.url), "utf8");
const app = fs.readFileSync(new URL("../src/App.vue", import.meta.url), "utf8");
if (!html.includes('id="app"')) throw new Error("missing Vue mount point");
for (const text of ["AI 学问", "智能搜索", "发帖助手", "校园技能", "记忆", "评测", "轨迹"]) {
  if (!app.includes(text)) throw new Error(`missing demo surface ${text}`);
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
for (const text of ["浙商小林", "浙江工商大学校园 Agent", "Agent 执行过程", "任务规划", "证据相关性判断"]) {
  if (!app.includes(text)) throw new Error(`missing xiaolin workbench ${text}`);
}
if (!app.includes("agentProcess") || !app.includes("toolLabel")) {
  throw new Error("xiaolin chat must map planner and tool traces");
}
if (!app.includes("uniqueCitations")) throw new Error("chat citations must be de-duplicated for display");
if (!app.includes("runCampusPrompt") || !app.includes("活动统筹") || !app.includes("200人的讲座场地")) {
  throw new Error("campus skills need executable demo actions");
}
console.log("frontend tests passed");
