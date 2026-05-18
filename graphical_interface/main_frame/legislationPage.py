from tkinter import Button, Frame, Label, StringVar

from database.database import selectAllSnapshots, selectDocumentsforPage, selectLastRulesSnapshot, selectRulesSnapshotByLabel, selectRulesFromSnapshot
from graphical_interface.createNewSnapshotWindows import makeNewSnapshot
from graphical_interface.widgets.searchableComboBoxClass import SearchableCombobox
from graphical_interface.widgets.searchableTableClass import SearchableTable

from graphical_interface.graphicalInterface import CARD

def openDocumentsPage(content):

    global documentsPageFrame, load_legislation_data

    documentsPageFrame = Frame(content, bg=CARD)
    documentsPageFrame.grid(row=0, column=0, sticky="nsew")

    Label(documentsPageFrame, text="Active Snapshot: " + selectLastRulesSnapshot()[0][1], font=("Arial", 12), bg=CARD).place(x=135, y=20, anchor="w")

    documentListFrame = Frame(documentsPageFrame, bg=CARD)
    documentListFrame.place(x=80, y=100, width=900, height=700)

    rulesListFrame = Frame(documentsPageFrame, bg=CARD)
    rulesListFrame.place(x=80, y=100, width=900, height=700)

    def show_frame(frame):
        frame.tkraise()
 
    snapshotsOptions = []
    snapshotSelected = StringVar()
    snapshotSelected.set(selectLastRulesSnapshot()[0][1])

    snapshotsCombobox = SearchableCombobox(
        documentsPageFrame,
        textvariable=snapshotSelected,
        values=snapshotsOptions,
        width=30,
        state="normal"   
    )
    snapshotsCombobox.place(x=135, y=60)

    Button(
        documentsPageFrame, 
        text="Legislation Update", 
        command= lambda: makeNewSnapshot(), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=14, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 800, y=40)

    # --- Legislation List Frame ---
    def selectLegislationListData():
        return selectDocumentsforPage(selectRulesSnapshotByLabel(snapshotSelected.get())[0][0])

    document_columns = ("name", "jurisdiction", "year", "version")
    document_table = SearchableTable(documentListFrame, document_columns, selectLegislationListData)
    document_table.place(relx=0.5, y=20, width=900, height=600, anchor='n')

    Button(
        documentListFrame, 
        text="Show Rules", 
        command= lambda: show_frame(rulesListFrame), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=14, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 35, y=650)

    show_frame(documentListFrame)

    # --- Rules List Frame ---
    Button(
        rulesListFrame, 
        text="Show Legislation", 
        command= lambda: show_frame(documentListFrame), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=14, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 35, y=650)

    def selectRulesListData():
        return selectRulesFromSnapshot(selectRulesSnapshotByLabel(snapshotSelected.get())[0][0])

    rules_columns = ("Code", "Name", "Category")
    rules_table = SearchableTable(rulesListFrame, rules_columns, selectRulesListData)
    rules_table.place(relx=0.5, y=20, width=900, height=600, anchor='n')


    def load_legislation_data():
        nonlocal snapshotsOptions

        snapshotSelected.set(selectLastRulesSnapshot()[0][1])
        snapshotsOptions = [row[1] for row in selectAllSnapshots()]

        document_table.all_data = document_table.load_function()
        rules_table.all_data = rules_table.load_function()

        document_table.refresh_table(document_table.all_data)
        rules_table.refresh_table(rules_table.all_data)