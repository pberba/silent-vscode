#!/usr/bin/env python3
import argparse
import json
import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

IDE_DIRS = {
    "vscode": Path.home() / ".vscode" / "extensions",
    "cursor": Path.home() / ".cursor" / "extensions",
    "antigravity-ide": Path.home() / ".antigravity-ide" / "extensions",
}


def extensions_dir(ide: str = None, raw_dir: str = None) -> Path:
    if raw_dir and ide:
        logging.warning("--dir overrides --ide; using %s", raw_dir)
        return Path(raw_dir).expanduser().resolve()
    if raw_dir:
        return Path(raw_dir).expanduser().resolve()
    return IDE_DIRS[ide or "vscode"].resolve()


def uri_path_to_fs(raw: str) -> Path:
    if len(raw) >= 3 and raw[0] == "/" and raw[2] == ":":
        raw = raw[1:]
    return Path(raw)


def entry_dir(root: Path, entry: dict) -> Path:
    rel = entry.get("relativeLocation")
    if rel:
        return (root / rel).resolve()
    loc = entry.get("location") or {}
    raw = loc.get("fsPath") or loc.get("path")
    if raw:
        return uri_path_to_fs(raw).resolve()
    return None


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--target", required=True, help="Installed extension id to uninstall")
    p.add_argument(
        "--ide",
        choices=sorted(IDE_DIRS),
        help="Shorthand for a common extensions dir (vscode, cursor, antigravity-ide)",
    )
    p.add_argument(
        "--dir",
        help="Extensions dir (use for IDEs other than vscode/cursor)",
    )
    args = p.parse_args()

    root = extensions_dir(args.ide, args.dir)
    js = root / "extensions.json"
    target = args.target
    dirs: list[Path] = []

    entries = []
    if js.exists() and js.stat().st_size:
        entries = json.loads(js.read_text(encoding="utf-8"))
    kept = []
    for entry in entries:
        if entry.get("identifier", {}).get("id") != target:
            kept.append(entry)
            continue
        dest = entry_dir(root, entry)
        if dest:
            dirs.append(dest)
    if js.exists():
        js.write_text(json.dumps(kept, separators=(",", ":")), encoding="utf-8")
        logging.info("Removed %s from %s", target, js)

    fallback = root / target
    if fallback.is_dir() and fallback not in dirs:
        dirs.append(fallback)

    if not dirs:
        raise FileNotFoundError(f"extension not found: {target}")

    for dest in dirs:
        if dest.is_dir():
            shutil.rmtree(dest)
            logging.info("Deleted %s", dest)
        else:
            logging.warning("Directory already missing: %s", dest)


if __name__ == "__main__":
    main()