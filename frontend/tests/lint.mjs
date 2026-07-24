import fs from "node:fs";

const files = ["index.html", "src/main.js", "src/App.vue", "src/styles.css", "vite.config.js"];
for (const file of files) {
  const source = fs.readFileSync(new URL(`../${file}`, import.meta.url), "utf8");
  if (/TEMP_MARKER|console\.log|JSON\.stringify\([^)]*null,\s*2\)/.test(source)) {
    throw new Error(`${file} contains debug or temporary output`);
  }
}
console.log("frontend lint passed");
