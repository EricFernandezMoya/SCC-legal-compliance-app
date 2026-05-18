from tkinter import Entry, Frame, Label, StringVar, Button, messagebox
from tkinter import ttk

from classesFile import User
from database.database import selectPrivileges, selectUserByName, selectPrivilegeByName, updateUser
from userHandling.userHandling import createUser, hash_password

from graphical_interface.graphicalInterface import (
    create_modal_window,
    closeSecondWindow,
    reset_border,
)


def createUserWindows(is_update=False, user=None):
    
    win = create_modal_window("User", toggle=False)
    if not win:
        return

    win.withdraw()

    Label(win, text="Create User", font=("Arial", 16)).pack(pady=10)

    createUserFrame = Frame(win)
    createUserFrame.pack(pady=10, padx=20)

    Label(createUserFrame, text="Username:").grid(row=0, column=0, sticky="w")
    if is_update:
        Label(createUserFrame, text=user.get_username()).grid(row=1, column=0, pady=(0, 20), sticky="w")
    else:
        usernameEntry = Entry(createUserFrame, width=35)
        usernameEntry.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky="w")
        usernameEntry.bind("<KeyRelease>", lambda e: reset_border((usernameEntry,)))

    Label(createUserFrame, text="Full name:").grid(row=2, column=0, sticky="w")
    fullNameEntry = Entry(createUserFrame, width=35)
    fullNameEntry.grid(row=3, column=0, columnspan=2, pady=(0, 20), sticky="w")
    if is_update:
        fullNameEntry.insert(0, user.get_name())

    if is_update:
        password_label_text = "New Password:"
    else:
        password_label_text = "Password:"
    Label(createUserFrame, text=password_label_text).grid(row=4, column=0, sticky="w")
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
    if is_update:
        privilegeSelectedValue = StringVar(value=user.get_privilege())
    else:
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
        
        if not is_update:
            user_name = usernameEntry.get()

            if not user_name:
                usernameEntry.config(highlightbackground="red", highlightcolor="red")
                fieldMissing = True
                missingInformationMessage += "\n- Username"
        else:
            user_name = user.get_username()
        user_fullName = fullNameEntry.get()
        user_password = passwordEntry.get()
        user_privilege = privilegeSelectedValue.get()

        if not is_update:
            if not user_password:
                passwordEntry.config(highlightbackground="red", highlightcolor="red")
                fieldMissing = True
                missingInformationMessage += "\n- Password"

        if fieldMissing:
            messagebox.showwarning("Missing Information", missingInformationMessage)
            return

        if not is_update:
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

        if is_update:

            if not user_password:
                user_password = selectUserByName(user.get_username())[0][3]

            updateUser(user.get_id(), user_fullName, hash_password(user_password), selectPrivilegeByName(user_privilege)[0][0])

        else:
                    
            createUser(
                user_name,
                user_fullName,
                user_password,
                selectPrivilegeByName(user_privilege)[0][0],
            )

        from graphical_interface.main_frame.usersPage import load_users
        load_users()
        
        closeSecondWindow(win, toggle=False)

    if is_update:
        saveUserButton_text = "Update"
    else:
        saveUserButton_text = "Save"    
    saveUserButton = Button(createUserFrame, text=saveUserButton_text, command=lambda: saveUser(), width=10)
    saveUserButton.grid(row=8, column=1, sticky="e", pady=20)

    win.update_idletasks()
    win.deiconify()
    win.grab_set()
