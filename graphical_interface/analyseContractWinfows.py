import threading
from time import time
from tkinter import Button, Frame, Label, StringVar, Tk, messagebox, ttk

from graphical_interface.graphicalInterface import closeSecondWindow, create_modal_window
from database.database import selectContractForPage, selectContractById
from graphical_interface.showReportWindows import showReports
from graphical_interface.widgets.circularSpinnerClass import CircularSpinner
from graphical_interface.widgets.searchableComboBoxClass import SearchableCombobox
from report_analysis.analysis import analyse_contract
from report_analysis.document_parser import parseFile
from report_analysis.reports import save_report

def analyseNewContract():
    global spinner, analyse_button

    win = create_modal_window("Contract", toggle=False)
    if not win:
        return

    win.withdraw()

    Label(win, text="Analyse Contract", font=("Arial", 16)).pack(pady=10)

    frame = Frame(win)
    frame.pack(pady=10, padx=20)


    Label(frame, text="Choose contract: ").grid(row=1, column=0, sticky="w", pady=(10, 0))

    contractOptions = []


    for r in selectContractForPage():
        contractOptions.append(f"{r[1]} - {r[3]}")

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

        analyse_button.config(state="disabled")

        # Lock the window so user cannot interact with anything else
        win.grab_set()
        spinner.place(relx=0.5, rely=0.5, anchor="center")
        spinner.start()


        for r in selectContractForPage():
            c = f"{r[1]} - {r[3]}"
            if c == contractSelected.get():
                contractSelectedId = r[0]
                print(contractSelected)
        
        contract = selectContractById(contractSelectedId)
        
        if len(contract) == 0:
            messagebox.showwarning("Invalid Contract", "Please, select a contract from the dropbox")
            return
        
        if contract[0][6]:
            fileSource = contract[0][6]
        else:
            fileSource = contract[0][7]

        if not fileSource or not (fileSource.endswith(".pdf") or fileSource.endswith("doc") or fileSource.endswith("odt") or fileSource.endswith(".docx") or fileSource.startswith("http")):

            messagebox.showwarning("Invalid File Source", "Wrong File Source — skipping analysis.")
            return

        documentText = parseFile(fileSource)

        if not documentText:
            messagebox.showwarning("Error: Contract Parsing", "The text could not be extracted from the source file — skipping analysis.")
            return
        
        # Show spinner
        
        def worker():
            findings = analyse_contract(documentText)
            report_id = save_report(contract[0][0], findings)

        # Back to main thread
            def finish():
                spinner.stop()
                spinner.destroy()
                analyse_button.config(state="normal")
                win.grab_release()
                closeSecondWindow(win, toggle=False)
                showReports(report_id)

            win.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

    

    analyse_button = Button(frame, text="Analyse", command=analyseConract, width=10)
    analyse_button.grid(row=3, column=0, sticky="e", pady=20)
    
    win.update_idletasks()
    win.deiconify()
    win.grab_set()


