from report_analysis.document_parser import *
from report_analysis.analysis import analyse_contract
import tkinter as tk
from tkinter import Frame, Label, Button, Text, PhotoImage, filedialog, Entry, StringVar, OptionMenu, scrolledtext, Toplevel
from report_analysis.reports import save_report
from database.database import *

LARGE_FRAME_SIZE = "1000x1000"
ERROR_SIZE = "250x80"


root = tk.Tk()
root.title("SCC Legal Compliance Software")
root.geometry(LARGE_FRAME_SIZE)
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)


anthropicFrame = Frame(root).grid(row=0, column=0, sticky='nsew')


def selectFilePath():
    types = [("Data Files", "*.pdf *.doc *.docx *.odt"), ("All Files", "*.*")]
    filePath = filedialog.askopenfilename(title="Select a File", filetypes=types)
    
    if filePath:
        filePathText.delete("1.0", "end")
        filePathText.insert("1.0", filePath)

labelTop = Label(anthropicFrame, text="Demo", font=("Arial", 26))
labelTop.place(relx=0.5, y=40, anchor='center')

labelAskQuestion = Label(anthropicFrame, text="Choose where to find the Document: ")
labelAskQuestion.place(relx=0.025, y=100)

def on_option_change(*args):
    choice = selected_option.get()

    # Hide both first
    sourceUrlLabel.place_forget()
    sourceUrlText.place_forget()
    filePathLabel.place_forget()
    filePathText.place_forget()
    filePathButton.place_forget()

    if choice == "Website":
        sourceUrlLabel.place(relx=0.025, y=140)
        sourceUrlText.place(relx=0.025, y=160)
        filePathText.delete("1.0", "end")

    elif choice == "Computer":
        filePathLabel.place(relx=0.025, y=140)
        filePathText.place(relx=0.025, y=160)
        filePathButton.place(relx=0.4, y=160)
        sourceUrlText.delete("1.0", "end")

# Dropdown variable
selected_option = StringVar(value="Website")
selected_option.trace("w", on_option_change)

# Dropdown menu
options = ["Website", "Computer"]
dropdown = OptionMenu(root, selected_option, *options)
dropdown.place(relx=0.26, y=95)

sourceUrlLabel = Label(anthropicFrame, text="Source url:")
sourceUrlLabel.place(relx=0.025, y=140)
sourceUrlText = Text(anthropicFrame, width=45, height=1)
sourceUrlText.place(relx=0.025, y=160)

filePathLabel = Label(anthropicFrame, text="File path:")
filePathText = Text(anthropicFrame, width=45, height=1)
filePathIcon = PhotoImage(file="searchFileIcon.png").subsample(8, 8)
filePathButton = Button(anthropicFrame, image=filePathIcon, command=lambda: selectFilePath(), padx=5, pady=5)
filePathButton.image = filePathIcon  

resultsScrolledText = scrolledtext.ScrolledText(anthropicFrame, width=115, height=45, bg="white")
resultsScrolledText.place(relx=0.025, y=200)

def show_findings(findings):

    resultText = ""
    for f in findings:
        resultText += (
            f"Rule ID: {f['rule_id']}\n"
            f"Outcome: {f['outcome']}\n"
            f"Clause: {f['clause_quoted'] or '(none)'}\n"
            f"Reason: {f['reason']}\n"
            f"Citation: {f['citation']}\n"
            f"Trigger: {f['trigger_phrase_matched'] or '(none)'}\n"
            + "-"*80 + "\n"
        )

    resultsScrolledText.insert("1.0", resultText)


def analyse():

    resultsScrolledText.delete("1.0", "end") 

    fileSource = None

    if selected_option.get() == "Website":
        
        fileSource = sourceUrlText.get("1.0", "end-1c")
        sourceUrlText.delete("1.0", "end")

    elif selected_option.get() == "Computer":

        fileSource = filePathText.get("1.0", "end-1c")
        filePathText.delete("1.0", "end")


    if not fileSource or not (fileSource.endswith(".pdf") or fileSource.endswith("doc") or fileSource.endswith("odt") or fileSource.endswith(".docx") or fileSource.startswith("http")):

        new_window = Toplevel(root)
        new_window.title("Error")
        new_window.geometry(ERROR_SIZE)
    
        titleLabel = Label(new_window, text="Wrong File Source — skipping analysis.", fg="red")
        titleLabel.place( relx= 0.5, rely= 0.5, anchor= 'center')

        return

    documentText = parseFile(fileSource)

    if not documentText:

        new_window = Toplevel(root)
        new_window.title("Error")
        new_window.geometry(ERROR_SIZE)
    
        titleLabel = Label(new_window, text="The text could not be extracted from the source file — skipping analysis.", fg="red")
        titleLabel.place( relx= 0.5, rely= 0.5, anchor= 'center')

        return
    
    findings = analyse_contract(documentText)
    show_findings(findings)
            
analyseButton = Button(anthropicFrame, text="Analyse", command=lambda: analyse())
analyseButton.place(relx=0.885, y=160)






root.mainloop()

