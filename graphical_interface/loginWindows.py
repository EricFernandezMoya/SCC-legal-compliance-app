from tkinter import  Frame, Label, Button, messagebox
from PIL import Image, ImageTk

from graphical_interface.widgets.entryClass import entry
from graphical_interface.widgets.roundedCardClass import make_rounded_card
from userHandling.userHandling import userLogin, selectUserByName
from classesFile import User
from state import state
from graphical_interface.mainWindows import openMainWindows

from graphical_interface.graphicalInterface import BG, BORDER, CARD, TXT, logInFrame

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

                state.current_user = User(userData[0][0], userData[0][1], userData[0][2], userData[0][3], userData[0][4])
                openMainWindows()                 
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.")

    usernameText.delete(0, "end")
    passwordEntry.delete(0, "end")

logInFrame.config(bg=BG)

wrap = Frame(logInFrame, bg=BG)
wrap.place(relx=0.5, rely=0.5, anchor="center")


# --- PAGE TITLE ---
Label(wrap, text="Software Compliance Tool", font=("Arial", 28, "bold"), fg="#000000", bg=BG).pack(pady=(40, 120))

# --- CARD FRAME ---
shadow, card = make_rounded_card(wrap, width=440, height=360)
shadow.pack()
loginCardFrame = card

# --- SIGN IN TITLE ---
Label(loginCardFrame, text="Sign in", font=("Arial", 22, "bold"), fg=TXT, bg=CARD).pack(anchor="w",padx=60, pady=(20, 40))

# ---LOGIN ENTRY ---
usernameLabel = Label(loginCardFrame, text="User name:", fg=TXT, bg=CARD)
usernameLabel.pack(anchor="w", padx=60)
usernameText = entry(loginCardFrame, "Enter username", width=320)
usernameText.pack(anchor="w",padx=60, pady=(4, 16))

passwordLabel = Label(loginCardFrame, text="Password:", fg=TXT, bg=CARD)
passwordLabel.pack(anchor="w", padx=60)
passwordEntry = entry(loginCardFrame, "Enter password", width=320, is_password=True)
passwordEntry.pack(anchor="w", padx=60, pady=(4, 40))
passwordEntry.bind("<Return>", lambda event: login())

loginButton = Button(
    loginCardFrame, 
    text="Sign in", 
    command= lambda: login(), 
    height=1, 
    width=12, 
    bg="#0078D4", 
    fg="white", 
    activebackground="#005A9E", 
    relief="flat"
    ).pack(pady=16)

# --- LOGO ---
img = Image.open("iconImages/council_logo.png")   
logo_img = ImageTk.PhotoImage(img)
if logo_img: 
    Label(wrap,image=logo_img, bg=BG).pack(pady=(120, 40))
