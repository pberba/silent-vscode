#!/usr/bin/env python3
import argparse
import json
import logging
import shutil
import time
from pathlib import Path
from urllib.parse import urlparse

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


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--extension-id",
        required=True,
        help="Local source folder next to this script to install",
    )
    p.add_argument(
        "--ide",
        choices=sorted(IDE_DIRS),
        help="Shorthand for a common extensions dir (vscode, cursor, antigravity-ide)",
    )
    p.add_argument(
        "--dir",
        help="Extensions dir (use for IDEs other than vscode/cursor)",
    )
    p.add_argument(
        "--builtin",
        action="store_true",
        help="Install as a builtin extension (metadata.isBuiltin)",
    )
    args = p.parse_args()

    source = Path(__file__).resolve().parent / args.extension_id
    if not source.is_dir():
        raise FileNotFoundError(source)

    pkg = json.loads((source / "package.json").read_text(encoding="utf-8"))
    missing = [k for k in ("publisher", "name", "version") if not pkg.get(k)]
    if missing:
        raise ValueError(f"{source / 'package.json'} missing {', '.join(missing)}")

    publisher = pkg["publisher"]
    name = pkg["name"]
    version = pkg["version"]
    identifier_id = f"{publisher}.{name}"
    relative_location = f"{publisher}.{name}-{version}"

    dest_root = extensions_dir(args.ide, args.dir)
    dest = dest_root / relative_location

    uri = dest.as_uri()
    metadata = {
        "installedTimestamp": 1664845552279,
        "isBuiltin": args.builtin,
        "source": "gallery"
    }
    entry = {
        "identifier": {"id": identifier_id},
        "version": version,
        "location": {
            "$mid": 1,
            "fsPath": str(dest),
            "external": uri,
            "path": urlparse(uri).path,
            "scheme": "file",
        },
        "relativeLocation": relative_location,
        "metadata": metadata,
    }

    js = dest_root / "extensions.json"
    entries = []
    if js.exists() and js.stat().st_size:
        entries = json.loads(js.read_text(encoding="utf-8"))
    entries = [e for e in entries if e.get("identifier", {}).get("id") != identifier_id]
    entries.append(entry)
    with open(js, "w") as f:
        f.write(json.dumps(entries))

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns("package.json"))
    pkg.pop("__metadata", None)
    pkg["__metadata"] = metadata
    (dest / "package.json").write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")



if __name__ == "__main__":
    main()
