import fs from "fs";

export async function validateEntry() {
  const rules = loadUDPRules("udp.rules.json");
  console.log("🔒 Validating UDP rules...");
  validateUDP(rules, { projectName: "my-project" });
}

export function loadUDPRules(p) {
  if (!fs.existsSync(p)) throw new Error(`Rules not found: ${p}`);
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

export function validateUDP(rules, ctx) {
  if (rules.namePattern) {
    const re = new RegExp(rules.namePattern);
    if (!re.test(ctx.projectName)) throw new Error("Project name violates UDP");
  }
  console.log("UDP validation passed");
}
