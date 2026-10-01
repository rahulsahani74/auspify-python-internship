# Task 05: Personal Expense Tracker & Analyzer

A financial tracking and analytics desktop application built with Python. Features SQLite database persistence, interactive dark-themed GUI, categorized spending breakdowns, monthly reporting, and CSV data interchange.

---

## 📌 Overview

The **Personal Expense Tracker** enables users to record, categorize, and analyze their daily expenses. It provides top-level metrics, customizable categories, payment methods, transaction editing, and monthly spending reports.

---

## ✨ Features

- **Expense Management:** Add, view, edit, and delete expense records with validation.
- **Categorization & Payment Modes:** Assign transactions to categories (`Food & Dining`, `Transportation`, `Housing`, etc.) and payment types (`Cash`, `UPI`, `Credit Card`, `Debit Card`, etc.).
- **SQLite Database Persistence:** Transactions are stored in a local SQLite database (`expenses.db`) with parameterized queries and indexed fields.
- **Financial Analytics Dashboard:** View Total Spending, This Month's Outlay, Daily Average, and Highest Single Expense via summary cards.
- **Monthly Reporting:** View spending breakdowns by category with percentages and transaction counts.
- **Search & Filter:** Filter expenses by category, month (YYYY-MM), or free-text keywords.
- **CSV Import & Export:** Backup records or load transactions from standard CSV files.
- **CLI & GUI Modes:** Operate through an intuitive desktop GUI or run terminal summaries and reports.

---

## 🛠️ Technologies Used

- **Language:** Python 3.10+
- **GUI Framework:** Tkinter (ttk Treeview styling)
- **Database:** SQLite3
- **Data Interchange:** `csv`
- **Testing:** `unittest`

---

## 📂 Project Structure

```text
Task_05_Expense_Tracker/
├── assets/                # Screenshots and UI assets
├── data/                  # SQLite storage directory
├── src/
│   ├── __init__.py        # Package marker
│   ├── database.py        # SQLite repository and analytical aggregations
│   ├── gui.py             # Tkinter desktop GUI and monthly report dialog
│   ├── models.py          # Expense dataclass and field validators
│   └── service.py         # Business operations, reports, CSV export/import
├── tests/
│   ├── __init__.py
│   └── test_tracker.py    # 19 automated unit and integration tests
├── main.py                # Application entry point (GUI / CLI router)
├── requirements.txt       # Project dependencies (Standard Library)
└── README.md              # Project documentation
```

---

## 🚀 Installation & Requirements

No third-party packages are required. The application runs entirely on standard Python modules:

```bash
python --version
```

---

## 💻 How to Run

### Desktop Graphical Interface (Default)
```bash
python main.py
```

### Command-Line Interface (CLI)

Print an overall financial summary:
```bash
python main.py --summary
```

Print a monthly breakdown report:
```bash
python main.py --report 2026-10
```

List all recorded transactions:
```bash
python main.py --list
```

Export expenses to a CSV file:
```bash
python main.py --export-csv expenses_backup.csv
```

---

## 🧪 Testing

Run the automated test suite covering models, SQLite transactions, analytical queries, and CSV interchange:

```bash
python -m unittest discover tests -v
```

**Results:** 19 unit tests passing cleanly.
