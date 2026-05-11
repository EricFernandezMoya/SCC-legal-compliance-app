from tkinter import (
    Frame,
    Label,
    Button,
    StringVar,
    Text,
    Entry,
    messagebox,
)
from tkinter import ttk
from datetime import datetime

from database.database import (
    selectDocumentByName, 
    insertDocument, 
    insertDocumentType, 
    selectDocumentTypeByName, 
    selectAllDocumentTypeNames
)
from state import state

from graphical_interface.graphicalInterface import (
    root,
    closeSecondWindow,
    reset_border,
    create_modal_window,
)


def openNewLegalDocument():

    win = create_modal_window("Legal Document", toggle=False)
    if not win:
        return

    win.withdraw()

    Label(win, text="New Legal Document", font=("Arial", 16)).pack(pady=10)

    frame = Frame(win)
    frame.pack(pady=10, padx=20)

    # --- Name ---
    Label(frame, text="Document name:").grid(row=0, column=0, sticky="w")
    nameEntry = Entry(frame, width=40)
    nameEntry.bind("<KeyRelease>", lambda e: reset_border((nameEntry,)))
    nameEntry.grid(row=1, column=0, columnspan=2, pady=5)

    # --- Year ---
    def validate_four_digits(text):
        return (text.isdigit() and len(text) <= 4) or text == ""

    vcmd = root.register(validate_four_digits)
    Label(frame, text="Year:").grid(row=2, column=0, sticky="w")
    yearEntry = Entry(frame, width=10, validate="key", validatecommand=(vcmd, "%P"))
    yearEntry.bind("<KeyRelease>", lambda e: reset_border((yearEntry,)))
    yearEntry.grid(row=3, column=0, sticky="w")

    # --- Jurisdiction ---
    Label(frame, text="Jurisdiction:").grid(row=4, column=0, sticky="w")
    jurisdictionEntry = Entry(frame, width=40)
    jurisdictionEntry.grid(row=5, column=0, columnspan=2, pady=5)

    # --- Description ---
    Label(frame, text="Description:").grid(row=6, column=0, sticky="w")
    descriptionText = Text(frame, width=40, height=5)
    descriptionText.grid(row=7, column=0, columnspan=2)

    # --- Document Type (existing + new) ---
    documentTypeLabel = Label(frame, text="Document Type:")
    documentTypeLabel.grid(row=8, column=0, sticky="w", pady=(10, 0))
    
    documentTypeComboboxStyle = ttk.Style()
    documentTypeComboboxStyle.theme_use("default")
    documentTypeComboboxStyle.configure(
        "CustomCombobox.TCombobox",
        fieldbackground="white",
        background="white",
        foreground="black",
    )
    documentTypeComboboxStyle.map(
        "CustomCombobox.TCombobox",
        fieldbackground=[("readonly", "white"), ("!disabled", "white")],
        foreground=[("readonly", "black"), ("!disabled", "black")],
        selectbackground=[("readonly", "white"), ("!disabled", "white")],
        selectforeground=[("readonly", "black"), ("!disabled", "black")],
    )
    
    documentTypeOptions = [r[0] for r in selectAllDocumentTypeNames()]
    documentTypeSelectedValue = StringVar(value=documentTypeOptions[0])
    documentTypeCombobox = ttk.Combobox(
        frame,
        textvariable=documentTypeSelectedValue,
        values=documentTypeOptions,
        state="readonly",
        style="CustomCombobox.TCombobox",
    )
    documentTypeCombobox.grid(row=9, column=0, sticky="w")

    newDocumentTypeLabel = Label(frame, text="New Document Type:")
    newDocumentTypeEntry = Entry(frame, width=20)

    def backNewDocumentType():
        newDocumentTypeLabel.grid_forget()
        newDocumentTypeEntry.grid_forget()
        backDocumentTypeButton.grid_forget()
        newDocumentTypeEntry.delete(0, "end")

        documentTypeLabel.grid(row=8, column=0, sticky="w", pady=(10, 0))
        documentTypeCombobox.grid(row=9, column=0, sticky="w")
        addDocumentTypeButton.grid(row=9, column=1, sticky="w")

    backDocumentTypeButton = Button(
        frame, text="Choose Type", command=lambda: backNewDocumentType()
    )

    def addNewDocumentType():
        documentTypeLabel.grid_forget()
        documentTypeCombobox.grid_forget()
        addDocumentTypeButton.grid_forget()

        newDocumentTypeLabel.grid(row=8, column=0, sticky="w", pady=(10, 0))
        newDocumentTypeEntry.grid(row=9, column=0, sticky="w")
        backDocumentTypeButton.grid(row=9, column=1, sticky="w")

    addDocumentTypeButton = Button(
        frame, text="Add New Type", command=lambda: addNewDocumentType()
    )
    addDocumentTypeButton.grid(row=9, column=1, sticky="w")

    def save():
        name = nameEntry.get().strip()
        jur = jurisdictionEntry.get().strip()
        year_text = yearEntry.get().strip()
        desc = descriptionText.get("1.0", "end-1c").strip()

        # decide type
        if newDocumentTypeEntry.get().strip():
            doc_type = newDocumentTypeEntry.get().strip()
        else:
            doc_type = documentTypeSelectedValue.get()

        # --- VALIDATIONS ---

        # required name
        if not name:
            messagebox.showwarning("Missing Information", "Please fill in the required field.")
            nameEntry.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
            return

        # duplicate name
        if len(selectDocumentByName(name)) == 1:
            messagebox.showwarning("Duplicate Document", "This document already exists.")
            nameEntry.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
            return

        # year validation
        year = None
        if year_text:
            if not year_text.isdigit() or len(year_text) != 4:
                messagebox.showwarning("Invalid Year", "Please enter a valid 4-digit year.")
                yearEntry.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
                return
            year = int(year_text)
            if not (1800 <= year <= datetime.now().year):
                messagebox.showwarning("Invalid Year", "Please enter a valid year.")
                yearEntry.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
                return

        # insert new type if needed
        if newDocumentTypeEntry.get().strip():
            insertDocumentType(doc_type)

        # insert document
        insertDocument(
            name,
            jur,
            year,
            desc,
            selectDocumentTypeByName(doc_type)[0][0],
        )
        from graphical_interface.mainWindows import load_documents
        load_documents()
        state.selected_document_name = name
        
        closeSecondWindow(win, toggle=False)

        from graphical_interface.createDocumentVersionWindows import documentNameOptions, documentNameCombobox
        documentNameOptions.append(name)
        documentNameCombobox["values"] = documentNameOptions
        documentNameCombobox.set(name)


    Button(frame, text="Save", command=save, width=10).grid(row=10, column=1, sticky="e", pady=20)
    Button(frame, text="Cancel", command=lambda: closeSecondWindow(win, toggle=True), width=10).grid(row=10, column=0, sticky="w", pady=20)

    win.update_idletasks()
    win.deiconify()
    win.grab_set()

