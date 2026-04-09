const { spawn } = require("child_process");
const http = require("http");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const venvBin = process.platform === "win32" ? path.join(repoRoot, ".venv", "Scripts") : path.join(repoRoot, ".venv", "bin");
const pythonCmd = path.join(venvBin, process.platform === "win32" ? "python.exe" : "python");
const npmCmd = process.platform === "win32" ? "npm.cmd" : "npm";
const backendPort = 8000;
const backendHost = "127.0.0.1";

function waitForHealthCheck(host, port, timeoutMs = 60000) {
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
          reject(new Error(`Timed out waiting for http://${host}:${port}/health`));
        } else {
          setTimeout(check, 500);
        }
      }
    };
    check();
  });
}

function spawnProcess(command, args, options = {}) {
  const proc = spawn(command, args, {
    shell: true,
    stdio: "inherit",
    ...options,
  });

  proc.on("error", (error) => {
    console.error(`Process spawn failed: ${error.message}`);
    process.exit(1);
  });

  proc.on("exit", (code, signal) => {
    if (signal) {
      process.exit(1);
    }
    if (code !== 0) {
      process.exit(code);
    }
  });

  return proc;
}

const backendArgs = ["app.py"];
const workerArgs = ["backend/scripts/sync_worker.py"];
const frontendArgs = ["run", "dev"];

(async () => {
  console.log("Starting backend process...");
  const backend = spawnProcess(pythonCmd, backendArgs, { cwd: repoRoot });

  console.log("Starting sync worker process...");
  const worker = spawnProcess(pythonCmd, workerArgs, { cwd: repoRoot });

  console.log("Starting frontend process...");
  const frontend = spawnProcess(npmCmd, frontendArgs, { cwd: path.join(repoRoot, "frontend") });

  const cleanup = () => {
    if (!backend.killed) backend.kill();
    if (!worker.killed) worker.kill();
    if (!frontend.killed) frontend.kill();
    process.exit(0);
  };

  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);

  try {
    await waitForHealthCheck(backendHost, backendPort, 60000);
    console.log(`Backend ready at http://${backendHost}:${backendPort}`);
  } catch (error) {
    console.error(error);
    cleanup();
  }
})();
