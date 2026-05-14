import tkinter as tk
from tkinter import Frame, Label, Text, Button, Toplevel

from state import state

PRIMARY   = "#005B8E"
TEAL      = "#00B5CC"
CARD      = "#F4F7FA"
BG        = "#FFFFFF"
SIDEBAR   = "#FFFFFF"
BORDER    = "#E5E7EB"
SHADOW    = "#D4DCE8"
TXT       = "#1A1A2E"
TXT2      = "#6B7280"
SUCCESS   = "#22C55E"
WARNING   = "#F59E0B"
ERROR     = "#EF4444"
NAV_HOVER = "#EFF6FF"


MEDIUM_FRAME_SIZE = "500x500"
LARGE_FRAME_SIZE = "1300x900"

root = tk.Tk()
logInFrame = Frame(root)
mainFrame = Frame(root)

def getSecondWindowsValue() -> bool:
    return state.second_window_open


def changeSecondWindowsValue():
    state.second_window_open = not state.second_window_open

def closeSecondWindow(frame, toggle=True):
    try:
        frame.grab_release()
    except:
        pass

    if toggle:
        changeSecondWindowsValue()

    frame.destroy()

def reset_border(entries):
    
    reset = False
    for entry in entries:
        if entry.get().strip():
            reset = True
    
    if reset:
        for entry in entries:
            entry.config(highlightbackground="grey",
                    highlightcolor="grey",
                    highlightthickness=1)


def show_frame(frame, frameSize: str):
    if getSecondWindowsValue():
        return
    root.geometry(frameSize)
    root.resizable(False, False)
    frame.tkraise()
    return root

def start_app():
    # Import UI modules here to avoid circular imports
    from graphical_interface import loginWindows

    root.title("Software Compliance Tool")

    # Layout so frames fill the space
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    loginWindows.logInFrame.grid(row=0, column=0, sticky="nsew")

    show_frame(loginWindows.logInFrame, LARGE_FRAME_SIZE)

    root.mainloop()
    
    
def create_modal_window(title, size="500x500", toggle=True):
    if toggle and getSecondWindowsValue():
        return None

    if toggle:
        changeSecondWindowsValue()

    win = Toplevel(root)
    win.withdraw()
    win.title(title)
    win.geometry(size)
    win.resizable(False, False)
    win.transient(root)

    win.protocol(
        "WM_DELETE_WINDOW",
        lambda: closeSecondWindow(win, toggle=toggle)
    )

    return win

