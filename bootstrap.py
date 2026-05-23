# bootstrap.py
"""Nirnaya automated cross-platform workspace bootstrap utility.

Sets up a local virtual environment, upgrades local packaging tools, 
installs dependencies, link-mounts the local codebase, and initializes Git.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(args: list[str], description: str) -> None:
    """Executes a sub-process command cleanly, failing loudly if steps collapse."""
    print(f"{description}...")
    try:
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Failed during: {description}")
        print(e.stderr.decode().strip())
        sys.exit(1)


def main():
    root_dir = Path(__file__).parent.resolve()
    os.chdir(root_dir)

    # 1. Enforce Git workspace instantiation boundaries
    if not (root_dir / ".git").exists():
        run_command(["git", "init"], "Initializing Git repository repository container")

    # 2. Derive active operating system pathing variations
    venv_dir = root_dir / ".venv"
    if sys.platform == "win32":
        pip_exe = str(venv_dir / "Scripts" / "pip.exe")
        python_exe = str(venv_dir / "Scripts" / "python.exe")
    else:
        pip_exe = str(venv_dir / "bin" / "pip")
        python_exe = str(venv_dir / "bin" / "python")

    # 3. Create virtual environment if missing
    if not venv_dir.exists():
        run_command([sys.executable, "-m", "venv", ".venv"], "Generating isolated virtual environment (.venv)")

    # 4. Handle tool upgrades and project setup
    run_command([python_exe, "-m", "pip", "install", "--upgrade", "pip"], "Upgrading internal virtual pip engine")
    
    if (root_dir / "requirements.txt").exists():
        run_command([pip_exe, "install", "-r", "requirements.txt"], "Deploying required packaging dependencies")
        
    run_command([pip_exe, "install", "-e", "."], "Link-mounting local Nirnaya package entrypoints")

    print("\n NIRNAYA BOOTSTRAP SUCCEEDED PERFECTLY!")
    print("──────────────────────────────────────────────────────────")
    print("To enter your environment and run tests, execute:")
    if sys.platform == "win32":
        print("  .\\.venv\\Scripts\\Activate.ps1   (PowerShell)")
        print("  .\\.venv\\Scripts\\activate.bat   (Command Prompt)")
    else:
        print("  source .venv/bin/activate      (Bash/Zsh)")
    print("  pytest")
    print("──────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()