# Task 03: Calculator with GUI

A desktop calculator application with a modern dark-themed graphical user interface built using Tkinter. Employs a secure AST (Abstract Syntax Tree) expression parser to safely compute mathematical operations without using unsafe `eval()`.

---

## 📌 Overview

The **Modern Calculator** provides a desktop calculation experience supporting both standard arithmetic and common utility operations. It includes a dual-line dynamic display, visual operator handling, full physical keyboard integration, and a dedicated calculation history panel.

---

## ✨ Features

- **Standard Arithmetic:** Addition, subtraction, multiplication, and division with operator precedence.
- **Advanced Operators:** Powers (`^`), percentages (`%`), square roots (`√`), and sign inversion (`±`).
- **Parentheses Support:** Fully supports nested expressions `( ... )` with automatic closing on evaluation.
- **Safe AST Evaluation:** Parses expressions strictly using Python's `ast` module, eliminating code injection risks.
- **Calculation History:** View, search, and reload previous calculation results via the dedicated History dialog.
- **Division-by-Zero Protection:** Detects zero division and mathematical errors gracefully without crashes.
- **Full Keyboard Bindings:** Operates seamlessly with numeric keys, Enter, Backspace, Escape, and arithmetic symbols.
- **Modern Dark UI:** Styled with high-contrast slate tones and responsive font auto-scaling for long numbers.

---

## 🛠️ Technologies Used

- **Language:** Python 3.10+
- **GUI Framework:** Tkinter (Python standard library)
- **Math Parsing:** `ast`, `operator`, `math`, `re`
- **Testing:** `unittest`

---

## 📂 Project Structure

```text
Task_03_Calculator_GUI/
├── assets/                # Screenshots and UI assets
├── src/
│   ├── __init__.py        # Package marker
│   ├── engine.py          # SafeEvaluator, CalculatorEngine, and history records
│   └── gui.py             # Tkinter layout, key bindings, and history dialog
├── tests/
│   ├── __init__.py
│   └── test_calculator.py # 33 automated unit and headless GUI tests
├── main.py                # Application entry point
├── requirements.txt       # Project dependencies (Standard Library)
└── README.md              # Project documentation
```

---

## 🚀 Installation & Requirements

No external packages are needed. Tkinter is included with standard Python distributions:

```bash
python --version
```

---

## 💻 How to Run

Launch the desktop GUI:

```bash
python main.py
```

### Keyboard Shortcuts

| Key | Action |
|---|---|
| `0-9` | Input digits |
| `+`, `-`, `*`, `/` | Addition, Subtraction, Multiplication, Division |
| `^`, `%` | Power, Percentage |
| `(`, `)` | Parentheses |
| `Enter` / `=` | Evaluate expression |
| `Backspace` | Delete last character |
| `Escape` / `Delete` | Clear all |

---

## 🧪 Testing

Run the automated test suite covering the AST parser, calculator engine state, and headless GUI updates:

```bash
python -m unittest discover tests -v
```

**Results:** 33 unit tests passing cleanly.

---

## 🛡️ Security & Safe Evaluation

Unlike basic calculator scripts that rely on Python's built-in `eval()`—which exposes systems to arbitrary code execution—this calculator inspects the syntax tree node-by-node using `ast.parse()`. Only safe arithmetic constants and designated mathematical operators are allowed.
