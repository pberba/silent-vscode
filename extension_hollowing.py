#!/usr/bin/env python3
import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

MARKER = ".inject-original"
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


def resolve_template(raw: str) -> Path:
    p = Path(raw).expanduser()
    if p.is_file():
        return p.resolve()
    alt = Path(__file__).resolve().parent / raw
    if alt.is_file():
        return alt.resolve()
    raise FileNotFoundError(raw)


def uri_path_to_fs(raw: str) -> Path:
    if len(raw) >= 3 and raw[0] == "/" and raw[2] == ":":
        raw = raw[1:]
    return Path(raw)


def find_target(extensions_dir: Path, target_id: str) -> Path:
    js = extensions_dir / "extensions.json"
    entries = json.loads(js.read_text(encoding="utf-8"))
    for entry in entries:
        if entry.get("identifier", {}).get("id") != target_id:
            continue
        rel = entry.get("relativeLocation")
        if rel:
            return (extensions_dir / rel).resolve()
        loc = entry.get("location") or {}
        raw = loc.get("fsPath") or loc.get("path")
        if raw:
            return uri_path_to_fs(raw).resolve()
    raise FileNotFoundError(f"extension not in extensions.json: {target_id}")


def original_main(pkg: dict) -> str:
    main = (pkg.get("main") or "./extension.js").replace("\\", "/")
    if not main.startswith("."):
        main = "./" + main
    if main.endswith('.js'):
        main = main[:-3]
    return main


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--inject", required=True, help="Inject template, e.g. inject.js")
    p.add_argument("--target", required=True, help="Installed extension id to wrap")
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

    template = resolve_template(args.inject)
    dest_root = extensions_dir(args.ide, args.dir)
    dest = find_target(dest_root, args.target)
    pkg_path = dest / "package.json"
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    marker = dest / MARKER
    wrapper = template.name

    if marker.exists():
        main = marker.read_text(encoding="utf-8").strip()
    else:
        main = original_main(pkg)
        if Path(main).name == wrapper:
            raise RuntimeError(f"{args.target} is already injected with no {MARKER}")
        marker.write_text(main, encoding="utf-8")

    body = template.read_text(encoding="utf-8").replace("__ORIGINAL_MAIN__", main)
    (dest / wrapper).write_text(body, encoding="utf-8")
    pkg["main"] = "./" + wrapper
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
    logging.info("Injected %s", args.target)
    logging.info("  dir:  %s", dest)
    logging.info("  orig: %s", main)
    logging.info("  main: ./%s", wrapper)


if __name__ == "__main__":
    main()
