#!/usr/bin/env node
/**
 * scripts/download_model.js
 * Downloads offline model weights for the pipeline service.
 */

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT_DIR = path.resolve(__dirname, "..");
const PIPELINE_DIR = path.join(ROOT_DIR, "pipeline");

function resolvePython() {
  const isWin = process.platform === "win32";
  const venvPy = isWin
    ? path.join(PIPELINE_DIR, ".venv", "Scripts", "python.exe")
    : path.join(PIPELINE_DIR, ".venv", "bin", "python");

  if (fs.existsSync(venvPy)) {
    return venvPy;
  }
  return process.platform === "win32" ? "python" : "python3";
}

function main() {
  const py = resolvePython();
  const scriptPath = path.join(PIPELINE_DIR, "src", "download_model.py");

  console.log("============================================================");
  console.log("  EduFlash AI - Download Offline Model Weights");
  console.log("============================================================");
  console.log(`Using Python: ${py}`);
  console.log(`Target: Qwen/Qwen2.5-0.5B-Instruct -> pipeline/models_weights/qwen2.5-0.5b\n`);

  const proc = spawnSync(py, [scriptPath], {
    cwd: PIPELINE_DIR,
    stdio: "inherit",
    shell: process.platform === "win32",
  });

  if (proc.status !== 0) {
    console.error(`[-] Download failed with code ${proc.status}`);
    process.exit(proc.status || 1);
  }
  console.log("\n[+] Model weights ready!");
}

main();

