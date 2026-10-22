const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const ROOT_DIR = path.resolve(__dirname, "..");

function resolvePython(serviceDir) {
  const isWin = process.platform === "win32";
  const venvPy = isWin
    ? path.join(ROOT_DIR, serviceDir, ".venv", "Scripts", "python.exe")
    : path.join(ROOT_DIR, serviceDir, ".venv", "bin", "python");

  if (fs.existsSync(venvPy)) {
    return venvPy;
  }

  // Check root .venv fallback
  const rootVenvPy = isWin
    ? path.join(ROOT_DIR, ".venv", "Scripts", "python.exe")
    : path.join(ROOT_DIR, ".venv", "bin", "python");

  if (fs.existsSync(rootVenvPy)) {
    return rootVenvPy;
  }

  return process.env.PYTHON || "python";
}

const SERVER_PORT = process.env.PORT || "3000";
const PIPELINE_PORT = process.env.PIPELINE_PORT || "8000";

const serverPython = resolvePython("server");
const pipelinePython = resolvePython("pipeline");

console.log("============================================================");
console.log("Starting Flashcard System (Server & AI Pipeline)...");
console.log(`Backend Server:     http://127.0.0.1:${SERVER_PORT} (Docs: /docs/)`);
console.log(`AI Pipeline:        http://127.0.0.1:${PIPELINE_PORT} (Docs: /docs)`);
console.log(`Server Python:      ${serverPython}`);
console.log(`Pipeline Python:    ${pipelinePython}`);
console.log("============================================================\n");

function streamOutput(stream, prefix, colorCode) {
  let buffer = "";
  stream.on("data", (chunk) => {
    buffer += chunk.toString();
    const lines = buffer.split("\n");
    buffer = lines.pop(); // keep partial line in buffer
    for (const line of lines) {
      if (line.trim().length > 0) {
        process.stdout.write(`\x1b[${colorCode}m[${prefix}]\x1b[0m ${line}\n`);
      }
    }
  });
  stream.on("end", () => {
    if (buffer.trim().length > 0) {
      process.stdout.write(`\x1b[${colorCode}m[${prefix}]\x1b[0m ${buffer}\n`);
    }
  });
}

const processes = [];

function runService(name, command, args, cwd, envExtra, colorCode) {
  const proc = spawn(command, args, {
    cwd,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: "1",
      ...envExtra,
    },
    stdio: ["inherit", "pipe", "pipe"],
  });

  processes.push(proc);

  streamOutput(proc.stdout, name, colorCode);
  streamOutput(proc.stderr, name, colorCode);

  proc.on("error", (err) => {
    console.error(`\x1b[${colorCode}m[${name}] ERROR:\x1b[0m`, err);
  });

  proc.on("close", (code) => {
    console.log(`\x1b[${colorCode}m[${name}]\x1b[0m Exited with code ${code}`);
  });

  return proc;
}

// 1. Start Server on port 3000
const serverProc = runService(
  `SERVER:${SERVER_PORT}`,
  serverPython,
  ["server/app/main.py"],
  ROOT_DIR,
  {
    PORT: SERVER_PORT,
    AI_PIPELINE_URL: `http://127.0.0.1:${PIPELINE_PORT}/api`,
  },
  "36" // Cyan
);

// 2. Start Pipeline on port 8000
const pipelineProc = runService(
  `PIPELINE:${PIPELINE_PORT}`,
  pipelinePython,
  ["pipeline/main.py"],
  ROOT_DIR,
  {
    PORT: PIPELINE_PORT,
  },
  "35" // Magenta
);

function killAll() {
  console.log("\n🛑 Stopping all services...");
  for (const proc of processes) {
    if (!proc || !proc.pid) continue;
    if (process.platform === "win32") {
      try {
        spawn("taskkill", ["/pid", proc.pid.toString(), "/t", "/f"], {
          stdio: "ignore",
        });
      } catch (_) {}
    } else {
      try {
        proc.kill("SIGINT");
      } catch (_) {}
    }
  }
  process.exit();
}

process.on("SIGINT", killAll);
process.on("SIGTERM", killAll);
