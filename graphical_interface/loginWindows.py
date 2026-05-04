import tkinter as tk
from tkinter import Label, Button, Entry, messagebox

from database.database import *
from userHandling.userHandling import *
from state import state

from graphical_interface.graphicalInterface import (
    logInFrame,
    mainFrame,
    show_frame,
    MEDIUM_FRAME_SIZE,
    LOGIN_FRAME_SIZE,
)


def login():
    global usernameText, passwordEntry

    username = usernameText.get()
    password = passwordEntry.get()

    if not username or not password:
        messagebox.showwarning("Invalid Input", "Please enter both username and password.")
    else:
        userData = selectUserByName(username)

        if len(userData) != 1:
            messagebox.showerror("Login Failed", "Invalid username or password.")
        else:
            if userLogin(username, password):
                from graphical_interface.mainWindows import userLabel  # imported here to avoid circular issues

                user = User(userData[0][1], userData[0][2], userData[0][3], userData[0][4])
                state.current_user = user

                userLabel.config(text=username)
                show_frame(mainFrame, MEDIUM_FRAME_SIZE)
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.")

    usernameText.delete(0, "end")
    passwordEntry.delete(0, "end")


loginTitleLabel = Label(logInFrame, text="Login", font=("Arial", 16))
loginTitleLabel.place(relx=0.5, y=20, anchor="center")

usernameLabel = Label(logInFrame, text="User name:")
usernameLabel.place(x=10, y=50)
usernameText = Entry(logInFrame, width=25)
usernameText.place(x=10, y=70)

passwordLabel = Label(logInFrame, text="Password:")
passwordLabel.place(x=10, y=110)
passwordEntry = Entry(logInFrame, width=25, show="*")
passwordEntry.place(x=10, y=130)
passwordEntry.bind("<Return>", lambda event: login())

loginButton = Button(logInFrame, text="Log in", command=lambda: login())
loginButton.place(x=10, y=170)
