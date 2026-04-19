# THIS IS JUST A SCRATCH CODE TO LEARN HOW TKINTER WORKS

from tkinter import *

rootInsertDoc = Tk()   
rootInsertDoc.geometry("500x500")

tittleLabel = Label(rootInsertDoc, text="Insert Legal Document", font=("Arial", 16))
tittleLabel.place(x=10, y=10)


nameLabel = Label(rootInsertDoc, text="Document name:")
nameLabel.place(x=10, y=100)
nameText = Text(rootInsertDoc, width=50, height=1)
nameText.place(x=10, y=120)

jurisdictionLabel = Label(rootInsertDoc, text="Jurisdiction:")
jurisdictionLabel.place(x=10, y=150)
jurisdictionText = Text(rootInsertDoc, width=50, height=1)
jurisdictionText.place(x=10, y=170)

descriptionLabel = Label(rootInsertDoc, text="Description:")
descriptionLabel.place(x=10, y=200)
descriptionText = Text(rootInsertDoc, width=50, height=15)
descriptionText.place(x=10, y=220)

def getFrame():
    return rootInsertDoc