#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const REPO_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const SKILLS_ROOT = path.join(REPO_ROOT, "skills");

function read(relativePath) {
  return fs.readFileSync(path.join(REPO_ROOT, relativePath), "utf8");
}

function exists(relativePath) {
  return fs.existsSync(path.join(REPO_ROOT, relativePath));
}

function skillNames() {
  return fs.readdirSync(SKILLS_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .filter((entry) => exists(path.join("skills", entry.name, "SKILL.md")))
    .map((entry) => entry.name)
    .sort();
}

function staleSkillDirs() {
  return fs.readdirSync(SKILLS_ROOT, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .filter((entry) => !exists(path.join("skills", entry.name, "SKILL.md")))
    .map((entry) => entry.name)
    .sort();
}

function frontmatter(text) {
  if (!text.startsWith("---\n")) return "";
  const end = text.indexOf("\n---", 4);
  return end < 0 ? "" : text.slice(4, end);
}

function checkSkillActivation(names) {
  const issues = [];
  for (const name of names) {
    const relativePath = path.join("skills", name, "SKILL.md");
    const text = read(relativePath);
    const fm = frontmatter(text);
    if (!/^activation-check:\s*(loose|normal|strict)\s*$/m.test(fm)) {
      issues.push(`${relativePath}: missing frontmatter activation-check`);
    }
    if (!/Step 0: Activation Check/.test(text)) {
      issues.push(`${relativePath}: missing Step 0: Activation Check`);
    }
    const body = text.slice(text.indexOf("\n---", 4) + 4);
    if (/^activation-check:/m.test(body)) {
      issues.push(`${relativePath}: duplicate activation-check in body`);
    }
  }
  return issues;
}

function main() {
  const names = skillNames();
  const issues = [];
  for (const dir of staleSkillDirs()) {
    issues.push(`skills/${dir}: directory has no SKILL.md`);
  }
  issues.push(...checkSkillActivation(names));

  const output = {
    ok: issues.length === 0,
    skillCount: names.length,
    issues,
  };
  process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
  if (!output.ok) process.exitCode = 1;
}

main();
