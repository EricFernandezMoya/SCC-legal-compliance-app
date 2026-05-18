from tkinter import Canvas, Frame

from graphical_interface.graphicalInterface import BG, CARD, SHADOW

def make_rounded_card(parent, width=340, height=260, radius=20, bg=CARD, shadow=SHADOW, frame_color=BG):
    """
    Return (canvas, inner_frame).
    Both shadow and card have rounded corners.
    """

    canvas = Canvas(parent, width=width+6, height=height+6,
                    bg=frame_color, highlightthickness=0, bd=0)
    canvas.pack()

    def draw_rounded_rect(x1, y1, x2, y2, r, color):
        """Draw a rounded rectangle."""
        canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=color, outline=color)
        canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=color, outline=color)
        canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=color, outline=color)
        canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=color, outline=color)
        canvas.create_rectangle(x1+r, y1, x2-r, y2, fill=color, outline=color)
        canvas.create_rectangle(x1, y1+r, x2, y2-r, fill=color, outline=color)

    # Draw shadow (slightly offset)
    draw_rounded_rect(3, 3, width+3, height+3, radius, shadow)

    # Draw card (on top)
    draw_rounded_rect(0, 0, width, height, radius, bg)

    # Inner frame for widgets
    inner_frame = Frame(canvas, bg=bg)
    canvas.create_window(
        10, 10,
        window=inner_frame,
        anchor="nw",
        width=width-20,
        height=height-20
    )
    return canvas, inner_frame
