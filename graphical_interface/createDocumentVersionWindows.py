import tkinter as tk
from tkinter import (
    BooleanVar,
    Checkbutton,
    Frame,
    Label,
    Button,
    StringVar,
    Text,
    filedialog,
    Entry,
    messagebox,
)
from tkinter import ttk
from tkcalendar import DateEntry


from graphical_interface.widgets.searchableComboBoxClass import SearchableCombobox
from graphical_interface.createDocumentWindows import openNewLegalDocument
from database.database import (
    selectDocumentByName, 
    insertDocumentVersion, 
    selectAllDocuments
)
from state import state

from graphical_interface.graphicalInterface import (
    closeSecondWindow,
    reset_border,
    create_modal_window,
)

def openCreateDocumentVersionWindows():
    global documentNameCombobox, documentNameOptions

    state.selected_document_name = ""

    win = create_modal_window("Legal Document", size="500x620", toggle=True)
    if not win:
        return

    win.withdraw

    frame = Frame(win)
    frame.pack(fill="both", expand=True, padx=20, pady=20)

    Label(frame, text="New Document Version", font=("Arial", 16)).grid(row=0, column=0, columnspan=3, pady=(0, 30))

    # --- Document Name ---
    documentLabel = Label(frame, text="Document: " + state.selected_document_name)
    documentLabel.grid(row=1, column=0, sticky="w", pady=(10, 0))

    documentNameOptions = [r[1] for r in selectAllDocuments()]
    documentNameSelected = StringVar()
    
    documentNameCombobox = SearchableCombobox(
        frame,
        textvariable=documentNameSelected,
        values=documentNameOptions,
        width=35,
        state="normal"
    )
    documentNameCombobox.grid(row=2, column=0, sticky="w")

    Button(frame, text="New", command=lambda: openNewLegalDocument()).grid(row=2, column=1, sticky="w", pady=10)

    # --- Version ---
    Label(frame, text="Version:").grid(row=3, column=0, sticky="w", pady=(10, 0))
    versionEntry = Entry(frame, width=20)
    versionEntry.grid(row=4, column=0, columnspan=2, sticky="w")

    # --- Effective Dates ---
    Label(frame, text="Effective From:").grid(row=5, column=0, sticky="w", pady=(10, 0))
    fromDate = DateEntry(frame, width=10)
    fromDate.grid(row=6, column=0, sticky="w")

    Label(frame, text="Effective To:").grid(row=5, column=0, sticky="e", pady=(10, 0), padx=18)
    toDate = DateEntry(frame, width=10)
    toDate.grid(row=6, column=0, sticky="e")

    entryEffectiveToDateEntry = next(
        (
            child
            for child in toDate.winfo_children()
            if isinstance(child, tk.Entry)
        ),
        None,
    )
    toDate.config(state="disabled")
    if entryEffectiveToDateEntry:
        entryEffectiveToDateEntry.delete(0, "end")

    noEndDateVar = BooleanVar(value=True)

    def toggle_end_date():
        if noEndDateVar.get():
            toDate.config(state="disabled")
            if entryEffectiveToDateEntry:
                entryEffectiveToDateEntry.delete(0, "end")
        else:
            toDate.config(state="normal")

    noEndDateCheckButton = Checkbutton(
        frame,
        text="No Effective To",
        variable=noEndDateVar,
        command=toggle_end_date,
    )
    noEndDateCheckButton.grid(row=6, column=1, sticky="w")

    # --- Source Url ---
    Label(frame, text="Source url:").grid(row=7, column=0, sticky="w", pady=(10, 0))
    sourceUrlEntry = Entry(frame, width=40)
    sourceUrlEntry.bind("<KeyRelease>", lambda e: reset_border((filePathEntry, sourceUrlEntry)))
    sourceUrlEntry.grid(row=8, column=0, columnspan=2, sticky="w")

    # --- File Path ---
    Label(frame, text="File path:").grid(row=9, column=0, sticky="w", pady=(10, 0))
    filePathEntry = Entry(frame, width=40)
    filePathEntry.bind("<KeyRelease>", lambda e: reset_border((filePathEntry, sourceUrlEntry)))
    filePathEntry.grid(row=10, column=0, columnspan=2, sticky="w")

    def selectFilePath(parent):
        parent.lift()
        parent.attributes("-topmost", True)

        reset_border((filePathEntry, sourceUrlEntry))
        
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
    
    filePathButton = Button(frame, text="Browse", command=lambda:selectFilePath(win))
    filePathButton.grid(row=10, column=1, sticky="e")
    

    # --- Notes ---
    Label(frame, text="Notes:").grid(row=11, column=0, sticky="w", pady=(10, 0))
    notesText = Text(frame, width=50, height=5)
    notesText.grid(row=12, column=0, columnspan=2)

    # --- Save ---
    def save():

        if not state.selected_document_name and not documentNameSelected.get().strip():
            messagebox.showwarning("Missing Information", "Please, select or add a document.")
            return
        
        if not sourceUrlEntry.get().strip() and not filePathEntry.get().strip():
            messagebox.showwarning("Missing Information", "Please, add source url or file path.")
            filePathEntry.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
            sourceUrlEntry.config(highlightbackground="red", highlightcolor="red", highlightthickness=2)
            return
        
        if state.selected_document_name:
            document_id = selectDocumentByName(state.selected_document_name)[0][0]
        else:
            if documentNameSelected.get().strip() in documentNameOptions:
                document_id = selectDocumentByName(documentNameSelected.get().strip())[0][0]
            else:
                messagebox.showwarning("Wrong Entry", "Please, select one of the Documents available.")
                return

        insertDocumentVersion(
            document_id,
            versionEntry.get().strip(),
            fromDate.get_date(),
            toDate.get_date(),
            sourceUrlEntry.get().strip(),
            filePathEntry.get().strip(), 
            notesText.get("1.0", "end-1c")
        )
        state.selected_document_name = ""
        from graphical_interface.main_frame.legislationPage import load_legislation_data
        load_legislation_data()
        closeSecondWindow(win, toggle=True)

    Button(frame, text="Save", command=save, width=10).grid(row=13, column=1, sticky="e", pady=10)
    Button(frame, text="Cancel", command=lambda: closeSecondWindow(win, toggle=True), width=10).grid(row=13, column=0, sticky="w", pady=10)

    win.update_idletasks()
    win.deiconify()
    win.grab_set()
