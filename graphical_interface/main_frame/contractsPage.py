from tkinter import Frame, Label

from database.database import selectContractForPage
from graphical_interface.widgets.searchableTableClass import SearchableTable
from graphical_interface.graphicalInterface import CARD

def openContractsPage(content):
   
    global load_contracts, contractsPageFrame

    contractsPageFrame = Frame(content, bg=CARD)
    contractsPageFrame.grid(row=0, column=0, sticky="nsew")

    Label(contractsPageFrame, text="Contracts", font=("Arial", 16), bg=CARD).place(relx=0.5, y=20, anchor="center")
    
    contract_columns = ("group", "name", "type", "version")
    contract_table = SearchableTable(contractsPageFrame, contract_columns, selectContractForPage)
    contract_table.place(relx=0.5, y=60, width=900, height=600, anchor='n')

    def load_contracts():
        contract_table.all_data = contract_table.load_function()
        contract_table.refresh_table(contract_table.all_data)
