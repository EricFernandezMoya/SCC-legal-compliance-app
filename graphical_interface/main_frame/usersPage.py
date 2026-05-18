from tkinter import Button, Frame, Label, messagebox

from classesFile import User
from database.database import deleteUser, selectUserForPage
from graphical_interface.createUserWindows import createUserWindows
from graphical_interface.widgets.searchableTableClass import SearchableTable
from graphical_interface.graphicalInterface import CARD
    
def openUsersPage(content):
    
    global usersPageFrame, load_users

    usersPageFrame = Frame(content, bg=CARD)
    usersPageFrame.grid(row=0, column=0, sticky="nsew")

    Label(usersPageFrame, text="Users", font=("Arial", 16), bg=CARD).place(relx=0.5, y=20, anchor="center")
    
    users_columns = ("Username", "Full Name", "Privilege")
    
    user_selected = None
    user_values = None

    def select_user_details(user_id, values):
        nonlocal user_values, user_selected
        user_selected = user_id
        user_values = values

    user_table = SearchableTable(usersPageFrame, users_columns, selectUserForPage, on_single_click=select_user_details, height=300)
    user_table.place(relx=0.5, y=60, width=900, height=400, anchor='n')

    global load_users

    def load_users():
        user_table.all_data = user_table.load_function()
        user_table.refresh_table(user_table.all_data)

    def deleteUserSelected():
        nonlocal user_values, user_selected

        if user_selected == None:
            messagebox.showerror("User Selection", "Please, select one user.")
            return

        confirm = messagebox.askyesno(
            "Confirm Save",
            "Are you sure you want to save this user?\n"
            f"- Username: {user_values[0]}\n"
            f"- Privilege: {user_values[2]}",
        )
        
        if not confirm:
            return
        deleteUser(user_selected)
        load_users()

    Button(
        usersPageFrame, 
        text="Delete", 
        command= lambda: deleteUserSelected(), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=14, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 135, y=450 )

    def update_user_selected():

        nonlocal user_values, user_selected

        if user_selected == None:
            messagebox.showerror("User Selection", "Please, select one user.")
            return
        
        user = User(user_selected, user_values[0], user_values[1], None, user_values[2])

        createUserWindows(is_update=True, user=user)

    Button(
        usersPageFrame, 
        text="Update", 
        command= lambda: update_user_selected(), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=14, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 325, y=450)

    Button(
        usersPageFrame, 
        text="Create User", 
        command= lambda: createUserWindows(), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=14, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x= 515, y=450)
