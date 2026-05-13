import tkinter as tk
from tkinter import (
    BooleanVar,
    Checkbutton,
    Frame,
    Label,
    Button,
    Listbox,
    StringVar,
    Toplevel,
    Text,
    PhotoImage,
    filedialog,
    Entry,
    messagebox,
)
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime

from userHandling.userHandling import *
from database.database import *
from state import state

from graphical_interface.graphicalInterface import (
    root,
    getSecondWindowsValue,
    changeSecondWindowsValue,
    closeSecondWindow,
    reset_border,
)

filePathIcon = PhotoImage(file="iconImages/searchFileIcon.png").subsample(8, 8)


def documentWindows(option, document_id):
    if getSecondWindowsValue():
        return

    changeSecondWindowsValue()

    documentFrame = Toplevel(root)
    documentFrame.title("Legal Document")
    documentFrame.geometry("500x500")
    documentFrame.transient(root)
    documentFrame.lift()
    documentFrame.attributes("-topmost", True)
    documentFrame.after(10, lambda: documentFrame.attributes("-topmost", False))
    documentFrame.protocol(
        "WM_DELETE_WINDOW", lambda: closeSecondWindow(documentFrame, toggle=True)
    )

    # -------------------------------------------------------------------------
    # New legal document frame
    # -------------------------------------------------------------------------
    newLegalDocumentFrame = Frame(documentFrame)

    titleLabel = Label(newLegalDocumentFrame, text="New Legal Document", font=("Arial", 16))
    titleLabel.place(relx=0.5, y=10, anchor="n")

    nameLabel = Label(newLegalDocumentFrame, text="Document name:")
    nameLabel.place(x=10, y=60)
    nameEntry = Entry(newLegalDocumentFrame, width=50)
    nameEntry.place(x=10, y=80)
    nameEntry.bind("<KeyRelease>", lambda e: reset_border(nameEntry))

    def validate_four_digits(text):
        return (text.isdigit() and len(text) <= 4) or text == ""

    vcmd = root.register(validate_four_digits)
    yearLabel = Label(newLegalDocumentFrame, text="Year:")
    yearLabel.place(x=10, y=110)
    yearEntry = Entry(newLegalDocumentFrame, validate="key", validatecommand=(vcmd, "%P"))
    yearEntry.bind("<KeyRelease>", lambda e: reset_border(yearEntry))
    yearEntry.place(x=10, y=130)

    jurisdictionLabel = Label(newLegalDocumentFrame, text="Jurisdiction:")
    jurisdictionLabel.place(x=10, y=160)
    jurisdictionEntry = Entry(newLegalDocumentFrame, width=50)
    jurisdictionEntry.place(x=10, y=180)

    descriptionLabel = Label(newLegalDocumentFrame, text="Description:")
    descriptionLabel.place(x=10, y=210)
    descriptionText = Text(newLegalDocumentFrame, width=50, height=7)
    descriptionText.place(x=10, y=230)

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

    documentTypeLabel = Label(newLegalDocumentFrame, text="Document Type:")
    documentTypeLabel.place(x=10, y=360)
    documentTypeOptions = [r[0] for r in selectAllDocumentTypeNames()]
    documentTypeSelectedValue = StringVar(value=documentTypeOptions[0])
    documentTypeCombobox = ttk.Combobox(
        newLegalDocumentFrame,
        textvariable=documentTypeSelectedValue,
        values=documentTypeOptions,
        state="readonly",
        style="CustomCombobox.TCombobox",
    )
    documentTypeCombobox.place(x=10, y=380)

    newDocumentTypeLabel = Label(newLegalDocumentFrame, text="New Document Type:")
    newDocumentTypeEntry = Entry(newLegalDocumentFrame, width=30)

    def backNewDocumentType():
        newDocumentTypeLabel.place_forget()
        newDocumentTypeEntry.place_forget()
        backDocumentTypeButton.place_forget()
        newDocumentTypeEntry.delete(0, "end")

        documentTypeLabel.place(x=10, y=360)
        documentTypeCombobox.place(x=10, y=380)
        addDocumentTypeButton.place(x=190, y=375)

    backDocumentTypeButton = Button(
        newLegalDocumentFrame, text="Choose Type", command=lambda: backNewDocumentType()
    )

    def addNewDocumentType():
        documentTypeLabel.place_forget()
        documentTypeCombobox.place_forget()
        addDocumentTypeButton.place_forget()

        newDocumentTypeLabel.place(x=10, y=360)
        newDocumentTypeEntry.place(x=10, y=380)
        backDocumentTypeButton.place(x=260, y=375)

    addDocumentTypeButton = Button(
        newLegalDocumentFrame, text="Add New Type", command=lambda: addNewDocumentType()
    )
    addDocumentTypeButton.place(x=190, y=375)

    documentLabel = Label()  # will be placed in version frame

    def showDocumentFrame(opt):
        if opt == "insert":
            newDocumentVersionFrame.pack_forget()
            newLegalDocumentFrame.pack(fill="both", expand=True)
        elif opt == "update":
            newLegalDocumentFrame.pack_forget()
            newDocumentVersionFrame.pack(fill="both", expand=True)

    def nextFrame():
        nonlocal documentLabel

        document_name = nameEntry.get()
        document_jurisdiction = jurisdictionEntry.get()
        document_year = None
        if yearEntry.get().strip():
            document_year = int(yearEntry.get())
        document_description = descriptionText.get("1.0", "end-1c")

        if newDocumentTypeEntry.get().strip():
            document_type = newDocumentTypeEntry.get()
        else:
            document_type = documentTypeSelectedValue.get()

        if not document_name:
            nameEntry.config(highlightbackground="red", highlightcolor="red")
            messagebox.showwarning("Missing Information", "Please fill in the required field.")
            return

        if len(selectDocumentByName(document_name)) == 1:
            nameEntry.config(highlightbackground="red", highlightcolor="red")
            messagebox.showwarning("Duplicate Document", "This document already exists.")
            return

        if document_year:
            if not (1800 <= document_year <= datetime.now().year):
                messagebox.showwarning("Invalid Year", "Please enter a valid year.")
                yearEntry.config(
                    highlightbackground="red",
                    highlightcolor="red",
                    highlightthickness=2,
                )
                return

        documentLabel.config(text="Document Name: " + document_name)
        # store in closure for saveDocument
        newDocumentVersionFrame.document_name = document_name
        newDocumentVersionFrame.document_jurisdiction = document_jurisdiction
        newDocumentVersionFrame.document_year = document_year
        newDocumentVersionFrame.document_description = document_description
        newDocumentVersionFrame.document_type = document_type

        showDocumentFrame("update")

    nextButton = Button(newLegalDocumentFrame, text="Next", command=lambda: nextFrame())
    nextButton.place(x=80, y=440)

    # -------------------------------------------------------------------------
    # New document version frame
    # -------------------------------------------------------------------------
    newDocumentVersionFrame = Frame(documentFrame)


    titleLabel2 = Label(newDocumentVersionFrame, text="New Document Version", font=("Arial", 16))
    titleLabel2.place(relx=0.5, y=10, anchor="n")

    
    documentLabel = Label(newDocumentVersionFrame, text="Document Name:" )
    documentLabel.place(x=20, y=50)

    def searchLegalDocument():
        

        def on_search(event=None):
            query = search_var.get().lower()
            results_listbox.delete(0, tk.END)

            for document in selectAllDocuments():
                item = document[1]
                if query in item.lower():
                    results_listbox.insert(tk.END, item)

        def on_select(event):
            
            selection = results_listbox.curselection()
            if not selection:
                return
            state.selected_document_name = results_listbox.get(selection[0])

        def on_doubleClick(event):
            
            selection = results_listbox.curselection()
            if not selection:
                return

            documentNameSelected = results_listbox.get(selection[0])
            state.selected_document_name = documentNameSelected

            documentLabel.config(text="Document name: " + documentNameSelected)
            
            closeSecondWindow(searchDocumentFrame, toggle=False)

        searchDocumentFrame = Toplevel(root)
        searchDocumentFrame.title("Search Document")
        searchDocumentFrame.geometry("500x500")
        searchDocumentFrame.transient(root)
        searchDocumentFrame.lift()
        searchDocumentFrame.attributes("-topmost", True)
        searchDocumentFrame.after(10, lambda: searchDocumentFrame.attributes("-topmost", False))
        searchDocumentFrame.grab_set()
        searchDocumentFrame.protocol(
            "WM_DELETE_WINDOW",
            lambda: closeSecondWindow(searchDocumentFrame, toggle=False)
        )

        seardhTitleLabel = Label(searchDocumentFrame, text="Document", font=("Arial", 16))
        seardhTitleLabel.place(relx=0.5, y=10, anchor="n")

        searchDocumentLabel = Label(searchDocumentFrame, text="Document Name:" )
        searchDocumentLabel.place(x=20, y=50)

        search_var = StringVar()

        search_icon = PhotoImage(file="iconImages/lensIcon.png").subsample(20, 20)
        search_icon_label = Label(searchDocumentFrame, image=search_icon)
        search_icon_label.image = search_icon
        search_icon_label.place(x=430, y=70)

        search_entry = Entry(searchDocumentFrame, textvariable=search_var, width=50)
        search_entry.place(x=20, y=70)
        search_entry.bind("<KeyRelease>", on_search)

        # --- Listbox + Scrollbar ---
        listbox_frame = Frame(searchDocumentFrame)
        listbox_frame.place(x=20, y=100)

        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        results_listbox = Listbox(
            listbox_frame,
            width=50,
            height=15,
            yscrollcommand=scrollbar.set
        )
        results_listbox.pack(side="left", fill="both")

        scrollbar.config(command=results_listbox.yview)

        results_listbox.bind("<Double-Button-1>", on_doubleClick)
        results_listbox.bind("<<ListboxSelect>>", on_select)

        def saveSearchDocument():

            documentLabel.config(text="Document name: " + state.selected_document_name)
            changeSecondWindowsValue()
            searchDocumentFrame.destroy()

        saveButton = Button(
            searchDocumentFrame,
            text="Save",
            command=lambda: saveSearchDocument(),
        )
        saveButton.place(x=410, y=440)

        def cancelFrame():
            changeSecondWindowsValue()
            state.selected_document_name = ""
            searchDocumentFrame.destroy()

        cancelButton = Button(
            searchDocumentFrame, 
            text="Cancel", 
            command=lambda: cancelFrame()
        )
        cancelButton.place(x=20, y=440)



    searchDocumentButton = Button(newDocumentVersionFrame, text="Select", command=lambda: searchLegalDocument())
    searchDocumentButton.place(x=20, y=80)

    if document_id > 0:
        documentLabel.config(text="Document Name: " + selectDocumentById(document_id)[0][1])

    versionLabel = Label(newDocumentVersionFrame, text="Version:")
    versionLabel.place(x=20, y=120)
    versionEntry = Entry(newDocumentVersionFrame, width=50)
    versionEntry.place(x=20, y=140)

    effectiveFromLabel = Label(newDocumentVersionFrame, text="Effective from:")
    effectiveFromLabel.place(x=20, y=170)
    effectiveFromDateEntry = DateEntry(
        newDocumentVersionFrame,
        width=10,
        background="darkblue",
        foreground="white",
        borderwidth=2,
    )
    effectiveFromDateEntry.place(x=20, y=190)

    effectiveToLabel = Label(newDocumentVersionFrame, text="Effective to:")
    effectiveToLabel.place(x=160, y=170)
    effectiveToDateEntry = DateEntry(
        newDocumentVersionFrame,
        width=10,
        background="darkblue",
        foreground="white",
        borderwidth=2,
    )
    effectiveToDateEntry.place(x=160, y=190)
    entryEffectiveToDateEntry = next(
        (
            child
            for child in effectiveToDateEntry.winfo_children()
            if isinstance(child, tk.Entry)
        ),
        None,
    )
    effectiveToDateEntry.config(state="disabled")
    if entryEffectiveToDateEntry:
        entryEffectiveToDateEntry.delete(0, "end")

    noEndDateVar = BooleanVar(value=True)

    def toggle_end_date():
        if noEndDateVar.get():
            effectiveToDateEntry.config(state="disabled")
            if entryEffectiveToDateEntry:
                entryEffectiveToDateEntry.delete(0, "end")
        else:
            effectiveToDateEntry.config(state="normal")

    noEndDateCheckButton = Checkbutton(
        newDocumentVersionFrame,
        text="No end date",
        variable=noEndDateVar,
        command=toggle_end_date,
    )
    noEndDateCheckButton.place(x=260, y=190)

    sourceUrlLabel = Label(newDocumentVersionFrame, text="Source url:")
    sourceUrlLabel.place(x=20, y=220)
    sourceUrlEntry = Entry(newDocumentVersionFrame, width=50)
    sourceUrlEntry.place(x=20, y=240)

    filePathLabel = Label(newDocumentVersionFrame, text="File path:")
    filePathLabel.place(x=20, y=270)
    filePathEntry = Entry(newDocumentVersionFrame, width=50)
    filePathEntry.place(x=20, y=290)

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

    filePathButton = Button(
        newDocumentVersionFrame,
        image=filePathIcon,
        command=lambda: selectFilePath(documentFrame),
        padx=5,
        pady=5,
    )
    filePathButton.image = filePathIcon
    filePathButton.place(x=440, y=290)

    notesLabel = Label(newDocumentVersionFrame, text="Notes:")
    notesLabel.place(x=20, y=320)
    notesText = Text(newDocumentVersionFrame, width=50, height=5)
    notesText.place(x=20, y=340)

    if document_id == -1:
        backButton = Button(
            newDocumentVersionFrame,
            text="Back",
            command=lambda: showDocumentFrame("insert"),
        )
        backButton.place(x=80, y=440)

    def saveDocument(doc_id):
        if doc_id == -1:
            document_name = newDocumentVersionFrame.document_name
            document_jurisdiction = newDocumentVersionFrame.document_jurisdiction
            document_year = newDocumentVersionFrame.document_year
            document_description = newDocumentVersionFrame.document_description
            document_type = newDocumentVersionFrame.document_type

            if newDocumentTypeEntry.get().strip():
                insertDocumentType(document_type)

            insertDocument(
                document_name,
                document_jurisdiction,
                document_year,
                document_description,
                selectDocumentTypeByName(document_type)[0][0],
            )

            doc_id = selectDocumentByName(document_name)[0][0]

        insertDocumentVersion(
            doc_id,
            versionEntry.get(),
            effectiveFromDateEntry.get_date(),
            effectiveToDateEntry.get_date() if not noEndDateVar.get() else None,
            sourceUrlEntry.get(),
            filePathEntry.get(),
            notesText.get("1.0", "end-1c"),
        )

        changeSecondWindowsValue()
        documentFrame.destroy()

    saveButton = Button(
        newDocumentVersionFrame,
        text="Save",
        command=lambda: saveDocument(document_id),
    )
    saveButton.place(x=410, y=440)

    def cancelFrame():
        changeSecondWindowsValue()
        documentFrame.destroy()

    cancelButton = Button(documentFrame, text="Cancel", command=lambda: cancelFrame())
    cancelButton.place(x=20, y=440)

    showDocumentFrame(option)
