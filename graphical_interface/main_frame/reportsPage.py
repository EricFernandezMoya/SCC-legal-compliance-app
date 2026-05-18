from tkinter import Button, Frame, Label

from database.database import selectContractReportForPage, selectGroupReportForPage
from graphical_interface.analyseContractWinfows import makeNewAnalysis
from graphical_interface.showReportWindows import showReports
from graphical_interface.widgets.searchableTableClass import SearchableTable
from graphical_interface.graphicalInterface import CARD

def openReportsPage(content):
    
    global reportsPageFrame, load_reports
    
    reportsPageFrame = Frame(content, bg=CARD)
    reportsPageFrame.grid(row=0, column=0, sticky="nsew")

    contractReportsListFrame = Frame(reportsPageFrame, bg=CARD)
    contractReportsListFrame.place(relx=0.5, y=20, width=900, height=700, anchor="n")

    groupReportsListFrame = Frame(reportsPageFrame, bg=CARD)
    groupReportsListFrame.place(relx=0.5, y=20, width=900, height=700, anchor="n")

    def show_frame(frame):
        frame.tkraise()

    def load_reports():
        contract_report_table.all_data = contract_report_table.load_function()
        group_report_table.all_data = group_report_table.load_function()

        contract_report_table.refresh_table(contract_report_table.all_data)
        group_report_table.refresh_table(group_report_table.all_data)

    # --- contract reports ---

    Label(contractReportsListFrame, text="Contract Reports", font=("Arial", 16), bg=CARD).place(relx=0.5, y=10, anchor="center")

    contract_reports_columns = ("Contract Group", "Contract Type", "Compliance Status", "Created at")

    
    def open_contract_report_details(report_id, values):

        showReports(report_id)

    contract_report_table = SearchableTable(contractReportsListFrame, contract_reports_columns, selectContractReportForPage, on_double_click=open_contract_report_details)
    contract_report_table.place(relx=0.5, y=40, width=900, height=600, anchor='n')

    Button(
        contractReportsListFrame, 
        text="Show Group Reports", 
        command= lambda: show_frame(groupReportsListFrame), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=18, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 50, y=620)


    Button(
        contractReportsListFrame, 
        text="Analyse Contract", 
        command= lambda: makeNewAnalysis(), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=18, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 250, y=620)


    show_frame(contractReportsListFrame)

    # --- group ---
    Label(groupReportsListFrame, text="Group Reports", font=("Arial", 16), bg=CARD).place(relx=0.5, y=10, anchor="center")

    group_reports_columns = ("Contract Group", "Compliance Status", "Created at")

    def open_group_report_details(report_id, values):
        showReports(report_id)

    group_report_table = SearchableTable(groupReportsListFrame, group_reports_columns, selectGroupReportForPage, on_double_click=open_group_report_details)
    group_report_table.place(relx=0.5, y=40, width=900, height=600, anchor='n')

    Button(
        groupReportsListFrame, 
        text="Show Contract Reports", 
        command= lambda: show_frame(contractReportsListFrame), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=18, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 50, y=620)


    Button(
        groupReportsListFrame, 
        text="Analyse Group", 
        command= lambda: makeNewAnalysis(is_group=True), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=18, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 250, y=620)


