import tkinter as tk
from tkinter import BooleanVar, Checkbutton, Frame, Label, Button, StringVar, Entry, messagebox
from tkinter import filedialog
from tkcalendar import DateEntry


from graphical_interface.widgets.searchableComboBoxClass import SearchableCombobox
from state import state
from database.database import *
from userHandling.userHandling import *
from graphical_interface.createContractGroupWindows import contractGroupWindows

from graphical_interface.graphicalInterface import (
    create_modal_window,
    closeSecondWindow,
    reset_border,
)

def openNewContractWindow():

    win = create_modal_window("Contract", size="500x600", toggle=False)
    if not win:
        return

    win.withdraw()

    Label(win, text="New Contract", font=("Arial", 16)).pack(pady=10)

    frame = Frame(win)
    frame.pack(pady=10, padx=20)

    # -----------------------------
    # CONTRACT NAME
    # -----------------------------
    Label(frame, text="Contract Name:").grid(row=0, column=0, sticky="w", pady=(10, 0))
    contractNameEntry = Entry(frame, width=40)
    contractNameEntry.grid(row=1, column=0, columnspan=2, sticky="w")

    # -----------------------------
    # CONTRACT GROUP 
    # -----------------------------
    Label(frame, text="Contract Group:").grid(row=2, column=0, sticky="w", pady=(10, 0))

    contractGroupOptions = [r[1] for r in selectAllContractGroups()]
    contractGroupSelected = StringVar()
    contractGroupCombobox = SearchableCombobox(
        frame,
        textvariable=contractGroupSelected,
        values=contractGroupOptions,
        width=30,
        state="normal"   # must be normal to allow typing
    )
    contractGroupCombobox.grid(row=3, column=0, sticky="w")
    Button(frame, text="New Group", command=lambda:contractGroupWindows()).grid(row=3, column=1, sticky="w")

    # -----------------------------
    # CONTRACT TYPE 
    # -----------------------------
    contractTypeLabel = Label(frame, text="Contract Type:")
    contractTypeLabel.grid(row=4, column=0, sticky="w", pady=(10, 0))

    contractTypeOptions = [r[1] for r in selectAllContractTypes()]
    contractTypeSelected = StringVar()
    contractTypeCombobox = SearchableCombobox(
        frame,
        textvariable=contractTypeSelected,
        values=contractTypeOptions,
        width=30,
        state="normal"   # must be normal to allow typing
    )
    contractTypeCombobox.grid(row=5, column=0, sticky="w")
    
    newContractTypeLabel = Label(frame, text="New Contract Type:")
    newContractTypeEntry = Entry(frame, width=20)

    def backNewContractType():
        newContractTypeLabel.grid_forget()
        newContractTypeEntry.grid_forget()
        backContractTypeButton.grid_forget()
        newContractTypeEntry.delete(0, "end")

        contractTypeLabel.grid(row=4, column=0, sticky="w", pady=(10, 0))
        contractTypeCombobox.grid(row=5, column=0, sticky="w")
        addContractTypeButton.grid(row=5, column=1, sticky="w")

    backContractTypeButton = Button(
        frame, text="Choose Type", command=lambda: backNewContractType()
    )

    def addNewContractType():
        contractTypeLabel.grid_forget()
        contractTypeCombobox.grid_forget()
        addContractTypeButton.grid_forget()

        newContractTypeLabel.grid(row=4, column=0, sticky="w", pady=(10, 0))
        newContractTypeEntry.grid(row=5, column=0, sticky="w")
        backContractTypeButton.grid(row=5, column=1, sticky="w")

    addContractTypeButton = Button(
        frame, text="Add New Type", command=lambda: addNewContractType()
    )
    addContractTypeButton.grid(row=5, column=1, sticky="w")

    # -----------------------------
    # VERSION NUMBER
    # -----------------------------
    Label(frame, text="Version Number:").grid(row=8, column=0, sticky="w", pady=(10, 0))
    versionEntry = Entry(frame, width=10)
    versionEntry.grid(row=9, column=0, sticky="w")

    # -----------------------------
    # FILE PATH
    # -----------------------------
    Label(frame, text="File Path:").grid(row=10, column=0, sticky="w", pady=(10, 0))
    filePathEntry = Entry(frame, width=40)
    filePathEntry.grid(row=11, column=0, sticky="w")

    def selectFilePath(parent):
        parent.lift()
        parent.attributes("-topmost", True)

        file_path = filedialog.askopenfilename(
            parent=parent,
            title="Select a document",
            filetypes=[("Document files", "*.doc *.docx *.pdf *.odt")],
        )

        parent.attributes("-topmost", False)
        parent.lift()

        if file_path:
            filePathEntry.delete(0, "end")
            filePathEntry.insert(0, file_path)

    Button(frame, text="Browse", command=lambda:selectFilePath(win)).grid(row=11, column=1, sticky="w")

    # -----------------------------
    # SOURCE URL
    # -----------------------------
    Label(frame, text="Source URL:").grid(row=12, column=0, sticky="w", pady=(10, 0))
    sourceUrlEntry = Entry(frame, width=40)
    sourceUrlEntry.grid(row=13, column=0, columnspan=2, sticky="w")

    # -----------------------------
    # PERIOD START / END
    # -----------------------------
    Label(frame, text="Period Start:").grid(row=14, column=0, sticky="w", pady=(10, 0))
    periodStartEntry = DateEntry(frame, width=12)
    periodStartEntry.grid(row=15, column=0, sticky="w")

    Label(frame, text="Period End (optional):").grid(row=14, column=0, sticky="w", pady=(10, 0), padx=(200, 0))
    periodEndEntry = DateEntry(frame, width=12)
    periodEndEntry.grid(row=15, column=0, sticky="w", padx=(200, 0))
    
    entryEffectiveToDateEntry = next(
        (
            child
            for child in periodEndEntry.winfo_children()
            if isinstance(child, tk.Entry)
        ),
        None,
    )
    periodEndEntry.config(state="disabled")
    if entryEffectiveToDateEntry:
        entryEffectiveToDateEntry.delete(0, "end")

    noEndDateVar = BooleanVar(value=True)

    def toggle_end_date():
        if noEndDateVar.get():
            periodEndEntry.config(state="disabled")
            if entryEffectiveToDateEntry:
                entryEffectiveToDateEntry.delete(0, "end")
        else:
            periodEndEntry.config(state="normal")

    noEndDateCheckButton = Checkbutton(
        frame,
        text="No Effective To",
        variable=noEndDateVar,
        command=toggle_end_date,
    )
    noEndDateCheckButton.grid(row=15, column=1, sticky="w")

# -----------------------------
# BUTTONS
# -----------------------------
    
    def save():
        name = contractNameEntry.get().strip()
        group = contractGroupSelected.get()
        
        if newContractTypeEntry.get().strip():
            ctype = newContractTypeEntry.get()
            print(ctype)
            insertContractType(ctype)
        else:
            ctype = contractTypeSelected.get()
        prev = findPreviousVersion(ctype, group)
        version_text = versionEntry.get().strip()
        file_path = filePathEntry.get().strip()
        url = sourceUrlEntry.get().strip()
        start = periodStartEntry.get_date()
        end = periodEndEntry.get_date()

        # VALIDATIONS
        if not name:
            messagebox.showwarning("Missing Information", "Contract name is required.")
            return

        if version_text and not version_text.isdigit():
            messagebox.showwarning("Invalid Version", "Version must be a number.")
            return

        version = int(version_text) if version_text else None

        group_id = selectContractGroupByName(group)[0][0]
        type_id = selectContractTypeByName(ctype)[0][0]

        insertContract(
            group_id,
            prev,
            name,
            type_id,
            version,
            file_path,
            url,
            state.current_user.get_id(),
            start,
            end
        )
        from graphical_interface.main_frame.contractsPage import load_contracts
        load_contracts()
        closeSecondWindow(win, toggle=False)

    Button(frame, text="Save", command=save, width=10).grid(row=16, column=0, sticky="e", pady=40)
    Button(frame, text="Cancel", command=lambda: closeSecondWindow(win, toggle=True), width=10).grid(row=16, column=0, sticky="w", pady=40)

    win.update_idletasks()
    win.deiconify()
    win.grab_set()