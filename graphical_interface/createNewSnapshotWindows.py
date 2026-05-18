import threading
from tkinter import Button, Frame, Label, StringVar, messagebox

from database.database import selectDocumentVersionUnused
from graphical_interface.graphicalInterface import create_modal_window
from graphical_interface.widgets.circularSpinnerClass import CircularSpinner
from graphical_interface.widgets.searchableComboBoxClass import SearchableCombobox
from legislation_update import analyse_legislation_update, save_reviewer_decisions
from graphical_interface.reviewLegislationWindows import openReviewWindow
from state import state


def makeNewSnapshot():
    global spinner

    win = create_modal_window("Analysis", toggle=False)
    if not win:
        return

    win.withdraw()


    Label(win, text="Update the Knowledge Base", font=("Arial", 16)).pack(pady=10)

    frame = Frame(win)
    frame.pack(pady=10, padx=20)

    Label(frame, text="Choose Legislation:").grid(row=1, column=0, sticky="w", pady=(10, 0))
    
    legislationOptions = [row[1] for row in selectDocumentVersionUnused()]
    
    legislationSelected = StringVar()    

    legilationCombobox = SearchableCombobox(
        frame,
        textvariable=legislationSelected,
        values=legislationOptions,
        width=35,
        state="normal"
    )
    legilationCombobox.grid(row=2, column=0, sticky="w")

    spinner = CircularSpinner(win, size=50, width=5, speed=8, color="#0078D7")

    def createNewSnapshot():
        global result

        spinner.place(relx=0.5, rely=0.5, anchor="center")
        spinner.start()
        newSnapshotButton.config(state="disabled")

        if not legislationSelected.get().strip():
            messagebox.showwarning("Invalid Legislation", "Please, select a Legislation Document from the dropbox")
            return

        documentSelected = None

        for document in selectDocumentVersionUnused():
            if document[1] == legislationSelected.get():
                documentSelected = document

        if documentSelected[2]:
            fileSource = documentSelected[2]
        else:
            fileSource = documentSelected[3]

        if not fileSource or not (fileSource.endswith(".pdf") or fileSource.endswith("doc") or fileSource.endswith("odt") or fileSource.endswith(".docx") or fileSource.startswith("http")):

            messagebox.showwarning("Invalid File Source", "Wrong File Source — skipping analysis.")
            return
        
        
        
        def worker():
            
            result = analyse_legislation_update(fileSource, documentSelected[0])
        
            openReviewWindow(
                review_data=result,
                review_id=result['review_id'],
                reviewed_by=state.current_user.get_id(),
                save_reviewer_decisions=save_reviewer_decisions,
                on_complete_callback=lambda: messagebox.showinfo("Done", "Review saved.")
            )


            def finish():
                spinner.stop()
                spinner.destroy()
                newSnapshotButton.config(state="normal")
                win.grab_release()

            win.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

        

    newSnapshotButton = Button(frame, text="Analyse", command=createNewSnapshot, width=10)
    newSnapshotButton.grid(row=3, column=0, sticky="e", pady=20)

    win.update_idletasks()
    win.deiconify()
    win.grab_set()
