#!/usr/bin/env node
/**
 * scripts/setup.js
 * Cross-platform environment setup runner for EduFlash AI monorepo.
 * Initializes Python virtual environments (.venv), installs dependencies,
 * and sets up local .env files for server, pipeline, and client.
 */

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT_DIR = path.resolve(__dirname, "..");
const SERVICES = ["server", "pipeline", "client"];

function detectSystemPython() {
  const candidates = process.platform === "win32"
    ? ["python", "python3", "py"]
    : ["python3", "python"];

  for (const cmd of candidates) {
    const result = spawnSync(cmd, ["--version"], { encoding: "utf-8" });
    if (!result.error && result.status === 0) {
      return cmd;
    }
  }
  return null;
}

function resolveVenvPython(serviceDir) {
  const isWin = process.platform === "win32";
  return isWin
    ? path.join(ROOT_DIR, serviceDir, ".venv", "Scripts", "python.exe")
    : path.join(ROOT_DIR, serviceDir, ".venv", "bin", "python");
}

function resolveVenvPip(serviceDir) {
  const isWin = process.platform === "win32";
  return isWin
    ? path.join(ROOT_DIR, serviceDir, ".venv", "Scripts", "pip.exe")
    : path.join(ROOT_DIR, serviceDir, ".venv", "bin", "pip");
}

function copyEnvIfMissing(dirPath) {
  const envPath = path.join(dirPath, ".env");
  const envExamplePath = path.join(dirPath, ".env.example");
  if (!fs.existsSync(envPath) && fs.existsSync(envExamplePath)) {
    fs.copyFileSync(envExamplePath, envPath);
    console.log(`  [+] Created .env from .env.example in ${path.relative(ROOT_DIR, dirPath) || "root"}`);
  }
}

function runCommand(command, args, cwd) {
  const proc = spawnSync(command, args, {
    cwd,
    stdio: "inherit",
    shell: process.platform === "win32",
  });
  if (proc.error) {
    throw proc.error;
  }
  if (proc.status !== 0) {
    throw new Error(`Command failed with exit code ${proc.status}: ${command} ${args.join(" ")}`);
  }
}

function main() {
  console.log("============================================================");
  console.log("  EduFlash AI - Automated Monorepo Setup");
  console.log("============================================================\n");

  const systemPython = detectSystemPython();
  if (!systemPython) {
    console.error("[-] ERROR: Python 3.10+ was not found on PATH.");
    console.error("    Please install Python (https://www.python.org/) and add it to PATH.");
    process.exit(1);
  }

  const verCheck = spawnSync(systemPython, ["--version"], { encoding: "utf-8" });
  console.log(`[*] System Python detected: ${verCheck.stdout.trim() || verCheck.stderr.trim()}`);

  // 1. Root .env setup
  copyEnvIfMissing(ROOT_DIR);

  // 2. Setup virtual environments and dependencies for each service
  for (const service of SERVICES) {
    const serviceDir = path.join(ROOT_DIR, service);
    const reqFile = path.join(serviceDir, "requirements.txt");
    const venvDir = path.join(serviceDir, ".venv");

    console.log(`\n------------------------------------------------------------`);
    console.log(`[*] Configuring [${service.toUpperCase()}] at ${path.relative(ROOT_DIR, serviceDir)}/`);
    console.log(`------------------------------------------------------------`);

    // Ensure .env exists
    copyEnvIfMissing(serviceDir);

    // Create venv if not existing
    if (!fs.existsSync(venvDir)) {
      console.log(`[*] Creating virtual environment (.venv)...`);
      runCommand(systemPython, ["-m", "venv", ".venv"], serviceDir);
      console.log(`[+] Virtual environment created.`);
    } else {
      console.log(`[=] Virtual environment (.venv) already exists.`);
    }

    // Install dependencies
    if (fs.existsSync(reqFile)) {
      const venvPip = resolveVenvPip(service);
      const pipCmd = fs.existsSync(venvPip) ? venvPip : systemPython;
      const installArgs = fs.existsSync(venvPip)
        ? ["install", "--no-warn-script-location", "-r", "requirements.txt"]
        : ["-m", "pip", "install", "--no-warn-script-location", "-r", "requirements.txt"];

      console.log(`[*] Installing dependencies from requirements.txt...`);
      runCommand(pipCmd, installArgs, serviceDir);
      console.log(`[+] Dependencies verified/installed for ${service}.`);
    }
  }

  console.log("\n============================================================");
  console.log("  Setup Complete!");
  console.log("============================================================");
  console.log("Next steps:");
  console.log("  1. Download AI offline weights: npm run download-model");
  console.log("  2. Start all 3 services:       npm start (or npm run dev)");
  console.log("============================================================\n");
}

main();
