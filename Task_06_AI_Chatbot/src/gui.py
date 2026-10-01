"""
Graphical User Interface for the NOVA AI Chatbot.

Provides a modern dark-slate desktop chat experience with speech cards,
quick suggestion chips, conversation export utilities, and real-time status indicators.
"""

import sys
import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox, ttk
from typing import Optional

from src.chatbot import Chatbot
from src.models import ChatMessage


# Palette Tokens (Modern Dark Slate)
COLOR_BG_MAIN = "#0f1117"
COLOR_BG_CONTAINER = "#161b26"
COLOR_BG_CHAT = "#11141c"
COLOR_BG_CARD = "#1c2230"
COLOR_BG_USER_MSG = "#1e293b"
COLOR_BG_BOT_MSG = "#1a2333"
COLOR_BG_INPUT = "#222a3a"

COLOR_TEXT_PRIMARY = "#f8fafc"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_TEXT_MUTED = "#64748b"

COLOR_ACCENT = "#38bdf8"
COLOR_ACCENT_HOVER = "#0284c7"
COLOR_SUCCESS = "#22c55e"
COLOR_WARNING = "#eab308"
COLOR_PURPLE = "#a855f7"
COLOR_BORDER = "#2e384d"


class ChatbotGUI:
    """Tkinter Desktop Chatbot Interface."""

    def __init__(self, root: tk.Tk, chatbot: Optional[Chatbot] = None):
        """Initialize Chatbot GUI window, widgets, and greeting."""
        self.root = root
        self.chatbot = chatbot or Chatbot()

        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        self._display_welcome_message()

    def _setup_window(self) -> None:
        """Configure root window geometry, minimum size, and title."""
        self.root.title("NOVA — Intelligent AI Chatbot (Task 06)")
        self.root.geometry("860x650")
        self.root.minsize(720, 520)
        self.root.configure(bg=COLOR_BG_MAIN)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _setup_styles(self) -> None:
        """Define font typography and element sizing."""
        self.font_title = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.font_subtitle = tkfont.Font(family="Segoe UI", size=9)
        self.font_msg_head = tkfont.Font(family="Segoe UI", size=9, weight="bold")
        self.font_msg_body = tkfont.Font(family="Segoe UI", size=10)
        self.font_input = tkfont.Font(family="Segoe UI", size=10)
        self.font_small = tkfont.Font(family="Segoe UI", size=8)

    def _create_widgets(self) -> None:
        """Construct visual components: header bar, chat transcript, chips, input."""
        main_frame = tk.Frame(self.root, bg=COLOR_BG_MAIN, padx=14, pady=12)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # 1. Header Bar
        header = tk.Frame(main_frame, bg=COLOR_BG_CONTAINER, padx=14, pady=10, highlightbackground=COLOR_BORDER, highlightthickness=1)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(1, weight=1)

        # Avatar / Status Badge
        avatar_frame = tk.Frame(header, bg=COLOR_ACCENT, width=38, height=38)
        avatar_frame.pack_propagate(False)
        avatar_frame.grid(row=0, column=0, rowspan=2, padx=(0, 10))
        tk.Label(avatar_frame, text="AI", font=self.font_title, fg="#0f172a", bg=COLOR_ACCENT).pack(expand=True)

        # Title & Engine Mode
        title_box = tk.Frame(header, bg=COLOR_BG_CONTAINER)
        title_box.grid(row=0, column=1, sticky="w")
        tk.Label(title_box, text="NOVA AI Assistant", font=self.font_title, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_CONTAINER).pack(side="left")

        mode_text = "● Cloud LLM Active" if self.chatbot.llm.is_configured() else "● Local NLP Engine (Offline)"
        mode_color = COLOR_PURPLE if self.chatbot.llm.is_configured() else COLOR_SUCCESS
        self.lbl_mode = tk.Label(title_box, text=f"  {mode_text}", font=self.font_small, fg=mode_color, bg=COLOR_BG_CONTAINER)
        self.lbl_mode.pack(side="left", padx=6)

        tk.Label(header, text="Natural Language Processing • Multi-Turn Memory • Slot Filling • Math Solver", font=self.font_subtitle, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_CONTAINER).grid(row=1, column=1, sticky="w")

        # Action Buttons
        btn_box = tk.Frame(header, bg=COLOR_BG_CONTAINER)
        btn_box.grid(row=0, column=2, rowspan=2, sticky="e")

        btn_export = tk.Button(
            btn_box, text="Export Chat", font=self.font_subtitle,
            bg=COLOR_BG_INPUT, fg=COLOR_TEXT_SECONDARY, relief="flat", bd=0, padx=8, pady=4,
            cursor="hand2", command=self._on_export_chat
        )
        btn_export.pack(side="left", padx=4)

        btn_clear = tk.Button(
            btn_box, text="Clear Chat", font=self.font_subtitle,
            bg=COLOR_BG_INPUT, fg="#ef4444", relief="flat", bd=0, padx=8, pady=4,
            cursor="hand2", command=self._on_clear_chat
        )
        btn_clear.pack(side="left", padx=4)

        # 2. Scrollable Chat Transcript Window
        chat_container = tk.Frame(main_frame, bg=COLOR_BG_CHAT, highlightbackground=COLOR_BORDER, highlightthickness=1)
        chat_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        chat_container.columnconfigure(0, weight=1)
        chat_container.rowconfigure(0, weight=1)

        self.chat_display = tk.Text(
            chat_container,
            bg=COLOR_BG_CHAT,
            fg=COLOR_TEXT_PRIMARY,
            font=self.font_msg_body,
            wrap="word",
            padx=16,
            pady=16,
            bd=0,
            cursor="xterm",
            state="disabled",
            highlightthickness=0,
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(chat_container, orient="vertical", command=self.chat_display.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_display.configure(yscrollcommand=scrollbar.set)

        # Setup custom text tags for styling
        self._configure_text_tags()

        # 3. Quick Suggestions / Chips Toolbar
        chip_frame = tk.Frame(main_frame, bg=COLOR_BG_MAIN)
        chip_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        tk.Label(chip_frame, text="Suggestions:", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_MAIN).pack(side="left", padx=(0, 6))
        chips = [
            "What is NLP?",
            "Tell me a joke",
            "Calculate 25 * 14 + 100",
            "What time is it?",
            "Motivate me",
        ]
        for chip_text in chips:
            btn_chip = tk.Button(
                chip_frame, text=chip_text, font=self.font_small,
                bg=COLOR_BG_CONTAINER, fg=COLOR_TEXT_SECONDARY, relief="flat", bd=0, padx=8, pady=2,
                cursor="hand2", command=lambda t=chip_text: self._send_quick_prompt(t)
            )
            btn_chip.pack(side="left", padx=3)

        # 4. Input Box & Send Button
        input_container = tk.Frame(main_frame, bg=COLOR_BG_CONTAINER, padx=6, pady=6, highlightbackground=COLOR_BORDER, highlightthickness=1)
        input_container.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        input_container.columnconfigure(0, weight=1)

        self.entry_input = tk.Entry(
            input_container,
            font=self.font_input,
            bg=COLOR_BG_INPUT,
            fg=COLOR_TEXT_PRIMARY,
            insertbackground="white",
            bd=0,
            relief="flat",
        )
        self.entry_input.grid(row=0, column=0, sticky="ew", padx=(4, 8), ipady=8)
        self.entry_input.bind("<Return>", lambda event: self._on_send_message())
        self.entry_input.focus_set()

        self.btn_send = tk.Button(
            input_container,
            text="Send  ➤",
            font=self.font_msg_head,
            bg=COLOR_ACCENT,
            fg="#0f172a",
            activebackground=COLOR_ACCENT_HOVER,
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._on_send_message,
        )
        self.btn_send.grid(row=0, column=1)

        # 5. Bottom Status Bar
        self.status_bar = tk.Label(
            main_frame,
            text="Ready • Type a query or calculation",
            font=self.font_small,
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG_MAIN,
            anchor="w",
        )
        self.status_bar.grid(row=4, column=0, sticky="ew")

    def _configure_text_tags(self) -> None:
        """Define visual colors and margins for chat roles."""
        self.chat_display.tag_config("user_header", foreground=COLOR_ACCENT, font=self.font_msg_head, spacing1=10)
        self.chat_display.tag_config("user_body", foreground=COLOR_TEXT_PRIMARY, font=self.font_msg_body, lmargin1=12, lmargin2=12, spacing3=8)

        self.chat_display.tag_config("bot_header", foreground="#34d399", font=self.font_msg_head, spacing1=10)
        self.chat_display.tag_config("bot_body", foreground=COLOR_TEXT_PRIMARY, font=self.font_msg_body, lmargin1=12, lmargin2=12, spacing3=8)

        self.chat_display.tag_config("system_banner", foreground=COLOR_PURPLE, font=self.font_subtitle, justify="center", spacing1=8, spacing3=8)
        self.chat_display.tag_config("meta_tag", foreground=COLOR_TEXT_MUTED, font=self.font_small)

    def _display_welcome_message(self) -> None:
        """Render initial greeting inside chat transcript."""
        self.chat_display.configure(state="normal")
        welcome_text = (
            "✦ Welcome to NOVA AI Assistant ✦\n"
            "Ask technical questions, compute mathematical formulas, request motivation,\n"
            "or explore NLP concepts. Type 'help' for full feature instructions.\n"
        )
        self.chat_display.insert("end", welcome_text, "system_banner")
        self.chat_display.configure(state="disabled")

    def _append_message(self, message: ChatMessage) -> None:
        """Render a single message with formatted role header and content body."""
        self.chat_display.configure(state="normal")

        if message.role == "user":
            header_str = f"You  •  {message.timestamp}\n"
            self.chat_display.insert("end", header_str, "user_header")
            self.chat_display.insert("end", f"{message.content}\n\n", "user_body")
        else:
            intent_meta = f" [{message.intent}]" if message.intent else ""
            header_str = f"NOVA (AI){intent_meta}  •  {message.timestamp}\n"
            self.chat_display.insert("end", header_str, "bot_header")
            self.chat_display.insert("end", f"{message.content}\n\n", "bot_body")

        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def _on_send_message(self) -> None:
        """Handle send button action and Return key press."""
        raw_text = self.entry_input.get().strip()
        if not raw_text:
            return

        # Clear input field
        self.entry_input.delete(0, "end")

        # Disable send button momentarily
        self.btn_send.configure(state="disabled")
        self.root.update_idletasks()

        # Process through Chatbot orchestrator
        reply_message = self.chatbot.process_message(raw_text)

        # Retrieve user message and display both
        messages = self.chatbot.get_conversation_history()
        if len(messages) >= 2:
            self._append_message(messages[-2])  # User message
            self._append_message(messages[-1])  # Bot reply
        elif len(messages) == 1:
            self._append_message(messages[-1])
        else:
            # Memory reset command
            self._append_message(reply_message)

        # Update status bar
        context = self.chatbot.conversation.get_context()
        turn_count = context.get("turn_count", 0)
        user_name = context.get("user_name") or "Anonymous"
        self.status_bar.configure(
            text=f"Turn #{turn_count} • User: {user_name} • Intent: {reply_message.intent} (Conf: {reply_message.confidence:.2f})"
        )

        self.btn_send.configure(state="normal")
        self.entry_input.focus_set()

    def _send_quick_prompt(self, prompt: str) -> None:
        """Populate input and trigger send for suggestion chip."""
        self.entry_input.delete(0, "end")
        self.entry_input.insert(0, prompt)
        self._on_send_message()

    def _on_clear_chat(self) -> None:
        """Prompt confirmation and clear conversation transcript and memory."""
        if not messagebox.askyesno("Clear Conversation", "Are you sure you want to clear the conversation history?"):
            return

        self.chatbot.clear_conversation()
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self._display_welcome_message()
        self.status_bar.configure(text="Conversation memory cleared • Ready")

    def _on_export_chat(self) -> None:
        """Save dialogue transcript to chosen file."""
        filepath = filedialog.asksaveasfilename(
            title="Export Conversation Transcript",
            defaultextension=".txt",
            filetypes=[("Text File (*.txt)", "*.txt"), ("JSON (*.json)", "*.json")],
        )
        if not filepath:
            return

        if filepath.endswith(".json"):
            count = self.chatbot.conversation.export_to_json(filepath)
        else:
            count = self.chatbot.conversation.export_to_txt(filepath)

        messagebox.showinfo("Export Successful", f"Saved {count} messages to:\n{filepath}")
