from tkinter import ttk
import tkinter as tk


class SearchableCombobox(ttk.Combobox):
    def __init__(self, master=None, **kwargs):
        
        kwargs.setdefault("style", "CustomCombobox.TCombobox")

        super().__init__(master, **kwargs)

        self._original_values = list(self["values"])
        self.bind("<KeyRelease>", self._on_keyrelease)

        comboboxStyle = ttk.Style()
        comboboxStyle.theme_use("default")
        comboboxStyle.configure(
            "CustomCombobox.TCombobox",
            fieldbackground="white",
            background="white",
            foreground="black",
        )
        comboboxStyle.map(
            "CustomCombobox.TCombobox",
            fieldbackground=[("readonly", "white"), ("!disabled", "white")],
            foreground=[("readonly", "black"), ("!disabled", "black")],
            selectbackground=[("readonly", "white"), ("!disabled", "white")],
            selectforeground=[("readonly", "black"), ("!disabled", "black")],
        )

        self.config(style="CustomCombobox.TCombobox")



    def _on_keyrelease(self, event):
        # Ignore navigation keys
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return

        typed = self.get().lower()

        # Filter values
        filtered = [v for v in self._original_values if typed in v.lower()]
        self["values"] = filtered

        if filtered:
            self.event_generate("<Down>")
            self._force_focus()

    def _force_focus(self, attempts=5):
        """Keep forcing focus back to the entry field."""
        if attempts <= 0:
            return

        self.focus_set()
        self.icursor(tk.END)

        # Try again shortly after, in case dropdown steals focus again
        self.after(20, lambda: self._force_focus(attempts - 1))
