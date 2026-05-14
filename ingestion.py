import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from database.database import *
from userHandling.userHandling import createUser
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
# Step 2 — Categories, Privileges and Users
# ---------------------------------------------------------------------------
def insert_privileges():
    
    for name in ["SYSTEM", "ADMIN", "ANALYST", "VIEWER"]:
        insertPrivilege(name)

def insert_users():

    createUser("system", "SYSTEM", os.getenv("SYSTEM_PASSWORD"), selectPrivilegeByName("SYSTEM") )
    createUser("admin", "ADMIN", os.getenv("ADMIN_PASSWORD"), selectPrivilegeByName("ADMIN") )


def insert_categories(categories):
    category_map = {}
    for cat in categories:
        
        insertCategory(cat['code'], cat['name'])
        category_map[cat['code']] = selectCategoryByName(cat['name'])[0][0]
        
    print(f"[2/5] Inserted {len(categories)} categories, 4 privileges and 2 users")
    return category_map

# ---------------------------------------------------------------------------
# Step 3 — Rules (with metadata JSON)
# ---------------------------------------------------------------------------

def insert_rules(rules, category_map, approved_by):

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

        insertRule(rule['id'], rule['id'], rule['check'], category_map[rule['category']], approved_by, json.dumps(metadata))
        
        rule_id_map[rule['id']] = selectRuleByCode(rule['id'])[0][0]
    
    print(f"[3/5] Inserted {len(rules)} rules with metadata")
    return rule_id_map


# ---------------------------------------------------------------------------
# Step 4 — Documents, document_versions, rule_basis
# ---------------------------------------------------------------------------

def _ensure_document_types():
  
    type_map = {}
    for type_name in ('legislation', 'vendor_policy'):

        row = selectDocumentTypeByName(type_name)
        if row:
            type_map[type_name] = row[0][0]
        else:
            insertDocumentType(type_name)
            type_map[type_name] = selectDocumentTypeByName(type_name)[0]
            
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

def insert_documents_versions_and_rule_basis(rules, rule_id_map):
    type_map = _ensure_document_types()

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

            insertDocument(doc_name, jurisdiction, year, "", type_id)           
            doc_id = selectDocumentByName(doc_name)[0][0]

            insertDocumentVersion(doc_id, '1.0', None, None, None, None, None)
            doc_version_map[doc_name] = selectDocumentVersionByDocumentIdAndVersion(doc_id, "1.0")[0][0]

    # rule_basis — one row per (rule, citation part)
    basis_count = 0
    for rule in rules:
        rule_db_id = rule_id_map[rule['id']]
        for part in rule['citation'].split(';'):
            doc_name, full_citation = _parse_citation(part)
            if not doc_name or doc_name not in doc_version_map:
                continue
            insertRuleBasis(rule_db_id, doc_version_map[doc_name], full_citation)
            basis_count += 1

    print(f"[4/5] Inserted {len(doc_version_map)} documents/versions and {basis_count} rule_basis records")

# ---------------------------------------------------------------------------
# Step 5 — Rules snapshot and Risk Levels
# ---------------------------------------------------------------------------
def insert_risks_levels():

    insertRiskLevels("Comply", "The document contains a clause that explicitly and unambiguously satisfies this rule. No further action needed.")
    insertRiskLevels("Pay attention", "A clause exists but the language is vague or ambiguous and cannot be confirmed as compliant. The reviewer must read the clause directly and make their own judgment.")
    insertRiskLevels("Not comply", "A clause is present but explicitly fails this rule. The specific language that caused the flag is quoted directly in the report.")
    insertRiskLevels("Missing", "No clause addressing this rule could be found in the document at all. The report states what should be present and why.")


def create_rules_snapshot(rule_id_map, approved_by):

    now = datetime.now()
    
    label = 'Initial load — artifact_b.json v1.0'

    insertRulesSnapshot(label, approved_by, now)

    snapshot_id = selectRulesSnapshotByLabel(label)[0][0]

    insert_risks_levels()

    for rule_db_id in rule_id_map.values():
        
        insertSnapshotRule(rule_db_id, snapshot_id) 

    print(f"[5/5] Created rules snapshot ID={snapshot_id} covering {len(rule_id_map)} rules and risk levels")
    return snapshot_id


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def run_ingestion():
    insertPrivilege()
    insert_users()
    
    data        = load_json()
    approved_by = selectUserByName("SYSTEM")[0][0]

    category_map = insert_categories(data['categories'])
    rule_id_map  = insert_rules(data['rules'], category_map, approved_by)

    insert_documents_versions_and_rule_basis(data['rules'], rule_id_map)
    create_rules_snapshot(rule_id_map, approved_by)

    print("\nIngestion complete.")
'''
if __name__ == '__main__':
    run_ingestion()
'''