from tkinter import Entry, Frame, Label, StringVar, Button, messagebox
from tkinter import ttk

from database.database import selectPrivileges, selectUserByName, selectPrivilegeByName
from userHandling.userHandling import createUser

from graphical_interface.graphicalInterface import (
    create_modal_window,
    closeSecondWindow,
    reset_border,
)


def createUserWindows():
    
    win = create_modal_window("User", toggle=False)
    if not win:
        return

    win.withdraw()

    Label(win, text="Create User", font=("Arial", 16)).pack(pady=10)

    createUserFrame = Frame(win)
    createUserFrame.pack(pady=10, padx=20)
 

    Label(createUserFrame, text="Username:").grid(row=0, column=0, sticky="w")
    usernameEntry = Entry(createUserFrame, width=35)
    usernameEntry.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky="w")
    usernameEntry.bind("<KeyRelease>", lambda e: reset_border((usernameEntry,)))

    Label(createUserFrame, text="Full name:").grid(row=2, column=0, sticky="w")
    fullNameEntry = Entry(createUserFrame, width=35)
    fullNameEntry.grid(row=3, column=0, columnspan=2, pady=(0, 20), sticky="w")

    Label(createUserFrame, text="Password:").grid(row=4, column=0, sticky="w")
    passwordEntry = Entry(createUserFrame, width=35)
    passwordEntry.grid(row=5, column=0, columnspan=2, pady=(0, 20), sticky="w")
    passwordEntry.bind("<KeyRelease>", lambda e: reset_border((passwordEntry,)))

    privilegeComboboxStyle = ttk.Style()
    privilegeComboboxStyle.theme_use("default")
    privilegeComboboxStyle.configure(
        "CustomCombobox.TCombobox",
        fieldbackground="white",
        background="white",
        foreground="black",
    )
    privilegeComboboxStyle.map(
        "CustomCombobox.TCombobox",
        fieldbackground=[("readonly", "white"), ("!disabled", "white")],
        foreground=[("readonly", "black"), ("!disabled", "black")],
        selectbackground=[("readonly", "white"), ("!disabled", "white")],
        selectforeground=[("readonly", "black"), ("!disabled", "black")],
    )

    Label(createUserFrame, text="Privilege:").grid(row=6, column=0, sticky="w")
    privilegeOptions = []
    for r in selectPrivileges():
        if r[1] == "SYSTEM":
            continue
        privilegeOptions.append(r[1])
    privilegeSelectedValue = StringVar(value=privilegeOptions[0])
    privilegeCombobox = ttk.Combobox(
        createUserFrame,
        textvariable=privilegeSelectedValue,
        values=privilegeOptions,
        state="readonly",
        style="CustomCombobox.TCombobox",
    )
    privilegeCombobox.grid(row=7, column=0, pady=(0, 20), sticky="w")

    def cancelFrame():
        closeSecondWindow(win, toggle=False)

    cancelButton = Button(createUserFrame, text="Cancel", command=lambda: cancelFrame(), width=10)
    cancelButton.grid(row=8, column=0, sticky="w", pady=20)

    def saveUser():
        fieldMissing = False
        missingInformationMessage = "Please fill in the required fields:\n"

        user_name = usernameEntry.get()
        user_fullName = fullNameEntry.get()
        user_password = passwordEntry.get()
        user_privilege = privilegeSelectedValue.get()

        if not user_name:
            usernameEntry.config(highlightbackground="red", highlightcolor="red")
            fieldMissing = True
            missingInformationMessage += "\n- Username"

        if not user_password:
            passwordEntry.config(highlightbackground="red", highlightcolor="red")
            fieldMissing = True
            missingInformationMessage += "\n- Password"

        if fieldMissing:
            messagebox.showwarning("Missing Information", missingInformationMessage)
            return

        if len(selectUserByName(user_name)) == 1:
            usernameEntry.config(highlightbackground="red", highlightcolor="red")
            messagebox.showwarning(
                "Duplicate User", f'User "{user_name}" already exists.'
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Save",
            "Are you sure you want to save this user?\n"
            f"- Username: {user_name}\n"
            f"- Privilege: {user_privilege}",
        )

        if not confirm:
            return
        
        createUser(
            user_name,
            user_fullName,
            user_password,
            selectPrivilegeByName(user_privilege)[0][0],
        )

        from graphical_interface.mainWindows import load_users
        load_users()
        
        closeSecondWindow(win, toggle=False)

    saveUserButton = Button(createUserFrame, text="Save", command=lambda: saveUser(), width=10)
    saveUserButton.grid(row=8, column=1, sticky="e", pady=20)

    win.update_idletasks()
    win.deiconify()
    win.grab_set()
