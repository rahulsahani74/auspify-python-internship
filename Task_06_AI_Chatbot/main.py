"""
Main entry point for Task 06: NOVA AI Chatbot Application.

Launches the Tkinter desktop GUI by default, and provides an interactive
terminal CLI mode (--cli) for headless environments and rapid testing.
"""

import argparse
import sys
import tkinter as tk

# Ensure terminal stdout/stderr handles UTF-8 (e.g. emojis and unicode on Windows cp1252)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.chatbot import Chatbot


def run_cli_interactive(chatbot: Chatbot) -> None:
    """Run interactive terminal chat loop."""
    print("=" * 64)
    print("  NOVA AI CHATBOT — INTERACTIVE TERMINAL MODE")
    print("=" * 64)
    mode_str = "Cloud LLM" if chatbot.llm.is_configured() else "Local NLP Engine (Offline)"
    print(f"  Engine Mode : {mode_str}")
    print("  Commands    : 'exit' or 'quit' to close, 'clear' to reset memory\n")

    initial_reply = "Hello! I am NOVA, your AI assistant. How can I help you today?"
    print(f"NOVA: {initial_reply}\n")

    while True:
        try:
            user_input = input("You > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("NOVA: Goodbye! Have a great day!")
            break

        reply = chatbot.process_message(user_input)
        print(f"NOVA: {reply.content}\n")


def run_gui_mode() -> int:
    """Launch Tkinter desktop GUI application."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"[!] Desktop display unavailable ({exc}). Falling back to CLI mode.\n")
        chatbot = Chatbot()
        run_cli_interactive(chatbot)
        return 0

    from src.gui import ChatbotGUI

    # Center window
    w, h = 860, 650
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = max(0, int((ws / 2) - (w / 2)))
    y = max(0, int((hs / 2) - (h / 2)))
    root.geometry(f"{w}x{h}+{x}+{y}")

    app = ChatbotGUI(root)
    root.mainloop()
    return 0


def main() -> None:
    """Command-line routing."""
    parser = argparse.ArgumentParser(
        description="Task 06: NOVA AI Chatbot Application"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in interactive terminal CLI mode instead of GUI.",
    )
    parser.add_argument(
        "--query",
        type=str,
        metavar="TEXT",
        help="Process a single query in terminal and print response.",
    )

    args = parser.parse_args()
    chatbot = Chatbot()

    if args.query:
        reply = chatbot.process_message(args.query)
        print(f"Intent: {reply.intent} (Confidence: {reply.confidence:.2f})")
        print(f"Reply : {reply.content}")
        sys.exit(0)
    elif args.cli:
        run_cli_interactive(chatbot)
        sys.exit(0)
    else:
        sys.exit(run_gui_mode())


if __name__ == "__main__":
    main()
