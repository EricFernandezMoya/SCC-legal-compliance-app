from tkinter import Frame, Label, Button, Text, Entry, messagebox

from database.database import selectContractGroupByName, insertContractGroup

from graphical_interface.graphicalInterface import (
    create_modal_window,
    closeSecondWindow,
    reset_border,
)


def contractGroupWindows():
    
    win = create_modal_window("Contract Group", toggle=False)
    if not win:
        return

    win.withdraw()

    Label(win, text="Create Contract Group", font=("Arial", 16)).pack(pady=10)

    createContractGroupFrame = Frame(win)
    createContractGroupFrame.pack(pady=10, padx=20)
 
    Label(createContractGroupFrame, text="Group Name:").grid(row=0, column=0, sticky="w")
    nameEntry = Entry(createContractGroupFrame, width=35)
    nameEntry.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky="w")
    nameEntry.bind("<KeyRelease>", lambda e: reset_border((nameEntry,)))

    Label(createContractGroupFrame, text="Contact Details:").grid(row=2, column=0, sticky="w")
    contactDetailstText = Text(createContractGroupFrame, width=50, height=10)
    contactDetailstText.grid(row=3, column=0, columnspan=2, pady=(0, 20))

    def cancelFrame():
        closeSecondWindow(win, toggle=False)

    cancelButton = Button(
        createContractGroupFrame, text="Cancel", command=lambda: cancelFrame(), width=10
    )
    cancelButton.grid(row=10, column=0, sticky="w", pady=20)

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
        
        closeSecondWindow(win, toggle=False)


    saveButton = Button(
        createContractGroupFrame, text="Save", command=lambda: saveContractGroup(), width=10
    )
    saveButton.grid(row=10, column=1, sticky="e", pady=20)

    win.update_idletasks()
    win.deiconify()
    win.grab_set()