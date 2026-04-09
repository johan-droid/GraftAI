const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname);
const isWindows = process.platform === "win32";

function check(name, fn) {
  try {
    fn();
    console.log(`✓ ${name}`);
    return true;
  } catch (error) {
    console.log(`✗ ${name}`);
    console.log(`  Error: ${error.message}`);
    return false;
  }
}

function checkCommand(cmd) {
  try {
    execSync(`${isWindows ? "where" : "which"} ${cmd}`, { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function checkFile(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`File not found: ${filePath}`);
  }
}

function checkDirectory(dirPath) {
  if (!fs.existsSync(dirPath)) {
    throw new Error(`Directory not found: ${dirPath}`);
  }
}

console.log("\n========================================");
console.log("  GraftAI Development Setup Checker");
console.log("========================================\n");

let allGood = true;

console.log("System Requirements:");
allGood &= check("Node.js installed", () => {
  if (!checkCommand("node")) throw new Error("Node.js not found in PATH");
});

allGood &= check("Python installed", () => {
  if (!checkCommand("python") && !checkCommand("python3")) {
    throw new Error("Python not found in PATH");
  }
});

allGood &= check("npm installed", () => {
  if (!checkCommand("npm")) throw new Error("npm not found in PATH");
});

console.log("\nProject Structure:");
allGood &= check("Backend directory exists", () => {
  checkDirectory(path.join(repoRoot, "backend"));
});

allGood &= check("Frontend directory exists", () => {
  checkDirectory(path.join(repoRoot, "frontend"));
});

allGood &= check("Scripts directory exists", () => {
  checkDirectory(path.join(repoRoot, "scripts"));
});

console.log("\nDependencies:");
allGood &= check("Backend requirements.txt exists", () => {
  checkFile(path.join(repoRoot, "backend", "requirements.txt"));
});

allGood &= check("Frontend package.json exists", () => {
  checkFile(path.join(repoRoot, "frontend", "package.json"));
});

console.log("\nVirtual Environment:");
const venvPath = path.join(repoRoot, ".venv");
const pythonExe = path.join(venvPath, isWindows ? "Scripts\\python.exe" : "bin/python");
allGood &= check("Virtual environment exists", () => {
  if (!fs.existsSync(venvPath)) {
    throw new Error("Virtual environment not found. Run: python -m venv .venv");
  }
});

console.log("\nDevelopment Scripts:");
allGood &= check("dev-concurrent.js exists", () => {
  checkFile(path.join(repoRoot, "scripts", "dev-concurrent.js"));
});

allGood &= check("package.json configured", () => {
  const pkg = JSON.parse(fs.readFileSync(path.join(repoRoot, "package.json"), "utf8"));
  if (!pkg.scripts.dev || !pkg.scripts.dev.includes("dev-concurrent")) {
    throw new Error("package.json not configured for concurrent development");
  }
});

console.log("\nConfiguration:");
allGood &= check("Backend .env exists", () => {
  checkFile(path.join(repoRoot, "backend", ".env"));
});

console.log("\n========================================");
if (allGood) {
  console.log("✓ All checks passed! Ready to start development.");
  console.log("\nRun: npm run dev");
} else {
  console.log("✗ Some checks failed. Please fix the issues above.");
  console.log("\nSetup instructions:");
  console.log("1. Create virtual environment: python -m venv .venv");
  console.log("2. Activate it:");
  console.log(isWindows ? "   .venv\\Scripts\\activate" : "   source .venv/bin/activate");
  console.log("3. Install backend deps: pip install -r backend/requirements.txt");
  console.log("4. Install frontend deps: cd frontend && npm install");
  console.log("5. Create backend/.env with required variables");
}
console.log("========================================\n");

process.exit(allGood ? 0 : 1);
