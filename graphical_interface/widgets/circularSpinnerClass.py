import tkinter as tk

class CircularSpinner(tk.Canvas):
    def __init__(self, parent, size=40, width=4, speed=5, color="#50db34"):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bg=parent["bg"])

        self.size = size
        self.width = width
        self.speed = speed
        self.color = color
        self.angle = 0
        self.running = False

        self.arc = self.create_arc(
            width, width, size - width, size - width,
            start=self.angle,
            extent=300,
            style="arc",
            outline=self.color,
            width=self.width
        )

    def start(self):
        self.running = True
        self._animate()

    def stop(self):
        self.running = False

    def _animate(self):
        if not self.running:
            return

        self.angle = (self.angle + self.speed) % 360
        self.itemconfig(self.arc, start=self.angle)

        self.after(20, self._animate)
