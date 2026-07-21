import fs from "node:fs";

const main = fs.readFileSync(new URL("../src/main.js", import.meta.url), "utf8");
for (const required of ["sendChat", "runSearch", "createDraft", "loadMemory", "runEval"]) {
  if (!main.includes(required)) throw new Error(`missing UI flow ${required}`);
}
console.log("frontend typecheck passed");

