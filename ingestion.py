import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from database import create_db_server_connection

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'SCCProject', 'artifact_b.json')


# ---------------------------------------------------------------------------
# Step 1 — Load source JSON
# ---------------------------------------------------------------------------

def load_json():
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    print(f"[1/5] Loaded {len(data['categories'])} categories and {len(data['rules'])} rules from artifact_b.json")
    return data


# ---------------------------------------------------------------------------
# Step 2 — Categories
# ---------------------------------------------------------------------------

def insert_categories(conn, categories):
    cursor = conn.cursor()
    category_map = {}
    for cat in categories:
        cursor.execute(
            "INSERT INTO categories (category_code, category_name) VALUES (%s, %s)",
            (cat['code'], cat['name'])
        )
        category_map[cat['code']] = cursor.lastrowid
    conn.commit()
    cursor.close()
    print(f"[2/5] Inserted {len(categories)} categories")
    return category_map


# ---------------------------------------------------------------------------
# Step 3 — Rules (with metadata JSON)
# ---------------------------------------------------------------------------

def _ensure_rule_metadata_column(conn):
    cursor = conn.cursor()
    cursor.execute("SHOW COLUMNS FROM rules LIKE 'rule_metadata'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE rules ADD COLUMN rule_metadata JSON")
        conn.commit()
        print("      Added rule_metadata column to rules table")
    cursor.close()


def insert_rules(conn, rules, category_map, approved_by, approved_at):
    _ensure_rule_metadata_column(conn)
    cursor = conn.cursor()
    rule_id_map = {}
    for rule in rules:
        metadata = {
            'ambiguity_triggers': rule.get('ambiguity_triggers', []),
            'comply_requires':    rule.get('comply_requires', ''),
            'applies_to':         rule.get('applies_to', []),
            'missing_if':         rule.get('missing_if', ''),
        }
        if 'note' in rule:
            metadata['note'] = rule['note']

        cursor.execute(
            """INSERT INTO rules
                   (rule_name, description, category_id, approved_by, approved_at, rule_metadata)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                rule['id'],
                rule['check'],
                category_map[rule['category']],
                approved_by,
                approved_at,
                json.dumps(metadata),
            )
        )
        rule_id_map[rule['id']] = cursor.lastrowid
    conn.commit()
    cursor.close()
    print(f"[3/5] Inserted {len(rules)} rules with metadata")
    return rule_id_map


# ---------------------------------------------------------------------------
# Step 4 — Documents, document_versions, rule_basis
# ---------------------------------------------------------------------------

def _ensure_document_types(conn):
    cursor = conn.cursor()
    type_map = {}
    for type_name in ('legislation', 'vendor_policy'):
        cursor.execute(
            "SELECT document_type_id FROM document_types WHERE type_name = %s",
            (type_name,)
        )
        row = cursor.fetchone()
        if row:
            type_map[type_name] = row[0]
        else:
            cursor.execute(
                "INSERT INTO document_types (type_name) VALUES (%s)",
                (type_name,)
            )
            type_map[type_name] = cursor.lastrowid
    conn.commit()
    cursor.close()
    return type_map


def _classify_doc_type(doc_name):
    if re.search(r'\b(Act|Regulation|Regulations)\b', doc_name, re.IGNORECASE):
        return 'legislation'
    return 'vendor_policy'


def _extract_jurisdiction(doc_name):
    if '(Qld)' in doc_name:
        return 'Queensland'
    if '(Cth)' in doc_name:
        return 'Commonwealth'
    return None


def _extract_year(doc_name):
    m = re.search(r'\b(19|20)\d{2}\b', doc_name)
    return int(m.group(0)) if m else None


def _parse_citation(raw):
    """Split 'Document Name (Jur) s.N' into (doc_name, full_citation_string)."""
    raw = raw.strip()
    m = re.search(
        r'\s+((?:ss?\.|Part\s+\d|Sch(?:edule)?\s*\.)\S.*)',
        raw,
        re.IGNORECASE
    )
    doc_name = raw[:m.start()].strip() if m else raw
    return doc_name, raw


def insert_documents_versions_and_rule_basis(conn, rules, rule_id_map):
    type_map = _ensure_document_types(conn)
    cursor = conn.cursor()

    doc_version_map = {}   # doc_name -> version_id

    # Collect unique documents across all citations
    for rule in rules:
        for part in rule['citation'].split(';'):
            doc_name, _ = _parse_citation(part)
            if not doc_name or doc_name in doc_version_map:
                continue

            doc_type   = _classify_doc_type(doc_name)
            type_id    = type_map[doc_type]
            jurisdiction = _extract_jurisdiction(doc_name)
            year       = _extract_year(doc_name)

            cursor.execute(
                """INSERT INTO documents
                       (document_name, jurisdiction, year, document_type_id)
                   VALUES (%s, %s, %s, %s)""",
                (doc_name, jurisdiction, year, type_id)
            )
            doc_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO document_versions (document_id, version_number) VALUES (%s, %s)",
                (doc_id, '1.0')
            )
            doc_version_map[doc_name] = cursor.lastrowid

    conn.commit()

    # rule_basis — one row per (rule, citation part)
    basis_count = 0
    for rule in rules:
        rule_db_id = rule_id_map[rule['id']]
        for part in rule['citation'].split(';'):
            doc_name, full_citation = _parse_citation(part)
            if not doc_name or doc_name not in doc_version_map:
                continue
            cursor.execute(
                """INSERT INTO rule_basis (rule_id, document_version_id, section_name)
                   VALUES (%s, %s, %s)""",
                (rule_db_id, doc_version_map[doc_name], full_citation)
            )
            basis_count += 1

    conn.commit()
    cursor.close()
    print(f"[4/5] Inserted {len(doc_version_map)} documents/versions and {basis_count} rule_basis records")


# ---------------------------------------------------------------------------
# Step 5 — Rules snapshot
# ---------------------------------------------------------------------------

def create_rules_snapshot(conn, rule_id_map, approved_by):
    cursor = conn.cursor()
    now = datetime.now()

    cursor.execute(
        """INSERT INTO rules_snapshots (label, approved_by, approved_at, created_at)
           VALUES (%s, %s, %s, %s)""",
        ('Initial load — artifact_b.json v1.0', approved_by, now, now)
    )
    snapshot_id = cursor.lastrowid

    for rule_db_id in rule_id_map.values():
        cursor.execute(
            "INSERT INTO snapshot_rules (rule_id, snapshot_id) VALUES (%s, %s)",
            (rule_db_id, snapshot_id)
        )

    conn.commit()
    cursor.close()
    print(f"[5/5] Created rules snapshot ID={snapshot_id} covering {len(rule_id_map)} rules")
    return snapshot_id


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def run_ingestion():
    data        = load_json()
    approved_by = data['metadata']['approved_by']
    approved_at = datetime(2026, 4, 1)

    conn = create_db_server_connection()

    category_map = insert_categories(conn, data['categories'])
    rule_id_map  = insert_rules(conn, data['rules'], category_map, approved_by, approved_at)

    insert_documents_versions_and_rule_basis(conn, data['rules'], rule_id_map)
    create_rules_snapshot(conn, rule_id_map, approved_by)

    conn.close()
    print("\nIngestion complete.")


if __name__ == '__main__':
    run_ingestion()
