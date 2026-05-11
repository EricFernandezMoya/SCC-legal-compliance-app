import json
from datetime import datetime, timezone
from pathlib import Path
from mysql.connector import Error
from dotenv import load_dotenv
from database.database import *

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Claude outcome strings → risk_levels.risk_name
_OUTCOME_TO_RISK_NAME = {
    'comply':        'PASS',
    'not_comply':    'NOT_COMPLY',
    'not comply':    'NOT_COMPLY',
    'missing':       'MISSING',
    'attention':     'PAY_ATTENTION',
    'ambiguous':     'PAY_ATTENTION',
    'pay_attention': 'PAY_ATTENTION',
    'pay attention': 'PAY_ATTENTION',
    'n/a':           'MISSING',
    'na':            'MISSING',
}


_RISK_NAME_TO_OUTCOME = {
    'PASS':          'comply',
    'NOT_COMPLY':    'not_comply',
    'MISSING':       'missing',
    'PAY_ATTENTION': 'pay_attention',
}


def fetch_prior_findings(prior_report_id, conn=None):
    """
    Fetch all findings from a prior report keyed by artifact rule_id.
    Returns {rule_name: {'outcome': str, 'clause_quoted': str, 'reason': str}}
    or an empty dict if the report is not found or the connection fails.
    """
    close_conn = conn is None
    if conn is None:
        conn = create_db_server_connection()
        if conn is None:
            print("fetch_prior_findings: database connection failed.")
            return {}

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.rule_name,
                   rl.risk_name,
                   cr.finding_text,
                   cr.description
            FROM compliance_risks cr
            JOIN rules       r  ON cr.rule_id       = r.rule_id
            JOIN risk_levels rl ON cr.risk_level_id = rl.risk_level_id
            WHERE cr.report_id = %s
            """,
            (prior_report_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
    except Error as err:
        print(f"fetch_prior_findings error: {err}")
        return {}
    finally:
        if close_conn and conn.is_connected():
            conn.close()

    return {
        row['rule_name']: {
            'outcome':       _RISK_NAME_TO_OUTCOME.get(row['risk_name'], row['risk_name'].lower()),
            'clause_quoted': row['finding_text'],
            'reason':        row['description'],
        }
        for row in rows
    }


def _fetch_risk_level_map():
    """Return {risk_name: risk_level_id} from the risk_levels table."""
    return {row[1]: row[0] for row in selectIdAndNameFromAllRiskLevels()}


def _fetch_db_rule_id(artifact_rule_id):
    """
    Resolve an artifact rule id (e.g. 'R1') to the DB rules.rule_id integer.
    Ingestion stores the artifact id in rules.rule_name.
    """
    rows = executeQuery("SELECT rule_id FROM rules WHERE rule_name = %s", (artifact_rule_id,))
    if not rows:
        return None
    return rows[0][0]

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

    insertComplianceReport(contract_id, lastSnapshot_id, prior_report_id, None)
    report_id = selectComplianceReportByContractId(contract_id)[0][0]

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

    insertAuditLog(
        'compliance_report',
        report_id,
        'report_generated',
        'system',
        json.dumps({
            'contract_id':      contract_id,
            'snapshot_id':      lastSnapshot_id,
            'findings_written': len(findings) - skipped,
            'findings_skipped': skipped,
        }),
    )

    return report_id


_ARTIFACT_B = Path(__file__).parent.parent / "artifact_b.json"

_RISK_TO_DOCX_OUTCOME = {
    'PASS':          'PASS',
    'NOT_COMPLY':    'FAIL',
    'MISSING':       'FAIL',
    'PAY_ATTENTION': 'WARNING',
}


def build_report_data(report_id, db_conn):
    """
    Query the database and return the dict structure expected by generate_word_report().
    Returns None if the report does not exist.
    """
    with open(_ARTIFACT_B, encoding="utf-8") as fh:
        artifact = json.load(fh)
    rules_by_id = {r["id"]: r for r in artifact.get("rules", [])}

    cursor = db_conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT cr.report_id, cr.created_at,
                   c.contract_name, c.counterparty, c.uploaded_by
            FROM compliance_reports cr
            JOIN contracts c ON cr.contract_id = c.contract_id
            WHERE cr.report_id = %s
            """,
            (report_id,),
        )
        report_row = cursor.fetchone()
        if report_row is None:
            return None

        cursor.execute(
            """
            SELECT r.rule_name AS rule_id,
                   r.description AS rule_title,
                   rl.risk_name,
                   cri.finding_text,
                   cri.description
            FROM compliance_risks cri
            JOIN rules r       ON cri.rule_id       = r.rule_id
            JOIN risk_levels rl ON cri.risk_level_id = rl.risk_level_id
            WHERE cri.report_id = %s
            ORDER BY cri.risk_id
            """,
            (report_id,),
        )
        risk_rows = cursor.fetchall()
    finally:
        cursor.close()

    passed = warnings = failed = critical_failures = 0
    findings = []

    for row in risk_rows:
        rule_id      = row["rule_id"] or ""
        artifact_rule = rules_by_id.get(rule_id, {})
        outcome      = _RISK_TO_DOCX_OUTCOME.get(row["risk_name"], "N/A")
        is_critical  = bool(artifact_rule.get("critical", False))

        if outcome == "PASS":
            passed += 1
        elif outcome == "WARNING":
            warnings += 1
        elif outcome == "FAIL":
            failed += 1
            if is_critical:
                critical_failures += 1

        findings.append({
            "rule_id":      rule_id,
            "rule_title":   artifact_rule.get("title") or row["rule_title"] or "",
            "critical":     is_critical,
            "outcome":      outcome,
            "clause_quoted": row["finding_text"] or "",
            "reason":       row["description"] or "",
            "citation":     artifact_rule.get("citation") or "",
        })

    created_at = report_row["created_at"]
    if isinstance(created_at, datetime):
        generated_at = created_at.strftime("%d %B %Y %H:%M")
    else:
        generated_at = str(created_at)[:16]

    return {
        "report_id":    report_id,
        "generated_at": generated_at,
        "contract_name": report_row["contract_name"] or "",
        "vendor_name":  report_row["counterparty"] or "",
        "analyst":      report_row["uploaded_by"] or "N/A",
        "summary": {
            "total_rules":       passed + warnings + failed,
            "passed":            passed,
            "warnings":          warnings,
            "failed":            failed,
            "critical_failures": critical_failures,
        },
        "findings": findings,
    }