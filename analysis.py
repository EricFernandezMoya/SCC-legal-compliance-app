import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'SCCProject', 'artifact_b.json')


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
            'description':        rule['check'],
            'citation':           rule['citation'],
            'ambiguity_triggers': rule.get('ambiguity_triggers', []),
            'comply_requires':    rule.get('comply_requires', ''),
            'missing_if':         rule.get('missing_if', ''),
            'why':                rule.get('why', ''),
        })
    return rules


# ---------------------------------------------------------------------------
# Step 2 — Build single user prompt (all rules + full contract)
# ---------------------------------------------------------------------------

def build_user_prompt(rules, contract_text):
    rules_block = []
    for rule in rules:
        triggers = rule['ambiguity_triggers']
        triggers_formatted = '\n'.join(f'  - {t}' for t in triggers) if triggers else '  (none)'
        rules_block.append(
            f"RULE ID: {rule['rule_id']}\n"
            f"RULE CHECK: {rule['description']}\n"
            f"CITATION: {rule['citation']}\n"
            f"COMPLY REQUIRES: {rule['comply_requires']}\n"
            f"MISSING IF: {rule['missing_if']}\n"
            f"WHY: {rule['why']}\n"
            f"AMBIGUITY TRIGGER PHRASES:\n{triggers_formatted}"
        )

    rules_text = '\n\n'.join(rules_block)

    return (
        "Analyse the contract text below against every rule listed. "
        "Return a JSON array — one finding object per rule, in rule order. "
        "Each object must contain exactly these fields: "
        "rule_id, outcome, clause_quoted, reason, citation, trigger_phrase_matched.\n\n"
        f"RULES:\n{rules_text}\n\n"
        f"CONTRACT TEXT:\n{contract_text}"
    )


# ---------------------------------------------------------------------------
# Step 3 — Call Claude (single call)
# ---------------------------------------------------------------------------

def call_claude(system_prompt, user_prompt):
    client = Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


# ---------------------------------------------------------------------------
# Step 4 — Parse findings array from Claude response
# ---------------------------------------------------------------------------

def parse_findings(response_text):
    text = response_text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[-1]
        text = text.rsplit('```', 1)[0].strip()

    try:
        findings = json.loads(text)
    except json.JSONDecodeError as e:
        return [{
            "rule_id":               "PARSE_ERROR",
            "outcome":               "PARSE_ERROR",
            "clause_quoted":         None,
            "reason":                f"Claude response was not valid JSON: {e}",
            "citation":              None,
            "trigger_phrase_matched": None,
            "_raw_response":         response_text,
        }]

    if not isinstance(findings, list):
        findings = [findings]

    return findings


# ---------------------------------------------------------------------------
# Step 5 — Main analysis function
# ---------------------------------------------------------------------------

def analyse_contract(contract_text):
    """
    Analyse a full contract text against all rules in artifact_b.json.
    Makes a single Claude API call and returns a list of finding dicts,
    one per rule, with fields: rule_id, outcome, clause_quoted, reason,
    citation, trigger_phrase_matched.
    """
    master_prompt = load_master_prompt()
    rules         = load_rules()

    print(f"Loaded {len(rules)} rules from artifact_b.json.")
    print("Calling Claude with full contract and all rules ...", flush=True)

    user_prompt = build_user_prompt(rules, contract_text)
    response    = call_claude(master_prompt, user_prompt)
    findings    = parse_findings(response)

    print("RAW CLAUDE RESPONSE:")
    print(response)
    print(f"Received {len(findings)} findings.")
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

'''
if __name__ == '__main__':
    run_test()
'''