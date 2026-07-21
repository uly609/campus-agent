import fs from "node:fs";

const html = fs.readFileSync(new URL("../index.html", import.meta.url), "utf8");
const required = ["AI 助手", "智能搜索", "发帖助手", "记忆管理", "Eval Dashboard", "Execution Trace"];
for (const text of required) {
  if (!html.includes(text)) throw new Error(`missing demo surface ${text}`);
}
console.log("frontend tests passed");

