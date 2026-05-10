import json
from datetime import datetime, timezone
from mysql.connector import Error
from dotenv import load_dotenv
from database import create_db_server_connection

load_dotenv()

SNAPSHOT_ID = 1

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


_RISK_NAME_TO_OUTCOME = {
    'Comply':        'comply',
    'Not comply':    'not_comply',
    'Missing':       'missing',
    'Pay attention': 'pay_attention',
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


def _fetch_risk_level_map(cursor):
    """Return {risk_name: risk_level_id} from the risk_levels table."""
    cursor.execute("SELECT risk_level_id, risk_name FROM risk_levels")
    return {row[1]: row[0] for row in cursor.fetchall()}


def _fetch_db_rule_id(cursor, artifact_rule_id):
    """
    Resolve an artifact rule id (e.g. 'R1') to the DB rules.rule_id integer.
    Ingestion stores the artifact id in rules.rule_name.
    """
    cursor.execute(
        "SELECT rule_id FROM rules WHERE rule_name = %s LIMIT 1",
        (artifact_rule_id,),
    )
    row = cursor.fetchone()
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
    conn = create_db_server_connection()
    if conn is None:
        print("save_report: database connection failed.")
        return None

    try:
        cursor = conn.cursor()
        risk_level_map = _fetch_risk_level_map(cursor)

        # --- Insert the report header (immutable from this point) ---
        cursor.execute(
            """
            INSERT INTO compliance_reports
                (contract_id, snapshot_id, prior_report_id, compliance_status, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (contract_id, SNAPSHOT_ID, prior_report_id, 'pending_review', datetime.now(timezone.utc)),
        )
        report_id = cursor.lastrowid

        # --- Insert one risk row per finding ---
        skipped = 0
        for finding in findings:
            artifact_rule_id = finding.get('rule_id')
            db_rule_id = _fetch_db_rule_id(cursor, artifact_rule_id)
            if db_rule_id is None:
                print(f"save_report: no DB rule found for rule_id '{artifact_rule_id}' — skipping.")
                skipped += 1
                continue

            outcome = (finding.get('outcome') or '').strip().lower()
            risk_name = _OUTCOME_TO_RISK_NAME.get(outcome)
            risk_level_id = risk_level_map.get(risk_name) if risk_name else None

            finding_text = finding.get('clause_quoted') or finding.get('reason') or ''
            description = finding.get('reason') or ''

            cursor.execute(
                """
                INSERT INTO compliance_risks
                    (report_id, risk_level_id, rule_id, finding_text, description)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (report_id, risk_level_id, db_rule_id, finding_text, description),
            )

        written = len(findings) - skipped

        cursor.execute(
            """
            INSERT INTO audit_logs
                (entity_type, entity_id, action, actor, timestamp_at, delta)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                'compliance_report',
                report_id,
                'report_generated',
                'system',
                datetime.now(timezone.utc),
                json.dumps({
                    'contract_id':     contract_id,
                    'snapshot_id':     SNAPSHOT_ID,
                    'findings_written': written,
                    'findings_skipped': skipped,
                }),
            ),
        )

        conn.commit()
        print(f"save_report: report_id={report_id} | {written} findings written, {skipped} skipped.")
        return report_id

    except Error as err:
        print(f"save_report error: {err}")
        conn.rollback()
        return None

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
