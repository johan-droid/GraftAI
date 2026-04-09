const { spawn } = require("child_process");
const http = require("http");
const path = require("path");
const os = require("os");

const repoRoot = path.resolve(__dirname, "..");
const isWindows = process.platform === "win32";
const venvBin = path.join(repoRoot, ".venv", isWindows ? "Scripts" : "bin");
const pythonCmd = path.join(venvBin, isWindows ? "python.exe" : "python");
const npmCmd = isWindows ? "npm.cmd" : "npm";

const backendPort = 8000;
const backendHost = "127.0.0.1";
const frontendPort = 3000;

let processes = [];

function log(service, message) {
  const timestamp = new Date().toLocaleTimeString();
  console.log(`[${timestamp}] [${service}] ${message}`);
}

function waitForHealthCheck(host, port, service, timeoutMs = 60000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const options = {
        hostname: host,
        port,
        path: "/health",
        method: "GET",
        timeout: 2000,
      };

      const req = http.request(options, (res) => {
        if (res.statusCode === 200) {
          res.resume();
          log(service, `✓ Service ready at http://${host}:${port}`);
          resolve();
        } else {
          res.resume();
          retry();
        }
      });

      req.on("error", retry);
      req.on("timeout", () => {
        req.destroy();
        retry();
      });
      req.end();

      function retry() {
        if (Date.now() - start >= timeoutMs) {
          reject(new Error(`Timeout waiting for ${service} at http://${host}:${port}/health`));
        } else {
          setTimeout(check, 500);
        }
      }
    };
    check();
  });
}

function spawnProcess(command, args, cwd, service) {
  log(service, `Starting with: ${command} ${args.join(" ")}`);
  
  const proc = spawn(command, args, {
    cwd,
    shell: isWindows,
    stdio: "inherit",
    env: { ...process.env },
  });

  proc.on("error", (error) => {
    log(service, `✗ Error: ${error.message}`);
    cleanup();
  });

  proc.on("exit", (code, signal) => {
    if (signal) {
      log(service, `Terminated by signal: ${signal}`);
    } else if (code !== 0) {
      log(service, `Exited with code: ${code}`);
    }
  });

  processes.push(proc);
  return proc;
}

function cleanup() {
  log("MAIN", "Shutting down all services...");
  processes.forEach((proc) => {
    if (proc && !proc.killed) {
      proc.kill();
    }
  });
  process.exit(0);
}

async function main() {
  log("MAIN", "GraftAI Development Server");
  log("MAIN", `Platform: ${isWindows ? "Windows" : "Unix-like"}`);
  log("MAIN", `Python: ${pythonCmd}`);
  log("MAIN", `NPM: ${npmCmd}`);

  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);

  try {
    // Start Backend API
    log("MAIN", "Starting Backend API...");
    const backendArgs = ["-m", "uvicorn", "api.main:app", "--reload", "--host", backendHost, "--port", backendPort];
    spawnProcess(pythonCmd, backendArgs, path.join(repoRoot, "backend"), "BACKEND");

    // Wait for backend to be ready
    try {
      await waitForHealthCheck(backendHost, backendPort, "BACKEND", 60000);
    } catch (error) {
      log("MAIN", `✗ Backend failed to start: ${error.message}`);
      cleanup();
      return;
    }

    // Start Frontend
    log("MAIN", "Starting Frontend...");
    const frontendArgs = ["run", "dev"];
    spawnProcess(npmCmd, frontendArgs, path.join(repoRoot, "frontend"), "FRONTEND");

    log("MAIN", "✓ All services started successfully!");
    log("MAIN", `Backend: http://${backendHost}:${backendPort}`);
    log("MAIN", `Frontend: http://localhost:${frontendPort}`);
    log("MAIN", "Press Ctrl+C to stop all services");

  } catch (error) {
    log("MAIN", `✗ Fatal error: ${error.message}`);
    cleanup();
  }
}

main();
