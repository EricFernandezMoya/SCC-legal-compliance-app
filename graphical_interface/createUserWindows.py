from tkinter import Entry, Label, StringVar, Button, Toplevel, messagebox
from tkinter import ttk

from database.database import *
from userHandling.userHandling import *

from graphical_interface.graphicalInterface import (
    root,
    getSecondWindowsValue,
    changeSecondWindowsValue,
    closeSecondWindow,
    reset_border,
)


def createUserWindows():
    if getSecondWindowsValue():
        return

    changeSecondWindowsValue()

    createUserFrame = Toplevel(root)
    createUserFrame.geometry("450x300")
    createUserFrame.transient(root)
    createUserFrame.lift()
    createUserFrame.attributes("-topmost", True)
    createUserFrame.after(10, lambda: createUserFrame.attributes("-topmost", False))
    createUserFrame.protocol("WM_DELETE_WINDOW", lambda: closeSecondWindow(createUserFrame))

    titleLabel = Label(createUserFrame, text="Create User", font=("Arial", 16))
    titleLabel.place(relx=0.5, y=10, anchor="n")

    usernameLabel = Label(createUserFrame, text="Username:")
    usernameLabel.place(x=20, y=40)
    usernameEntry = Entry(createUserFrame, width=35)
    usernameEntry.place(x=20, y=60)
    usernameEntry.bind("<KeyRelease>", lambda e: reset_border(usernameEntry))

    fullNameLabel = Label(createUserFrame, text="Full name:")
    fullNameLabel.place(x=20, y=90)
    fullNameEntry = Entry(createUserFrame, width=35)
    fullNameEntry.place(x=20, y=110)

    passwordLabel = Label(createUserFrame, text="Password:")
    passwordLabel.place(x=20, y=140)
    passwordEntry = Entry(createUserFrame, width=35)
    passwordEntry.place(x=20, y=160)
    passwordEntry.bind("<KeyRelease>", lambda e: reset_border(passwordEntry))

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

    privilegeLabel = Label(createUserFrame, text="Privilege:")
    privilegeLabel.place(x=20, y=190)
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
    privilegeCombobox.place(x=20, y=210)

    def cancelFrame():
        changeSecondWindowsValue()
        createUserFrame.destroy()

    cancelButton = Button(createUserFrame, text="Cancel", command=lambda: cancelFrame())
    cancelButton.place(x=20, y=250)

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
        changeSecondWindowsValue()
        createUserFrame.destroy()

    saveUserButton = Button(createUserFrame, text="Save", command=lambda: saveUser())
    saveUserButton.place(x=430, y=250, anchor="ne")
