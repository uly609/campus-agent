import fs from "node:fs";

const files = ["index.html", "src/main.js", "src/styles.css"];
for (const file of files) {
  const text = fs.readFileSync(new URL(`../${file}`, import.meta.url), "utf8");
  if (text.includes("TODO") || text.includes("console.log")) {
    throw new Error(`${file} contains temporary code`);
  }
}
console.log("frontend lint passed");

