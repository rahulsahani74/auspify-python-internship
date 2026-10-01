"""
Comprehensive tests for the Password Generator.

Covers:
- Valid password lengths
- Invalid lengths (too short, too long, non-integer)
- Character-set selection and guarantees
- Multiple password generation
- Edge cases and error handling
- Password strength evaluation
"""

import string
import sys
import os
import unittest

# Ensure the project root is on sys.path so `src` can be imported.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.generator import (
    PasswordConfig,
    PasswordGenerator,
    password_strength,
    MIN_PASSWORD_LENGTH,
    MAX_PASSWORD_LENGTH,
    DEFAULT_PASSWORD_LENGTH,
)


class TestPasswordConfig(unittest.TestCase):
    """Tests for PasswordConfig validation."""

    def test_default_config_is_valid(self):
        """Default config should pass validation with no errors."""
        config = PasswordConfig()
        self.assertEqual(config.validate(), [])

    def test_minimum_length_valid(self):
        config = PasswordConfig(length=MIN_PASSWORD_LENGTH)
        self.assertEqual(config.validate(), [])

    def test_maximum_length_valid(self):
        config = PasswordConfig(length=MAX_PASSWORD_LENGTH)
        self.assertEqual(config.validate(), [])

    def test_length_too_short(self):
        config = PasswordConfig(length=2)
        errors = config.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("at least", errors[0].lower())

    def test_length_too_long(self):
        config = PasswordConfig(length=200)
        errors = config.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("at most", errors[0].lower())

    def test_length_zero(self):
        config = PasswordConfig(length=0)
        errors = config.validate()
        self.assertTrue(len(errors) >= 1)

    def test_length_negative(self):
        config = PasswordConfig(length=-5)
        errors = config.validate()
        self.assertTrue(len(errors) >= 1)

    def test_no_character_types_selected(self):
        config = PasswordConfig(
            use_uppercase=False,
            use_lowercase=False,
            use_digits=False,
            use_symbols=False,
        )
        errors = config.validate()
        self.assertEqual(len(errors), 1)
        self.assertIn("at least one", errors[0].lower())

    def test_only_uppercase(self):
        config = PasswordConfig(
            use_uppercase=True,
            use_lowercase=False,
            use_digits=False,
            use_symbols=False,
        )
        self.assertEqual(config.validate(), [])

    def test_only_digits(self):
        config = PasswordConfig(
            use_uppercase=False,
            use_lowercase=False,
            use_digits=True,
            use_symbols=False,
        )
        self.assertEqual(config.validate(), [])

    def test_multiple_errors(self):
        """Length too short AND no character types -> 2 errors."""
        config = PasswordConfig(
            length=1,
            use_uppercase=False,
            use_lowercase=False,
            use_digits=False,
            use_symbols=False,
        )
        errors = config.validate()
        self.assertEqual(len(errors), 2)


class TestPasswordGenerator(unittest.TestCase):
    """Tests for PasswordGenerator.generate()."""

    def setUp(self):
        self.gen = PasswordGenerator()

    # --- Length tests -------------------------------------------------------

    def test_generates_correct_length(self):
        for length in (4, 8, 16, 32, 64, 128):
            config = PasswordConfig(length=length)
            pwd = self.gen.generate(config)
            self.assertEqual(len(pwd), length, f"Expected length {length}")

    def test_default_length(self):
        config = PasswordConfig()
        pwd = self.gen.generate(config)
        self.assertEqual(len(pwd), DEFAULT_PASSWORD_LENGTH)

    # --- Character-set guarantee tests --------------------------------------

    def test_contains_uppercase(self):
        config = PasswordConfig(length=20, use_uppercase=True)
        pwd = self.gen.generate(config)
        self.assertTrue(
            any(c in string.ascii_uppercase for c in pwd),
            "Password should contain at least one uppercase letter.",
        )

    def test_contains_lowercase(self):
        config = PasswordConfig(length=20, use_lowercase=True)
        pwd = self.gen.generate(config)
        self.assertTrue(
            any(c in string.ascii_lowercase for c in pwd),
            "Password should contain at least one lowercase letter.",
        )

    def test_contains_digits(self):
        config = PasswordConfig(length=20, use_digits=True)
        pwd = self.gen.generate(config)
        self.assertTrue(
            any(c in string.digits for c in pwd),
            "Password should contain at least one digit.",
        )

    def test_contains_symbols(self):
        config = PasswordConfig(length=20, use_symbols=True)
        pwd = self.gen.generate(config)
        self.assertTrue(
            any(c in string.punctuation for c in pwd),
            "Password should contain at least one symbol.",
        )

    def test_only_uppercase_chars(self):
        config = PasswordConfig(
            length=30,
            use_uppercase=True,
            use_lowercase=False,
            use_digits=False,
            use_symbols=False,
        )
        pwd = self.gen.generate(config)
        for c in pwd:
            self.assertIn(c, string.ascii_uppercase)

    def test_only_lowercase_chars(self):
        config = PasswordConfig(
            length=30,
            use_uppercase=False,
            use_lowercase=True,
            use_digits=False,
            use_symbols=False,
        )
        pwd = self.gen.generate(config)
        for c in pwd:
            self.assertIn(c, string.ascii_lowercase)

    def test_only_digits_chars(self):
        config = PasswordConfig(
            length=30,
            use_uppercase=False,
            use_lowercase=False,
            use_digits=True,
            use_symbols=False,
        )
        pwd = self.gen.generate(config)
        for c in pwd:
            self.assertIn(c, string.digits)

    def test_only_symbols_chars(self):
        config = PasswordConfig(
            length=30,
            use_uppercase=False,
            use_lowercase=False,
            use_digits=False,
            use_symbols=True,
        )
        pwd = self.gen.generate(config)
        for c in pwd:
            self.assertIn(c, string.punctuation)

    def test_min_length_all_categories(self):
        """With length=4 and all 4 categories, each char is from a different pool."""
        config = PasswordConfig(length=4)
        pwd = self.gen.generate(config)
        self.assertEqual(len(pwd), 4)
        self.assertTrue(any(c in string.ascii_uppercase for c in pwd))
        self.assertTrue(any(c in string.ascii_lowercase for c in pwd))
        self.assertTrue(any(c in string.digits for c in pwd))
        self.assertTrue(any(c in string.punctuation for c in pwd))

    # --- Error tests --------------------------------------------------------

    def test_invalid_config_raises(self):
        config = PasswordConfig(length=2)
        with self.assertRaises(ValueError):
            self.gen.generate(config)

    def test_no_charset_raises(self):
        config = PasswordConfig(
            use_uppercase=False,
            use_lowercase=False,
            use_digits=False,
            use_symbols=False,
        )
        with self.assertRaises(ValueError):
            self.gen.generate(config)

    # --- Randomness test (statistical) --------------------------------------

    def test_passwords_are_not_identical(self):
        """Generate 10 passwords; they should not all be the same."""
        config = PasswordConfig(length=16)
        passwords = {self.gen.generate(config) for _ in range(10)}
        self.assertGreater(len(passwords), 1, "All 10 passwords were identical!")


class TestGenerateMultiple(unittest.TestCase):
    """Tests for PasswordGenerator.generate_multiple()."""

    def setUp(self):
        self.gen = PasswordGenerator()
        self.config = PasswordConfig(length=12)

    def test_generates_correct_count(self):
        for count in (1, 3, 10):
            passwords = self.gen.generate_multiple(self.config, count)
            self.assertEqual(len(passwords), count)

    def test_all_correct_length(self):
        passwords = self.gen.generate_multiple(self.config, 5)
        for pwd in passwords:
            self.assertEqual(len(pwd), 12)

    def test_count_zero_raises(self):
        with self.assertRaises(ValueError):
            self.gen.generate_multiple(self.config, 0)

    def test_count_negative_raises(self):
        with self.assertRaises(ValueError):
            self.gen.generate_multiple(self.config, -1)

    def test_count_non_integer_raises(self):
        with self.assertRaises(ValueError):
            self.gen.generate_multiple(self.config, "five")  # type: ignore

    def test_single_password(self):
        passwords = self.gen.generate_multiple(self.config, 1)
        self.assertEqual(len(passwords), 1)
        self.assertEqual(len(passwords[0]), 12)


class TestPasswordStrength(unittest.TestCase):
    """Tests for the password_strength() helper."""

    def test_short_password_is_weak(self):
        self.assertEqual(password_strength("abc"), "Weak")

    def test_single_category_is_weak(self):
        self.assertEqual(password_strength("abcdefghijklmno"), "Weak")

    def test_strong_password(self):
        # 16 chars, all 4 categories
        self.assertEqual(password_strength("Abc1!defGH2@ijkL"), "Strong")

    def test_moderate_password(self):
        # 10 chars, 2 categories
        self.assertEqual(password_strength("Abcdefghij"), "Moderate")

    def test_empty_password_is_weak(self):
        self.assertEqual(password_strength(""), "Weak")


if __name__ == "__main__":
    unittest.main()
