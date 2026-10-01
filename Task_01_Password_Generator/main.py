"""
Password Generator -- CLI Interface.

Provides a polished command-line experience for generating secure passwords.
Handles all user interaction, input validation, and display formatting.
"""

import sys
import io
from src.generator import (
    PasswordConfig,
    PasswordGenerator,
    password_strength,
    MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH,
    DEFAULT_PASSWORD_LENGTH,
)

# ---------------------------------------------------------------------------
# Force UTF-8 output on Windows so box-drawing chars work in modern terminals.
# Falls back gracefully if reconfiguration is not possible.
# ---------------------------------------------------------------------------
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, io.UnsupportedOperation):
    pass


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

BANNER = """
+------------------------------------------------------+
|         SECURE PASSWORD GENERATOR                    |
|         Cryptographically Strong Passwords           |
+------------------------------------------------------+
"""

MENU = """
+----------- MENU -----------+
|  1. Generate password(s)   |
|  2. Change settings        |
|  3. View current settings  |
|  4. Exit                   |
+----------------------------+
"""


def print_separator() -> None:
    """Print a thin horizontal rule."""
    print("-" * 54)


def print_password_result(index: int, password: str) -> None:
    """Pretty-print a single generated password with its strength."""
    strength = password_strength(password)
    strength_label = {
        "Weak": "[WEAK]",
        "Moderate": "[MODERATE]",
        "Strong": "[STRONG]",
    }.get(strength, "")
    label = f"  Password {index}" if index > 0 else "  Password"
    print(f"{label}: {password}")
    print(f"  Strength : {strength_label}  |  Length: {len(password)}")


# ---------------------------------------------------------------------------
# Input helpers
# ---------------------------------------------------------------------------

def read_int(prompt: str, default: int | None = None) -> int:
    """Prompt the user for an integer, with an optional default.

    Keeps asking until a valid integer is entered.
    """
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            return int(raw)
        except ValueError:
            print("  [!] Please enter a valid integer.")


def read_yes_no(prompt: str, default: bool = True) -> bool:
    """Prompt the user for a yes/no answer.

    Args:
        prompt: The question to display.
        default: Default value when the user presses Enter.

    Returns:
        True for yes, False for no.
    """
    hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt} [{hint}]: ").strip().lower()
        if raw == "":
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  [!] Please enter 'y' or 'n'.")


# ---------------------------------------------------------------------------
# Settings management
# ---------------------------------------------------------------------------

def display_settings(config: PasswordConfig) -> None:
    """Show the current password configuration."""
    on = "ON "
    off = "OFF"
    print()
    print("+---- Current Settings ----+")
    print(f"|  Length     : {config.length:<11}|")
    print(f"|  Uppercase  : {on if config.use_uppercase else off:<11}|")
    print(f"|  Lowercase  : {on if config.use_lowercase else off:<11}|")
    print(f"|  Digits     : {on if config.use_digits else off:<11}|")
    print(f"|  Symbols    : {on if config.use_symbols else off:<11}|")
    print("+--------------------------+")


def change_settings(config: PasswordConfig) -> PasswordConfig:
    """Interactive settings editor.  Returns a new validated config."""
    print("\n  Configure password options (press Enter to keep current value):\n")

    length = read_int(
        f"  Password length ({MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH})",
        default=config.length,
    )
    use_upper = read_yes_no("  Include uppercase (A-Z)?", default=config.use_uppercase)
    use_lower = read_yes_no("  Include lowercase (a-z)?", default=config.use_lowercase)
    use_digits = read_yes_no("  Include digits (0-9)?", default=config.use_digits)
    use_symbols = read_yes_no("  Include symbols (!@#$...)?", default=config.use_symbols)

    new_config = PasswordConfig(
        length=length,
        use_uppercase=use_upper,
        use_lowercase=use_lower,
        use_digits=use_digits,
        use_symbols=use_symbols,
    )

    errors = new_config.validate()
    if errors:
        print()
        for err in errors:
            print(f"  [!] {err}")
        print("  Settings were NOT changed. Keeping previous configuration.")
        return config

    print("\n  [OK] Settings updated successfully!")
    return new_config


# ---------------------------------------------------------------------------
# Generation flow
# ---------------------------------------------------------------------------

def generate_passwords(generator: PasswordGenerator, config: PasswordConfig) -> None:
    """Ask how many passwords to generate, then display them."""
    count = read_int("  How many passwords to generate?", default=1)
    if count < 1:
        print("  [!] Count must be at least 1.")
        return
    if count > 100:
        print("  [!] Maximum 100 passwords at a time. Generating 100.")
        count = 100

    try:
        passwords = generator.generate_multiple(config, count)
    except ValueError as exc:
        print(f"\n  [!] Error: {exc}")
        return

    print()
    print_separator()
    for i, pwd in enumerate(passwords, start=1):
        label = i if count > 1 else 0
        print_password_result(label, pwd)
        if i < len(passwords):
            print()
    print_separator()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the Password Generator CLI application."""
    print(BANNER)

    generator = PasswordGenerator()
    config = PasswordConfig()  # sensible defaults

    while True:
        print(MENU)
        choice = input("  Select an option (1-4): ").strip()

        if choice == "1":
            generate_passwords(generator, config)
        elif choice == "2":
            config = change_settings(config)
        elif choice == "3":
            display_settings(config)
        elif choice == "4":
            print("\n  Goodbye! Stay secure.\n")
            break
        else:
            print("  [!] Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
