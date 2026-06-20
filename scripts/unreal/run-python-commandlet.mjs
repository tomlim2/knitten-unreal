#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const REPO_ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..", "..");
const DEFAULT_ENGINE = "/Users/Shared/Epic Games/UE_5.8";
const DEFAULT_PROJECT = "/Users/younsoolim/Documents/UE5d8/Advent/Advent.uproject";

function usage() {
  return `Usage:
  run-python-commandlet.mjs --script=<path> [--engine=<path>] [--project=<path>] [--ue-cmd=<path>] [--editor-arg=<arg>] [--show-command]

Examples:
  node scripts/unreal/run-python-commandlet.mjs --script=scripts/unreal/probe-python.py
  KNITTEN_UNREAL_LEVEL=/Game/Levels/Lvl_MCPPCG node scripts/unreal/run-python-commandlet.mjs --script=scripts/unreal/list-level-actors.py
  node scripts/unreal/run-python-commandlet.mjs --script=scripts/unreal/build-box-city.py --editor-arg=-NoLogTimes`;
}

function parseArgs(argv) {
  const options = {
    engine: process.env.KNITTEN_UNREAL_ENGINE || DEFAULT_ENGINE,
    project: process.env.KNITTEN_UNREAL_PROJECT || DEFAULT_PROJECT,
    script: null,
    ueCmd: null,
    editorArgs: [],
    showCommand: false,
  };

  for (const arg of argv) {
    if (arg.startsWith("--engine=")) {
      options.engine = arg.slice("--engine=".length);
    } else if (arg.startsWith("--project=")) {
      options.project = arg.slice("--project=".length);
    } else if (arg.startsWith("--script=")) {
      options.script = arg.slice("--script=".length);
    } else if (arg.startsWith("--ue-cmd=")) {
      options.ueCmd = arg.slice("--ue-cmd=".length);
    } else if (arg.startsWith("--editor-arg=")) {
      options.editorArgs.push(arg.slice("--editor-arg=".length));
    } else if (arg === "--show-command") {
      options.showCommand = true;
    } else if (arg === "-h" || arg === "--help") {
      process.stdout.write(`${usage()}\n`);
      process.exit(0);
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  if (!options.script) {
    throw new Error("--script is required");
  }

  options.engine = path.resolve(options.engine);
  options.project = path.resolve(options.project);
  options.script = path.resolve(REPO_ROOT, options.script);
  options.ueCmd = options.ueCmd
    ? path.resolve(options.ueCmd)
    : path.join(options.engine, "Engine", "Binaries", "Mac", "UnrealEditor-Cmd");

  return options;
}

function assertFile(label, filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`${label} does not exist: ${filePath}`);
  }
}

function shellQuote(value) {
  return `'${String(value).replace(/'/g, "'\\''")}'`;
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  assertFile("UnrealEditor-Cmd", options.ueCmd);
  assertFile("project", options.project);
  assertFile("script", options.script);

  const args = [
    options.project,
    "-run=PythonScript",
    `-Script=${options.script}`,
    "-unattended",
    "-nop4",
    "-nosplash",
    "-NoSound",
    "-NullRHI",
    "-stdout",
    "-FullStdOutLogOutput",
    ...options.editorArgs,
  ];

  if (options.showCommand) {
    process.stderr.write(`${[options.ueCmd, ...args].map(shellQuote).join(" ")}\n`);
  }

  const result = spawnSync(options.ueCmd, args, {
    cwd: REPO_ROOT,
    env: process.env,
    stdio: "inherit",
  });

  if (result.error) {
    throw result.error;
  }
  process.exitCode = result.status ?? 1;
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
