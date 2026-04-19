from anthropicConnection import textQueryToAntropic
import tkinter as tk
from tkinter import Frame, Label, Button, Toplevel, Text


def show_frame(frame):
    frame.tkraise()

root = tk.Tk()
root.geometry("1000x1000")
root.title("SCC Legal")

# Setup layout to make frames fill the space
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

mainFrame = Frame(root)
anthropicFrame = Frame(root)

for frame in (mainFrame, anthropicFrame ):
    frame.grid(row=0, column=0, sticky='nsew')

show_frame(mainFrame)

label = Label(mainFrame, text="Home Page", font=("Arial", 16))
label.pack(pady=20)
        
buttonSettingPage = Button(mainFrame, text="Go to Settings", command=lambda: show_frame(anthropicFrame))
buttonSettingPage.pack(pady=20)

        
buttonInsertLegalDocument = Button(mainFrame, text="Insert Doc", command= lambda: insertDocWindows())
buttonInsertLegalDocument.pack(pady=20)




labelTop = Label(anthropicFrame, text="Anthropic Conection", font=("Arial", 16))
labelTop.pack(pady=20)

labelAskQuestion = Label(anthropicFrame, text="Ask a question to the AI")
labelAskQuestion.pack(pady=20)

questionText = Text(anthropicFrame,  height=15, width=100, bg="light blue")
questionText.pack(pady=20, padx=20)

searchButton = Button(anthropicFrame, width = 20, text ="Search", command = lambda: queryAI())
searchButton.pack()

answerText = Text(anthropicFrame,height=15, width=100, bg="light blue")
answerText.pack(pady=20, padx=20)
        
button = Button(anthropicFrame, text="Go to Home", command=lambda: show_frame(mainFrame))
button.pack()

def queryAI():
    textInput = questionText.get("1.0", "end-1c")
    textOutput = textQueryToAntropic(textInput)
    answerText.insert(tk.END, textOutput)


def insertDocWindows():
                
    new_window = Toplevel(root)
    new_window.title("Insert Legal Document")
    new_window.geometry("500x500")

    
    Label(new_window, text="Insert Legal Document", font=("Arial", 16)).place(x=10, y=10)

    Label(new_window, text="Document name:").place(x=10, y=100)
    Text(new_window, width=50, height=1).place(x=10, y=120)

    Label(new_window, text="Jurisdiction:").place(x=10, y=150)
    Text(new_window, width=50, height=1).place(x=10, y=170)

    Label(new_window, text="Description:").place(x=10, y=200)
    Text(new_window, width=50, height=15).place(x=10, y=220)


root.mainloop()
