/* eslint-disable @typescript-eslint/no-require-imports */
const { spawn } = require("child_process");
const net = require("net");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..");
const backendCommand = path.join(repoRoot, ".venv", "Scripts", "python.exe");
const backendArgs = ["app.py"];
const frontendCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const frontendArgs = ["run", "dev"];
const backendPort = 8000;
const backendHost = "127.0.0.1";

function waitForPort(host, port, timeoutMs = 30000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const socket = net.createConnection(port, host);
      socket.on("connect", () => {
        socket.destroy();
        resolve();
      });
      socket.on("error", () => {
        socket.destroy();
        if (Date.now() - start >= timeoutMs) {
          reject(new Error(`Timed out waiting for ${host}:${port}`));
        } else {
          setTimeout(check, 200);
        }
      });
    };
    check();
  });
}

function spawnProcess(command, args, options = {}) {
  const proc = spawn(command, args, {
    shell: false,
    stdio: "inherit",
    ...options,
  });

  proc.on("exit", (code, signal) => {
    if (signal) {
      process.exit(1);
    }
    if (code !== 0) {
      process.exit(code);
    }
  });

  proc.on("error", (error) => {
    console.error(`Process spawn failed: ${error.message}`);
    process.exit(1);
  });

  return proc;
}

(async () => {
  console.log("Starting backend process...");
  const backend = spawnProcess(backendCommand, backendArgs, { cwd: repoRoot });

  const shutdown = () => {
    if (!backend.killed) backend.kill();
    process.exit(0);
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  try {
    await waitForPort(backendHost, backendPort, 30000);
    console.log(`Backend ready at http://${backendHost}:${backendPort}`);
  } catch (error) {
    console.error(error);
    backend.kill();
    process.exit(1);
  }

  console.log("Starting frontend process...");
  const frontend = spawnProcess(frontendCommand, frontendArgs, {
    cwd: path.join(__dirname, ".."),
    shell: true,
  });

  frontend.on("error", (error) => {
    console.error(`Frontend spawn failed: ${error.message}`);
    backend.kill();
    process.exit(1);
  });
})();
