import threading
from time import time
from tkinter import Button, Frame, Label, StringVar, Tk, messagebox, ttk

from graphical_interface.graphicalInterface import closeSecondWindow, create_modal_window
from database.database import selectAllContractGroups, selectContractForPage, selectContractById, selectContractGroupByName, selectContractsByGroup
from graphical_interface.showReportWindows import showReports
from graphical_interface.widgets.circularSpinnerClass import CircularSpinner
from graphical_interface.widgets.searchableComboBoxClass import SearchableCombobox
from report_analysis.analysis import analyse_contract, analyse_vendor_group
from report_analysis.document_parser import parseFile
from report_analysis.reports import save_report

def makeNewAnalysis(is_group=False):
    global spinner, analyse_button

    win = create_modal_window("Analysis", toggle=False)
    if not win:
        return

    win.withdraw()

    if is_group:
        label_text = "Group"
    else:
        label_text = "Contract"

    Label(win, text=label_text + " Analysis", font=("Arial", 16)).pack(pady=10)

    frame = Frame(win)
    frame.pack(pady=10, padx=20)

    Label(frame, text="Choose " + label_text + ": ").grid(row=1, column=0, sticky="w", pady=(10, 0))

    contractOptions = []

    if is_group:

        for group in selectAllContractGroups():
            contractOptions.append(group[1])
    else:

        for contract in selectContractForPage():
            contractOptions.append(f"{contract[1]} - {contract[3]}")


    contractSelected = StringVar()    

    contractCombobox = SearchableCombobox(
        frame,
        textvariable=contractSelected,
        values=contractOptions,
        width=35,
        state="normal"
    )
    contractCombobox.grid(row=2, column=0, sticky="w")

    spinner = CircularSpinner(win, size=50, width=5, speed=8, color="#0078D7")
    


    def analyseConract():
        global documentText, contract
        contractSelectedId = None

        spinner.place(relx=0.5, rely=0.5, anchor="center")
        spinner.start()

        analyse_button.config(state="disabled")

        # Lock the window so user cannot interact with anything else
        win.grab_set()
        if not contractSelected.get().strip():
            messagebox.showwarning("Invalid" + label_text, "Please, select a " + label_text + " from the dropbox")
            return
        
        if not is_group:    

            for contract in selectContractForPage():
                contractFormated = f"{contract[1]} - {contract[3]}"
                if contractFormated == contractSelected.get():
                    contractSelectedId = contract[0]
        
            contract = selectContractById(contractSelectedId)
        
            if contract[6]:
                fileSource = contract[6]
            else:
                fileSource = contract[7]

            if not fileSource or not (fileSource.endswith(".pdf") or fileSource.endswith("doc") or fileSource.endswith("odt") or fileSource.endswith(".docx") or fileSource.startswith("http")):

                messagebox.showwarning("Invalid File Source", "Wrong File Source — skipping analysis.")
                return

            documentText = parseFile(fileSource) 

            if not documentText:
                messagebox.showwarning("Error: Contract Parsing", "The text could not be extracted from the source file — skipping analysis.")
                return
            
        def worker():
    
            if is_group:
                findings = analyse_vendor_group(selectContractGroupByName(contractSelected.get())[0][0])
            else:
                findings = analyse_contract(documentText)

            if is_group:
                contract_id = selectContractGroupByName(contractSelected.get())[0][0]
                report_id = save_report(contract_id, findings, is_group=1)
            else:
                contract_id = contractSelectedId
                report_id = save_report(contract_id, findings)

            

        # Back to main thread
            def finish():
                spinner.stop()
                spinner.destroy()
                analyse_button.config(state="normal")
                win.grab_release()
                closeSecondWindow(win, toggle=False)
                showReports(report_id)
                
                from graphical_interface.main_frame.dashBoardPage import load_dashboard
                from graphical_interface.main_frame.reportsPage import load_reports
                load_dashboard()
                load_reports()

            win.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

    

    analyse_button = Button(frame, text="Analyse", command=analyseConract, width=10)
    analyse_button.grid(row=3, column=0, sticky="e", pady=20)
    
    win.update_idletasks()
    win.deiconify()
    win.grab_set()


