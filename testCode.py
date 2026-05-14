from graphical_interface.showReportWindows import showReports
from report_analysis.document_parser import parseWebsite
from report_analysis.reports import save_report
from database.database import insertRiskLevels, selectComplianceReportByContractId, createAuditLogsTable, createComplianceRisksTable, selectComplianceRiskFromReportId


text = parseWebsite("https://www.zoom.com/en/trust/privacy/privacy-statement/?ampDeviceId=e4004e69-267a-4105-9900-a1641f2ac339&ampSessionId=undefined")
print(text)