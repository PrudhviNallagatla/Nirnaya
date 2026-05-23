# Nirnaya 

> **निर्णय** (Sanskrit), **నిర్ణయ** (Telugu) — *verdict, decision, determination*

A lightweight, git-native **C++ interface contract engine**. Nirnaya tracks the structural shape of your C++ headers and tells you — loudly and clearly — when something breaks the ABI contract, before it breaks your users.

No compiled binaries. No debug symbols. No XML config hell. Just source.

> Nirnaya is a personal project built to solve problems encountered while managing C++ libraries: catching silent, runtime-crashing ABI layout slips before they hit consumer binaries. I hope its helpful for as many people as possible.

---

## The Problem

You ship a C++ library. A developer adds a private member variable to a struct. All unit tests pass. CI is green. Your consumers' code silently breaks at runtime because the memory layout shifted. You find out three weeks later via a bug report.

Standard tooling won't catch this. `nirnaya` will.

---

## When to Use Nirnaya

- You maintain a C++ shared library and need to catch ABI breaks before release
- Your CI needs to fail when a header's memory layout changes unexpectedly  
- You want to commit interface contracts to git like source code
- You ship headers to consumers and cannot break binary compatibility

---

## How It Works

```
nirnaya init
└─► Automatically crawls your workspace for public C++ headers
└─► Extracts the structural AST via libclang (offsets, sizes, qualifiers)
└─► Saves a deterministic JSON "Golden Blueprint" to .nirnaya/

nirnaya check  (run locally or integrate into your PR pipelines)
└─► Re-parses the current headers
└─► Diffs layout shapes against your saved blueprint
└─► Passes silently or fails loudly with exact diagnostic readouts
```

---

## Quick Start

### Requirements
To execute the engine, ensure your local path context has **Python 3.11+** and the **LLVM/libclang** system binaries available:
* **Ubuntu/Debian:** `sudo apt install libclang-dev`
* **macOS:** `brew install llvm`
* **Windows:** Install the official pre-compiled LLVM binaries via the [LLVM Release Portal](https://github.com/llvm/llvm-project/releases).
  
```bash
# 1. Install directly from GitHub (PyPI registry will be added later)
pip install git+https://github.com/PrudhviNallagatla/Nirnaya.git@v0.1.0

# 2. Lock down your public headers automatically with zero-config scanning
cd your-cpp-project
nirnaya init

# ... someone introduces a structural layout change ...

# 3. Audit your interface contract stability bounds
nirnaya check
```
> Note: Installation via `pip install git+https://github.com/PrudhviNallagatla/Nirnaya.git@v0.1.0` is recommended as it installs the latest stable release.
> If you want to install the main branch, install via `pip install git+https://github.com/PrudhviNallagatla/Nirnaya.git`.
> PyPI registry (`pip install nirnaya`) will be added later and will be updated here when its updated.
---

## Sample Output

When a contract is clean:

```
✅ All public interface layout commitments verified perfectly.

```

When something drifts:

```
────────────────────────────────────────────────────────────────────────────────
ABI CONTRACT VIOLATIONS DETECTED
Target Header: include/interface.h

Severity      Category             Details
                                                                                
BREAKING      struct_layout        Entity: NetworkPacket
                                   Type memory footprint size shifted from 24 to 32 bytes.
                                   This breaks binary packaging structures.
                                     └─ Baseline State: 24 bytes
                                     └─ Modified State: 32 bytes
                                                                                
BREAKING      struct_layout        Entity: NetworkPacket::timestamp
                                   Field member 'timestamp' memory offset drifted from 
                                   bit 32 to bit 64. Spills alignment corruption to 
                                   downstream consumers.
                                     └─ Baseline State: bit 32
                                     └─ Modified State: bit 64

╭──────────────────────────────────────────────────────────╮
│ Audit Status: FAILED                                     │
│ Discovered 2 total anomalies. (2 breaking layout shifts) │
╰──────────────────────────────────────────────────────────╯
────────────────────────────────────────────────────────────────────────────────
```

---

## Commands

| Command | Description |
| --- | --- |
| `nirnaya init` | Auto-discover and capture baseline blueprints for all headers |
| `nirnaya init <header>` | Parse and track an isolated header file explicitly |
| `nirnaya check` | Verify all tracked headers against their stored baselines |
| `nirnaya update` | Acknowledge local modifications and advance the baseline blueprint |
| `nirnaya show` | Open the interactive TUI dashboard panels |
| `nirnaya version` | Display installation index and engine version details |

---

## TUI Shortcuts

Inside the `nirnaya show` visual dashboard, use:

* **`r`** : Recheck workspace contracts and catch active drifts live
* **`u`** : Accept current modifications and refresh the baseline snapshot in-place
* **`h`** : Toggle the floating interactive key command help overlay panel
* **`q`** or **`esc`** : Safely close panels or quit the dashboard session

---

## Context Awareness

Nirnaya reads your `compile_commands.json` (generated automatically by CMake, Meson, Bazel, or Xmake) to cleanly inherit your project's include paths, platform macros, and compiler flags with zero configuration.

```bash
# CMake users
cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ..

# Nirnaya will automatically find and parse build/compile_commands.json
nirnaya check
```

---

## The `.nirnaya/` Vault

Nirnaya stores its blueprints using flat cross-platform path slugifiers at the root of your project:

```
.nirnaya/
├── config.toml                     # Project tracking rules & target headers
├── blueprints/
│    ├── include__interface.h.json  # Portable absolute path blueprint slugs
│    └── include__network.h.json
└── history/
     └── include__interface.h/      # Timestamped rolling snapshot logs
          └── 20260522__203000.json

```

**Commit `.nirnaya/` to Git.** This is intentional — your interface blueprints become part of your repository's verifiable contract history, just like your source code.

---

## Running Locally from Source

To run the engine locally from source or tweak core components using our cross-platform automation scripts:

1. Clone the repository container:
```bash
git clone https://github.com/PrudhviNallagatla/Nirnaya.git
cd Nirnaya
```

2. Run the automated environment setup script (Initializes Git, configures a standalone local `.venv`, and handles editable link mounts safely):
```bash
python bootstrap.py
```

3. Activate the environment and execute the test pyramid layout rules:
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pytest

# macOS / Linux
source .venv/bin/activate
pytest
```

---

## License

Distributed entirely under the commercial-safe and patent-protective terms of the [Apache License, Version 2.0](https://www.google.com/search?q=LICENSE).
