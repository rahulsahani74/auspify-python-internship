"""
Password Generator Core Module.

Provides the PasswordGenerator class that creates cryptographically secure
random passwords with configurable character sets and lengths.

Uses Python's `secrets` module for cryptographically strong random generation.
"""

import secrets
import string
from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_PASSWORD_LENGTH = 4
MAX_PASSWORD_LENGTH = 128
DEFAULT_PASSWORD_LENGTH = 16


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class PasswordConfig:
    """Configuration for password generation.

    Attributes:
        length: Desired password length (4–128).
        use_uppercase: Include uppercase letters (A-Z).
        use_lowercase: Include lowercase letters (a-z).
        use_digits: Include digits (0-9).
        use_symbols: Include special symbols (!@#$%^&* etc.).
    """

    length: int = DEFAULT_PASSWORD_LENGTH
    use_uppercase: bool = True
    use_lowercase: bool = True
    use_digits: bool = True
    use_symbols: bool = True

    def validate(self) -> List[str]:
        """Validate the configuration and return a list of error messages.

        Returns:
            A list of human-readable error strings.  Empty means valid.
        """
        errors: List[str] = []

        if not isinstance(self.length, int):
            errors.append(
                f"Password length must be an integer, got {type(self.length).__name__}."
            )
        elif self.length < MIN_PASSWORD_LENGTH:
            errors.append(
                f"Password length must be at least {MIN_PASSWORD_LENGTH}, got {self.length}."
            )
        elif self.length > MAX_PASSWORD_LENGTH:
            errors.append(
                f"Password length must be at most {MAX_PASSWORD_LENGTH}, got {self.length}."
            )

        if not any([
            self.use_uppercase,
            self.use_lowercase,
            self.use_digits,
            self.use_symbols,
        ]):
            errors.append(
                "At least one character type must be selected "
                "(uppercase, lowercase, digits, or symbols)."
            )

        return errors


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class PasswordGenerator:
    """Generates cryptographically secure random passwords.

    Example::

        gen = PasswordGenerator()
        config = PasswordConfig(length=20, use_symbols=False)
        password = gen.generate(config)
    """

    # Character pools
    UPPERCASE = string.ascii_uppercase       # A-Z
    LOWERCASE = string.ascii_lowercase       # a-z
    DIGITS = string.digits                   # 0-9
    SYMBOLS = string.punctuation             # !@#$%^&*()_+-= etc.

    def _build_charset(self, config: PasswordConfig) -> str:
        """Build the combined character set from the configuration.

        Args:
            config: A validated PasswordConfig instance.

        Returns:
            A string containing all allowed characters.
        """
        charset = ""
        if config.use_uppercase:
            charset += self.UPPERCASE
        if config.use_lowercase:
            charset += self.LOWERCASE
        if config.use_digits:
            charset += self.DIGITS
        if config.use_symbols:
            charset += self.SYMBOLS
        return charset

    def _guaranteed_chars(self, config: PasswordConfig) -> List[str]:
        """Return one random character from each enabled pool.

        This guarantees that the final password contains at least one
        character from every selected category.

        Args:
            config: A validated PasswordConfig instance.

        Returns:
            A list of single-character strings.
        """
        chars: List[str] = []
        if config.use_uppercase:
            chars.append(secrets.choice(self.UPPERCASE))
        if config.use_lowercase:
            chars.append(secrets.choice(self.LOWERCASE))
        if config.use_digits:
            chars.append(secrets.choice(self.DIGITS))
        if config.use_symbols:
            chars.append(secrets.choice(self.SYMBOLS))
        return chars

    def generate(self, config: PasswordConfig) -> str:
        """Generate a single password according to *config*.

        Args:
            config: Password generation configuration.

        Returns:
            The generated password string.

        Raises:
            ValueError: If *config* fails validation.
        """
        errors = config.validate()
        if errors:
            raise ValueError("Invalid password configuration: " + "; ".join(errors))

        charset = self._build_charset(config)
        guaranteed = self._guaranteed_chars(config)

        # Fill the remaining length with random picks from the full charset.
        remaining = config.length - len(guaranteed)
        rest = [secrets.choice(charset) for _ in range(remaining)]

        # Combine and securely shuffle so guaranteed chars are not predictable.
        password_chars = guaranteed + rest
        # Fisher-Yates shuffle using secrets for unbiased randomness.
        for i in range(len(password_chars) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

        return "".join(password_chars)

    def generate_multiple(self, config: PasswordConfig, count: int) -> List[str]:
        """Generate *count* passwords with the same configuration.

        Args:
            config: Password generation configuration.
            count: Number of passwords to generate (must be >= 1).

        Returns:
            A list of generated password strings.

        Raises:
            ValueError: If *count* < 1 or *config* is invalid.
        """
        if not isinstance(count, int) or count < 1:
            raise ValueError(f"Count must be a positive integer, got {count!r}.")
        return [self.generate(config) for _ in range(count)]


# ---------------------------------------------------------------------------
# Password strength helper
# ---------------------------------------------------------------------------

def password_strength(password: str) -> str:
    """Return a simple strength label for *password*.

    Strength levels:
        - **Weak**: length < 8 or uses only one character category.
        - **Moderate**: length 8-11 with ≥ 2 categories, or length ≥ 12 with 1-2 categories.
        - **Strong**: length ≥ 12 with ≥ 3 categories.

    Args:
        password: The password to evaluate.

    Returns:
        One of ``"Weak"``, ``"Moderate"``, or ``"Strong"``.
    """
    length = len(password)
    categories = 0
    if any(c in string.ascii_uppercase for c in password):
        categories += 1
    if any(c in string.ascii_lowercase for c in password):
        categories += 1
    if any(c in string.digits for c in password):
        categories += 1
    if any(c in string.punctuation for c in password):
        categories += 1

    if length < 8 or categories <= 1:
        return "Weak"
    if length >= 12 and categories >= 3:
        return "Strong"
    return "Moderate"
