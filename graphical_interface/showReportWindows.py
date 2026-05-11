

from tkinter import Frame, Label, scrolledtext

from graphical_interface.graphicalInterface import create_modal_window
from database.database import selectComplianceRiskFromReportId, selectRuleById, selectRiskLevelByID


def showReports(report_id):

    global resultsScrolledText

    win = create_modal_window("Report", toggle=False)
    if not win:
        return

    win.withdraw()

    Label(win, text="Report", font=("Arial", 16)).pack(pady=10)

    frame = Frame(win)
    frame.pack(pady=10, padx=20, fill="both", expand=True)   # FIXED

    resultsScrolledText = scrolledtext.ScrolledText(
        frame,
        width=115,
        height=45,
        bg="white"
    )
    resultsScrolledText.pack(fill="both", expand=True)

    show_findings(report_id)

    win.update_idletasks()
    win.deiconify()
    win.grab_set()

def show_findings(report_id):
    risks = selectComplianceRiskFromReportId(report_id)
    print(risks)
    resultText = ""
    for risk in risks:
        rule = selectRuleById(risk[3])[0]
        risk_level = selectRiskLevelByID(risk[2])[0]
        resultText += (
            f"Rule ID: {rule[2]}\n"
            f"Outcome: {risk_level[1]}\n"
            f"Findings: {risk[5] or '(none)'}\n"
            f"Description: {risk[4]}\n"
           + "-"*80 + "\n"
        )

    resultsScrolledText.insert("1.0", resultText)
    print(resultText)
