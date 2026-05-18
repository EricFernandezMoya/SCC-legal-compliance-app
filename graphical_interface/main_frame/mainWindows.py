from tkinter import Frame, Menu

from graphical_interface.main_frame.sidebarMenuFrame import logout, openSideButtonMenu

from graphical_interface.graphicalInterface import (
    BG,
    root,
    show_frame,
    LARGE_FRAME_SIZE,
    mainFrame,
)

from graphical_interface.main_frame.dashBoardPage import openDashboardPage
from graphical_interface.main_frame.legislationPage import openDocumentsPage
from graphical_interface.main_frame.contractsPage import openContractsPage
from graphical_interface.main_frame.usersPage import openUsersPage
from graphical_interface.main_frame.reportsPage import  openReportsPage

from graphical_interface.analyseContractWinfows import makeNewAnalysis
from graphical_interface.createContractGroupWindows import contractGroupWindows
from graphical_interface.createContractWindows import openNewContractWindow
from graphical_interface.createDocumentVersionWindows import openCreateDocumentVersionWindows
from graphical_interface.createDocumentWindows import openNewLegalDocument
from graphical_interface.createUserWindows import createUserWindows

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

    openDashboardPage(content)
    openDocumentsPage(content)
    openContractsPage(content)
    openReportsPage(content)
    openUsersPage(content)

    openSideButtonMenu(sidebar)
    
    menubar = Menu(root)

    # Documents menu
    doc_menu = Menu(menubar, tearoff=0)
    doc_menu.add_command(label="Add Legislation", command=openNewLegalDocument)
    doc_menu.add_command(label="Add Legislation Version", command=openCreateDocumentVersionWindows)
    menubar.add_cascade(label="Legislation", menu=doc_menu)

    # Contracts menu
    contract_menu = Menu(menubar, tearoff=0)
    contract_menu.add_command(label="Add Contract", command=openNewContractWindow)
    contract_menu.add_command(label="Add Group", command=contractGroupWindows)
    contract_menu.add_command(label="Analyse Contract", command=makeNewAnalysis)
    contract_menu.add_command(label="Analyse Group", command=lambda:makeNewAnalysis(is_group=True))
    menubar.add_cascade(label="Contracts", menu=contract_menu)

    # User menu
    user_menu = Menu(menubar, tearoff=0)
    user_menu.add_command(label="Create User", command=createUserWindows)
    user_menu.add_separator()
    user_menu.add_command(label="Logout", command=logout)
    menubar.add_cascade(label="User", menu=user_menu)

    root.config(menu=menubar)

