# Design Document — Task 01: Password Generator

## 1. UI & Visual Design Philosophy
The Password Generator utilizes an **ASCII-safe Command-Line Interface (CLI)** optimized for maximum portability, visual clarity, and high responsiveness across terminal emulators. 

### Key Principles
- **Universal Terminal Compatibility**: Uses standard 7-bit ASCII characters (`+`, `-`, `|`, `*`, `!`) for all borders, frames, and dividers, guaranteeing flawless rendering on Windows Command Prompt (`cp1252`), PowerShell, Linux shells, and macOS terminals without glyph corruption.
- **Zero ANSI Color Reliance**: By omitting escape color codes, the interface maintains perfect readability in high-contrast mode, dark themes, light themes, redirected stdout streams, and headless server environments.
- **Predictable Monospace Typography**: Visual alignments, column widths, and box frames assume standard fixed-width terminal fonts (e.g., Consolas, Courier New, Cascadia Code, JetBrains Mono).

---

## 2. Layout Structure & Wireframes

The visual layout is organized into 4 standardized screen areas:
1. **Header Banner**: Welcomes the user and establishes security context.
2. **Navigation Menu**: Outlines available operations in a structured box.
3. **Action & Input Area**: Provides clear prompt queries with default indicators.
4. **Result / Feedback Display**: Presents generated outputs, strength metrics, or validation feedback encased by dividers.

### 2.1 Header Banner
```
+------------------------------------------------------+
|         SECURE PASSWORD GENERATOR                    |
|         Cryptographically Strong Passwords           |
+------------------------------------------------------+
```

### 2.2 Navigation Menu
```
+----------- MENU -----------+
|  1. Generate password(s)   |
|  2. Change settings        |
|  3. View current settings  |
|  4. Exit                   |
+----------------------------+
```

### 2.3 Settings Display Box
```
+---- Current Settings ----+
|  Length     : 16         |
|  Uppercase  : ON         |
|  Lowercase  : ON         |
|  Digits     : ON         |
|  Symbols    : ON         |
+--------------------------+
```

---

## 3. Component Hierarchy

```
Application Entry (main.py)
 └── Display BANNER
 └── Main Menu Loop
      ├── Option 1: Generate Passwords Flow
      │    ├── Prompt: Count (1-100, default [1])
      │    ├── Execution: PasswordGenerator.generate_multiple()
      │    ├── Separator: Thin rule (54 hyphens)
      │    ├── Password Result Row(s)
      │    │    ├── Password value
      │    │    └── Strength rating ([STRONG] | [MODERATE] | [WEAK]) + Length
      │    └── Separator: Thin rule
      │
      ├── Option 2: Change Settings Flow
      │    ├── Prompt: Length (4-128, default [current])
      │    ├── Prompt: Uppercase toggle ([Y/n])
      │    ├── Prompt: Lowercase toggle ([Y/n])
      │    ├── Prompt: Digits toggle ([Y/n])
      │    ├── Prompt: Symbols toggle ([Y/n])
      │    ├── Validation step: PasswordConfig.validate()
      │    └── Feedback: [OK] Success confirmation OR [!] Error notice
      │
      ├── Option 3: View Settings Flow
      │    └── Render: Current Settings box with ON/OFF statuses
      │
      └── Option 4: Exit Flow
           └── Print: Exit farewell message & terminate process
```

---

## 4. Typography & Monospace Formatting
- **Standard Width**: Menus and banners are standardized to clean tabular widths (e.g., Banner is 56 characters wide, Separators are 54 characters wide).
- **Text Alignment**: Settings columns are formatted with left-aligned keys and padded values:
  `| Length : 16 |`
  `| Uppercase : ON |`
- **Brackets for Visual Hierarchy**:
  - Prompts show default fallbacks in brackets: `[16]`, `[Y/n]`, `[1]`.
  - Severity tags use bracketed prefixes: `[OK]`, `[!]`.
  - Strength ratings use bracketed badges: `[STRONG]`, `[MODERATE]`, `[WEAK]`.

---

## 5. Interaction States & Input Mechanics

### 5.1 Menu Selection
- Prompt: `Select an option (1-4): `
- Valid Options: `"1"`, `"2"`, `"3"`, `"4"`.
- Error Handling: Invalid entries trigger `[!] Invalid choice. Please enter 1, 2, 3, or 4.` and re-render the menu.

### 5.2 Numeric Input (`read_int`)
- Loops continuously until a valid integer is supplied.
- Pressing `Enter` without typing adopts the bracketed default value.
- Non-numeric inputs output `[!] Please enter a valid integer.` and re-prompt.

### 5.3 Boolean Confirmation (`read_yes_no`)
- Prompt suffix illustrates default casing: `[Y/n]` (default True) or `[y/N]` (default False).
- Pressing `Enter` defaults to the indicated state.
- Accepts case-insensitive `"y"`, `"yes"`, `"n"`, `"no"`.
- Any other string outputs `[!] Please enter 'y' or 'n'.` and re-prompts.

---

## 6. Detailed Interaction Flows

### 6.1 Generate Flow
```
User selects Option 1:
------------------------------------------------------
  Select an option (1-4): 1
  How many passwords to generate? [1]: 2

------------------------------------------------------
  Password 1: pK9$xL2!vQ#9aZ&4
  Strength : [STRONG]  |  Length: 16

  Password 2: mR5*uW8@bT#1yE%7
  Strength : [STRONG]  |  Length: 16
------------------------------------------------------
```

*Single password variation:*
```
  Select an option (1-4): 1
  How many passwords to generate? [1]: 1

------------------------------------------------------
  Password: kF8#vP2!wL9$qM&1
  Strength : [STRONG]  |  Length: 16
------------------------------------------------------
```

### 6.2 Settings Configuration Flow
```
User selects Option 2:
------------------------------------------------------
  Select an option (1-4): 2

  Configure password options (press Enter to keep current value):

  Password length (4-128) [16]: 24
  Include uppercase (A-Z)? [Y/n]: y
  Include lowercase (a-z)? [Y/n]: y
  Include digits (0-9)? [Y/n]: y
  Include symbols (!@#$...)? [Y/n]: n

  [OK] Settings updated successfully!
```

*Invalid settings attempt (graceful recovery):*
```
  Password length (4-128) [16]: 2
  Include uppercase (A-Z)? [Y/n]: n
  Include lowercase (a-z)? [Y/n]: n
  Include digits (0-9)? [Y/n]: n
  Include symbols (!@#$...)? [Y/n]: n

  [!] Password length must be at least 4, got 2.
  [!] At least one character type must be selected (uppercase, lowercase, digits, or symbols).
  Settings were NOT changed. Keeping previous configuration.
```

---

## 7. Password Strength Formatting & Heuristics

Strength indicator badges provide instant feedback on generated entropy:

| Rating | Badge | Criteria |
| :--- | :--- | :--- |
| **Weak** | `[WEAK]` | Password length < 8 OR contains characters from only 1 category. |
| **Moderate** | `[MODERATE]` | Password length 8–11 with ≥ 2 categories, OR length ≥ 12 with 1–2 categories. |
| **Strong** | `[STRONG]` | Password length ≥ 12 with characters spanning ≥ 3 distinct categories. |

Display string syntax:
```
  Password 1: <string>
  Strength : [STRONG]  |  Length: 16
```
