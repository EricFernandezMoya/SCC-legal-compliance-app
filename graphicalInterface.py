from claudeConnection import textQueryToAntropic
import tkinter as tk
from tkinter import Frame, Label, Button, Toplevel, Text, PhotoImage, filedialog
from tkcalendar import DateEntry

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
        
buttonSettingPage = Button(mainFrame, text="Go to AI Query", command=lambda: show_frame(anthropicFrame))
buttonSettingPage.pack(pady=20)

        
buttonInsertLegalDocument = Button(mainFrame, text="Insert Doc", command= lambda: insertDocWindows())
buttonInsertLegalDocument.pack(pady=20)

buttonUpdateLegalDocument = Button(mainFrame, text="Update Doc", command= lambda: updateDocWindows())
buttonUpdateLegalDocument.pack(pady=20)



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

    
    titleLabel = Label(new_window, text="Insert Legal Document", font=("Arial", 16))
    titleLabel.place(x=10, y=10)

    Label(new_window, text="Document name:").place(x=10, y=100)
    Text(new_window, width=50, height=1).place(x=10, y=120)

    Label(new_window, text="Jurisdiction:").place(x=10, y=150)
    Text(new_window, width=50, height=1).place(x=10, y=170)

    Label(new_window, text="Description:").place(x=10, y=200)
    Text(new_window, width=50, height=15).place(x=10, y=220)

def selectFilePath(filePathText, parent_window):
    types = [("Data Files", "*.pdf *.doc *.docx *.odt"), ("All Files", "*.*")]
    filePath = filedialog.askopenfilename(title="Select a File", filetypes=types)
    
    parent_window.deiconify()
    parent_window.lift()
    parent_window.focus_force()
    
    if filePath:
        filePathText.delete("1.0", "end")
        filePathText.insert("1.0", filePath)

def updateDocWindows():
    
    new_window = Toplevel(root)
    new_window.title("Insert Legal Document")
    new_window.geometry("500x500")
    new_window.transient(root)
    new_window.grab_set()
    new_window.focus_force()

    versionLabel = Label(new_window, text="Version:")
    versionLabel.place(x=10, y=100)
    versionText = Text(new_window, width=50, height=1)
    versionText.place(x=10, y=120)

    effectiveFromLabel = Label(new_window, text="Effective from:")
    effectiveFromLabel.place(x=10, y=150)
    effectiveFromDateEntry = DateEntry(new_window, width=10, background='darkblue', foreground='white', borderwidth=2)
    effectiveFromDateEntry.place(x=10, y=170)

    effectiveToLabel = Label(new_window, text="Effective to:")
    effectiveToLabel.place(x=150, y=150)
    effectiveToDateEntry = DateEntry(new_window, width=10, background='darkblue', foreground='white', borderwidth=2)
    effectiveToDateEntry.place(x=150, y=170)

    sourceUrlLabel = Label(new_window, text="Source url:")
    sourceUrlLabel.place(x=10, y=200)
    sourceUrlText = Text(new_window, width=50, height=1)
    sourceUrlText.place(x=10, y=220)

    filePathLabel = Label(new_window, text="File path:")
    filePathLabel.place(x=10, y=250)
    filePathText = Text(new_window, width=50, height=1)
    filePathText.place(x=10, y=270)
    filePathIcon = PhotoImage(file="searchFileIcon.png").subsample(8, 8)

    filePathButton = Button(new_window, image=filePathIcon, command=lambda: selectFilePath(filePathText, new_window), padx=5, pady=5)
    filePathButton.image = filePathIcon  # prevent garbage collection
    filePathButton.place(x=430, y=270)
    
    notesLabel = Label(new_window, text="Description:")
    notesLabel.place(x=10, y=300)
    notesText = Text(new_window, width=50, height=5)
    notesText.place(x=10, y=320)


root.mainloop()
