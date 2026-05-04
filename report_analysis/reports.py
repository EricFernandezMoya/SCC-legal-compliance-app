import json
from datetime import datetime, timezone
from mysql.connector import Error
from dotenv import load_dotenv
from database.database import *

load_dotenv()

# Claude outcome strings → risk_levels.risk_name
_OUTCOME_TO_RISK_NAME = {
    'comply':      'Comply',
    'not_comply':  'Not comply',
    'not comply':  'Not comply',
    'missing':     'Missing',
    'attention':   'Pay attention',
    'ambiguous':   'Pay attention',
    'pay_attention': 'Pay attention',
    'pay attention': 'Pay attention',
}


def _fetch_risk_level_map():
    """Return {risk_name: risk_level_id} from the risk_levels table."""
    return {row[1]: row[0] for row in selectIdAndNameFromAllRiskLevels()}


def _fetch_db_rule_id(artifact_rule_id):
    """
    Resolve an artifact rule id (e.g. 'R1') to the DB rules.rule_id integer.
    Ingestion stores the artifact id in rules.rule_code.
    """
    row = selectRuleByCode(artifact_rule_id)[0]
    return row[0] if row else None

def save_report(contract_id, findings, prior_report_id=None):
    """
    Persist one compliance_reports row and one compliance_risks row per finding.

    Returns the new report_id on success, or None on failure.
    Reports are immutable — this function only inserts, never updates or deletes.

    Args:
        contract_id:     FK to contracts.contract_id
        findings:        list of finding dicts from analyse_contract()
        prior_report_id: FK to compliance_reports.report_id (renewal only)
    """
        
    risk_level_map = _fetch_risk_level_map()

    lastSnapshot_id = selectLastRulesSnapshot()[0][0]

    insertComplianceReport(contract_id, lastSnapshot_id, prior_report_id, 'pending_review')
    report_id = selectComplianceReportByContractId(contract_id)

        # --- Insert one risk row per finding ---
    skipped = 0
    for finding in findings:
        artifact_rule_id = finding.get('rule_id')
        db_rule_id = _fetch_db_rule_id(artifact_rule_id)
        if db_rule_id is None:
            print(f"save_report: no DB rule found for rule_id '{artifact_rule_id}' — skipping.")
            skipped += 1
            continue

        outcome = (finding.get('outcome') or '').strip().lower()
        risk_name = _OUTCOME_TO_RISK_NAME.get(outcome)
        risk_level_id = risk_level_map.get(risk_name) if risk_name else None

        finding_text = finding.get('clause_quoted') or finding.get('reason') or ''
        description = finding.get('reason') or ''

        insertComplianceRisk(report_id, risk_level_id, db_rule_id, finding_text, description)
        
        written = len(findings) - skipped

        insertAuditLog(
                'compliance_report',
                report_id,
                'report_generated',
                'system',
                json.dumps({
                    'contract_id':     contract_id,
                    'snapshot_id':     lastSnapshot_id,
                    'findings_written': written,
                    'findings_skipped': skipped,
                }),
            )