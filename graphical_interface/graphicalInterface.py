from report_analysis.claudeConnection import textQueryToAntropic  # if you use it in anthropicFrame
import tkinter as tk
from tkinter import Frame, Label, Text, Button

from state import state


LOGIN_FRAME_SIZE = "300x300"
MEDIUM_FRAME_SIZE = "500x500"
LARGE_FRAME_SIZE = "1000x1000"

root = tk.Tk()
root.title("SCC Legal")

# Layout so frames fill the space
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

logInFrame = Frame(root)
mainFrame = Frame(root)
anthropicFrame = Frame(root)

for frame in (logInFrame, mainFrame, anthropicFrame):
    frame.grid(row=0, column=0, sticky="nsew")


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

def reset_border(entry):
    if entry.get().strip():
        entry.config(highlightbackground="grey",
                     highlightcolor="grey",
                     highlightthickness=1)


def show_frame(frame, frameSize: str):
    if getSecondWindowsValue():
        return
    root.geometry(frameSize)
    root.resizable(False, False)
    frame.tkraise()


def start_app():
    # Import UI modules here to avoid circular imports
    from graphical_interface import loginWindows  # noqa: F401
    from graphical_interface import mainWindows     # noqa: F401

    show_frame(mainFrame, MEDIUM_FRAME_SIZE)
   # show_frame(logInFrame, LOGIN_FRAME_SIZE)
    root.mainloop()



#################################################################################
#                                                                               #
#                                ANTHROPIC FRAME                                #
#      building                                                                 #
#################################################################################

labelTop = Label(anthropicFrame, text="Anthropic Conection", font=("Arial", 16))
labelTop.place(relx=0.5, y=20, anchor='center')

labelAskQuestion = Label(anthropicFrame, text="Ask a question to Anthropic:")
labelAskQuestion.place(x=100, y=80)

questionText = Text(anthropicFrame,  height=15, width=100, bg="light blue")
questionText.place(relx=0.5, y=110, anchor='n')

def queryAI():
    textInput = questionText.get("1.0", "end-1c")
    textOutput = textQueryToAntropic(textInput)
    answerText.insert(tk.END, str(textOutput))

searchButton = Button(anthropicFrame, width = 20, text ="Search", command = lambda: queryAI())
searchButton.place(relx=0.5, y=390, anchor='n')

answerText = Text(anthropicFrame,height=15, width=100, bg="light blue")
answerText.place(relx=0.5, y=450, anchor='n')
        
button = Button(anthropicFrame, text="Go to Home", command=lambda: show_frame(mainFrame, MEDIUM_FRAME_SIZE))
button.place(relx=0.5, y=730, anchor='n')

