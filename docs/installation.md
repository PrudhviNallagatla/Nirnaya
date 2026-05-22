# Installation

Nirnaya is developed and tested with Python 3.11 in a project-local virtual environment.

## Local Development Setup

From the repository root:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -e .
```

The `requirements.txt` file contains the direct runtime and developer dependencies used by this repo:

- `libclang`
- `pydantic`
- `typing_extensions`
- `pytest`
- `mypy`
- `ruff`
- `hatchling`

## Validation

After installation, verify the environment with:

```powershell
python -m mypy nirnaya/
python -m pytest
```

## libclang Notes

Nirnaya uses `clang`/`libclang` for header parsing. On Windows, if libclang cannot find standard headers such as `stdint.h` or `string`, make sure you have a C++ toolchain installed or pass the correct include paths through your project build flags.

For this repository's isolated `.venv`, the parser has a small fallback for the bundled fixtures so the tests can run without a system toolchain, but real projects should still use their actual compiler include paths and `compile_commands.json`.
