from tkinter import Button, Frame, Label

from database.database import selectLastReportDone, selectAllComplianceReports
from graphical_interface.widgets.roundedCardClass import make_rounded_card
from graphical_interface.graphicalInterface import BG, CARD, PRIMARY
from graphical_interface.analyseContractWinfows import makeNewAnalysis

def openDashboardPage(content):
    
    global dashboardPageFrame

    dashboardPageFrame = Frame(content, bg=CARD)
    dashboardPageFrame.grid(row=0, column=0, sticky="nsew")


    shadow_topCard, topCard = make_rounded_card(dashboardPageFrame, width=1000, height=200, radius=12, bg=BG, frame_color=CARD)
    shadow_topCard.pack(fill="x", padx=35, pady=35)
    Label(topCard, text="Welcome to the SCC Compliance Tool", font=("Arial", 16, "bold"), bg=BG).place(relx=0.5, y=40, anchor="center")
    Label(topCard, text="Analyse third-party contracts against approved rules derived from", bg=BG).place(relx=0.5, y=100, anchor="center")
    Label(topCard, text="legislation and internal policies. Findings are factual - no severity judgements.", bg=BG).place(relx=0.5, y=140, anchor="center")

    secondLineFrame = Frame(dashboardPageFrame, bg=CARD)
    secondLineFrame.pack(fill="x", pady=(0,35))

    shadow_reportsCard, reportsCard = make_rounded_card(secondLineFrame, width=480, height=200, radius=12, bg=BG, frame_color=CARD)
    shadow_reportsCard.pack(side="left", padx=(35, 15))
    Label(reportsCard, text="📋",font=("Arial", 20), bg=BG).place(x=20, y=40, anchor="w")
    Label(reportsCard, text="Total of Reports Run", font=("Arial", 12, "bold"), bg=BG).place(x=20, y=100, anchor='w')
    numberOfReportsLabel = Label(reportsCard, text=str(len(selectAllComplianceReports())), font=("Arial", 16, "bold"), fg=PRIMARY, bg=BG)
    numberOfReportsLabel.place(x=20, y=140, anchor='w')
    
    shadow_lastAnalysisCard, lastAnalysisCard = make_rounded_card(secondLineFrame, width=480, height=200, radius=12, bg=BG, frame_color=CARD)
    shadow_lastAnalysisCard.pack(side="left", padx=(15, 35))
    Label(lastAnalysisCard, text="🗓",font=("Arial", 20), bg=BG).place(x=20, y=40, anchor="w")
    Label(lastAnalysisCard, text="Last Analysis", font=("Arial", 12, "bold"), bg=BG).place(x=20, y=100, anchor='w')
    lastAnalysisLabel = Label(lastAnalysisCard, text=selectLastReportDone()[0][5], font=("Arial", 16, "bold"), fg=PRIMARY, bg=BG)
    lastAnalysisLabel.place(x=20, y=140, anchor='w')

    shadow_bottomCard, bottomCard = make_rounded_card(dashboardPageFrame, width=1000, height=200, radius=12, bg=BG, frame_color=CARD)
    shadow_bottomCard.pack(fill="x", padx=35)
    Label(bottomCard, text="Quick Actions", font=("Arial", 16, "bold"), bg=BG).place(x=20, y=20, anchor="w")
    
    def goToContractAnalysis():
        makeNewAnalysis()
        load_dashboard()

    Button(
        bottomCard, 
        text="Analyse Contract", 
        command= lambda: goToContractAnalysis(), 
        font=("Arial", 12, "bold"),
        height=2, 
        width=14, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E",
        activeforeground="white", 
        relief="flat"
    ).place(x=20, y= 80)

    def goToGroupAnalysis():
        makeNewAnalysis(is_group=True)
        load_dashboard()

    Button(
        bottomCard, 
        text="Analyse Group", 
        font=("Arial", 12, "bold"),
        command= lambda: goToGroupAnalysis(), 
        height=2, 
        width=14, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x=200, y= 80)

    def goToReports():
        from graphical_interface.main_frame.reportsPage import load_reports, reportsPageFrame
        from graphical_interface.main_frame.sidebarMenuFrame import dashboard_side_button, reports_side_button, show_page

        dashboard_side_button.deactivate()
        reports_side_button.activate()
        load_reports()
        show_page(reportsPageFrame)

    Button(
        bottomCard, 
        text="View Reports", 
        font=("Arial", 12, "bold"),
        command= lambda: goToReports(), 
        height=2, 
        width=14, 
        bg="#0078D4", 
        fg="white", 
        activebackground="#005A9E", 
        activeforeground="white",
        relief="flat"
    ).place(x=380, y= 80)

    global load_dashboard

    def load_dashboard():

        numberOfReportsLabel.config(text=str(len(selectAllComplianceReports())))
        lastAnalysisLabel.config(text=selectLastReportDone()[0][5])
    