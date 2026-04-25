const { spawn, execSync } = require("child_process");
const http = require("http");
const net = require("net");
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
let isShuttingDown = false;

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

function isPortAvailable(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.unref();
    server.once("error", () => resolve(false));
    server.once("listening", () => {
      server.close(() => resolve(true));
    });
    server.listen(port);
  });
}

async function findAvailablePort(startPort, maxPort = startPort + 50) {
  for (let port = startPort; port <= maxPort; port += 1) {
    if (await isPortAvailable(port)) {
      return port;
    }
  }
  throw new Error(`No available port found between ${startPort} and ${maxPort}`);
}

function waitForPort(host, port, timeoutMs = 60000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const socket = net.createConnection({ host, port }, () => {
        socket.destroy();
        resolve();
      });

      socket.on("error", () => {
        socket.destroy();
        if (Date.now() - start >= timeoutMs) {
          reject(new Error(`Timeout waiting for port ${port} on ${host}`));
        } else {
          setTimeout(check, 500);
        }
      });
    };
    check();
  });
}

function spawnProcess(command, args, cwd, service) {
  log(service, `Starting with: ${command} ${args.join(" ")}`);
  const useShell = isWindows && command.toLowerCase().endsWith(".cmd");
  
  const proc = spawn(command, args, {
    cwd,
    shell: useShell,
    stdio: "inherit",
    env: { ...process.env },
    windowsHide: true,
  });

  proc.on("error", (error) => {
    log(service, `✗ Error: ${error.message}`);
    cleanup(`${service} spawn error`);
  });

  proc.on("exit", (code, signal) => {
    if (isShuttingDown) {
      return;
    }

    if (signal) {
      log(service, `Terminated by signal: ${signal}`);
      cleanup(`${service} terminated by signal ${signal}`);
    } else if (code !== 0) {
      log(service, `Exited with code: ${code}`);
      cleanup(`${service} exited with code ${code}`);
    }
  });

  processes.push(proc);
  return proc;
}

function killProcessTree(proc) {
  if (!proc || proc.killed) return;

  try {
    if (isWindows) {
      execSync(`taskkill /PID ${proc.pid} /T /F`, { stdio: "ignore" });
    } else {
      proc.kill("SIGTERM");
    }
  } catch {
    // Best-effort shutdown; ignore cleanup errors.
  }
}

function cleanup(reason = "manual shutdown") {
  if (isShuttingDown) return;
  isShuttingDown = true;

  log("MAIN", `Shutting down all services... (${reason})`);
  processes.forEach((proc) => {
    killProcessTree(proc);
  });
  process.exit(0);
}

async function main() {
  log("MAIN", "GraftAI Development Server");
  log("MAIN", `Platform: ${isWindows ? "Windows" : "Unix-like"}`);
  log("MAIN", `Python: ${pythonCmd}`);
  log("MAIN", `NPM: ${npmCmd}`);

  process.on("SIGINT", () => cleanup("SIGINT"));
  process.on("SIGTERM", () => cleanup("SIGTERM"));
  process.on("uncaughtException", (error) => {
    log("MAIN", `✗ Uncaught exception: ${error.message}`);
    cleanup("uncaughtException");
  });
  process.on("unhandledRejection", (error) => {
    const msg = error instanceof Error ? error.message : String(error);
    log("MAIN", `✗ Unhandled rejection: ${msg}`);
    cleanup("unhandledRejection");
  });

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
      cleanup("backend health check failed");
      return;
    }

    // Start Frontend
    const selectedFrontendPort = await findAvailablePort(frontendPort, frontendPort + 50);
    if (selectedFrontendPort !== frontendPort) {
      log("MAIN", `Port ${frontendPort} is busy; using frontend port ${selectedFrontendPort} instead.`);
    }

    log("MAIN", "Starting Frontend...");
    const frontendArgs = ["run", "dev", "--", "--port", `${selectedFrontendPort}`];
    spawnProcess(npmCmd, frontendArgs, path.join(repoRoot, "frontend"), "FRONTEND");

    try {
      await waitForPort("127.0.0.1", selectedFrontendPort, 60000);
    } catch (error) {
      log("MAIN", `✗ Frontend failed to start: ${error.message}`);
      cleanup("frontend health check failed");
      return;
    }

    log("MAIN", "✓ All services started successfully!");
    log("MAIN", `Backend: http://${backendHost}:${backendPort}`);
    log("MAIN", `Frontend: http://localhost:${selectedFrontendPort}`);
    log("MAIN", "Press Ctrl+C to stop all services");

  } catch (error) {
    log("MAIN", `✗ Fatal error: ${error.message}`);
    cleanup("fatal error");
  }
}

main();
  