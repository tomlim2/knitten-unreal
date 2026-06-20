#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const REPO_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

function usage() {
  return `Usage:
  validate-boundary.mjs [--warn-only]

Delegates payload boundary validation to knitten/scripts/validate-payload-boundary.mjs.`;
}

function parseArgs(argv) {
  const args = [];
  for (const arg of argv) {
    if (arg === "--warn-only") args.push(arg);
    else if (arg === "-h" || arg === "--help") {
      process.stdout.write(`${usage()}\n`);
      process.exit(0);
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}

function candidateRoots() {
  return [
    process.env.KNITTEN_CORE_ROOT,
    process.env.KNITTEN_PLUGIN_ROOT,
    process.env.KNITTEN_PLUGINS_ROOT ? path.join(process.env.KNITTEN_PLUGINS_ROOT, "knitten") : "",
    path.join(path.dirname(REPO_ROOT), "knitten"),
    path.join(process.env.HOME || "", "plugins", "knitten"),
  ].filter(Boolean);
}

function findValidator() {
  for (const root of candidateRoots()) {
    const validator = path.join(path.resolve(root), "scripts", "validate-payload-boundary.mjs");
    if (fs.existsSync(validator)) return validator;
  }
  throw new Error("unable to find knitten/scripts/validate-payload-boundary.mjs");
}

function main() {
  const passthrough = parseArgs(process.argv.slice(2));
  const validator = findValidator();
  const result = spawnSync("node", [validator, "--payload", REPO_ROOT, ...passthrough], {
    cwd: REPO_ROOT,
    stdio: "inherit",
  });
  process.exit(result.status ?? 1);
}

try {
  main();
} catch (error) {
  console.error(error.message);
  process.exitCode = 2;
}
