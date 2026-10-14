const { execSync } = require("child_process");
const fs = require("fs");
const https = require("https");
const os = require("os");
const path = require("path");

const TMP_DIR = process.platform === "win32" ? os.tmpdir() : "/tmp";
const OUT_FILE = path.join(TMP_DIR, "silent-vscode.out");
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

function activate() {
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

function deactivate() {}

module.exports = { activate, deactivate };
