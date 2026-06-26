#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const engine = path.join(root, "src", "context_pack", "bundled", "context_pack.py");
const argv = process.argv.slice(2);
const candidates = process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python"];
const versionCheck = "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)";

function argsFor(command, scriptArgs) {
  return command === "py" ? ["-3", ...scriptArgs] : scriptArgs;
}

for (const command of candidates) {
  const probe = spawnSync(command, argsFor(command, ["-c", versionCheck]), { stdio: "ignore" });
  if (probe.error && probe.error.code === "ENOENT") {
    continue;
  }
  if (probe.error) {
    console.error(`context-pack failed to inspect ${command}: ${probe.error.message}`);
    process.exit(1);
  }
  if (probe.status !== 0) {
    continue;
  }

  const result = spawnSync(command, argsFor(command, [engine, ...argv]), { stdio: "inherit" });
  if (result.error) {
    console.error(`context-pack failed to run ${command}: ${result.error.message}`);
    process.exit(1);
  }
  if (result.signal) {
    process.kill(process.pid, result.signal);
  }
  process.exit(result.status === null ? 1 : result.status);
}

console.error("context-pack requires Python 3.11+ on PATH. Install Python, then rerun this command.");
process.exit(127);
