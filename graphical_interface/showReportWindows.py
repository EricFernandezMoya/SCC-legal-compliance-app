from docx import Document

from tkinter import Button, Frame, Label, scrolledtext, filedialog

from graphical_interface.graphicalInterface import create_modal_window, LARGE_FRAME_SIZE
from database.database import selectComplianceRiskFromReportId, selectRuleById, selectRiskLevelByID, selectComplianceReportById


def showReports(report_id):

    global resultsScrolledText

    win = create_modal_window("Report", size=LARGE_FRAME_SIZE, toggle=False)
    if not win:
        return

    win.withdraw()


    Label(win, text="Report", font=("Arial", 16)).pack(pady=10)

    save_button = Button(
        win,
        text="Save as Word Document",
        command=lambda: save_report_to_word(resultsScrolledText),
        width=25
    )
    save_button.pack(pady=10)

    frame = Frame(win)
    frame.pack(pady=10, padx=20, fill="x", expand=True) 

    resultsScrolledText = scrolledtext.ScrolledText(
        frame,
        width=215,
        height=125,
        bg="white"
    )
    resultsScrolledText.pack(fill="x", expand=True)

    show_findings(report_id)

    win.update_idletasks()
    win.deiconify()
    win.grab_set()

def show_findings(report_id):
    risks = selectComplianceRiskFromReportId(report_id)
    
    resultText = ""
    
    for risk in risks:
        rule = selectRuleById(risk[3])[0]
        risk_level = selectRiskLevelByID(risk[2])[0]
        resultText += (
            f"Rule: {rule[2]} - {rule[1]}\n"
            f"Outcome: {risk_level[1]}\n"
            f"Findings: {risk[5] or '(none)'}\n"
            f"Description: {risk[4]}\n"
           + "-"*80 + "\n"
        )

    resultsScrolledText.insert("1.0", resultText)
    
def save_report_to_word(text_widget):
    # Ask user where to save
    file_path = filedialog.asksaveasfilename(
        defaultextension=".docx",
        filetypes=[("Word Document", "*.docx")],
        title="Save Report As"
    )

    if not file_path:
        return  # user cancelled

    # Get text from the widget
    content = text_widget.get("1.0", "end-1c")

    # Save to Word
    doc = Document()
    for line in content.split("\n"):
        doc.add_paragraph(line)

    doc.save(file_path)
