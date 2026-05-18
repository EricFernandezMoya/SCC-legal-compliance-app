from tkinter import Frame, Image, Label, Menu
from state import state
from PIL import Image, ImageTk

from database.database import selectPrivilegeById

from graphical_interface.graphicalInterface import BG, CARD, TXT
from graphical_interface.widgets.roundedCardClass import make_rounded_card
from graphical_interface.widgets.sideMenuButtonClass import FlatHoverButton

def getDashboardPageFrame():
    from graphical_interface.main_frame.dashBoardPage import dashboardPageFrame
    return dashboardPageFrame

def getContractsPageFrame():
    from graphical_interface.main_frame.contractsPage import contractsPageFrame
    return contractsPageFrame

def load_contractsData():
    from graphical_interface.main_frame.contractsPage import load_contracts
    load_contracts()

def getDocumentsPageFrame():
    from graphical_interface.main_frame.legislationPage import documentsPageFrame
    return documentsPageFrame

def load_documentsData():
    from graphical_interface.main_frame.legislationPage import load_legislation_data
    load_legislation_data()

def getReportsPageFrame():
    from graphical_interface.main_frame.reportsPage import reportsPageFrame
    return reportsPageFrame

def load_reportsData():
    from graphical_interface.main_frame.reportsPage import load_reports
    load_reports()

def getUsersPageFrame():
    from graphical_interface.main_frame.usersPage import usersPageFrame
    return usersPageFrame

def load_usersData():
    from graphical_interface.main_frame.usersPage import load_users
    load_users()

def openSideButtonMenu(sidebar):

    # -----------------------------
    # LEFT SIDEBAR
    # -----------------------------
    global dashboard_side_button, reports_side_button
    # --- User ---
    userShadow, userCard = make_rounded_card(sidebar, width=180, height=80, radius=12)
    userShadow.pack(fill="x", padx=10, pady=16)

    Label(
        userCard,
        text=state.current_user.get_username(),
        bg=CARD,
        fg=TXT,
        font=("Arial", 12, "bold"),
        anchor="w"
    ).pack(fill="x", padx=14, pady=5)

    Label(
        userCard,
        text=selectPrivilegeById(state.current_user.get_privilege())[0][1],
        bg=CARD,
        fg=TXT,
        font=("Arial", 11),
        anchor="w"
    ).pack(fill="x", padx=14, pady=5)

    dashboard_side_button = add_button("Dashboard",lambda: show_page(getDashboardPageFrame()), sidebar)
    dashboard_side_button.activate() 
    add_button("Legislation",lambda: (load_documentsData(),show_page(getDocumentsPageFrame())), sidebar)
    contracts_side_button = add_button("Contracts", lambda: (load_contractsData(), show_page(getContractsPageFrame())), sidebar)
    add_button("Users", lambda: (load_usersData(), show_page(getUsersPageFrame())), sidebar)
    reports_side_button = add_button("Reports", lambda:(load_reportsData(), show_page(getReportsPageFrame())), sidebar)
    add_button("Logout", logout, sidebar)

    Frame(sidebar, bg=BG).pack(fill="both", expand=True)
    
    # --- LOGO ---
    img = Image.open("iconImages/council_logo_menu.png")
    img = img.resize((200, 200), Image.LANCZOS)
    logo_img = ImageTk.PhotoImage(img)

    # keep reference
    sidebar.logo_img = logo_img

    Label(sidebar, image=sidebar.logo_img, bg=BG).pack(pady=5)

    show_page(getDashboardPageFrame())

def add_button(text, command, frame, width=20, height=3, **kw):
    
    btn = FlatHoverButton(
        frame,
        text=text,
        command=command,
        height=height,
        **kw
    )

    if width:
        btn.config(width=width)

    btn.pack(fill="x", pady=2)

    return btn
    
def show_page(page):
    page.tkraise()

def logout():
    from graphical_interface.graphicalInterface import (
        root,
        show_frame,
        LARGE_FRAME_SIZE,
        logInFrame,
    )

    # Clear user
    state.current_user = None

    # Remove menu bar
    root.config(menu="")

    # Show login frame again
    
    show_frame(logInFrame, LARGE_FRAME_SIZE)
  