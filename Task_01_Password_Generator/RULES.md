# Project Rules & Standards — Task 01: Password Generator

## 1. Coding Standards
- **PEP 8 Compliance**: All Python code must strictly conform to PEP 8 style guidelines (maximum line length 88–100 characters, 4 spaces for indentation, no trailing whitespace).
- **Type Annotations**: All public and private functions, methods, and dataclass fields must include explicit type hints (`str`, `int`, `bool`, `List[str]`, etc.).
- **Docstrings**:
  - Every module, class, method, and function must include comprehensive docstrings in Google/Sphinx format.
  - Docstrings must clearly specify purpose, arguments (`Args:`), return values (`Returns:`), and exceptions (`Raises:`).
- **No Dead Code or Placeholders**: Code must be production-ready. No `TODO`, `FIXME`, `pass` placeholders, or commented-out blocks in final deliverables.

---

## 2. Naming Conventions

| Entity | Convention | Example |
| :--- | :--- | :--- |
| **Modules / Files** | `snake_case.py` | `generator.py`, `test_generator.py` |
| **Classes** | `PascalCase` | `PasswordConfig`, `PasswordGenerator` |
| **Methods & Functions** | `snake_case` | `generate()`, `read_int()`, `password_strength()` |
| **Internal Helpers** | `_leading_underscore` | `_build_charset()`, `_guaranteed_chars()` |
| **Variables & Parameters** | `snake_case` | `password_chars`, `use_uppercase`, `count` |
| **Constants** | `UPPER_SNAKE_CASE` | `MIN_PASSWORD_LENGTH`, `MAX_PASSWORD_LENGTH`, `BANNER` |
| **Test Classes & Methods** | `Test<Target>`, `test_<scenario>` | `TestPasswordGenerator`, `test_contains_digits()` |

---

## 3. File Organization
- **Root Entry Point**: `main.py` is the designated CLI entry point. Top-level execution logic is guarded by `if __name__ == "__main__": main()`.
- **Core Package (`src/`)**: All domain models, core utilities, and algorithm implementations must reside in `src/` (e.g., `src/generator.py`), exposed via `src/__init__.py`.
- **Automated Tests (`tests/`)**: All unit test files must reside in `tests/` prefixed with `test_` (e.g., `tests/test_generator.py`).
- **Documentation**: All Markdown documentation files (`PRD.md`, `ARCHITECTURE.md`, `RULES.md`, `DESIGN.md`, `TASKS.md`, `MEMORY.md`, `README.md`) reside at the project root.

---

## 4. Error Handling & Validation Rules
- **Validation Prior to Execution**: Configuration must be validated before running any generation logic.
- **Config Level Validation**: `PasswordConfig.validate()` must not throw exceptions; it must return a `List[str]` containing descriptive validation error strings. If valid, it returns an empty list `[]`.
- **Engine Level Exception Enforcement**: Methods in `PasswordGenerator` (`generate()`, `generate_multiple()`) must raise `ValueError` with clear diagnostic messages when provided with invalid inputs or configurations.
- **Presentation Layer Containment**: The CLI layer (`main.py`) must catch expected exceptions (`ValueError`, `int` conversion errors) and display user-friendly warnings (`[!] Error: ...`), ensuring the interactive application never crashes or exposes raw stack traces to the end user.
- **Resilient Fallback**: If an invalid configuration is submitted during the interactive editor, the system must reject the change and retain the previous valid configuration.

---

## 5. Dependency Rules
- **Pure Standard Library**: No third-party packages or external libraries (`pip install`) are permitted.
- **Approved Standard Library Modules**:
  - `secrets`: CSPRNG for random token generation and unbiased indexing.
  - `string`: Standard character category definitions.
  - `dataclasses`: Configuration modeling.
  - `typing`: Type hinting constructs.
  - `sys` & `io`: Stream reconfiguration and runtime handling.
  - `unittest` & `os`: Testing framework and path setup.
- **Zero Lock-in**: Code must run out-of-the-box on a standard Python 3.10+ installation across Windows, Linux, and macOS.

---

## 6. Security Rules
- **CSPRNG Exclusivity**: Use `secrets.choice()` and `secrets.randbelow()`. Under no circumstances should `random.choice()`, `random.randint()`, or `random.seed()` be used for password or token creation.
- **No Dynamic Code Evaluation**: Never use `eval()`, `exec()`, or untrusted serialization formats.
- **Strict Input Validation**: Sanitize and validate all user inputs (bounds checking on lengths, numeric ranges on password counts, sanitization of yes/no prompts).
- **No Hardcoded Credentials**: No static, default, or example passwords stored in source code.
- **Ephemeral State**: Passwords exist in memory only as long as needed for terminal display and are never logged, cached, or written to temp files.

---

## 7. UI / UX Rules
- **ASCII-Safe Formatting**: The CLI interface must use standard 7-bit ASCII characters (`+`, `-`, `|`, `*`, `!`) for borders, menus, and banners to ensure compatibility with Windows Command Prompt (`cp1252`), PowerShell, and remote shells without character corruption.
- **Encoding Defense**: Call `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` defensively with fallback handling.
- **Intuitive Prompts**: All interactive prompts must show default options in brackets (e.g., `Password length (4-128) [16]: `, `Include uppercase (A-Z)? [Y/n]: `).
- **Clear Status Indicators**:
  - Success messages marked with `[OK]`.
  - Errors and warnings marked with `[!]`.
  - Password strength labeled with brackets (`[STRONG]`, `[MODERATE]`, `[WEAK]`).
- **Bounded Batch Limits**: Impose a maximum batch ceiling of 100 passwords per generation command with clear notice if exceeded.

---

## 8. Data Handling & Persistence Rules
- **Session-Based Configuration**: Configuration settings (`PasswordConfig`) are maintained in volatile session memory during the CLI run loop.
- **No Disk Persistence**: No configuration files (`.ini`, `.json`, `.yaml`) or local databases are written to disk, preventing stale or compromised policy states.
- **Clean Termination**: Upon selecting `Exit`, all memory structures are released without leaving lingering disk artifacts or lock files.
