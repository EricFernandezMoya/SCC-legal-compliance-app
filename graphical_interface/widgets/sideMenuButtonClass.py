import tkinter as tk
from graphical_interface.graphicalInterface import BG, PRIMARY, TEAL, TXT, NAV_HOVER

class FlatHoverButton(tk.Label):
    active_button = None

    def __init__(self, parent, text, command,
                 fg=BG, hover=NAV_HOVER, active_color=PRIMARY, active_hover=TEAL,
                 text_color=TXT, height=40,
                 anchor="w", font=("Arial", 14, "bold"),
                 padx=12, **kw):

        super().__init__(
            parent,
            text=text,
            bg=fg,
            fg=text_color,
            font=font,
            anchor=anchor,
            padx=padx,
            **kw
        )

        self.fg_color = fg
        self.hover_color = hover
        self.active_hover_color = active_hover
        self.active_color = active_color
        self.command = command
        self.fixed_height = height
        self.is_active = False

        # Force pixel height
        self.bind("<Configure>", self._fix_height)

        # Hover effects
        # Hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # Click
        self.bind("<Button-1>", self._on_click)


    def _fix_height(self, event):
        self.config(height=self.fixed_height)

    def _on_enter(self, event):
        if not self.is_active:
            self.config(bg=self.hover_color, fg=TXT)
        else:
            self.config(bg=self.active_hover_color, fg=BG)


    def _on_leave(self, event):
        if not self.is_active:
            self.config(bg=self.fg_color, fg=TXT)
        else:
            self.config(bg=self.active_color, fg=BG)

    def _on_click(self, event):
        # Deactivate previous active button
        if FlatHoverButton.active_button and FlatHoverButton.active_button is not self:
            FlatHoverButton.active_button.deactivate()

        # Activate this one
        self.activate()

        # Run the command
        self.command()

    def activate(self):
        self.is_active = True
        self.config(bg=self.active_color, fg=BG)
        FlatHoverButton.active_button = self

    def deactivate(self):
        self.is_active = False
        self.config(bg=self.fg_color, fg=TXT)