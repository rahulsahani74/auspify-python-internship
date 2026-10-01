# Task 02: To-Do List Application

A modular, feature-rich command-line To-Do List and task management system built with Python. Features persistent JSON storage, priority levels, categories, due dates, robust search/filtering, and productivity statistics.

---

## 📌 Overview

The **To-Do List Manager** helps users track and organize their daily tasks efficiently directly from the terminal. Built following a decoupled three-layer architecture (Data Models, Repository, and Service layer), the application provides atomic disk-writing guarantees so task data is never corrupted during unexpected interruptions.

---

## ✨ Features

- **Full CRUD Management:** Create, view, update, and delete tasks with ease.
- **Priority & Categorization:** Assign priorities (`High`, `Medium`, `Low`) and categories (`Work`, `Personal`, `Study`, `Urgent`, `General`).
- **Due Dates & Timestamps:** Set due dates (YYYY-MM-DD) and automatically track creation and completion timestamps.
- **Atomic File Persistence:** Persists tasks in a structured JSON file with temporary-file swapping to prevent data loss.
- **Search & Filter:** Search tasks across titles, descriptions, and categories, or filter by completion status and priority.
- **Productivity Statistics:** View completion rates, pending counts, and categorical distributions in clean ASCII cards.
- **Bulk Cleanup:** Clear all completed tasks with a single confirmation.
- **Robust Input Handling:** Defensive input parsers handle malformed dates, invalid numbers, and edge cases gracefully.

---

## 🛠️ Technologies Used

- **Language:** Python 3.10+
- **Standard Library:** `json`, `dataclasses`, `datetime`, `shutil`, `tempfile`, `unittest`
- **Dependencies:** None (100% Python Standard Library)

---

## 📂 Project Structure

```text
Task_02_Todo_List/
├── data/                  # Local runtime data directory (JSON storage)
├── src/
│   ├── __init__.py        # Package marker
│   ├── models.py          # Task dataclass, validation rules, serialization
│   ├── repository.py      # Atomic JSON file persistence and recovery
│   ├── service.py         # Business logic layer for task operations
│   └── cli.py             # ASCII table formatting and user prompts
├── tests/
│   ├── __init__.py
│   └── test_todo.py       # 32 automated unit tests
├── main.py                # Application entry point and menu loop
├── requirements.txt       # Project dependencies (Standard Library)
└── README.md              # Project documentation
```

---

## 🚀 Installation & Requirements

No external libraries are required. Simply verify your Python installation:

```bash
python --version
```

---

## 💻 How to Run

Launch the interactive CLI application:

```bash
python main.py
```

### Main Menu Options

```text
+------------------------ MENU -------------------------------+
|  1. View All Tasks              6. Search Tasks             |
|  2. Add New Task                7. Filter Tasks             |
|  3. Toggle Task Completion      8. View Task Statistics     |
|  4. Edit Task Details           9. Clear Completed Tasks    |
|  5. Delete Task                 0. Exit Application         |
+-------------------------------------------------------------+
```

---

## 🧪 Testing

Run the automated test suite covering models, repository operations, service logic, and corrupted-file recovery:

```bash
python -m unittest discover tests -v
```

**Results:** 32 unit tests passing cleanly.

---

## 🛡️ Error Handling & Reliability

- **Corrupted Data Recovery:** Automatically creates timestamped `.bak` backups if JSON files become malformed on disk, resetting safely to an empty task state without crashing.
- **Atomic Disk Writes:** Writes to a `.tmp` file and performs an atomic rename to guarantee data consistency.
- **Defensive Type Checking:** Prevents empty titles, invalid priority tags, or out-of-range dates.
