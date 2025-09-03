import fs from "fs";
import path from "path";

export async function scaffoldProjectEntry() {
  const projectName = "my-project";
  const templates = loadTemplates("js", "local");
  const udpRules = loadUDPRules("udp.rules.json");
  const targetDir = path.resolve(process.cwd(), projectName);
  scaffoldProject(targetDir, templates, udpRules);
}

export function loadTemplates(lang, envProfile) {
  const tplDir = path.resolve(__dirname, "..", "templates", lang, envProfile);
  if (!fs.existsSync(tplDir)) throw new Error(`Templates not found: ${tplDir}`);
  return fs.readdirSync(tplDir).reduce((acc, file) => {
    acc[file] = fs.readFileSync(path.join(tplDir, file), "utf-8");
    return acc;
  }, {});
}

export function scaffoldProject(targetDir, templates) {
  if (!fs.existsSync(targetDir)) fs.mkdirSync(targetDir, { recursive: true });
  ["src", "tests", "docs"].forEach(dir => {
    const dp = path.join(targetDir, dir);
    if (!fs.existsSync(dp)) fs.mkdirSync(dp);
  });
  Object.entries(templates).forEach(([fn, content]) => {
    fs.writeFileSync(path.join(targetDir, fn), content);
  });
  console.log("Scaffold complete for", targetDir);
}
