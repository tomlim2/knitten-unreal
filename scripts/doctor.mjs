#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const PLUGIN_NAME = "knitten-unreal";
const CORE_PLUGIN_NAME = "knitten";
const REPO_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

function parseArgs(argv) {
  const args = {
    marketplaceRoot: os.homedir(),
    allowSourceVersion: false,
  };
  for (const arg of argv) {
    if (arg.startsWith("--marketplace-root=")) {
      args.marketplaceRoot = path.resolve(arg.slice("--marketplace-root=".length));
    } else if (arg === "--allow-source-version") {
      args.allowSourceVersion = true;
    } else if (arg === "-h" || arg === "--help") {
      process.stdout.write(`${usage()}\n`);
      process.exit(0);
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}

function usage() {
  return `Usage:
  doctor.mjs [--marketplace-root=<path>] [--allow-source-version]

Checks the Knitten Unreal source checkout and its personal-marketplace
plugin copy.`;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function check(checks, id, run) {
  try {
    const detail = run();
    checks.push({ id, ok: true, detail });
  } catch (error) {
    checks.push({ id, ok: false, detail: error.message });
  }
}

function runJson(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || REPO_ROOT,
    env: options.env || process.env,
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw new Error((result.stderr || result.stdout || `${command} failed`).trim());
  }
  return JSON.parse(result.stdout);
}

function resolveKnittenPathBin(marketplaceRoot) {
  const candidates = [
    process.env.KNITTEN_PATH_BIN,
    path.join(path.dirname(REPO_ROOT), "knitten", "bin", "knitten-path"),
    path.join(marketplaceRoot, "plugins", CORE_PLUGIN_NAME, "bin", "knitten-path"),
  ].filter(Boolean);
  for (const candidate of candidates) {
    const resolved = path.resolve(candidate);
    if (fs.existsSync(resolved)) return resolved;
  }
  throw new Error("unable to find KNITTEN_PATH_BIN");
}

function countSkillFiles(root) {
  const skillsRoot = path.join(root, "skills");
  if (!fs.existsSync(skillsRoot)) return 0;
  let count = 0;
  const stack = [skillsRoot];
  while (stack.length) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const next = path.join(current, entry.name);
      if (entry.isDirectory()) stack.push(next);
      if (entry.isFile() && entry.name === "SKILL.md") count += 1;
    }
  }
  return count;
}

function listSkillDirsWithPrefix(root, prefix) {
  const skillsRoot = path.join(root, "skills");
  if (!fs.existsSync(skillsRoot)) return [];
  return fs
    .readdirSync(skillsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.startsWith(prefix))
    .map((entry) => entry.name)
    .sort();
}

function listForbiddenFindingReportRefs(root) {
  const forbidden = /ah-report-finding|operational-findings|operational finding|finding report|PROMOTED_FINDINGS|shotloom-promote-findings|Mechanical Finding Capture|knitten:ah-report-finding/i;
  const allowedSelfFiles = new Set(["scripts/doctor.mjs", "scripts/validate-boundary.mjs"]);
  const matches = [];
  const stack = [root];
  while (stack.length) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      if (entry.name === ".git" || entry.name === "node_modules" || entry.name === ".agent-local") continue;
      const absolutePath = path.join(current, entry.name);
      const relativePath = path.relative(root, absolutePath);
      if (entry.isDirectory()) {
        stack.push(absolutePath);
      } else if (entry.isFile() && !allowedSelfFiles.has(relativePath)) {
        const text = fs.readFileSync(absolutePath, "utf8");
        if (forbidden.test(text)) matches.push(relativePath);
      }
    }
  }
  return matches.sort();
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const checks = [];
  const sourceManifestPath = path.join(REPO_ROOT, ".codex-plugin", "plugin.json");
  const marketplacePath = path.join(args.marketplaceRoot, ".agents", "plugins", "marketplace.json");
  const copiedRoot = path.join(args.marketplaceRoot, "plugins", PLUGIN_NAME);
  const copiedManifestPath = path.join(copiedRoot, ".codex-plugin", "plugin.json");
  const knittenPathBin = resolveKnittenPathBin(args.marketplaceRoot);

  let sourceManifest = null;
  let marketplace = null;
  let entry = null;
  let copiedManifest = null;

  check(checks, "source-manifest", () => {
    sourceManifest = readJson(sourceManifestPath);
    if (sourceManifest.name !== PLUGIN_NAME) {
      throw new Error(`expected name ${PLUGIN_NAME}, got ${sourceManifest.name}`);
    }
    return sourceManifestPath;
  });

  check(checks, "source-skills-root", () => {
    const count = countSkillFiles(REPO_ROOT);
    return `${count} skills`;
  });

  check(checks, "source-no-ah-skills", () => {
    const skills = listSkillDirsWithPrefix(REPO_ROOT, "ah-");
    if (skills.length) throw new Error(`payload plugin must not include AH skills: ${skills.join(", ")}`);
    return "no skills/ah-* directories";
  });

  check(checks, "source-no-finding-report-refs", () => {
    const refs = listForbiddenFindingReportRefs(REPO_ROOT);
    if (refs.length) throw new Error(`payload plugin must not reference finding report capture: ${refs.join(", ")}`);
    return "no finding report references";
  });

  check(checks, "source-activation", () => {
    const result = runJson("node", ["scripts/validate-activation.mjs"]);
    if (!result.ok) throw new Error(`${result.issues.length} activation issues`);
    return `${result.skillCount} activation-checked skills`;
  });

  check(checks, "source-payload-output-shim", () => {
    const shimPath = path.join(REPO_ROOT, "scripts", "resolve-knitten-output");
    if (!fs.existsSync(shimPath)) throw new Error(`missing ${shimPath}`);
    const result = runJson(shimPath, ["--kind=review-json", "--name=ku-doctor-smoke"], {
      env: { ...process.env, KNITTEN_PATH_BIN: knittenPathBin },
    });
    if (result.selectedKind !== "review-json") throw new Error("unexpected selectedKind");
    return result.selectedPath || result.path || "review-json";
  });

  check(checks, "source-payload-boundary-warn-only", () => {
    const result = runJson("node", ["scripts/validate-boundary.mjs", "--warn-only"], {
      env: { ...process.env, KNITTEN_PATH_BIN: knittenPathBin },
    });
    if (!result.ok) throw new Error("warn-only boundary validation failed");
    return `${result.warningCount} warnings`;
  });

  check(checks, "source-payload-boundary-strict-status", () => {
    const result = spawnSync("node", ["scripts/validate-boundary.mjs"], {
      cwd: REPO_ROOT,
      env: { ...process.env, KNITTEN_PATH_BIN: knittenPathBin },
      encoding: "utf8",
    });
    let parsed = null;
    try {
      parsed = JSON.parse(result.stdout);
    } catch {
      throw new Error((result.stderr || result.stdout || "strict boundary validator failed").trim());
    }
    return parsed.ok ? "strict pass" : `strict pending: ${parsed.errorCount} errors, ${parsed.warningCount} warnings`;
  });

  check(checks, "marketplace-file", () => {
    marketplace = readJson(marketplacePath);
    if (!Array.isArray(marketplace.plugins)) throw new Error("marketplace.plugins must be an array");
    return marketplacePath;
  });

  check(checks, "marketplace-entry", () => {
    if (!marketplace) throw new Error("marketplace file did not load");
    entry = marketplace.plugins.find((plugin) => plugin?.name === PLUGIN_NAME);
    if (!entry) throw new Error(`missing ${PLUGIN_NAME} marketplace entry`);
    return entry.source?.path || "";
  });

  check(checks, "marketplace-core-entry", () => {
    if (!marketplace) throw new Error("marketplace file did not load");
    const coreEntry = marketplace.plugins.find((plugin) => plugin?.name === CORE_PLUGIN_NAME);
    if (!coreEntry) throw new Error(`missing ${CORE_PLUGIN_NAME} marketplace entry`);
    if (coreEntry.source?.path !== `./plugins/${CORE_PLUGIN_NAME}`) {
      throw new Error(`${CORE_PLUGIN_NAME} entry path must be ./plugins/${CORE_PLUGIN_NAME}`);
    }
    return coreEntry.source.path;
  });

  check(checks, "marketplace-entry-path", () => {
    if (!entry) throw new Error("marketplace entry did not load");
    if (entry.source?.source !== "local") throw new Error("entry source must be local");
    if (entry.source?.path !== `./plugins/${PLUGIN_NAME}`) {
      throw new Error(`entry path must be ./plugins/${PLUGIN_NAME}`);
    }
    return entry.source.path;
  });

  check(checks, "copied-manifest", () => {
    copiedManifest = readJson(copiedManifestPath);
    if (copiedManifest.name !== PLUGIN_NAME) {
      throw new Error(`expected copied name ${PLUGIN_NAME}, got ${copiedManifest.name}`);
    }
    return copiedManifestPath;
  });

  check(checks, "copied-version", () => {
    if (!copiedManifest) throw new Error("copied manifest did not load");
    if (!args.allowSourceVersion && !String(copiedManifest.version).includes("+codex.")) {
      throw new Error(`copied version lacks +codex. cachebuster: ${copiedManifest.version}`);
    }
    return copiedManifest.version;
  });

  check(checks, "copied-skills-root", () => {
    const count = countSkillFiles(copiedRoot);
    return `${count} skills`;
  });

  check(checks, "copied-no-ah-skills", () => {
    const skills = listSkillDirsWithPrefix(copiedRoot, "ah-");
    if (skills.length) throw new Error(`copied payload plugin must not include AH skills: ${skills.join(", ")}`);
    return "no copied skills/ah-* directories";
  });

  check(checks, "copied-no-finding-report-refs", () => {
    const refs = listForbiddenFindingReportRefs(copiedRoot);
    if (refs.length) throw new Error(`copied payload plugin must not reference finding report capture: ${refs.join(", ")}`);
    return "no copied finding report references";
  });

  check(checks, "copied-activation", () => {
    const result = runJson("node", ["scripts/validate-activation.mjs"], {
      cwd: copiedRoot,
    });
    if (!result.ok) throw new Error(`${result.issues.length} copied activation issues`);
    return `${result.skillCount} activation-checked skills`;
  });

  check(checks, "copied-payload-output-shim", () => {
    const shimPath = path.join(copiedRoot, "scripts", "resolve-knitten-output");
    if (!fs.existsSync(shimPath)) {
      throw new Error(`missing ${shimPath}; run node scripts/materialize-local-plugin.mjs`);
    }
    const result = runJson(shimPath, ["--kind=review-json", "--name=ku-copied-doctor-smoke"], {
      cwd: copiedRoot,
      env: { ...process.env, KNITTEN_PATH_BIN: knittenPathBin },
    });
    if (result.selectedKind !== "review-json") throw new Error("unexpected selectedKind");
    return result.selectedPath || result.path || "review-json";
  });

  const ok = checks.every((item) => item.ok);
  process.stdout.write(`${JSON.stringify({ ok, checks }, null, 2)}\n`);
  if (!ok) process.exitCode = 1;
}

main();
