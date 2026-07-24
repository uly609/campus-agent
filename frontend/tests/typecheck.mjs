git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
import fs from "node:fs";

const app = fs.readFileSync(new URL("../src/App.vue", import.meta.url), "utf8");
for (const flow of ["sendChat", "runSearch", "createDraft", "loadMemory", "runEval", "loadTrace"]) {
  if (!app.includes(`function ${flow}`)) throw new Error(`missing UI flow ${flow}`);
}
if (!app.includes("<script setup>")) throw new Error("frontend is not a Vue 3 setup component");
console.log("frontend source checks passed");
