from tkinter import Frame, Label, Menu
from PIL import Image, ImageTk

from graphical_interface.widgets.roundedCardClass import make_rounded_card
from graphical_interface.widgets.searchableTableClass import SearchableTable

from graphical_interface.createDocumentWindows import openNewLegalDocument
from graphical_interface.showReportWindows import showReports
from graphical_interface.createDocumentVersionWindows import openCreateDocumentVersionWindows
from graphical_interface.createContractGroupWindows import contractGroupWindows
from graphical_interface.createUserWindows import createUserWindows
from graphical_interface.createContractWindows import openNewContractWindow
from graphical_interface.analyseContractWinfows import analyseNewContract

from graphical_interface.widgets.sideMenuButtonClass import FlatHoverButton
from state import state
from database.database import selectDocumentsforPage, selectContractForPage, selectUserForPage, selectReportForPage, selectPrivilegeById

from graphical_interface.graphicalInterface import (
    BG,
    CARD,
    PRIMARY,
    TEAL,
    TXT,
    root,
    show_frame,
    LARGE_FRAME_SIZE,
    mainFrame,
    logInFrame
)



def openMainWindows():

    # Attach mainFrame to root
    mainFrame.grid(row=0, column=0, sticky="nsew")
    show_frame(mainFrame, LARGE_FRAME_SIZE)

    # Create sidebar and content INSIDE mainFrame
    sidebar = Frame(mainFrame, width=400, bg=BG)
    sidebar.grid(row=0, column=0, sticky="ns")

    content = Frame(mainFrame, bg="white")
    content.grid(row=0, column=1, sticky="nsew")

    content.grid_rowconfigure(0, weight=1)
    content.grid_columnconfigure(0, weight=1)

    mainFrame.grid_columnconfigure(1, weight=1)
    mainFrame.grid_rowconfigure(0, weight=1)

    # Create pages INSIDE content
    homePage = Frame(content, bg=CARD)
    documentsPage = Frame(content, bg=CARD)
    contractsPage = Frame(content, bg=CARD)
    usersPage = Frame(content, bg=CARD)
    reportsPage = Frame(content, bg=CARD)


    for page in (homePage, documentsPage, contractsPage, usersPage, reportsPage):
        page.grid(row=0, column=0, sticky="nsew")

    # Menu bar
    menubar = Menu(root)
    root.config(menu=menubar)

    # -----------------------------
    # MENU BAR
    # -----------------------------

    menubar = Menu(root)

    # File menu
    file_menu = Menu(menubar, tearoff=0)
    file_menu.add_command(label="Logout", command=logout)
    file_menu.add_separator()
    file_menu.add_command(label="Close", command=root.quit)
    menubar.add_cascade(label="File", menu=file_menu)

    # Documents menu
    doc_menu = Menu(menubar, tearoff=0)
    doc_menu.add_command(label="Add Legislation", command=openNewLegalDocument)
    doc_menu.add_command(label="Add Legislation Version", command=openCreateDocumentVersionWindows)
    menubar.add_cascade(label="Legislation", menu=doc_menu)

    # Contracts menu
    contract_menu = Menu(menubar, tearoff=0)
    contract_menu.add_command(label="Add Contract", command=openNewContractWindow)
    contract_menu.add_command(label="Add Group", command=contractGroupWindows)
    contract_menu.add_command(label="Analyse Contract", command=analyseNewContract)
    menubar.add_cascade(label="Contracts", menu=contract_menu)

    # Admin menu
    user_menu = Menu(menubar, tearoff=0)
    user_menu.add_command(label="Create User", command=createUserWindows)
    menubar.add_cascade(label="User", menu=user_menu)

    root.config(menu=menubar)

    # -----------------------------
    # CONTENT PAGES
    # -----------------------------

    # --- HOME PAGE ---

    Label(homePage, text="Home Page", font=("Arial", 16), bg=CARD).place(relx=0.5, y=20, anchor="center")
   
    # --- LEGISLATION PAGE ---

    Label(documentsPage, text="Legislation", font=("Arial", 16), bg=CARD).place(relx=0.5, y=20, anchor="center")
    
    document_columns = ("name", "jurisdiction", "year")
    document_table = SearchableTable(documentsPage, document_columns, selectDocumentsforPage)
    document_table.place(relx=0.5, y=60, width=900, height=600, anchor='n')

    def load_documents():
        document_table.all_data = document_table.load_function()
        document_table.refresh_table(document_table.all_data)

    # --- CONTRACTS PAGE ---

    Label(contractsPage, text="Contracts", font=("Arial", 16), bg=CARD).place(relx=0.5, y=20, anchor="center")
    
    contract_columns = ("group", "name", "type", "version")
    contract_table = SearchableTable(contractsPage, contract_columns, selectContractForPage)
    contract_table.place(relx=0.5, y=60, width=900, height=600, anchor='n')

    def load_contracts():
        contract_table.all_data = contract_table.load_function()
        contract_table.refresh_table(contract_table.all_data)

   # --- USERS PAGE ---

    Label(usersPage, text="Users", font=("Arial", 16), bg=CARD).place(relx=0.5, y=20, anchor="center")
    
    users_columns = ("Username", "Full Name", "Privilege")

    def open_user_details(user_id, values):
        print("Double-clicked user:", user_id, values)

    user_table = SearchableTable(usersPage, users_columns, selectUserForPage, on_double_click=open_user_details)
    user_table.place(relx=0.5, y=60, width=900, height=600, anchor='n')

    def load_users():
        user_table.all_data = user_table.load_function()
        user_table.refresh_table(user_table.all_data)

    # --- REPORTS PAGE ---

    Label(reportsPage, text="Reports", font=("Arial", 16), bg=CARD).place(relx=0.5, y=20, anchor="center")
    
    reports_columns = ("Contract Group", "Contract Type", "Compliance Status", "Created at")

    def load_reports():
        report_table.all_data = report_table.load_function()
        report_table.refresh_table(report_table.all_data)

    def open_report_details(report_id, values):

        showReports(report_id)
        print("Double-clicked user:", report_id, values)

    report_table = SearchableTable(reportsPage, reports_columns, selectReportForPage, on_double_click=open_report_details)
    report_table.place(relx=0.5, y=60, width=900, height=600, anchor='n')

    # -----------------------------
    # LEFT SIDEBAR
    # -----------------------------
    
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
    ).pack(fill="x", padx=14, pady=(20, 2))

    Label(
        userCard,
        text=selectPrivilegeById(state.current_user.get_privilege())[0][1],
        bg=CARD,
        fg=TXT,
        font=("Arial", 11),
        anchor="w"
    ).pack(fill="x", padx=14, pady=(0, 10))
    
    add_button("Home",lambda: show_page(homePage), sidebar, active=True).activate()
    add_button("Legislation",lambda: (load_documents(),show_page(documentsPage)), sidebar)
    add_button("Contracts", lambda: (load_contracts(), show_page(contractsPage)), sidebar)
    add_button("Users", lambda: (load_users(), show_page(usersPage)), sidebar)
    add_button("Reports", lambda:(load_reports(), show_page(reportsPage)), sidebar)
    add_button("Logout", logout, sidebar)

    Frame(sidebar, bg=BG).pack(fill="both", expand=True)
    
    # --- LOGO ---
    img = Image.open("iconImages/council_logo_menu.png")
    img = img.resize((200, 200), Image.LANCZOS)
    logo_img = ImageTk.PhotoImage(img)

    # keep reference
    sidebar.logo_img = logo_img

    Label(sidebar, image=sidebar.logo_img, bg=BG).pack(pady=5)



    show_page(homePage)

def add_button(text, command, frame, fg=BG, hover=TEAL, active=PRIMARY, width=20, height=3, **kw):
    
    btn = FlatHoverButton(
        frame,
        text=text,
        command=command,
        fg=fg,
        hover=hover,
        active=active,
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

    # Clear user
    state.current_user = None

    # Remove menu bar
    root.config(menu="")

    # Show login frame again
    show_frame(logInFrame, LARGE_FRAME_SIZE)
    
