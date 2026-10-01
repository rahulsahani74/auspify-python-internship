# Python Developer Internship Projects

A repository containing 6 standalone Python projects developed by **Rahul Sahani** during the **Python Developer Internship** at **Auspify Technologies**.

Each project is designed, implemented, and thoroughly tested as an independent application following clean architecture, comprehensive test coverage, and clear user documentation.

---

## 📌 Internship Information

- **Organization:** Auspify Technologies
- **Program:** Python Developer Internship
- **Projects Completed:** 6 / 6
- **Intern:** Rahul Sahani

---

## 🚀 Projects Overview

| Task # | Project Name | Domain / Stack | Interface | Key Highlights |
|---|---|---|---|---|
| **01** | [Password Generator](./Task_01_Password_Generator) | Cryptography / Standard Library | CLI | Cryptographically secure PRNG via `secrets`, custom lengths, charset toggles, Fisher-Yates shuffle, password strength meter. |
| **02** | [To-Do List](./Task_02_Todo_List) | Data Structures / File Handling | CLI | Full task CRUD, priority levels, categories, due dates, atomic JSON persistence, search & filtering, task statistics. |
| **03** | [Calculator GUI](./Task_03_Calculator_GUI) | GUI / AST Expression Evaluation | Desktop (Tkinter) | AST-based mathematical parsing without `eval()`, history panel, square root, percentage, sign toggle, keyboard shortcuts. |
| **04** | [Weather App](./Task_04_Weather_App) | REST APIs / Network Services | Desktop (Tkinter) + CLI | Live weather forecaster with OpenWeatherMap integration, keyless Open-Meteo fallback, async fetching, metric/imperial toggle. |
| **05** | [Expense Tracker](./Task_05_Expense_Tracker) | Database / Financial Analytics | Desktop (Tkinter) + CLI | SQLite database persistence, category breakdowns, monthly analytics, dashboard metric cards, CSV import/export. |
| **06** | [AI Chatbot](./Task_06_AI_Chatbot) | NLP / Conversational AI | Desktop (Tkinter) + CLI | Rule-based & TF-IDF intent matching, sentiment analysis, safe AST math, multi-turn memory, DuckDuckGo & Wikipedia search, optional LLM hook. |

---

## 🛠️ Technologies Used

- **Language:** Python 3.10+
- **GUI Framework:** Tkinter (Desktop GUI applications)
- **Database & Storage:** SQLite3, JSON (atomic write guarantees)
- **APIs & Web:** `requests`, `urllib` (OpenWeatherMap, Open-Meteo, DuckDuckGo, Wikipedia)
- **Math & Security:** `secrets`, `ast` (safe syntax tree evaluation)
- **Testing:** `unittest` (167 automated unit & integration tests)

---

## 📂 Repository Structure

```text
auspify-python-internship/
├── Task_01_Password_Generator/
│   ├── src/
│   │   ├── __init__.py
│   │   └── generator.py
│   ├── tests/
│   │   └── test_generator.py
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── Task_02_Todo_List/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   └── cli.py
│   ├── tests/
│   │   └── test_todo.py
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── Task_03_Calculator_GUI/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── gui.py
│   ├── tests/
│   │   └── test_calculator.py
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── Task_04_Weather_App/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── gui.py
│   │   └── models.py
│   ├── tests/
│   │   ├── mock_data.py
│   │   └── test_weather.py
│   ├── .env.example
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── Task_05_Expense_Tracker/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── service.py
│   │   └── gui.py
│   ├── tests/
│   │   └── test_tracker.py
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── Task_06_AI_Chatbot/
│   ├── data/
│   │   └── knowledge_base.json
│   ├── src/
│   │   ├── __init__.py
│   │   ├── chatbot.py
│   │   ├── conversation_manager.py
│   │   ├── llm_client.py
│   │   ├── models.py
│   │   ├── nlp_processor.py
│   │   ├── response_generator.py
│   │   ├── web_search.py
│   │   └── gui.py
│   ├── tests/
│   │   └── test_chatbot.py
│   ├── .env.example
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
├── .gitignore
└── README.md
```

---

## 🏃 Quick Start & How to Run

Clone the repository and enter the project folder:

```bash
git clone https://github.com/rahulsahani74/auspify-python-internship.git
cd auspify-python-internship
```

### Running Each Project

1. **Task 01 — Password Generator**
   ```bash
   cd Task_01_Password_Generator
   python main.py
   ```

2. **Task 02 — To-Do List**
   ```bash
   cd Task_02_Todo_List
   python main.py
   ```

3. **Task 03 — Calculator GUI**
   ```bash
   cd Task_03_Calculator_GUI
   python main.py
   ```

4. **Task 04 — Weather App**
   ```bash
   cd Task_04_Weather_App
   pip install -r requirements.txt
   python main.py          # Launches GUI
   python main.py --cli    # Runs in CLI mode
   ```

5. **Task 05 — Expense Tracker**
   ```bash
   cd Task_05_Expense_Tracker
   python main.py          # Launches GUI
   python main.py --cli    # Runs in CLI mode
   ```

6. **Task 06 — AI Chatbot**
   ```bash
   cd Task_06_AI_Chatbot
   python main.py          # Launches GUI
   python main.py --cli    # Runs in CLI mode
   ```

---

## 🧪 Running the Automated Test Suite

All 6 projects include automated test suites using Python's built-in `unittest` framework:

```bash
python -m unittest discover Task_01_Password_Generator/tests
python -m unittest discover Task_02_Todo_List/tests
python -m unittest discover Task_03_Calculator_GUI/tests
python -m unittest discover Task_04_Weather_App/tests
python -m unittest discover Task_05_Expense_Tracker/tests
python -m unittest discover Task_06_AI_Chatbot/tests
```

**Total Tests:** **167 tests** across all 6 applications (100% passing).

---

## 👤 Author

**Rahul Sahani**  
BCA Student | Python Developer | AI & Automation Enthusiast  
- GitHub: [@rahulsahani74](https://github.com/rahulsahani74)
- Repository: [rahulsahani74/auspify-python-internship](https://github.com/rahulsahani74/auspify-python-internship)
