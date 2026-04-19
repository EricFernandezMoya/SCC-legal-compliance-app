from tkinter import *
from tkinter import filedialog
from tkcalendar import DateEntry


rootInsertVersion = Tk()
rootInsertVersion.geometry('1000x1000')

def selectFilePath():
    types = [("Data Files", "*.pdf *.doc *.docx *.odt"), ("All Files", "*.*")]
    filePath = filedialog.askopenfilename(title="Select a File", filetypes=types)
    if filePath:
        filePathText.delete("1.0", "end")
        filePathText.insert("1.0", filePath)
    
versionLabel = Label(rootInsertVersion, text="Version:")
versionLabel.place(x=510, y=100)
versionText = Text(rootInsertVersion, width=50, height=1)
versionText.place(x=510, y=120)

effectiveFromLabel = Label(rootInsertVersion, text="Effective from:")
effectiveFromLabel.place(x=510, y=150)
effectiveFromDateEntry = DateEntry(rootInsertVersion, width=10, background='darkblue', foreground='white', borderwidth=2)
effectiveFromDateEntry.place(x=510, y=170)

effectiveToLabel = Label(rootInsertVersion, text="Effective to:")
effectiveToLabel.place(x=650, y=150)
effectiveToDateEntry = DateEntry(rootInsertVersion, width=10, background='darkblue', foreground='white', borderwidth=2)
effectiveToDateEntry.place(x=650, y=170)

sourceUrlLabel = Label(rootInsertVersion, text="Source url:")
sourceUrlLabel.place(x=510, y=200)
sourceUrlText = Text(rootInsertVersion, width=50, height=1)
sourceUrlText.place(x=510, y=220)

filePathLabel = Label(rootInsertVersion, text="File path:")
filePathLabel.place(x=510, y=250)
filePathText = Text(rootInsertVersion, width=50, height=1)
filePathText.place(x=510, y=270)
filePathIcon = PhotoImage(file="searchFileIcon.png").subsample(8, 8)
# filePathButton = Button(root, image=filePathIcon, width=50, command=selectFilePath)
# filePathButton.place(x=920, y=270)

filePathButton = Button(rootInsertVersion, image=filePathIcon, command=selectFilePath, padx=5, pady=5)
filePathButton.place(x=920, y=270)

notesLabel = Label(rootInsertVersion, text="Description:")
notesLabel.place(x=510, y=300)
notesText = Text(rootInsertVersion, width=50, height=5)
notesText.place(x=510, y=320)




rootInsertVersion.mainloop()

