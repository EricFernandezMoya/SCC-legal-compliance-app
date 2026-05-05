"""
legislation_update.py

Analyses a new or updated piece of legislation against the existing rules in
artifact_b.json and returns proposed changes for reviewer approval.

Workflow:
  1. analyse_legislation_update(file_path, document_version_id)
        → calls Claude, saves proposed changes to DB, returns {review_id, proposed_changes}
  2. Reviewer inspects proposed_changes and builds a decisions list
  3. save_reviewer_decisions(review_id, decisions, reviewed_by)
        → persists decisions into the review row, logs each to audit_logs
  4. apply_accepted_changes(review_id, reviewed_by)
        → applies accepted decisions to rules table + artifact_b.json
        → creates a new rules_snapshot
        → sets review status to APPLIED
        → returns a summary dict
"""

import json
import os
import shutil
from datetime import datetime, timezone

from anthropic import Anthropic
from dotenv import load_dotenv
from mysql.connector import Error

from database import create_db_server_connection
from document_parser import parseDOC, parsePDF

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, 'artifact_b.json')


# ---------------------------------------------------------------------------
# 1 — Extract text from legislation file
# ---------------------------------------------------------------------------

def extract_legislation_text(file_path):
    """
    Parse a legislation file (PDF or DOCX) and return its text.
    Raises ValueError for unsupported file types.
    """
    ext = os.path.splitext(file_path)[1].lower()
    print(f"extract_legislation_text: reading '{os.path.basename(file_path)}' ({ext})")

    if ext == '.pdf':
        return parsePDF(file_path)
    if ext in ('.doc', '.docx'):
        return parseDOC(file_path)

    raise ValueError(
        f"Unsupported file type '{ext}'. Only .pdf, .doc, and .docx are supported."
    )


# ---------------------------------------------------------------------------
# 2 — Load current rules from artifact_b.json
# ---------------------------------------------------------------------------

def load_current_rules():
    """
    Load artifact_b.json and return (master_prompt, rules_list, full_data).
    full_data is the complete parsed dict — needed to preserve all fields on write.
    """
    print(f"load_current_rules: reading {JSON_PATH}")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    master_prompt = data.get('master_prompt', '')
    rules         = data.get('rules', [])
    print(f"load_current_rules: loaded {len(rules)} rules.")
    return master_prompt, rules, data


# ---------------------------------------------------------------------------
# 3 — Build Claude prompt
# ---------------------------------------------------------------------------

def build_legislation_prompt(current_rules, legislation_text):
    """
    Build the prompt sent to Claude.

    current_rules:    list of rule dicts from artifact_b.json
    legislation_text: full text of the new or updated legislation

    Returns the user-turn string.
    """
    rules_block = []
    for rule in current_rules:
        triggers     = rule.get('ambiguity_triggers', [])
        triggers_fmt = '\n'.join(f'  - {t}' for t in triggers) if triggers else '  (none)'
        rules_block.append(
            f"RULE ID: {rule['id']}\n"
            f"CATEGORY: {rule.get('category', '')}\n"
            f"CHECK: {rule.get('check', '')}\n"
            f"WHY: {rule.get('why', '')}\n"
            f"CITATION: {rule.get('citation', '')}\n"
            f"COMPLY REQUIRES: {rule.get('comply_requires', '')}\n"
            f"MISSING IF: {rule.get('missing_if', '')}\n"
            f"APPLIES TO: {rule.get('applies_to', '')}\n"
            f"AMBIGUITY TRIGGERS:\n{triggers_fmt}"
        )

    rules_text = '\n\n'.join(rules_block)

    return (
        "You are reviewing a new or updated piece of legislation against an existing set of compliance rules.\n\n"
        "Your task: identify only changes that are genuinely required by the new legislation. "
        "Do not propose cosmetic edits, speculative improvements, or changes not directly driven by the text provided.\n\n"
        "For each required change, return one object in the JSON array. "
        "Use exactly these three change types:\n"
        "  MODIFY_RULE   — an existing rule needs its text updated\n"
        "  NEW_RULE      — a new compliance obligation not covered by any existing rule\n"
        "  OBSOLETE_RULE — an existing rule is no longer required by current law\n\n"
        "Each change object must have exactly this structure "
        "(include only the keys relevant to the change type — see notes below):\n"
        "{\n"
        '  "type": "MODIFY_RULE | NEW_RULE | OBSOLETE_RULE",\n'
        '  "rule_id": "existing rule id, or null for NEW_RULE",\n'
        '  "field": "for MODIFY_RULE only — the rule field being changed, e.g. check, citation, comply_requires",\n'
        '  "current_value": "for MODIFY_RULE only — the current text of that field",\n'
        '  "proposed_value": "for MODIFY_RULE only — the proposed new text for that field",\n'
        '  "proposed_rule": {\n'
        '    "id": "for NEW_RULE — suggest an id continuing the existing numbering scheme",\n'
        '    "category": "existing category code that best fits",\n'
        '    "check": "...",\n'
        '    "why": "...",\n'
        '    "citation": "...",\n'
        '    "comply_requires": "...",\n'
        '    "missing_if": "...",\n'
        '    "applies_to": "...",\n'
        '    "ambiguity_triggers": []\n'
        "  },\n"
        '  "reason": "plain English explanation of why this change is needed — written for a non-technical reviewer",\n'
        '  "citation": "the specific section or clause of the new legislation that drives this change"\n'
        "}\n\n"
        "Notes:\n"
        "- For MODIFY_RULE: include rule_id, field, current_value, proposed_value, reason, citation. Omit proposed_rule.\n"
        "- For NEW_RULE: include proposed_rule, reason, citation. Set rule_id to null. Omit field, current_value, proposed_value.\n"
        "- For OBSOLETE_RULE: include rule_id, reason, citation. Omit all other fields.\n"
        "- Return ONLY a JSON array. No preamble, no explanation outside the array.\n\n"
        f"EXISTING RULES:\n{rules_text}\n\n"
        f"NEW LEGISLATION:\n{legislation_text}"
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _call_claude(user_prompt):
    """Single Claude call — same model and pattern as analysis.py."""
    client = Anthropic()
    print("_call_claude: sending request to Claude ...", flush=True)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def _parse_proposed_changes(response_text):
    """Extract and validate the JSON array from Claude's response."""
    text = response_text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[-1]
        text = text.rsplit('```', 1)[0].strip()

    try:
        changes = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"_parse_proposed_changes: JSON parse error — {e}")
        return [{
            "type":   "PARSE_ERROR",
            "reason": f"Claude response was not valid JSON: {e}",
            "_raw":   response_text,
        }]

    if not isinstance(changes, list):
        changes = [changes]

    return changes


def _backup_artifact():
    """
    Copy artifact_b.json to a timestamped backup in the same directory.
    Returns the backup path.
    """
    timestamp   = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BASE_DIR, f'artifact_b_backup_{timestamp}.json')
    shutil.copy2(JSON_PATH, backup_path)
    print(f"_backup_artifact: backup written to {backup_path}")
    return backup_path


def _get_conn(conn):
    """Return (conn, close_conn) — opens a new connection only if conn is None."""
    if conn is not None:
        return conn, False
    new_conn = create_db_server_connection()
    if new_conn is None:
        raise RuntimeError("Database connection failed.")
    return new_conn, True


# ---------------------------------------------------------------------------
# DB functions
# ---------------------------------------------------------------------------

def save_proposed_changes(document_version_id, proposed_changes, conn=None):
    """
    Insert a new legislation_update_reviews row with status PENDING.

    Args:
        document_version_id: FK to document_versions.version_id
        proposed_changes:    list of proposed change dicts from Claude

    Returns:
        review_id of the inserted row
    """
    db, close = _get_conn(conn)
    try:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO legislation_update_reviews
                (document_version_id, proposed_changes, status)
            VALUES (%s, %s, 'PENDING')
            """,
            (document_version_id, json.dumps(proposed_changes)),
        )
        review_id = cursor.lastrowid
        db.commit()
        print(f"save_proposed_changes: review_id={review_id} saved ({len(proposed_changes)} change(s)).")
        return review_id
    except Error as err:
        db.rollback()
        raise RuntimeError(f"save_proposed_changes failed: {err}") from err
    finally:
        if close and db.is_connected():
            cursor.close()
            db.close()


def fetch_pending_review(review_id, conn=None):
    """
    Fetch a single legislation_update_reviews row by review_id.

    Returns:
        dict with keys: review_id, document_version_id, proposed_changes (list), status

    Raises:
        ValueError if the review is not found.
    """
    db, close = _get_conn(conn)
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT review_id, document_version_id, proposed_changes, status
            FROM legislation_update_reviews
            WHERE review_id = %s
            """,
            (review_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"fetch_pending_review: review_id={review_id} not found.")
        # MySQL may return JSON column as str or dict depending on driver version
        if isinstance(row['proposed_changes'], str):
            row['proposed_changes'] = json.loads(row['proposed_changes'])
        print(f"fetch_pending_review: review_id={review_id} status={row['status']}.")
        return row
    except ValueError:
        raise
    except Error as err:
        raise RuntimeError(f"fetch_pending_review failed: {err}") from err
    finally:
        if close and db.is_connected():
            cursor.close()
            db.close()


def save_reviewer_decisions(review_id, decisions, reviewed_by, conn=None):
    """
    Persist reviewer decisions back into the legislation_update_reviews row
    and log each decision to audit_logs.

    decisions: list of dicts, each with:
        {
          "change":       { ...original proposed change object... },
          "decision":     "ACCEPT | DECLINE | ACCEPT_WITH_EDITS",
          "edited_value": "only present for ACCEPT_WITH_EDITS"
        }

    The proposed_changes column is updated so each change object includes
    a 'decision' field (and 'edited_value' where applicable).
    """
    db, close = _get_conn(conn)
    try:
        cursor = db.cursor()
        now = datetime.now(timezone.utc)

        # Merge decision metadata into the change objects for storage
        updated_changes = []
        for d in decisions:
            entry = dict(d.get('change', {}))
            entry['decision'] = (d.get('decision') or 'DECLINE').upper().strip()
            if 'edited_value' in d:
                entry['edited_value'] = d['edited_value']
            updated_changes.append(entry)

        cursor.execute(
            """
            UPDATE legislation_update_reviews
            SET reviewed_by     = %s,
                reviewed_at     = %s,
                status          = 'REVIEWED',
                proposed_changes = %s
            WHERE review_id = %s
            """,
            (reviewed_by, now, json.dumps(updated_changes), review_id),
        )

        # Log each individual decision to audit_logs
        for entry in updated_changes:
            action  = entry.get('decision', 'DECLINE')
            rule_id = entry.get('rule_id', 'NEW')
            cursor.execute(
                """
                INSERT INTO audit_logs
                    (entity_type, entity_id, action, actor, timestamp_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                ('legislation_update_review', review_id, action, reviewed_by, now),
            )
            print(f"  audit_log: review_id={review_id} rule_id={rule_id} decision={action}")

        db.commit()
        print(f"save_reviewer_decisions: review_id={review_id} set to REVIEWED by '{reviewed_by}'.")
    except Error as err:
        db.rollback()
        raise RuntimeError(f"save_reviewer_decisions failed: {err}") from err
    finally:
        if close and db.is_connected():
            cursor.close()
            db.close()


def apply_accepted_changes(review_id, reviewed_by, conn=None):
    """
    Fetch the review, apply all ACCEPT / ACCEPT_WITH_EDITS decisions to:
      - the rules DB table (MODIFY, INSERT, DELETE)
      - artifact_b.json (backup first, then write)
    Then create a new rules_snapshot and set review status to APPLIED.

    Returns a summary dict:
        {
          "backup_path": str,
          "applied":     [list of applied change summaries],
          "declined":    [list of declined change summaries],
          "snapshot_id": int,
          "errors":      [list of error strings]
        }
    """
    print("=" * 60)
    print("APPLYING ACCEPTED CHANGES")
    print("=" * 60)

    db, close = _get_conn(conn)
    applied  = []
    declined = []
    errors   = []
    backup_path = None

    try:
        cursor = db.cursor()
        now = datetime.now(timezone.utc)

        # --- Fetch review and its decisions ---
        review = fetch_pending_review(review_id, conn=db)
        changes = review['proposed_changes']  # already have decision fields from save_reviewer_decisions

        # --- Load artifact_b.json ---
        _, _, art_data  = load_current_rules()
        art_rules       = art_data['rules']
        art_rule_index  = {r['id']: r for r in art_rules}

        # --- Backup artifact_b.json before any writes ---
        backup_path = _backup_artifact()

        # --- Apply each accepted change ---
        for change in changes:
            verdict = (change.get('decision') or 'DECLINE').upper().strip()
            ch_type = (change.get('type') or '').upper().strip()
            rule_id = change.get('rule_id')
            edited  = change.get('edited_value')

            if verdict == 'DECLINE':
                declined.append({'type': ch_type, 'rule_id': rule_id})
                print(f"  DECLINED  {ch_type} rule_id={rule_id}")
                continue

            if verdict not in ('ACCEPT', 'ACCEPT_WITH_EDITS'):
                errors.append(f"Unknown decision '{verdict}' for {ch_type} rule_id={rule_id} — skipped.")
                continue

            # ---- MODIFY_RULE ----
            if ch_type == 'MODIFY_RULE':
                if rule_id not in art_rule_index:
                    errors.append(f"MODIFY_RULE: rule_id '{rule_id}' not found — skipped.")
                    continue
                field = change.get('field')
                if not field:
                    errors.append(f"MODIFY_RULE: no 'field' specified for rule_id '{rule_id}' — skipped.")
                    continue
                value = edited if verdict == 'ACCEPT_WITH_EDITS' else change.get('proposed_value')

                # Update artifact_b.json in-memory
                art_rule_index[rule_id][field] = value

                # Update DB rules row: refresh description if field is 'check', always stamp approval
                if field == 'check':
                    cursor.execute(
                        "UPDATE rules SET description = %s, approved_by = %s, approved_at = %s WHERE rule_name = %s",
                        (value, reviewed_by, now, rule_id),
                    )
                else:
                    cursor.execute(
                        "UPDATE rules SET approved_by = %s, approved_at = %s WHERE rule_name = %s",
                        (reviewed_by, now, rule_id),
                    )
                applied.append({'type': ch_type, 'rule_id': rule_id, 'field': field, 'new_value': value})
                print(f"  APPLIED   MODIFY_RULE  rule_id={rule_id}  field={field}")

            # ---- NEW_RULE ----
            elif ch_type == 'NEW_RULE':
                proposed = change.get('proposed_rule', {})
                if verdict == 'ACCEPT_WITH_EDITS' and isinstance(edited, dict):
                    proposed = edited
                elif verdict == 'ACCEPT_WITH_EDITS' and edited:
                    errors.append(f"NEW_RULE ACCEPT_WITH_EDITS: edited_value must be a dict — used original.")

                if not proposed:
                    errors.append("NEW_RULE: no 'proposed_rule' in change — skipped.")
                    continue
                new_id = proposed.get('id')
                if new_id in art_rule_index:
                    errors.append(f"NEW_RULE: rule id '{new_id}' already exists — skipped.")
                    continue

                # Look up category_id from categories table
                category_code = proposed.get('category', '')
                cursor.execute(
                    "SELECT category_id FROM categories WHERE category_code = %s LIMIT 1",
                    (category_code,),
                )
                cat_row    = cursor.fetchone()
                category_id = cat_row[0] if cat_row else None
                if category_id is None:
                    errors.append(
                        f"NEW_RULE '{new_id}': category_code '{category_code}' not found in DB — "
                        "rule added to artifact_b.json but NOT inserted into rules table."
                    )

                # Insert into DB rules table (skip if no category_id)
                if category_id is not None:
                    cursor.execute(
                        """
                        INSERT INTO rules
                            (rule_name, description, category_id, approved_by, approved_at)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (new_id, proposed.get('check', ''), category_id, reviewed_by, now),
                    )

                # Add to artifact_b.json in-memory
                art_rules.append(proposed)
                art_rule_index[new_id] = proposed
                applied.append({'type': ch_type, 'rule_id': new_id, 'check': proposed.get('check', '')[:80]})
                print(f"  APPLIED   NEW_RULE     rule_id={new_id}")

            # ---- OBSOLETE_RULE ----
            elif ch_type == 'OBSOLETE_RULE':
                if rule_id not in art_rule_index:
                    errors.append(f"OBSOLETE_RULE: rule_id '{rule_id}' not found — skipped.")
                    continue

                # Delete from DB rules table
                cursor.execute("DELETE FROM rules WHERE rule_name = %s", (rule_id,))

                # Remove from artifact_b.json in-memory
                art_rules[:] = [r for r in art_rules if r['id'] != rule_id]
                del art_rule_index[rule_id]
                applied.append({'type': ch_type, 'rule_id': rule_id})
                print(f"  APPLIED   OBSOLETE_RULE rule_id={rule_id}")

            else:
                errors.append(f"Unknown change type '{ch_type}' — skipped.")

        # --- Create new rules_snapshot ---
        snapshot_label = f'legislation_update_{review_id}'
        cursor.execute(
            """
            INSERT INTO rules_snapshots (label, approved_by, approved_at, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (snapshot_label, reviewed_by, now, now),
        )
        snapshot_id = cursor.lastrowid
        print(f"  Created rules_snapshot: snapshot_id={snapshot_id} label='{snapshot_label}'")

        # Populate snapshot_rules with all current DB rule IDs
        cursor.execute("SELECT rule_id FROM rules")
        for (db_rule_id,) in cursor.fetchall():
            cursor.execute(
                "INSERT INTO snapshot_rules (rule_id, snapshot_id) VALUES (%s, %s)",
                (db_rule_id, snapshot_id),
            )

        # --- Set review status to APPLIED ---
        cursor.execute(
            "UPDATE legislation_update_reviews SET status = 'APPLIED' WHERE review_id = %s",
            (review_id,),
        )

        db.commit()

        # --- Write updated artifact_b.json (after successful DB commit) ---
        art_data['rules'] = art_rules
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(art_data, f, indent=2, ensure_ascii=False)
        print(f"  artifact_b.json updated ({len(art_rules)} rules).")

        summary = {
            'backup_path': backup_path,
            'applied':     applied,
            'declined':    declined,
            'snapshot_id': snapshot_id,
            'errors':      errors,
        }

        print(f"\nSummary: {len(applied)} applied, {len(declined)} declined, {len(errors)} error(s).")
        for err in errors:
            print(f"  ERROR: {err}")

        return summary

    except Exception as err:
        db.rollback()
        raise RuntimeError(f"apply_accepted_changes failed — rolled back: {err}") from err
    finally:
        if close and db.is_connected():
            cursor.close()
            db.close()


# ---------------------------------------------------------------------------
# 4 — Orchestrate the full analysis
# ---------------------------------------------------------------------------

def analyse_legislation_update(file_path, document_version_id):
    """
    Full pipeline: extract text → load rules → build prompt → call Claude
                   → save proposed changes to DB → return {review_id, proposed_changes}.

    Args:
        file_path:            path to the legislation document (.pdf / .doc / .docx)
        document_version_id:  FK to document_versions.version_id for audit trail

    Returns:
        {'review_id': int, 'proposed_changes': list}
    """
    print("=" * 60)
    print("LEGISLATION UPDATE ANALYSIS")
    print("=" * 60)

    legislation_text = extract_legislation_text(file_path)
    print(f"  Extracted {len(legislation_text):,} characters from legislation.")

    _, current_rules, _ = load_current_rules()

    user_prompt = build_legislation_prompt(current_rules, legislation_text)
    print(f"  Prompt built ({len(user_prompt):,} chars). Calling Claude ...")

    response = _call_claude(user_prompt)
    print("  Claude response received.")

    proposed_changes = _parse_proposed_changes(response)
    print(f"  Parsed {len(proposed_changes)} proposed change(s).")
    for i, ch in enumerate(proposed_changes, 1):
        print(f"    [{i}] {ch.get('type', '?')} rule_id={ch.get('rule_id', 'n/a')} — {ch.get('reason', '')[:80]}")

    review_id = save_proposed_changes(document_version_id, proposed_changes)

    return {'review_id': review_id, 'proposed_changes': proposed_changes}
