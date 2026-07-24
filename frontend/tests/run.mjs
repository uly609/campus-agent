git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
import fs from "node:fs";

const html = fs.readFileSync(new URL("../index.html", import.meta.url), "utf8");
const app = fs.readFileSync(new URL("../src/App.vue", import.meta.url), "utf8");
if (!html.includes('id="app"')) throw new Error("missing Vue mount point");
for (const text of ["AI 助手", "智能搜索", "发帖助手", "长期记忆", "质量评测", "执行轨迹"]) {
  if (!app.includes(text)) throw new Error(`missing demo surface ${text}`);
}
if (!app.includes('type="file"') || !app.includes("resizeImage")) throw new Error("missing real image upload flow");
if (app.includes("JSON.stringify(attrs")) throw new Error("raw image attributes must not be rendered");
console.log("frontend tests passed");
