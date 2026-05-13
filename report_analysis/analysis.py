import json
import os
import re
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

from database.database import create_db_server_connection
from report_analysis.document_parser import parseDOC, parsePDF, parseWebsite
from report_analysis.reports import fetch_prior_findings

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'artifact_b.json')


# ---------------------------------------------------------------------------
# Step 1 — Load from artifact_b.json
# ---------------------------------------------------------------------------

def _load_artifact():
    with open(JSON_PATH, 'r') as f:
        return json.load(f)


def load_master_prompt():
    return _load_artifact()['master_prompt']


def load_rules():
    """Return all rules from artifact_b.json as normalised dicts."""
    data = _load_artifact()
    rules = []
    for rule in data['rules']:
        rules.append({
            'rule_id':            rule['id'],
            'title':              rule.get('title', rule['id']),
            'description':        rule['check'],
            'citation':           rule['citation'],
            'ambiguity_triggers': rule.get('ambiguity_triggers', []),
            'comply_requires':    rule.get('comply_requires', ''),
            'missing_if':         rule.get('missing_if', ''),
            'why':                rule.get('why', ''),
            'critical':           rule.get('critical', False),
            'notes':              rule.get('notes', ''),
        })
    return rules


# ---------------------------------------------------------------------------
# Step 2 — Build single user prompt (all rules + full contract)
# ---------------------------------------------------------------------------

def build_user_prompt(rules, contract_text, prior_findings=None):
    rules_block = []
    for rule in rules:
        triggers = rule['ambiguity_triggers']
        triggers_formatted = '\n'.join(f'  - {t}' for t in triggers) if triggers else '  (none)'
        lines = [
            f"RULE ID: {rule['rule_id']}",
            f"RULE TITLE: {rule['title']}",
            f"RULE CHECK: {rule['description']}",
            f"CITATION: {rule['citation']}",
            f"COMPLY REQUIRES: {rule['comply_requires']}",
            f"MISSING IF: {rule['missing_if']}",
            f"WHY: {rule['why']}",
            f"AMBIGUITY TRIGGER PHRASES:\n{triggers_formatted}",
        ]
        if rule.get('critical'):
            lines.insert(2, "CRITICAL RULE: Yes — ambiguity triggers must return PAY_ATTENTION, not COMPLY")
        if rule.get('notes'):
            lines.append(f"NOTES: {rule['notes']}")
        rules_block.append('\n'.join(lines))

    rules_text = '\n\n'.join(rules_block)

    comparison_section = ""
    if prior_findings:
        comparison_section = (
            "\n\n=== YEAR-TO-YEAR COMPARISON ===\n"
            "A prior report exists for this vendor. Where relevant, note if a "
            "clause that previously failed now complies, or if a previously "
            "compliant clause has changed or been removed.\n"
            "Change labels priority order (if multiple apply, use the highest): "
            "ESCALATED > REGRESSED > NEW_GAP > GAP_FILLED > IMPROVED > NEW_RULE > UNCHANGED"
        )

    return (
        "Analyse the contract text below against every rule listed. "
        "Return a JSON array — one finding object per rule, in rule order. "
        "Each object must contain exactly these fields: "
        f"rule_id, rule_title, outcome, clause_quoted, reason, citation, trigger_phrase_matched.{comparison_section}\n\n"
        f"RULES:\n{rules_text}\n\n"
        f"CONTRACT TEXT:\n{contract_text}"
    )


# ---------------------------------------------------------------------------
# Step 3 — Call Claude (single call)
# ---------------------------------------------------------------------------

_JSON_ONLY_INSTRUCTION = (
    "\n\nIMPORTANT: Respond with ONLY the JSON array. "
    "No introductory text, preamble, explanation, or markdown outside the JSON array itself."
)


def call_claude(system_prompt, user_prompt):
    client = Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=system_prompt + _JSON_ONLY_INSTRUCTION,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Step 4 — Parse findings array from Claude response
# ---------------------------------------------------------------------------

def extract_json_findings(raw_response: str) -> list:
    match = re.search(r'```json\s*(\[.*?\])\s*```', raw_response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Claude response was truncated or malformed. "
                f"Try reducing the number of documents or "
                f"document size. JSON error: {e}"
            )
    start = raw_response.find('[')
    end   = raw_response.rfind(']')
    if start != -1 and end != -1:
        try:
            return json.loads(raw_response[start:end + 1])
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Claude response was truncated or malformed. "
                f"Try reducing the number of documents or "
                f"document size. JSON error: {e}"
            )
    print("RAW CLAUDE RESPONSE (parse failure):")
    print(raw_response)
    raise ValueError(f"No JSON array found in Claude response: {raw_response[:200]}")


# ---------------------------------------------------------------------------
# Year-to-year comparison helpers
# ---------------------------------------------------------------------------

def _normalize_outcome(outcome):
    o = (outcome or '').strip().lower().replace(' ', '_')
    if o in ('attention', 'ambiguous'):
        return 'pay_attention'
    return o


def _change_label_and_explanation(prior, current):
    if prior == 'pay_attention' and current == 'not_comply':
        return 'ESCALATED', "Worsened from 'Pay attention' to 'Not comply'."
    if prior == 'comply' and current in ('not_comply', 'pay_attention'):
        return 'REGRESSED', f"Previously complying — now '{current.replace('_', ' ')}'."
    if prior == 'comply' and current == 'missing':
        return 'NEW_GAP', "Previously complying — clause now absent."
    if prior == 'missing' and current != 'missing':
        return 'GAP_FILLED', "Previously missing — clause now present."
    if prior in ('not_comply', 'pay_attention') and current == 'comply':
        return 'IMPROVED', f"Previously '{prior.replace('_', ' ')}' — now complying."
    return 'UNCHANGED', f"No change from prior report ({current.replace('_', ' ')})."


def compare_findings(current_findings, prior_findings):
    """
    Attach a change_summary dict to each finding in current_findings.
    prior_findings: {rule_id: {outcome, ...}} from fetch_prior_findings().
    Mutates and returns current_findings.
    """
    for finding in current_findings:
        rule_id = finding.get('rule_id')
        current = _normalize_outcome(finding.get('outcome', ''))

        if rule_id not in prior_findings:
            label       = 'NEW_RULE'
            explanation = 'Rule not assessed in the prior report.'
        else:
            prior = _normalize_outcome(prior_findings[rule_id].get('outcome', ''))
            if prior == current:
                label       = 'UNCHANGED'
                explanation = f"No change from prior report ({current.replace('_', ' ')})."
            else:
                label, explanation = _change_label_and_explanation(prior, current)

        finding['change_summary'] = {'label': label, 'explanation': explanation}

    return current_findings


# ---------------------------------------------------------------------------
# Step 5a — Single-document analysis (backward compatible)
# ---------------------------------------------------------------------------

def analyse_contract(contract_text, prior_report_id=None):
    """
    Analyse a full contract text against all rules in artifact_b.json.
    Makes a single Claude API call and returns a list of finding dicts,
    one per rule, with fields: rule_id, outcome, clause_quoted, reason,
    citation, trigger_phrase_matched.
    If prior_report_id is given, each finding also gets a change_summary field.
    """
    master_prompt  = load_master_prompt()
    rules          = load_rules()
    prior_findings = fetch_prior_findings(prior_report_id) if prior_report_id else {}

    print(f"Loaded {len(rules)} rules from artifact_b.json.")
    print("Calling Claude with full contract and all rules ...", flush=True)

    user_prompt = build_user_prompt(rules, contract_text, prior_findings or None)
    response    = call_claude(master_prompt, user_prompt)
    findings    = extract_json_findings(response)

    print("RAW CLAUDE RESPONSE:")
    print(response)
    print(f"Received {len(findings)} findings.")

    rules_title_map = {r['rule_id']: r['title'] for r in rules}
    for finding in findings:
        rid = finding.get('rule_id', '')
        finding['rule_title'] = rules_title_map.get(rid, rid)

    if prior_findings:
        compare_findings(findings, prior_findings)

    return findings


# ---------------------------------------------------------------------------
# Step 5b — Multi-document vendor group analysis
# ---------------------------------------------------------------------------

PRECEDENCE_PATTERNS = [
    r'in the event of (?:any )?conflict',
    r'in case of (?:any )?conflict',
    r'order of precedence',
    r'shall (?:take )?prevail',
    r'shall take precedence',
    r'supersedes?(?: and)?(?:\s+replaces?)?',
    r'in the event of (?:any )?inconsistency',
    r'conflict(?:ing)? (?:terms?|provisions?|clauses?)',
    r'notwithstanding (?:any )?(?:other|conflicting)',
    r'takes? priority over',
    r'controls? over',
]


def detect_precedence_clause(documents):
    """
    Pre-scan all documents for precedence language using regex.
    Returns {'clause': str, 'source': str} for the first match found, else None.
    'clause' is the surrounding sentence context; 'source' is the document name.
    """
    for doc in documents:
        text = doc['text']
        for pattern in PRECEDENCE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = max(0, match.start() - 100)
                end   = min(len(text), match.end() + 200)
                return {
                    'clause': text[start:end].strip(),
                    'source': doc['name'],
                }
    return None


def build_fetch_summary(successful_urls, failed_urls):
    lines = []
    for item in successful_urls:
        lines.append(f"  \u2713 {item['url']}")
    for item in failed_urls:
        lines.append(f"  \u2717 {item['url']} \u2014 {item['reason']}")
    lines.append("")
    lines.append("Do NOT penalise rules for content that may exist in unretrieved documents.")
    return "\n".join(lines)


def build_group_user_prompt(rules, documents, precedence=None, prior_findings=None, fetch_summary=None):
    """
    Build a combined analysis prompt for multiple documents from one vendor.
    documents:     list of {'name': str, 'text': str}
    precedence:    {'clause': str, 'source': str} or None
    prior_findings: {rule_id: {outcome, ...}} or None
    """
    rules_block = []
    for rule in rules:
        triggers = rule['ambiguity_triggers']
        triggers_formatted = '\n'.join(f'  - {t}' for t in triggers) if triggers else '  (none)'
        lines = [
            f"RULE ID: {rule['rule_id']}",
            f"RULE TITLE: {rule['title']}",
            f"RULE CHECK: {rule['description']}",
            f"CITATION: {rule['citation']}",
            f"COMPLY REQUIRES: {rule['comply_requires']}",
            f"MISSING IF: {rule['missing_if']}",
            f"WHY: {rule['why']}",
            f"AMBIGUITY TRIGGER PHRASES:\n{triggers_formatted}",
        ]
        if rule.get('critical'):
            lines.insert(2, "CRITICAL RULE: Yes — ambiguity triggers must return PAY_ATTENTION, not COMPLY")
        if rule.get('notes'):
            lines.append(f"NOTES: {rule['notes']}")
        rules_block.append('\n'.join(lines))

    rules_text = '\n\n'.join(rules_block)

    docs_block = []
    for i, doc in enumerate(documents, start=1):
        if doc.get('url'):
            header = f"=== SOURCE: {doc['url']} ==="
        else:
            header = f"=== DOCUMENT {i}: {doc['name']} ==="
        docs_block.append(f"{header}\n{doc['text']}")
    combined_text = '\n\n'.join(docs_block)

    if precedence:
        hierarchy_section = (
            "=== DOCUMENT HIERARCHY ===\n"
            f"A precedence clause was found in: {precedence['source']}\n"
            f"Precedence clause: \"{precedence['clause']}\"\n"
            "When documents conflict, apply this clause to determine which document controls."
        )
    else:
        hierarchy_section = (
            "=== DOCUMENT HIERARCHY ===\n"
            "No explicit precedence clause was found across these documents. "
            "Apply the principle of Specific Over General: "
            "a more specific clause in any document overrides a more general clause in another."
        )

    comparison_section = ""
    if prior_findings:
        comparison_section = (
            "\n\n=== YEAR-TO-YEAR COMPARISON ===\n"
            "A prior report exists for this vendor. Where relevant, note if a "
            "clause that previously failed now complies, or if a previously "
            "compliant clause has changed or been removed.\n"
            "Change labels priority order (if multiple apply, use the highest): "
            "ESCALATED > REGRESSED > NEW_GAP > GAP_FILLED > IMPROVED > NEW_RULE > UNCHANGED"
        )

    retrieval_section = ""
    if fetch_summary:
        retrieval_section = (
            "=== DOCUMENT RETRIEVAL SUMMARY ===\n"
            f"{fetch_summary}\n\n"
            "=== CRITICAL INSTRUCTIONS ===\n"
            "a. If a rule cannot be assessed because the relevant document was not retrieved, "
            "set result to MISSING and state: \"This rule could not be assessed \u2014 [document name] "
            "was not successfully retrieved.\" Do NOT say FAIL or NOT_COMPLY.\n"
            "b. If a rule IS addressed in retrieved text, assess normally and return PASS, "
            "PAY_ATTENTION, or NOT_COMPLY.\n"
            "c. If a rule is genuinely absent from all retrieved documents, return NOT_COMPLY "
            "and cite which documents were searched.\n"
            "d. Always quote the exact clause from retrieved text that informed the finding. "
            "If none exists, say so explicitly.\n"
            "e. Do not assume content exists in documents that were not retrieved.\n\n"
        )

    return (
        f"{retrieval_section}"
        f"{hierarchy_section}\n\n"
        f"You are reviewing {len(documents)} document(s) from the same vendor as one combined compliance picture. "
        "Analyse all documents together against every rule listed. "
        "A rule complies if the requirement is satisfied by any document in the set. "
        "A rule is missing only if the required clause is absent across all documents. "
        "For each finding, state which document controls and the legal basis for that determination. "
        "Return a JSON array — one finding object per rule, in rule order. "
        "Each object must contain exactly these fields: "
        "rule_id, rule_title, outcome, clause_quoted, clause_source (the document name where the clause was found, or null), "
        "controlling_document (which document controls for this finding and why), "
        f"reason, citation, trigger_phrase_matched.{comparison_section}\n\n"
        f"RULES:\n{rules_text}\n\n"
        f"VENDOR DOCUMENTS:\n{combined_text}"
    )


def _parse_file(file_path):
    """Parse a contract file or URL to text."""
    if file_path.startswith("http"):
        return parseWebsite(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return parsePDF(file_path)
    if ext in ('.doc', '.docx'):
        return parseDOC(file_path)
    raise ValueError(f"Unsupported file type for vendor group analysis: {ext}")


def fetch_group_documents(group_id, conn=None):
    """
    Fetch and parse all contracts for a vendor group from the database.
    Returns list of {'contract_id': int, 'name': str, 'text': str}.
    Opens its own DB connection when conn is None.
    """
    close_conn = conn is None
    if conn is None:
        conn = create_db_server_connection()
        if conn is None:
            raise RuntimeError("Could not connect to database.")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT contract_id, contract_name, file_path
            FROM contracts
            WHERE contract_group = %s
            ORDER BY contract_id
            """,
            (group_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
    finally:
        if close_conn and conn.is_connected():
            conn.close()

    if not rows:
        raise ValueError(f"No contracts found for group_id={group_id}.")

    documents = []
    failed_docs = []
    for row in rows:
        file_path = row['file_path']
        name = row['contract_name'] or os.path.basename(file_path)
        print(f"  Parsing: {name} ({file_path})")
        if file_path.startswith("http"):
            try:
                text = parseWebsite(file_path)
                documents.append({
                    'contract_id': row['contract_id'],
                    'name':        name,
                    'text':        text,
                    'url':         file_path,
                })
            except ValueError as exc:
                print(f"  Failed to fetch {file_path}: {exc}")
                failed_docs.append({"url": file_path, "reason": str(exc)})
        else:
            text = _parse_file(file_path)
            documents.append({
                'contract_id': row['contract_id'],
                'name':        name,
                'text':        text,
            })

    return documents, failed_docs


def analyse_vendor_group(group_id, conn=None, prior_report_id=None):
    """
    Fetch all contracts for a vendor group, combine them, and analyse as one
    unified compliance picture. Returns findings list (one entry per rule).
    Makes a single Claude call — findings reflect the full vendor document set.
    If prior_report_id is given, each finding also gets a change_summary field.
    """
    print(f"Fetching documents for group_id={group_id} ...", flush=True)
    documents, failed_docs = fetch_group_documents(group_id, conn=conn)

    successful_urls = [{"url": d["url"], "text": d["text"]} for d in documents if "url" in d]
    failed_urls     = failed_docs

    fetch_summary = None
    if successful_urls or failed_urls:
        fetch_summary = build_fetch_summary(successful_urls, failed_urls)

    precedence     = detect_precedence_clause(documents)
    prior_findings = fetch_prior_findings(prior_report_id) if prior_report_id else {}

    if precedence:
        print(f"  Precedence clause found in: {precedence['source']}")
    else:
        print("  No precedence clause found — applying Specific Over General.")

    master_prompt = load_master_prompt()
    rules         = load_rules()

    doc_names = [d['name'] for d in documents]
    if failed_urls:
        print(f"  Failed to retrieve {len(failed_urls)} URL(s): {[f['url'] for f in failed_urls]}")
    print(f"Loaded {len(rules)} rules. Analysing {len(documents)} document(s): {doc_names}")
    print("Calling Claude with combined vendor documents and all rules ...", flush=True)

    user_prompt = build_group_user_prompt(rules, documents, precedence, prior_findings or None, fetch_summary)
    response    = call_claude(master_prompt, user_prompt)
    findings    = extract_json_findings(response)

    print(f"Received {len(findings)} findings.")

    rules_title_map = {r['rule_id']: r['title'] for r in rules}
    for finding in findings:
        rid = finding.get('rule_id', '')
        finding['rule_title'] = rules_title_map.get(rid, rid)

    if prior_findings:
        compare_findings(findings, prior_findings)

    return findings


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

def run_test():
    sample_contract = (
        "11.1 Data Storage. The Supplier shall store all Council data, including "
        "backups and disaster recovery copies, within its geographically distributed "
        "cloud infrastructure. Data may be replicated across multiple regions to "
        "ensure high availability. The Supplier will endeavour to keep data within "
        "Australia where operationally feasible."
    )

    print("=" * 60)
    print("ANALYSIS TEST")
    print("=" * 60)
    print(f"\nContract text under review:\n{sample_contract}\n")
    print("-" * 60)

    findings = analyse_contract(sample_contract)

    print("\n" + "=" * 60)
    print("FINDINGS")
    print("=" * 60)
    for f in findings:
        print(f"\nRule:     {f['rule_id']}")
        print(f"Outcome:  {f['outcome']}")
        print(f"Quoted:   {f.get('clause_quoted') or '(none)'}")
        print(f"Reason:   {f.get('reason')}")
        print(f"Citation: {f.get('citation')}")
        print(f"Trigger:  {f.get('trigger_phrase_matched') or '(none)'}")
