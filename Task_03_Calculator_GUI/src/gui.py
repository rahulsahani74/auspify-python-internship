"""
Graphical User Interface for the Calculator Application.

Built with Python's built-in Tkinter framework. Implements a responsive,
modern dual-line display, organized keypad, calculation history panel,
division-by-zero alerts, and full keyboard binding integration.
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from typing import Optional

from src.engine import CalculatorEngine


# Visual Color Palette (Modern Dark Theme)
COLOR_BG_MAIN = "#1a1a1e"
COLOR_BG_DISPLAY = "#222228"
COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_SECONDARY = "#8e8e98"
COLOR_TEXT_ERROR = "#ff5c5c"

# Button color themes
BTN_NUM_BG = "#2c2c34"
BTN_NUM_FG = "#ffffff"
BTN_NUM_ACTIVE = "#3e3e4a"

BTN_OP_BG = "#2a3b5c"
BTN_OP_FG = "#80b5ff"
BTN_OP_ACTIVE = "#364d78"

BTN_FN_BG = "#353540"
BTN_FN_FG = "#dcdce4"
BTN_FN_ACTIVE = "#454554"

BTN_EQUAL_BG = "#2563eb"
BTN_EQUAL_FG = "#ffffff"
BTN_EQUAL_ACTIVE = "#1d4ed8"

BTN_CLEAR_BG = "#7f1d1d"
BTN_CLEAR_FG = "#fca5a5"
BTN_CLEAR_ACTIVE = "#991b1b"


class CalculatorGUI:
    """Tkinter-based Graphical User Interface for the Calculator."""

    def __init__(self, root: tk.Tk):
        """Initialize calculator window, widgets, and key bindings.

        Args:
            root: The root Tkinter window.
        """
        self.root = root
        self.engine = CalculatorEngine()
        self.history_window: Optional[tk.Toplevel] = None

        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        self._bind_keyboard()
        self._update_display()

    def _setup_window(self) -> None:
        """Configure root window properties."""
        self.root.title("Modern Calculator")
        self.root.geometry("380x560")
        self.root.minsize(340, 500)
        self.root.configure(bg=COLOR_BG_MAIN)

        # Allow resizing to expand proportionally
        self.root.rowconfigure(0, weight=0)  # Top bar
        self.root.rowconfigure(1, weight=2)  # Display area
        self.root.rowconfigure(2, weight=6)  # Keypad area
        self.root.columnconfigure(0, weight=1)

    def _setup_styles(self) -> None:
        """Configure typography and custom font assets."""
        self.font_display = tkfont.Font(family="Segoe UI", size=24, weight="bold")
        self.font_sub_display = tkfont.Font(family="Segoe UI", size=11)
        self.font_btn = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        self.font_btn_fn = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.font_status = tkfont.Font(family="Segoe UI", size=9)

    def _create_widgets(self) -> None:
        """Create header, dynamic displays, and keypad button grid."""
        # --- Top Menu / Action Bar ---
        top_bar = tk.Frame(self.root, bg=COLOR_BG_MAIN)
        top_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        top_bar.columnconfigure(0, weight=1)
        top_bar.columnconfigure(1, weight=0)

        app_title = tk.Label(
            top_bar,
            text="CALCULATOR",
            font=self.font_status,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
        )
        app_title.grid(row=0, column=0, sticky="w")

        btn_history = tk.Button(
            top_bar,
            text="History ⏱",
            font=self.font_status,
            bg=BTN_FN_BG,
            fg=COLOR_TEXT_SECONDARY,
            activebackground=BTN_FN_ACTIVE,
            activeforeground=COLOR_TEXT_PRIMARY,
            relief="flat",
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self._toggle_history_window,
        )
        btn_history.grid(row=0, column=1, sticky="e")

        # --- Dynamic Display Area ---
        display_frame = tk.Frame(self.root, bg=COLOR_BG_DISPLAY, bd=0, relief="flat")
        display_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=6)
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(0, weight=1)
        display_frame.rowconfigure(1, weight=2)
        display_frame.rowconfigure(2, weight=1)

        # Secondary expression line (shows previous calculation or expression)
        self.sub_display_var = tk.StringVar(value="")
        self.lbl_sub_display = tk.Label(
            display_frame,
            textvariable=self.sub_display_var,
            font=self.font_sub_display,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_DISPLAY,
            anchor="e",
            padx=12,
            pady=2,
        )
        self.lbl_sub_display.grid(row=0, column=0, sticky="ew")

        # Primary input / result line
        self.main_display_var = tk.StringVar(value="0")
        self.lbl_main_display = tk.Label(
            display_frame,
            textvariable=self.main_display_var,
            font=self.font_display,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_DISPLAY,
            anchor="e",
            padx=12,
            pady=4,
        )
        self.lbl_main_display.grid(row=1, column=0, sticky="ew")

        # Status / Error line
        self.status_var = tk.StringVar(value="")
        self.lbl_status = tk.Label(
            display_frame,
            textvariable=self.status_var,
            font=self.font_status,
            fg=COLOR_TEXT_ERROR,
            bg=COLOR_BG_DISPLAY,
            anchor="e",
            padx=12,
            pady=2,
        )
        self.lbl_status.grid(row=2, column=0, sticky="ew")

        # --- Keypad Grid ---
        keypad_frame = tk.Frame(self.root, bg=COLOR_BG_MAIN)
        keypad_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=8)

        # 6 rows, 4 columns
        for c in range(4):
            keypad_frame.columnconfigure(c, weight=1)
        for r in range(6):
            keypad_frame.rowconfigure(r, weight=1)

        # Button Layout: (text, row, col, type, command)
        buttons_spec = [
            # Row 0: Scientific / Utility helpers
            ("(", 0, 0, "fn", lambda: self._on_paren("(")),
            (")", 0, 1, "fn", lambda: self._on_paren(")")),
            ("^", 0, 2, "fn", lambda: self._on_operator("^")),
            ("√", 0, 3, "fn", self._on_sqrt),

            # Row 1: Clear & Deletion
            ("C", 1, 0, "clear", self._on_clear),
            ("CE", 1, 1, "clear", self._on_clear_entry),
            ("%", 1, 2, "fn", self._on_percent),
            ("÷", 1, 3, "op", lambda: self._on_operator("÷")),

            # Row 2: 7, 8, 9, ×
            ("7", 2, 0, "num", lambda: self._on_digit("7")),
            ("8", 2, 1, "num", lambda: self._on_digit("8")),
            ("9", 2, 2, "num", lambda: self._on_digit("9")),
            ("×", 2, 3, "op", lambda: self._on_operator("×")),

            # Row 3: 4, 5, 6, −
            ("4", 3, 0, "num", lambda: self._on_digit("4")),
            ("5", 3, 1, "num", lambda: self._on_digit("5")),
            ("6", 3, 2, "num", lambda: self._on_digit("6")),
            ("−", 3, 3, "op", lambda: self._on_operator("-")),

            # Row 4: 1, 2, 3, +
            ("1", 4, 0, "num", lambda: self._on_digit("1")),
            ("2", 4, 1, "num", lambda: self._on_digit("2")),
            ("3", 4, 2, "num", lambda: self._on_digit("3")),
            ("+", 4, 3, "op", lambda: self._on_operator("+")),

            # Row 5: ±, 0, ., =
            ("±", 5, 0, "fn", self._on_toggle_sign),
            ("0", 5, 1, "num", lambda: self._on_digit("0")),
            (".", 5, 2, "num", self._on_decimal),
            ("=", 5, 3, "equal", self._on_equal),
        ]

        # Add Backspace overlay at row 1 col 1 alternative or corner
        # We also create a dedicated Backspace button in keypad
        # Let's replace CE or put Backspace on row 1 col 1:
        # Better: Row 1 is C, ⌫, %, ÷
        buttons_spec[5] = ("⌫", 1, 1, "clear", self._on_backspace)

        for text, r, c, btn_type, cmd in buttons_spec:
            btn = self._build_button(keypad_frame, text, btn_type, cmd)
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

    def _build_button(self, parent: tk.Widget, text: str, btn_type: str, command) -> tk.Button:
        """Create a consistently styled button based on its category."""
        if btn_type == "num":
            bg, fg, active = BTN_NUM_BG, BTN_NUM_FG, BTN_NUM_ACTIVE
            font = self.font_btn
        elif btn_type == "op":
            bg, fg, active = BTN_OP_BG, BTN_OP_FG, BTN_OP_ACTIVE
            font = self.font_btn
        elif btn_type == "equal":
            bg, fg, active = BTN_EQUAL_BG, BTN_EQUAL_FG, BTN_EQUAL_ACTIVE
            font = self.font_btn
        elif btn_type == "clear":
            bg, fg, active = BTN_CLEAR_BG, BTN_CLEAR_FG, BTN_CLEAR_ACTIVE
            font = self.font_btn
        else:  # "fn"
            bg, fg, active = BTN_FN_BG, BTN_FN_FG, BTN_FN_ACTIVE
            font = self.font_btn_fn

        return tk.Button(
            parent,
            text=text,
            font=font,
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=fg,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=command,
        )

    def _bind_keyboard(self) -> None:
        """Bind physical keyboard keys to calculator actions."""
        for num in range(10):
            self.root.bind(str(num), lambda e, n=str(num): self._on_digit(n))

        self.root.bind(".", lambda e: self._on_decimal())
        self.root.bind("+", lambda e: self._on_operator("+"))
        self.root.bind("-", lambda e: self._on_operator("-"))
        self.root.bind("*", lambda e: self._on_operator("×"))
        self.root.bind("/", lambda e: self._on_operator("÷"))
        self.root.bind("^", lambda e: self._on_operator("^"))
        self.root.bind("%", lambda e: self._on_percent())
        self.root.bind("(", lambda e: self._on_paren("("))
        self.root.bind(")", lambda e: self._on_paren(")"))

        self.root.bind("<Return>", lambda e: self._on_equal())
        self.root.bind("<KP_Enter>", lambda e: self._on_equal())
        self.root.bind("=", lambda e: self._on_equal())

        self.root.bind("<BackSpace>", lambda e: self._on_backspace())
        self.root.bind("<Escape>", lambda e: self._on_clear())
        self.root.bind("<Delete>", lambda e: self._on_clear())

    # --- Button Handler Methods ---

    def _on_digit(self, digit: str) -> None:
        self.status_var.set("")
        self.engine.input_digit(digit)
        self._update_display()

    def _on_decimal(self) -> None:
        self.status_var.set("")
        self.engine.input_decimal()
        self._update_display()

    def _on_operator(self, op: str) -> None:
        self.status_var.set("")
        self.engine.input_operator(op)
        self._update_display()

    def _on_paren(self, paren: str) -> None:
        self.status_var.set("")
        self.engine.input_parenthesis(paren)
        self._update_display()

    def _on_percent(self) -> None:
        self.status_var.set("")
        self.engine.input_percentage()
        self._update_display()

    def _on_toggle_sign(self) -> None:
        self.status_var.set("")
        self.engine.toggle_sign()
        self._update_display()

    def _on_sqrt(self) -> None:
        self.status_var.set("")
        expr_before = self.engine.expression or "0"
        result, error = self.engine.square_root()
        if error:
            self.status_var.set(f"Error: {error}")
        else:
            self.sub_display_var.set(f"√({expr_before}) =")
            self._update_display()

    def _on_backspace(self) -> None:
        self.status_var.set("")
        self.engine.backspace()
        self._update_display()

    def _on_clear(self) -> None:
        self.status_var.set("")
        self.sub_display_var.set("")
        self.engine.clear()
        self._update_display()

    def _on_clear_entry(self) -> None:
        self.status_var.set("")
        self.engine.clear_entry()
        self._update_display()

    def _on_equal(self) -> None:
        expr_before = self.engine.expression
        if not expr_before:
            return

        result, error = self.engine.calculate()
        if error:
            self.status_var.set(f"Error: {error}")
        else:
            self.status_var.set("")
            self.sub_display_var.set(f"{expr_before} =")
            self._update_display()
            self._refresh_history_if_open()

    def _update_display(self) -> None:
        """Synchronize UI display label with calculator engine expression."""
        current_expr = self.engine.expression
        if not current_expr:
            self.main_display_var.set("0")
        else:
            # Dynamically adjust font size if expression gets long
            if len(current_expr) > 18:
                self.font_display.configure(size=16)
            elif len(current_expr) > 12:
                self.font_display.configure(size=20)
            else:
                self.font_display.configure(size=24)
            self.main_display_var.set(current_expr)

    # --- History Window ---

    def _toggle_history_window(self) -> None:
        """Open or focus the calculation history dialog."""
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.lift()
            self.history_window.focus_force()
            return

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("Calculation History")
        self.history_window.geometry("320x420")
        self.history_window.minsize(280, 300)
        self.history_window.configure(bg=COLOR_BG_MAIN)

        lbl_header = tk.Label(
            self.history_window,
            text="Calculation History",
            font=self.font_btn_fn,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
            pady=8,
        )
        lbl_header.pack(fill="x")

        # Frame with Listbox & Scrollbar
        list_frame = tk.Frame(self.history_window, bg=COLOR_BG_MAIN)
        list_frame.pack(fill="both", expand=True, padx=12, pady=4)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.history_listbox = tk.Listbox(
            list_frame,
            font=self.font_sub_display,
            bg=COLOR_BG_DISPLAY,
            fg=COLOR_TEXT_PRIMARY,
            selectbackground=BTN_OP_ACTIVE,
            selectforeground=COLOR_TEXT_PRIMARY,
            bd=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
        )
        self.history_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_listbox.yview)

        # Instructions
        lbl_hint = tk.Label(
            self.history_window,
            text="Double-click an item to load into calculator",
            font=self.font_status,
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_BG_MAIN,
            pady=4,
        )
        lbl_hint.pack(fill="x")

        # Bottom buttons (Use Result, Clear History)
        btn_frame = tk.Frame(self.history_window, bg=COLOR_BG_MAIN)
        btn_frame.pack(fill="x", padx=12, pady=8)

        btn_load = tk.Button(
            btn_frame,
            text="Use Result",
            font=self.font_status,
            bg=BTN_OP_BG,
            fg=BTN_OP_FG,
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            command=self._use_selected_history_item,
        )
        btn_load.pack(side="left", expand=True, fill="x", padx=(0, 4))

        btn_clear_hist = tk.Button(
            btn_frame,
            text="Clear All",
            font=self.font_status,
            bg=BTN_CLEAR_BG,
            fg=BTN_CLEAR_FG,
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            command=self._clear_history_list,
        )
        btn_clear_hist.pack(side="right", expand=True, fill="x", padx=(4, 0))

        self.history_listbox.bind("<Double-Button-1>", lambda e: self._use_selected_history_item())

        self._populate_history()

    def _populate_history(self) -> None:
        """Fill history listbox with recorded items."""
        if not hasattr(self, "history_listbox") or not self.history_listbox.winfo_exists():
            return
        self.history_listbox.delete(0, tk.END)
        records = self.engine.history
        if not records:
            self.history_listbox.insert(tk.END, "  (No calculations yet)")
            return

        for rec in reversed(records):
            item_text = f"[{rec.timestamp}] {rec.expression} = {rec.result}"
            self.history_listbox.insert(tk.END, item_text)

    def _refresh_history_if_open(self) -> None:
        """Update history listbox dynamically if dialog is open."""
        if self.history_window is not None and self.history_window.winfo_exists():
            self._populate_history()

    def _use_selected_history_item(self) -> None:
        """Load result from selected history row into calculator engine."""
        if not hasattr(self, "history_listbox") or not self.history_listbox.winfo_exists():
            return
        selection = self.history_listbox.curselection()
        if not selection:
            return

        selected_idx = selection[0]
        records = list(reversed(self.engine.history))
        if selected_idx < len(records):
            rec = records[selected_idx]
            self.engine.set_expression(rec.result)
            self.sub_display_var.set(f"Loaded: {rec.expression}")
            self._update_display()
            self.history_window.destroy()

    def _clear_history_list(self) -> None:
        """Clear all history in engine and view."""
        self.engine.clear_history()
        self._populate_history()
