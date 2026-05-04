import tkinter as tk
from tkinter import Label, Button

from database.database import *
from userHandling.userHandling import *

from graphical_interface.graphicalInterface import (
    mainFrame,
    logInFrame,
    anthropicFrame,
    show_frame,
    LOGIN_FRAME_SIZE,
    MEDIUM_FRAME_SIZE,
    LARGE_FRAME_SIZE,
)

from graphical_interface.documentWindows import documentWindows
from graphical_interface.contractGroupWindows import contractGroupWindows
from graphical_interface.createUserFrame import createUserWindows


homePageTitlelabel = Label(mainFrame, text="Home Page", font=("Arial", 16))
homePageTitlelabel.place(relx=0.5, y=20, anchor="center")

userLabel = Label(mainFrame)
userLabel.place(x=10, y=10)

buttonSettingPage = Button(
    mainFrame,
    text="Go to AI Query",
    command=lambda: show_frame(anthropicFrame, LARGE_FRAME_SIZE),
)
buttonSettingPage.place(relx=0.5, y=120, anchor="center")

buttonInsertLegalDocument = Button(
    mainFrame,
    text="Insert Doc",
    command=lambda: documentWindows("insert", -1),
)
buttonInsertLegalDocument.place(relx=0.5, y=170, anchor="center")

buttonUpdateLegalDocument = Button(
    mainFrame,
    text="Update Doc",
    command=lambda: documentWindows("update", 1),
)
buttonUpdateLegalDocument.place(relx=0.5, y=220, anchor="center")

logoutButton = Button(
    mainFrame,
    text="Log out",
    command=lambda: show_frame(logInFrame, LOGIN_FRAME_SIZE),
)
logoutButton.place(relx=0.5, y=270, anchor="center")

addContractGroupButton = Button(
    mainFrame,
    text="Add Group",
    command=lambda: contractGroupWindows(),
)
addContractGroupButton.place(relx=0.5, y=320, anchor="center")

createUserButton = Button(
    mainFrame,
    text="Create User",
    command=lambda: createUserWindows(),
)
createUserButton.place(relx=0.5, y=370, anchor="center")
