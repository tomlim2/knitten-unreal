#!/usr/bin/env node

const DEFAULT_URL = "http://127.0.0.1:8000/mcp";

function usage() {
  return `Usage:
  mcp-toolsets.mjs [--url=<mcp-url>] [--describe=<toolset>] [--json]

Examples:
  node scripts/unreal/mcp-toolsets.mjs
  node scripts/unreal/mcp-toolsets.mjs --describe=EditorToolset
  node scripts/unreal/mcp-toolsets.mjs --url=http://127.0.0.1:8000/mcp --json`;
}

function parseArgs(argv) {
  const options = {
    url: DEFAULT_URL,
    describe: null,
    json: false,
  };

  for (const arg of argv) {
    if (arg.startsWith("--url=")) {
      options.url = arg.slice("--url=".length);
    } else if (arg.startsWith("--describe=")) {
      options.describe = arg.slice("--describe=".length);
    } else if (arg === "--json") {
      options.json = true;
    } else if (arg === "-h" || arg === "--help") {
      process.stdout.write(`${usage()}\n`);
      process.exit(0);
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  return options;
}

function parseMcpResponse(text) {
  const trimmed = text.trim();
  if (!trimmed) return null;

  const dataLines = trimmed
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice("data:".length).trim());

  const payload = dataLines.length ? dataLines.join("\n") : trimmed;
  try {
    return JSON.parse(payload);
  } catch {
    return { raw: payload };
  }
}

function textFromToolResult(result) {
  const parts = result?.content || [];
  return parts
    .filter((part) => part?.type === "text" && typeof part.text === "string")
    .map((part) => part.text)
    .join("\n");
}

async function postJsonRpc(url, payload, sessionId) {
  const headers = {
    accept: "application/json, text/event-stream",
    "content-type": "application/json",
  };
  if (sessionId) headers["mcp-session-id"] = sessionId;

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`MCP HTTP ${response.status}: ${text || response.statusText}`);
  }

  return {
    data: parseMcpResponse(text),
    sessionId: response.headers.get("mcp-session-id") || sessionId || null,
  };
}

let nextId = 1;

function request(method, params = undefined) {
  const payload = {
    jsonrpc: "2.0",
    id: nextId,
    method,
  };
  nextId += 1;
  if (params !== undefined) payload.params = params;
  return payload;
}

function notification(method, params = undefined) {
  const payload = {
    jsonrpc: "2.0",
    method,
  };
  if (params !== undefined) payload.params = params;
  return payload;
}

async function callTool(url, sessionId, name, args = {}) {
  const response = await postJsonRpc(url, request("tools/call", { name, arguments: args }), sessionId);
  if (response.data?.error) {
    throw new Error(`${name} failed: ${JSON.stringify(response.data.error)}`);
  }
  return response.data?.result;
}

function maybeParseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function printTextSummary(output) {
  process.stdout.write(`MCP URL: ${output.url}\n`);
  process.stdout.write(`Session: ${output.sessionId || "none"}\n\n`);

  const toolNames = (output.tools?.tools || []).map((tool) => tool.name).sort();
  process.stdout.write(`Tools (${toolNames.length}):\n`);
  for (const name of toolNames) process.stdout.write(`- ${name}\n`);

  if (output.toolsets !== undefined) {
    process.stdout.write("\nToolsets:\n");
    if (typeof output.toolsets === "string") {
      process.stdout.write(`${output.toolsets}\n`);
    } else {
      process.stdout.write(`${JSON.stringify(output.toolsets, null, 2)}\n`);
    }
  }

  if (output.described !== undefined) {
    process.stdout.write(`\nDescription for ${output.describe}:\n`);
    if (typeof output.described === "string") {
      process.stdout.write(`${output.described}\n`);
    } else {
      process.stdout.write(`${JSON.stringify(output.described, null, 2)}\n`);
    }
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));

  const initialized = await postJsonRpc(
    options.url,
    request("initialize", {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "knitten-unreal-mcp-toolsets", version: "0.1.0" },
    }),
  );

  if (!initialized.sessionId) {
    throw new Error("MCP initialize did not return an mcp-session-id header");
  }

  await postJsonRpc(options.url, notification("notifications/initialized"), initialized.sessionId);

  const toolsResponse = await postJsonRpc(options.url, request("tools/list"), initialized.sessionId);
  if (toolsResponse.data?.error) {
    throw new Error(`tools/list failed: ${JSON.stringify(toolsResponse.data.error)}`);
  }

  const output = {
    url: options.url,
    sessionId: initialized.sessionId,
    initialize: initialized.data?.result || null,
    tools: toolsResponse.data?.result || null,
  };

  const toolNames = new Set((output.tools?.tools || []).map((tool) => tool.name));
  if (toolNames.has("list_toolsets")) {
    const toolsets = await callTool(options.url, initialized.sessionId, "list_toolsets");
    output.toolsets = maybeParseJson(textFromToolResult(toolsets));
  }

  if (options.describe) {
    if (!toolNames.has("describe_toolset")) {
      throw new Error("server does not expose describe_toolset");
    }
    const described = await callTool(options.url, initialized.sessionId, "describe_toolset", {
      toolset_name: options.describe,
    });
    output.describe = options.describe;
    output.described = maybeParseJson(textFromToolResult(described));
  }

  if (options.json) {
    process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
  } else {
    printTextSummary(output);
  }
}

main().catch((error) => {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
});
