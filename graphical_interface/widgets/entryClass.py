from tkinter import Entry

from graphical_interface.graphicalInterface import BORDER, TXT

def entry(parent, placeholder="", width=300, is_password=False):
    newEntry = Entry(
        parent,
        width=int(width / 8),  
        fg=TXT,
        bg="white",
        relief="flat",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=BORDER,
    )

    # --- Placeholder logic ---
    if placeholder:
        newEntry.insert(0, placeholder)
        newEntry.config(fg="#888888")  # grey placeholder text

        def on_focus_in(event):
            if newEntry.get() == placeholder:
                newEntry.delete(0, "end")
                newEntry.config(fg=TXT)

                if is_password:
                    newEntry.config(show="*")   

        def on_focus_out(event):
            if not newEntry.get():
                newEntry.insert(0, placeholder)
                newEntry.config(fg="#888888")

                if is_password:
                    newEntry.config(show="")

        newEntry.bind("<FocusIn>", on_focus_in)
        newEntry.bind("<FocusOut>", on_focus_out)

    return newEntry

