# Task 06: AI Chatbot Application

A conversational AI desktop and terminal application built with Python. Features local Natural Language Processing (NLP), rule-based and TF-IDF similarity intent matching, sentiment analysis, safe mathematical evaluation, multi-turn dialogue memory, live web search, and an optional OpenAI-compatible external LLM integration.

---

## 📌 Overview

The **AI Chatbot** operates as an intelligent personal assistant that can converse with users, answer questions from its knowledge base, execute safe math calculations, report current time/date, search Wikipedia and DuckDuckGo for live facts, and remember user details (such as names) across dialogue turns.

It is designed to run **100% locally and offline** without requiring external API keys. However, an optional integration bridge allows connecting to any OpenAI-compatible LLM endpoint (OpenAI, Groq, OpenRouter, Ollama) if desired.

---

## ✨ Features

- **Local NLP Pipeline:** Custom tokenization, stopword removal, word stemming, and lexical sentiment scoring (positive / neutral / negative).
- **Hybrid Intent Classification:** Matches user queries using exact pattern triggers and TF-IDF cosine similarity against an extensible JSON knowledge base.
- **Safe Mathematical Evaluation:** Computes math expressions (`15 * 8 + 40`, `2^8`, `(100 - 20) / 4`) strictly using Python's `ast` parser without insecure `eval()`.
- **Multi-Turn Dialogue Memory:** Remembers user names and conversation context across turns, with conversation history tracking and reset support.
- **Live Online Search:** Retrieves live encyclopedic summaries from DuckDuckGo Instant Answers and Wikipedia via standard library HTTP requests.
- **Optional External LLM Support:** Easily route complex queries through OpenAI, Groq, or local Ollama servers via standard environment variables.
- **Dual Mode (GUI & CLI):** Modern dark-themed chat interface with speech bubbles and status tags, alongside an interactive terminal interface.

---

## 🛠️ Technologies Used

- **Language:** Python 3.10+
- **GUI Framework:** Tkinter
- **NLP & Search:** Custom TF-IDF, Regex, `urllib` (Wikipedia & DuckDuckGo APIs)
- **Security & Math:** `ast`, `operator`
- **Testing:** `unittest` with mock providers

---

## 📂 Project Structure

```text
Task_06_AI_Chatbot/
├── assets/                # Screenshots and UI assets
├── data/
│   └── knowledge_base.json # Intent definitions, patterns, and responses
├── src/
│   ├── __init__.py        # Package marker
│   ├── chatbot.py         # Main Chatbot coordinator and dialogue pipeline
│   ├── conversation_manager.py # Multi-turn memory and history tracking
│   ├── gui.py             # Tkinter chat interface
│   ├── llm_client.py      # Optional external LLM client
│   ├── models.py          # ChatMessage, IntentMatch, and SentimentResult
│   ├── nlp_processor.py   # Tokenization, stemming, sentiment, query extractors
│   ├── response_generator.py # TF-IDF matcher, response renderer, AST math
│   └── web_search.py      # DuckDuckGo and Wikipedia web search engine
├── tests/
│   ├── __init__.py
│   └── test_chatbot.py    # 24 automated unit and integration tests
├── .env.example           # Example configuration for optional LLM
├── main.py                # Application entry point (GUI / CLI router)
├── requirements.txt       # Project dependencies (Standard Library)
└── README.md              # Project documentation
```

---

## 🚀 Installation & Requirements

No third-party packages are required for offline local operation. The entire application runs on Python standard library modules:

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
Run interactive chat in the terminal:
```bash
python main.py --cli
```

### Optional: Connecting an External LLM
To connect an external API provider (e.g. Groq, OpenAI, Ollama):
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set your API credentials in `.env`:
   ```env
   CHATBOT_API_KEY=your_actual_api_key
   CHATBOT_API_BASE=https://api.openai.com/v1
   CHATBOT_MODEL=gpt-4o-mini
   ```

---

## 🧪 Testing

Run the automated test suite covering NLP normalization, intent classification, multi-turn memory, AST math evaluation, and web search integration:

```bash
python -m unittest discover tests -v
```

**Results:** 24 unit tests passing cleanly.
