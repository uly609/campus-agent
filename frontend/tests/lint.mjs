git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
import fs from "node:fs";

const files = ["index.html", "src/main.js", "src/App.vue", "src/styles.css", "vite.config.js"];
for (const file of files) {
  const source = fs.readFileSync(new URL(`../${file}`, import.meta.url), "utf8");
  if (/TEMP_MARKER|console\.log|JSON\.stringify\([^)]*null,\s*2\)/.test(source)) {
    throw new Error(`${file} contains debug or temporary output`);
  }
}
console.log("frontend lint passed");
