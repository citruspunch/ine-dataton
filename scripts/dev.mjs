#!/usr/bin/env node
/**
 * Starts the Python engine and the Next.js app together, without a Makefile.
 * Ctrl+C stops both.
 */
import { spawn } from "node:child_process";

const children = [];
let stopping = false;

function start(name, command, args, options = {}) {
  const child = spawn(command, args, { stdio: "inherit", ...options });
  children.push(child);
  child.on("exit", (code) => {
    if (!stopping) {
      console.error(`[dev] ${name} exited with code ${code}`);
      stop(code ?? 1);
    }
  });
  return child;
}

function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  for (const child of children) {
    if (!child.killed) child.kill("SIGTERM");
  }
  setTimeout(() => process.exit(code), 300);
}

process.on("SIGINT", () => stop(0));
process.on("SIGTERM", () => stop(0));

console.log("[dev] engine  → http://127.0.0.1:8000");
start("engine", "uv", [
  "run",
  "uvicorn",
  "engine.api:app",
  "--host",
  "127.0.0.1",
  "--port",
  "8000",
]);

console.log("[dev] web     → http://127.0.0.1:3000");
start("web", "pnpm", ["--dir", "web", "dev"]);
