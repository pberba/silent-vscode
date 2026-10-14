# silent-vscode

Silently installing extensions on VSCodium-based IDEs such as VSCode, Cursor, and Antigravity for persistence. 

https://pberba.github.io/security/2026/10/14/silent-vscode/

## Scope and intent

This is a **research POC for a blog post**, meant to be run against your own
local IDE install to observe the behavior. The sample payloads here are benign and to be used for testing.

This has only been tested in VSCode, Cursor and Antigravity on macOS.

## Contents

| File | Purpose |
|---|---|
| `silent_vscode.py` | Installs `sample-publisher.silent-extension` directly into the IDE's extensions directory by writing an `extensions.json` entry and copying the contents to the extensions directory. |
| `uninstall_extension.py` | Uninstalls the target extension ID |
| `extension_hollowing.py` | Wraps an **existing, already-installed** extension: swaps its `main` entry for `inject.js`, |


## Usage

All scripts default to `--ide vscode` (`~/.vscode/extensions`). Use
`--ide cursor`, `--ide antigravity-ide`, or `--dir <path>` for other
IDEs/locations.

### 1. Silent install

```bash
python3 silent_vscode.py --extension-id sample-publisher.silent-extension
python3 silent_vscode.py --ide cursor --extension-id sample-publisher.silent-extension --builtin
```

Adds `sample-publisher.silent-extension` (or whatever extension is in the current directory) to the IDE by copying the contents to `~/.vscode/extensions/`

Add `--builtin` to mark it `isBuiltin: true` in the metadata, hiding it from regular extension lists.

To remove it again:

```bash
python3 uninstall_extension.py --target sample-publisher.silent-extension
```

### 2. Extension hollowing

Pick an already-installed extension's identifier (publisher.name, as shown in `extensions.json` or the Extensions sidebar), then:

```bash
python3 extension_hollowing.py --inject inject.js --target <publisher.name>
```

This:
- Reads the extension's current `main` entry and saves it to a
  `.inject-original` marker file inside the extension's folder.
- Writes `inject.js` (with `__ORIGINAL_MAIN__` substituted in) as the new
  main file.
- Updates `package.json["main"]` to point at it.

This requires a reload of the IDE to work. Check `/tmp/extension-hollowing-vscode.out` to see if it has worked.

We don't have an unhollow script for this.  To restore the extension, you'll want to reset `main` in its `package.json`
back to the value saved in `.inject-original` and delete the marker/wrapper file (there's no dedicated "unhollow" script here — `uninstall_extension.py` only handles the silent-install case).
