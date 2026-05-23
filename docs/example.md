# Nirnaya Local Testing 

This tutorial walks you through setting up a completely fresh C++ workspace, configuring automatic interface contract tracking, and safely simulating an ABI memory padding crash to see Nirnaya in action.

---

## Part 1: Automated Workspace Scaffolding

First, clone the repostory inside the folder you want to work in. 

```bash
git clone https://github.com/PrudhviNallagatla/Nirnaya.git
```

Open the terminal and execute the Python `bootstrap.py` inside the main repo `Nirnaya`. This configures the local `.venv` engine and packages automatically:

```bash
# Execute the single-file setup script
python /Nirnaya/bootstrap.py

```

Now, activate the newly generated local virtual environment layer:

```powershell
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# On macOS / Linux:
source .venv/bin/activate

```

---

## Part 2: Building a Clean Consumer Sandbox

To see how the engine handles a real-world developer workflow, let's step completely out of the project repository and create a brand-new, isolated folder layout representing a game engine component:

```bash
# Jump up one folder level
cd ..

# Create an isolated mock library workspace
mkdir HighSpeedPhysics
cd HighSpeedPhysics

# Initialize a clean Git history tracker (Nirnaya requires this!)
git init

```

Next, mount your freshly built local Nirnaya tool executable to this active sandbox environment session:

```bash
pip install -e ../Nirnaya

```

*(Verify by running `nirnaya version`. It should instantly return `Nirnaya Contract Engine — v0.1.0`.)*

---

## Part 3: The Stable Baseline ("The Promise")

Let's write a simple C++ data layout tracking object representing a physical object container inside space. Create a folder named `include/` and drop this clean code matrix into `include/rigid_body.h`:

```cpp
// include/rigid_body.h
#pragma once
#include <stdint.h>

namespace physics {

/**
 * @brief Represents a spatial mass block boundary in memory.
 */
struct RigidBody {
    uint8_t  layer_id;         // Bit Offset: 0
    // ⚠️ The compiler automatically injects 3 hidden bytes of padding here
    // to align the 32-bit integer below on a 4-byte boundary!
    int32_t  velocity_scalar;  // Bit Offset: 32 (Byte 4)
    double   gravitational_mass; // Bit Offset: 64 (Byte 8)
};

} // namespace physics

```

### Let Nirnaya Crawl and Lock the Interface Structure

Because we updated our tool to support automated zero-config workspace harvesting, you do not need to type out individual path arguments. Just type:

```bash
nirnaya init

```

### What Happens Behind the Scenes:

1. Nirnaya dynamically crawls your sandbox layout, discovers `include/rigid_body.h`, and auto-registers it inside `.nirnaya/config.toml`.
2. It calls `libclang` to map out the structure, registering that `velocity_scalar` naturally sits at bit offset `32` due to compiler byte spacing rules.
3. It saves an un-mutated, sorted "Golden Blueprint" snapshot mapping to your `.nirnaya/blueprints/` folder.

Commit these contract promises to version control just like a production engineering team:

```bash
git add .
git commit -m "chore: lock baseline public interface contract parameters"

```

Verify that your running contract check reads completely stable out of the gate:

```bash
nirnaya check

```

*(Returns: `✓ All public interface layout commitments verified perfectly.`)*

---

## Part 4: Introducing the Layout Chaos ("The Bug")

Now, let's simulate a silent, runtime-crashing mistake that standard unit tests cannot flag. Imagine a junior engineer steps in to add a boolean state configuration toggle, and carelessly drops it **right into the middle of your structure layout**.

Open `include/rigid_body.h` and inject `is_colliding` right between `layer_id` and `velocity_scalar`:

```cpp
// include/rigid_body.h
#pragma once
#include <stdint.h>

namespace physics {

struct RigidBody {
    uint8_t  layer_id;         // Bit Offset: 0
    bool     is_colliding;     // 💥 INJECTED BUG: Placed directly at Bit 8 (Byte 1)
    int32_t  velocity_scalar;  // ⚠️ CRASH DRIFT: Shifted out of its slot!
    double   gravitational_mass;
};

} // namespace physics

```

### Why This Crashes Pre-Compiled Binaries:

Before this change, third-party software compiled against your library expected to find the `velocity_scalar` integer data sitting exactly at **Byte 4** of the struct buffer payload. Because a new field was injected, the compiler shifts `velocity_scalar` to fit alignment boundaries. At runtime, older applications will read the wrong bytes, causing catastrophic segmentation faults or tracking drift.

---

## Part 5: Triggering the Nirnaya Verdict

Let's see Nirnaya stop this break before it ever reaches production. Execute the validation command in your console:

```bash
nirnaya check

```

### The Plain Text Output Diagnostic Readout:

The command line environment immediately rejects the execution path with **exit code 1**, outputting a clean layout report showing precisely what warped:

```
ABI CONTRACT VIOLATIONS DETECTED
Target Header: include/rigid_body.h

Severity      Category             Details

BREAKING      struct_layout        Entity: physics::RigidBody::velocity_scalar
                                   Field member 'velocity_scalar' memory offset 
                                   drifted from bit 32 to bit 64. Spills alignment 
                                   corruption to downstream consumers.
                                    └─ Baseline State: bit 32
                                    └─ Modified State: bit 64

BREAKING      struct_layout        Entity: physics::RigidBody::is_colliding
                                   Field member 'is_colliding' was newly injected 
                                   into the structural footprint of 'physics::RigidBody'.

```

---

## Part 6: Reviewing the Drift Interactively

To explore this structural failure visually inside a real-time tracking interface, launch your terminal user dashboard panel layout:

```bash
nirnaya show

```

### What to Do Inside the TUI:

1. The dashboard loads showing `rigid_body.h` automatically targeted with a bright red **`✗ FAIL`** alert badge on the left column sidebar layout block.
2. The right column instantly populates with beautifully framed **red border cards** breaking down your structural layout anomalies side-by-side.
3. Press **`[h]`** to verify your custom help system pops up smoothly over the screen background. Hit `Esc` to dim it out.
4. **Accepting the Evolved State:** If this ABI break was intentional (e.g., prepping for a major semver update release), hit **`[u]`** right inside the dashboard.
* The file snapshot re-compiles instantly, the historical transition log backups to the ledger, and the status badge dynamically switches to a green **`✓ PASS`** right before your eyes!


5. Press **`[q]`** to exit the application frame safely.
