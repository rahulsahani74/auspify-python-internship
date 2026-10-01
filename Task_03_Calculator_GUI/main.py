"""
Main entry point for Task 03: Calculator with GUI.

Initializes the Tkinter root window and launches the Calculator application.
"""

import sys
import tkinter as tk
from src.gui import CalculatorGUI


def main() -> None:
    """Launch the Calculator GUI application."""
    root = tk.Tk()

    # Center window on screen
    window_width = 380
    window_height = 560
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    pos_x = max(0, int((screen_width - window_width) / 2))
    pos_y = max(0, int((screen_height - window_height) / 2))
    root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    # Initialize GUI application
    app = CalculatorGUI(root)

    # Start main event loop
    root.mainloop()


if __name__ == "__main__":
    main()
