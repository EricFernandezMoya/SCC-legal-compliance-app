import tkinter as tk
from tkinter import Label, Button, Toplevel, Text, Entry, messagebox

from database.database import *
from userHandling.userHandling import *

from graphical_interface.graphicalInterface import (
    root,
    getSecondWindowsValue,
    changeSecondWindowsValue,
    closeSecondWindow,
    reset_border,
)


def contractGroupWindows():
    if getSecondWindowsValue():
        return

    changeSecondWindowsValue()

    createContractGroupFrame = Toplevel(root)
    createContractGroupFrame.geometry("450x300")
    createContractGroupFrame.transient(root)
    createContractGroupFrame.lift()
    createContractGroupFrame.attributes("-topmost", True)
    createContractGroupFrame.after(
        10, lambda: createContractGroupFrame.attributes("-topmost", False)
    )
    createContractGroupFrame.protocol(
        "WM_DELETE_WINDOW", lambda: closeSecondWindow(createContractGroupFrame)
    )

    titleLabel = Label(
        createContractGroupFrame, text="Create Contract Group", font=("Arial", 16)
    )
    titleLabel.place(relx=0.5, y=10, anchor="n")

    nameLabel = Label(createContractGroupFrame, text="Group Name:")
    nameLabel.place(x=20, y=60)
    nameEntry = Entry(createContractGroupFrame, width=35)
    nameEntry.place(x=20, y=80)
    nameEntry.bind("<KeyRelease>", lambda e: reset_border(nameEntry))

    contactDetailsLabel = Label(createContractGroupFrame, text="Contact Details:")
    contactDetailsLabel.place(x=20, y=110)
    contactDetailstText = Text(createContractGroupFrame, width=50, height=5)
    contactDetailstText.place(x=20, y=130)

    def cancelFrame():
        changeSecondWindowsValue()
        createContractGroupFrame.destroy()

    cancelButton = Button(
        createContractGroupFrame, text="Cancel", command=lambda: cancelFrame()
    )
    cancelButton.place(x=20, y=250)

    def saveContractGroup():
        contractGroup_name = nameEntry.get()
        contractGroup_detail = contactDetailstText.get("1.0", "end-1c")

        if not contractGroup_name:
            nameEntry.config(highlightbackground="red", highlightcolor="red")
            messagebox.showwarning(
                "Missing Information", "Please fill in the required field."
            )
            return

        if len(selectContractGroupByName(contractGroup_name)) == 1:
            nameEntry.config(highlightbackground="red", highlightcolor="red")
            messagebox.showwarning(
                "Duplicate Contract Group", "This Contract Group already exists."
            )
            return

        insertContractGroup(contractGroup_name, contractGroup_detail)
        changeSecondWindowsValue()
        createContractGroupFrame.destroy()

    saveButton = Button(
        createContractGroupFrame, text="Save", command=lambda: saveContractGroup()
    )
    saveButton.place(x=430, y=250, anchor="ne")
