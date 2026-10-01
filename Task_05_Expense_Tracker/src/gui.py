"""
Graphical User Interface for the Expense Tracker System.

Built with Python's standard Tkinter framework. Features top-level metric cards,
expense input/edit forms, filterable Treeview tables, CSV export utilities,
and an interactive Monthly Spending Report dialog.
"""

import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox, ttk
from typing import Optional

from src.models import (
    CURRENCY_SYMBOL,
    DEFAULT_CATEGORIES,
    PAYMENT_METHODS,
    Expense,
    current_date_str,
)
from src.service import ExpenseService


# Palette (Modern Dark Slate)
COLOR_BG_MAIN = "#12141a"
COLOR_BG_CARD = "#1c202a"
COLOR_BG_INPUT = "#252b38"
COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_TEXT_MUTED = "#64748b"

COLOR_ACCENT = "#38bdf8"
COLOR_ACCENT_HOVER = "#0284c7"
COLOR_SUCCESS = "#22c55e"
COLOR_DANGER = "#ef4444"
COLOR_PURPLE = "#a855f7"


class ExpenseTrackerGUI:
    """Tkinter desktop interface for tracking and analyzing personal expenses."""

    def __init__(self, root: tk.Tk, service: Optional[ExpenseService] = None):
        """Initialize Expense Tracker window, widgets, and state."""
        self.root = root
        self.service = service or ExpenseService()
        self.editing_expense_id: Optional[int] = None
        self.report_dialog: Optional[tk.Toplevel] = None

        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        self.refresh_data()

    def _setup_window(self) -> None:
        """Configure root window geometry and resizing weights."""
        self.root.title("Personal Expense Tracker & Analytics")
        self.root.geometry("960x680")
        self.root.minsize(820, 580)
        self.root.configure(bg=COLOR_BG_MAIN)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _setup_styles(self) -> None:
        """Configure ttk styles and fonts."""
        self.font_header = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.font_card_val = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        self.font_body_bold = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.font_body = tkfont.Font(family="Segoe UI", size=10)
        self.font_small = tkfont.Font(family="Segoe UI", size=9)

        # Style Treeview table for dark theme
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=COLOR_BG_CARD,
            foreground=COLOR_TEXT_PRIMARY,
            fieldbackground=COLOR_BG_CARD,
            font=self.font_body,
            rowheight=26,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=COLOR_BG_INPUT,
            foreground=COLOR_TEXT_PRIMARY,
            font=self.font_body_bold,
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", COLOR_ACCENT_HOVER)],
            foreground=[("selected", COLOR_TEXT_PRIMARY)],
        )

    def _create_widgets(self) -> None:
        """Build layout components: cards, form, filters, and table."""
        main_container = tk.Frame(self.root, bg=COLOR_BG_MAIN, padx=16, pady=14)
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.columnconfigure(0, weight=1)

        # 1. Header Bar
        header_frame = tk.Frame(main_container, bg=COLOR_BG_MAIN)
        header_frame.pack(fill="x", pady=(0, 10))

        lbl_title = tk.Label(
            header_frame,
            text="EXPENSE TRACKER & ANALYZER",
            font=self.font_header,
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_BG_MAIN,
        )
        lbl_title.pack(side="left")

        # 2. Metric Summary Cards (4 Cards)
        cards_frame = tk.Frame(main_container, bg=COLOR_BG_MAIN)
        cards_frame.pack(fill="x", pady=(0, 12))
        for col in range(4):
            cards_frame.columnconfigure(col, weight=1)

        self.lbl_card_total = self._build_card(cards_frame, 0, "Total Spending", "₹ 0.00", COLOR_ACCENT)
        self.lbl_card_month = self._build_card(cards_frame, 1, "This Month", "₹ 0.00", COLOR_SUCCESS)
        self.lbl_card_avg = self._build_card(cards_frame, 2, "Average Expense", "₹ 0.00", COLOR_PURPLE)
        self.lbl_card_highest = self._build_card(cards_frame, 3, "Highest Single", "₹ 0.00", "#f59e0b")

        # 3. Expense Input Form Frame
        form_frame = tk.LabelFrame(
            main_container,
            text=" Record New Expense ",
            font=self.font_body_bold,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            padx=12,
            pady=10,
            bd=1,
            relief="flat",
        )
        form_frame.pack(fill="x", pady=(0, 12))
        self.form_frame = form_frame

        # Form Inputs: Date, Amount, Category, Description, Payment Method
        # Row 0: Date, Amount, Category
        tk.Label(form_frame, text="Date (YYYY-MM-DD):", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_CARD).grid(row=0, column=0, sticky="w", padx=4)
        tk.Label(form_frame, text="Amount (₹):", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_CARD).grid(row=0, column=2, sticky="w", padx=4)
        tk.Label(form_frame, text="Category:", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_CARD).grid(row=0, column=3, sticky="w", padx=4)

        date_input_frame = tk.Frame(form_frame, bg=COLOR_BG_CARD)
        date_input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 6))

        self.entry_date = tk.Entry(date_input_frame, font=self.font_body, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_PRIMARY, insertbackground="white", bd=0, width=12)
        self.entry_date.pack(side="left", ipady=4)
        self.entry_date.insert(0, current_date_str())

        btn_today = tk.Button(date_input_frame, text="Today", font=self.font_small, bg=COLOR_BG_INPUT, fg=COLOR_ACCENT, bd=0, command=lambda: self._set_date_today())
        btn_today.pack(side="left", padx=4)

        self.entry_amount = tk.Entry(form_frame, font=self.font_body, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_PRIMARY, insertbackground="white", bd=0, width=12)
        self.entry_amount.grid(row=1, column=2, sticky="ew", padx=4, pady=(2, 6), ipady=4)

        self.combo_category = ttk.Combobox(form_frame, values=list(DEFAULT_CATEGORIES), font=self.font_body, state="readonly", width=18)
        self.combo_category.grid(row=1, column=3, sticky="ew", padx=4, pady=(2, 6), ipady=3)
        self.combo_category.current(0)

        # Row 1: Description, Payment Method, Buttons
        tk.Label(form_frame, text="Description / Memo:", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_CARD).grid(row=2, column=0, columnspan=2, sticky="w", padx=4)
        tk.Label(form_frame, text="Payment Method:", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_CARD).grid(row=2, column=2, sticky="w", padx=4)

        self.entry_desc = tk.Entry(form_frame, font=self.font_body, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_PRIMARY, insertbackground="white", bd=0)
        self.entry_desc.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 4), ipady=4)

        self.combo_payment = ttk.Combobox(form_frame, values=list(PAYMENT_METHODS), font=self.font_body, state="readonly", width=14)
        self.combo_payment.grid(row=3, column=2, sticky="ew", padx=4, pady=(2, 4), ipady=3)
        self.combo_payment.current(0)

        # Form action buttons
        btn_box = tk.Frame(form_frame, bg=COLOR_BG_CARD)
        btn_box.grid(row=3, column=3, sticky="e", padx=4)

        self.btn_submit = tk.Button(
            btn_box,
            text="+ Add Expense",
            font=self.font_body_bold,
            bg=COLOR_ACCENT,
            fg="#0f172a",
            activebackground=COLOR_ACCENT_HOVER,
            relief="flat",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self._on_submit_expense,
        )
        self.btn_submit.pack(side="left", padx=4)

        btn_cancel = tk.Button(
            btn_box,
            text="Clear",
            font=self.font_body,
            bg=COLOR_BG_INPUT,
            fg=COLOR_TEXT_SECONDARY,
            relief="flat",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self._clear_form,
        )
        btn_cancel.pack(side="left")

        # 4. Filter & Search Bar
        filter_frame = tk.Frame(main_container, bg=COLOR_BG_MAIN)
        filter_frame.pack(fill="x", pady=(0, 8))

        tk.Label(filter_frame, text="Filter Category:", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_MAIN).pack(side="left", padx=(0, 4))
        self.filter_category = ttk.Combobox(filter_frame, state="readonly", width=16)
        self.filter_category.pack(side="left", padx=(0, 10))
        self.filter_category.bind("<<ComboboxSelected>>", lambda e: self._on_filter_changed())

        tk.Label(filter_frame, text="Month:", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_MAIN).pack(side="left", padx=(0, 4))
        self.filter_month = ttk.Combobox(filter_frame, state="readonly", width=12)
        self.filter_month.pack(side="left", padx=(0, 10))
        self.filter_month.bind("<<ComboboxSelected>>", lambda e: self._on_filter_changed())

        tk.Label(filter_frame, text="Search:", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_MAIN).pack(side="left", padx=(0, 4))
        self.entry_search = tk.Entry(filter_frame, font=self.font_small, bg=COLOR_BG_INPUT, fg=COLOR_TEXT_PRIMARY, insertbackground="white", bd=0, width=16)
        self.entry_search.pack(side="left", ipady=3, padx=(0, 4))
        self.entry_search.bind("<KeyRelease>", lambda e: self._on_filter_changed())

        btn_reset_filter = tk.Button(
            filter_frame,
            text="Reset",
            font=self.font_small,
            bg=COLOR_BG_CARD,
            fg=COLOR_TEXT_SECONDARY,
            bd=0,
            padx=6,
            command=self._reset_filters,
        )
        btn_reset_filter.pack(side="left")

        # 5. Treeview Table Frame
        table_frame = tk.Frame(main_container, bg=COLOR_BG_CARD)
        table_frame.pack(fill="both", expand=True, pady=(0, 8))

        columns = ("id", "date", "category", "description", "payment", "amount")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID", command=lambda: self._sort_column("id", False))
        self.tree.heading("date", text="Date", command=lambda: self._sort_column("date", False))
        self.tree.heading("category", text="Category", command=lambda: self._sort_column("category", False))
        self.tree.heading("description", text="Description", command=lambda: self._sort_column("description", False))
        self.tree.heading("payment", text="Payment Method", command=lambda: self._sort_column("payment", False))
        self.tree.heading("amount", text=f"Amount ({CURRENCY_SYMBOL})", command=lambda: self._sort_column("amount", False))

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("date", width=95, anchor="center")
        self.tree.column("category", width=140, anchor="w")
        self.tree.column("description", width=260, anchor="w")
        self.tree.column("payment", width=110, anchor="center")
        self.tree.column("amount", width=100, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-Button-1>", lambda e: self._on_edit_selected())

        # 6. Action Bar (Edit, Delete, Monthly Report, Export CSV)
        action_bar = tk.Frame(main_container, bg=COLOR_BG_MAIN)
        action_bar.pack(fill="x")

        btn_edit = tk.Button(action_bar, text="Edit Selected", font=self.font_body, bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY, bd=0, padx=10, pady=4, cursor="hand2", command=self._on_edit_selected)
        btn_edit.pack(side="left", padx=(0, 6))

        btn_delete = tk.Button(action_bar, text="Delete Selected", font=self.font_body, bg=COLOR_DANGER, fg="white", bd=0, padx=10, pady=4, cursor="hand2", command=self._on_delete_selected)
        btn_delete.pack(side="left", padx=(0, 10))

        btn_report = tk.Button(action_bar, text="📊 Monthly Report", font=self.font_body_bold, bg=COLOR_PURPLE, fg="white", bd=0, padx=12, pady=4, cursor="hand2", command=self._open_monthly_report)
        btn_report.pack(side="left", padx=(0, 6))

        btn_export = tk.Button(action_bar, text="Export CSV", font=self.font_body, bg=COLOR_BG_CARD, fg=COLOR_TEXT_PRIMARY, bd=0, padx=10, pady=4, cursor="hand2", command=self._on_export_csv)
        btn_export.pack(side="left")

        self.lbl_record_count = tk.Label(action_bar, text="0 records", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_MAIN)
        self.lbl_record_count.pack(side="right")

    def _build_card(self, parent: tk.Widget, col: int, title: str, init_val: str, accent_color: str) -> tk.Label:
        """Create a metric card tile."""
        card = tk.Frame(parent, bg=COLOR_BG_CARD, padx=12, pady=10)
        card.grid(row=0, column=col, sticky="nsew", padx=4)

        lbl_title = tk.Label(card, text=title, font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_CARD)
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(card, text=init_val, font=self.font_card_val, fg=accent_color, bg=COLOR_BG_CARD)
        lbl_val.pack(anchor="w", pady=(2, 0))
        return lbl_val

    # --- Data Population & Refresh ---

    def refresh_data(self) -> None:
        """Reload all database summaries, category filters, and records."""
        # 1. Update summary cards
        summary = self.service.get_dashboard_summary()
        self.lbl_card_total.configure(text=f"{CURRENCY_SYMBOL} {summary['total_spent']:,.2f}")
        self.lbl_card_month.configure(text=f"{CURRENCY_SYMBOL} {summary['this_month_spent']:,.2f}")
        self.lbl_card_avg.configure(text=f"{CURRENCY_SYMBOL} {summary['avg_expense']:,.2f}")
        self.lbl_card_highest.configure(text=f"{CURRENCY_SYMBOL} {summary['highest_expense']:,.2f}")

        # 2. Update filter options
        categories = ["All Categories"] + self.service.get_categories()
        current_cat_sel = self.filter_category.get()
        self.filter_category["values"] = categories
        if not current_cat_sel or current_cat_sel not in categories:
            self.filter_category.current(0)

        months = ["All Months"] + self.service.get_months()
        current_month_sel = self.filter_month.get()
        self.filter_month["values"] = months
        if not current_month_sel or current_month_sel not in months:
            self.filter_month.current(0)

        # 3. Reload table records
        self._on_filter_changed()

    def _on_filter_changed(self) -> None:
        """Filter table based on current combobox and search selections."""
        cat = self.filter_category.get()
        month = self.filter_month.get()
        search = self.entry_search.get().strip()

        records = self.service.filter_expenses(
            category=cat if cat != "All Categories" else None,
            month=month if month != "All Months" else None,
            search_query=search if search else None,
        )

        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        for e in records:
            self.tree.insert(
                "",
                "end",
                iid=str(e.id),
                values=(
                    e.id,
                    e.date,
                    e.category,
                    e.description,
                    e.payment_method,
                    f"{e.amount:,.2f}",
                ),
            )

        self.lbl_record_count.configure(text=f"{len(records)} record{'s' if len(records) != 1 else ''}")

    # --- Form Actions ---

    def _set_date_today(self) -> None:
        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, current_date_str())

    def _on_submit_expense(self) -> None:
        """Validate input and save/update expense in database."""
        date_val = self.entry_date.get().strip()
        amt_val = self.entry_amount.get().strip()
        cat_val = self.combo_category.get().strip()
        desc_val = self.entry_desc.get().strip()
        pm_val = self.combo_payment.get().strip()

        try:
            amt = float(amt_val)
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid numeric amount.")
            return

        try:
            if self.editing_expense_id is None:
                # Add new expense
                self.service.add_expense(
                    date=date_val,
                    amount=amt,
                    category=cat_val,
                    description=desc_val,
                    payment_method=pm_val,
                )
            else:
                # Update existing
                self.service.update_expense(
                    expense_id=self.editing_expense_id,
                    date=date_val,
                    amount=amt,
                    category=cat_val,
                    description=desc_val,
                    payment_method=pm_val,
                )
            self._clear_form()
            self.refresh_data()
        except ValueError as err:
            messagebox.showerror("Validation Error", str(err))
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to save expense: {exc}")

    def _on_edit_selected(self) -> None:
        """Load selected row into edit form."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select an expense row to edit.")
            return

        item_id = int(selected[0])
        expense = self.service.get_expense(item_id)
        if not expense:
            return

        self.editing_expense_id = expense.id
        self.form_frame.configure(text=f" Edit Expense #{expense.id} ")
        self.btn_submit.configure(text="Save Changes", bg=COLOR_SUCCESS)

        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, expense.date)

        self.entry_amount.delete(0, tk.END)
        self.entry_amount.insert(0, f"{expense.amount:.2f}")

        if expense.category in self.combo_category["values"]:
            self.combo_category.set(expense.category)
        else:
            self.combo_category.set("Miscellaneous")

        self.entry_desc.delete(0, tk.END)
        self.entry_desc.insert(0, expense.description)

        if expense.payment_method in self.combo_payment["values"]:
            self.combo_payment.set(expense.payment_method)

    def _on_delete_selected(self) -> None:
        """Delete selected expense with confirmation."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select an expense row to delete.")
            return

        item_id = int(selected[0])
        expense = self.service.get_expense(item_id)
        if not expense:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete expense #{expense.id}?\n\n'{expense.description}' - {expense.formatted_amount}",
        )
        if confirm:
            self.service.delete_expense(item_id)
            if self.editing_expense_id == item_id:
                self._clear_form()
            self.refresh_data()

    def _clear_form(self) -> None:
        """Reset form inputs to blank defaults."""
        self.editing_expense_id = None
        self.form_frame.configure(text=" Record New Expense ")
        self.btn_submit.configure(text="+ Add Expense", bg=COLOR_ACCENT)

        self._set_date_today()
        self.entry_amount.delete(0, tk.END)
        self.combo_category.current(0)
        self.entry_desc.delete(0, tk.END)
        self.combo_payment.current(0)

    def _reset_filters(self) -> None:
        self.filter_category.current(0)
        self.filter_month.current(0)
        self.entry_search.delete(0, tk.END)
        self._on_filter_changed()

    def _sort_column(self, col: str, reverse: bool) -> None:
        """Sort Treeview rows by clicked column header."""
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]

        # Numerical sorting for ID and Amount
        if col in ("id", "amount"):
            try:
                data.sort(key=lambda t: float(t[0].replace(",", "")), reverse=reverse)
            except ValueError:
                data.sort(reverse=reverse)
        else:
            data.sort(reverse=reverse)

        for index, (_, child) in enumerate(data):
            self.tree.move(child, "", index)

        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))

    def _on_export_csv(self) -> None:
        """Export current filtered or all records to CSV."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile="expenses_export.csv",
        )
        if not filepath:
            return

        cat = self.filter_category.get()
        month = self.filter_month.get()
        search = self.entry_search.get().strip()

        records = self.service.filter_expenses(
            category=cat if cat != "All Categories" else None,
            month=month if month != "All Months" else None,
            search_query=search if search else None,
        )

        count = self.service.export_to_csv(filepath, expenses=records)
        messagebox.showinfo("Export Successful", f"Successfully exported {count} expense records to '{filepath}'.")

    # --- Monthly Report Dialog ---

    def _open_monthly_report(self) -> None:
        """Display Monthly Report window."""
        if self.report_dialog is not None and self.report_dialog.winfo_exists():
            self.report_dialog.lift()
            self.report_dialog.focus_force()
            return

        self.report_dialog = tk.Toplevel(self.root)
        self.report_dialog.title("Monthly Expense Report")
        self.report_dialog.geometry("640x520")
        self.report_dialog.minsize(560, 440)
        self.report_dialog.configure(bg=COLOR_BG_MAIN)

        container = tk.Frame(self.report_dialog, bg=COLOR_BG_MAIN, padx=14, pady=12)
        container.pack(fill="both", expand=True)

        # Header with Month selector
        top_bar = tk.Frame(container, bg=COLOR_BG_MAIN)
        top_bar.pack(fill="x", pady=(0, 10))

        tk.Label(top_bar, text="Monthly Financial Report", font=self.font_header, fg=COLOR_TEXT_PRIMARY, bg=COLOR_BG_MAIN).pack(side="left")

        months = self.service.get_months()
        if not months:
            months = [current_date_str()[:7]]

        combo_month = ttk.Combobox(top_bar, values=months, state="readonly", width=12, font=self.font_body)
        combo_month.pack(side="right")
        combo_month.current(0)

        # Month Metric Cards
        metric_frame = tk.Frame(container, bg=COLOR_BG_MAIN)
        metric_frame.pack(fill="x", pady=(0, 10))
        for c in range(3):
            metric_frame.columnconfigure(c, weight=1)

        lbl_rep_total = self._build_card(metric_frame, 0, "Monthly Total", "₹ 0.00", COLOR_ACCENT)
        lbl_rep_avg = self._build_card(metric_frame, 1, "Daily Average", "₹ 0.00", COLOR_SUCCESS)
        lbl_rep_count = self._build_card(metric_frame, 2, "Transactions", "0", COLOR_PURPLE)

        # Category Breakdown Table
        tk.Label(container, text="Category Spending Breakdown:", font=self.font_body_bold, fg=COLOR_TEXT_SECONDARY, bg=COLOR_BG_MAIN).pack(anchor="w", pady=(4, 4))

        breakdown_table_frame = tk.Frame(container, bg=COLOR_BG_CARD)
        breakdown_table_frame.pack(fill="both", expand=True, pady=(0, 10))

        rep_tree = ttk.Treeview(breakdown_table_frame, columns=("category", "total", "pct", "count"), show="headings", height=8)
        rep_tree.heading("category", text="Category")
        rep_tree.heading("total", text=f"Total ({CURRENCY_SYMBOL})")
        rep_tree.heading("pct", text="Share (%)")
        rep_tree.heading("count", text="Transactions")

        rep_tree.column("category", width=180, anchor="w")
        rep_tree.column("total", width=120, anchor="e")
        rep_tree.column("pct", width=100, anchor="e")
        rep_tree.column("count", width=100, anchor="center")

        rep_scrollbar = ttk.Scrollbar(breakdown_table_frame, orient="vertical", command=rep_tree.yview)
        rep_tree.configure(yscrollcommand=rep_scrollbar.set)
        rep_tree.pack(side="left", fill="both", expand=True)
        rep_scrollbar.pack(side="right", fill="y")

        lbl_top_cats = tk.Label(container, text="", font=self.font_small, fg=COLOR_TEXT_MUTED, bg=COLOR_BG_MAIN)
        lbl_top_cats.pack(anchor="w")

        def populate_report(month_val: str):
            rep = self.service.get_monthly_report(month_val)
            lbl_rep_total.configure(text=f"{CURRENCY_SYMBOL} {rep['total_spending']:,.2f}")
            lbl_rep_avg.configure(text=f"{CURRENCY_SYMBOL} {rep['daily_average']:,.2f}")
            lbl_rep_count.configure(text=str(rep['transaction_count']))

            for item in rep_tree.get_children():
                rep_tree.delete(item)

            for b in rep["category_breakdown"]:
                rep_tree.insert(
                    "",
                    "end",
                    values=(
                        b["category"],
                        f"{b['total']:,.2f}",
                        f"{b['percentage']:.1f} %",
                        b["count"],
                    ),
                )

            top_names = [f"{c['category']} ({c['percentage']}%)" for c in rep["top_categories"]]
            if top_names:
                lbl_top_cats.configure(text=f"Top Spending: {', '.join(top_names)}")
            else:
                lbl_top_cats.configure(text="No spending recorded for this month.")

        combo_month.bind("<<ComboboxSelected>>", lambda e: populate_report(combo_month.get()))
        populate_report(combo_month.get())
