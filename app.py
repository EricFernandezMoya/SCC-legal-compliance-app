import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests as _http
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from mysql.connector import Error
from pydantic import BaseModel

try:
    from bs4 import BeautifulSoup as _BeautifulSoup
    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False

from report_analysis.analysis import analyse_contract
from database.database import create_db_server_connection
from report_analysis.document_parser import parseDOC, parsePDF
from legislation_update import (
    analyse_legislation_update,
    apply_accepted_changes,
    save_reviewer_decisions,
)
from report_analysis.reports import save_report, build_report_data
from report_analysis.report_word import generate_word_report

app = FastAPI()


def _fetch_url_text(url: str) -> str:
    resp = _http.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    if _BS4_AVAILABLE:
        soup = _BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    return resp.text


def _find_latest_report_for_group(group_id: int) -> Optional[int]:
    conn = create_db_server_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT cr.report_id
            FROM compliance_reports cr
            JOIN contracts c ON cr.contract = c.contract_id
            WHERE c.contract_group = %s
            ORDER BY cr.created_at DESC
            LIMIT 1
            """,
            (group_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception:
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

_ARTIFACT_B = Path(__file__).parent / "artifact_b.json"


def _persist_failed_urls(report_id: int, failed_urls: List[str]) -> None:
    conn = create_db_server_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE compliance_reports SET failed_urls = %s WHERE report_id = %s",
            (json.dumps(failed_urls), report_id),
        )
        conn.commit()
    except Exception:
        pass
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def _backup_artifact() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = _ARTIFACT_B.parent / f"artifact_b_backup_{ts}.json"
    shutil.copy2(_ARTIFACT_B, dest)
    return str(dest)


def _read_artifact() -> Dict:
    with open(_ARTIFACT_B, encoding="utf-8") as f:
        return json.load(f)


def _write_artifact(data: Dict) -> None:
    with open(_ARTIFACT_B, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# POST /analyse
# ---------------------------------------------------------------------------

@app.get("/vendors")
def get_vendors():
    conn = create_db_server_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT group_id, group_name FROM contract_groups ORDER BY group_name"
        )
        return cursor.fetchall()
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@app.post("/analyse")
async def analyse(
    files: List[UploadFile] = File(default=[]),
    contract_name: Optional[str] = Form(None),
    group_id: Optional[int] = Form(None),
    vendor_name: Optional[str] = Form(None),
    period_start: Optional[str] = Form(None),
    period_end: Optional[str] = Form(None),
    compare_prior: Optional[str] = Form(None),
    urls: Optional[str] = Form(None),
    uploaded_by: str = Form(""),
):
    text_parts: List[str] = []

    # Parse uploaded files
    for file in files:
        if not file.filename:
            continue
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in (".pdf", ".doc", ".docx"):
            raise HTTPException(status_code=400, detail=f"{filename}: only PDF and DOCX files are supported.")
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        try:
            file_text = parsePDF(tmp_path) if ext == ".pdf" else parseDOC(tmp_path)
            text_parts.append(f"=== SOURCE: {filename} ===\n{file_text}")
        finally:
            os.unlink(tmp_path)

    # Fetch URLs
    failed_urls: List[str] = []
    if urls:
        for raw_url in urls.splitlines():
            url = raw_url.strip()
            if not url:
                continue
            try:
                url_text = _fetch_url_text(url)
                text_parts.append(f"=== SOURCE: {url} ===\n{url_text}")
            except Exception as exc:
                failed_urls.append(url)
                text_parts.append(f"=== SOURCE: {url} (fetch failed: {exc}) ===")

    if not text_parts:
        raise HTTPException(status_code=400, detail="No contract content provided. Upload a file or supply at least one URL.")

    contract_text = "\n\n".join(text_parts)

    conn = create_db_server_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")

    try:
        cursor = conn.cursor()

        # Ensure vendor group exists
        if group_id is None and vendor_name:
            cursor.execute(
                "SELECT group_id FROM contract_groups WHERE group_name = %s LIMIT 1",
                (vendor_name,),
            )
            existing = cursor.fetchone()
            if existing:
                group_id = existing[0]
            else:
                cursor.execute(
                    "INSERT INTO contract_groups (group_name, contact_details, created_at)"
                    " VALUES (%s, %s, NOW())",
                    (vendor_name, vendor_name),
                )
                conn.commit()
                group_id = cursor.lastrowid

        # Auto-generate contract name for multi-document submissions
        if not contract_name:
            print(f"DEBUG vendor_name at contract_name build: {vendor_name!r}")
            vendor_label = vendor_name or "Unknown Vendor"
            contract_name = f"{vendor_label} — Group Analysis {datetime.now().strftime('%Y-%m-%d')}"

        # Auto-create contract row
        cursor.execute(
            """
            INSERT INTO contracts
                (contract_group, contract_name, version_number, uploaded_at, uploaded_by, period_start, period_end)
            VALUES (%s, %s, 1, NOW(), %s, %s, %s)
            """,
            (group_id, contract_name, uploaded_by or None, period_start or None, period_end or None),
        )
        conn.commit()
        contract_id = cursor.lastrowid

    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    # Auto-find prior report for year-on-year comparison
    prior_report_id: Optional[int] = None
    if (compare_prior or "").lower() == "true" and group_id is not None:
        prior_report_id = _find_latest_report_for_group(group_id)

    findings = analyse_contract(contract_text)
    report_id = save_report(contract_id, findings, prior_report_id)

    if report_id is None:
        raise HTTPException(status_code=500, detail="Failed to save report to database.")

    if failed_urls:
        _persist_failed_urls(report_id, failed_urls)

    return {
        "report_id":   report_id,
        "contract_id": contract_id,
        "findings":    findings,
        "group_id":    group_id,
        "failed_urls": failed_urls,
    }


# ---------------------------------------------------------------------------
# GET /reports/contract/{contract_id}  — must be defined before /{report_id}
# ---------------------------------------------------------------------------

@app.get("/reports/contract/{contract_id}")
def get_reports_for_contract(contract_id: int):
    conn = create_db_server_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT report_id, contract, snapshot, prior_report,
                   created_at
            FROM compliance_reports
            WHERE contract = %s
            ORDER BY created_at DESC
            """,
            (contract_id,),
        )
        reports = cursor.fetchall()
        for r in reports:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return {"reports": reports}

    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ---------------------------------------------------------------------------
# GET /reports/{report_id}/download-docx
# ---------------------------------------------------------------------------

@app.get("/reports/{report_id}/download-docx")
def download_report_docx(report_id: int):
    conn = create_db_server_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    try:
        report_data = build_report_data(report_id, conn)
    finally:
        if conn.is_connected():
            conn.close()

    if report_data is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    filepath = generate_word_report(report_data, output_dir="reports/")
    return FileResponse(
        path=filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=os.path.basename(filepath),
    )


# ---------------------------------------------------------------------------
# GET /reports/{report_id}
# ---------------------------------------------------------------------------

@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = create_db_server_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT cr.report_id, cr.contract, cr.snapshot, cr.prior_report,
                   cr.created_at,
                   cg.group_name AS vendor_name,
                   c.contract_name,
                   c.uploaded_by AS analyst
            FROM compliance_reports cr
            JOIN contracts c ON cr.contract = c.contract_id
            JOIN contract_groups cg ON c.contract_group = cg.group_id
            WHERE cr.report_id = %s
            """,
            (report_id,),
        )
        report = cursor.fetchone()
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found.")
        if report.get("created_at"):
            report["created_at"] = report["created_at"].isoformat()

        cursor.execute(
            """
            SELECT cr.risk_id,
                   cr.finding_text,
                   cr.description,
                   r.rule_id,
                   r.rule_name,
                   r.description  AS rule_description,
                   rl.risk_level_id,
                   rl.risk_name
            FROM compliance_risks cr
            JOIN rules      r  ON cr.rule       = r.rule_id
            JOIN risk_levels rl ON cr.risk_level = rl.risk_level_id
            WHERE cr.report = %s
            """,
            (report_id,),
        )
        risks = cursor.fetchall()

        with open(_ARTIFACT_B, encoding="utf-8") as fh:
            _artifact = json.load(fh)
        _rules_title_map = {r["id"]: r.get("title", r["id"]) for r in _artifact.get("rules", [])}
        for risk in risks:
            risk["rule_title"] = _rules_title_map.get(risk.get("rule_name", ""), risk.get("rule_name", ""))

        return {"report": report, "risks": risks}

    except HTTPException:
        raise
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ---------------------------------------------------------------------------
# POST /legislation/upload
# ---------------------------------------------------------------------------

@app.post("/legislation/upload")
async def legislation_upload(
    file: UploadFile = File(...),
    document_version_id: int = Form(...),
):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".pdf", ".doc", ".docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    print(f"legislation_upload: saved temp file {tmp_path}, document_version_id={document_version_id}")

    try:
        result = analyse_legislation_update(tmp_path, document_version_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Legislation analysis failed: {e}")
    finally:
        os.unlink(tmp_path)

    return {"review_id": result["review_id"], "proposed_changes": result["proposed_changes"]}


# ---------------------------------------------------------------------------
# POST /legislation/apply
# ---------------------------------------------------------------------------

class LegislationApplyRequest(BaseModel):
    review_id: int
    reviewed_by: str
    decisions: List[Any]


@app.post("/legislation/apply")
def legislation_apply(body: LegislationApplyRequest):
    if not body.review_id or not body.reviewed_by or body.decisions is None:
        raise HTTPException(status_code=400, detail="review_id, reviewed_by, and decisions are required.")

    print(f"legislation_apply: review_id={body.review_id} reviewed_by='{body.reviewed_by}' decisions={len(body.decisions)}")

    try:
        save_reviewer_decisions(body.review_id, body.decisions, body.reviewed_by)
        summary = apply_accepted_changes(body.review_id, body.reviewed_by)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply legislation changes: {e}")

    return {"status": "success", "summary": summary}


# ---------------------------------------------------------------------------
# Rules CRUD  GET /rules  POST /rules  PUT /rules/{id}  DELETE /rules/{id}
# ---------------------------------------------------------------------------

class RuleBody(BaseModel):
    id: str
    title: Optional[str] = None
    category: str
    check: str
    why: Optional[str] = None
    citation: Optional[str] = None
    comply_requires: Optional[str] = None
    missing_if: Optional[str] = None
    ambiguity_triggers: Optional[List[str]] = None
    notes: Optional[str] = None
    critical: Optional[bool] = None


@app.get("/rules")
def get_rules():
    try:
        data = _read_artifact()
        return {"rules": data.get("rules", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rules")
def create_rule(body: RuleBody):
    try:
        data = _read_artifact()
        rules = data.get("rules", [])
        if any(r["id"] == body.id for r in rules):
            raise HTTPException(status_code=400, detail=f"Rule ID {body.id} already exists.")
        _backup_artifact()
        new_rule = {k: v for k, v in body.dict().items() if v is not None}
        rules.append(new_rule)
        data["rules"] = rules
        _write_artifact(data)
        _db_upsert_rule(body.id, body.check, body.category, insert=True)
        return {"status": "created", "rule": new_rule}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/rules/{rule_id}")
def update_rule(rule_id: str, body: RuleBody):
    try:
        data = _read_artifact()
        rules = data.get("rules", [])
        idx = next((i for i, r in enumerate(rules) if r["id"] == rule_id), None)
        if idx is None:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found.")
        _backup_artifact()
        updated = {k: v for k, v in body.dict().items() if v is not None}
        rules[idx] = updated
        data["rules"] = rules
        _write_artifact(data)
        _db_upsert_rule(body.id, body.check, body.category, insert=False, old_id=rule_id)
        return {"status": "updated", "rule": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/rules/{rule_id}")
def delete_rule(rule_id: str):
    try:
        data = _read_artifact()
        rules = data.get("rules", [])
        before = len(rules)
        rules = [r for r in rules if r["id"] != rule_id]
        if len(rules) == before:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found.")
        _backup_artifact()
        data["rules"] = rules
        _write_artifact(data)
        _db_delete_rule(rule_id)
        return {"status": "deleted", "rule_id": rule_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _db_upsert_rule(rule_id: str, description: str, category: str,
                    insert: bool, old_id: Optional[str] = None) -> None:
    conn = create_db_server_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        if insert:
            cursor.execute(
                "INSERT INTO rules (rule_name, description, category, approved_by, approved_at)"
                " SELECT %s, %s, category_id, NULL, NULL"
                " FROM categories WHERE category_code = %s LIMIT 1",
                (rule_id, description, category),
            )
        else:
            cursor.execute(
                "UPDATE rules SET rule_name = %s, description = %s WHERE rule_name = %s",
                (rule_id, description, old_id or rule_id),
            )
        conn.commit()
    except Exception:
        pass
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def _db_delete_rule(rule_id: str) -> None:
    conn = create_db_server_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rules WHERE rule_name = %s", (rule_id,))
        conn.commit()
    except Exception:
        pass
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ---------------------------------------------------------------------------
# GET /vendors/list
# ---------------------------------------------------------------------------

@app.get("/vendors/list")
def get_vendors_list():
    conn = create_db_server_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT MIN(group_id) AS group_id, group_name FROM contract_groups GROUP BY group_name ORDER BY group_name"
        )
        return cursor.fetchall()
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ---------------------------------------------------------------------------
# GET /vendors/{group_id}/latest-report
# ---------------------------------------------------------------------------

@app.get("/vendors/{group_id}/latest-report")
def get_latest_report_for_vendor(group_id: int):
    report_id = _find_latest_report_for_group(group_id)
    if report_id is None:
        raise HTTPException(status_code=404, detail="No reports found for this vendor group.")
    return {"report_id": report_id}


# ---------------------------------------------------------------------------
# GET /vendors/{group_id}/reports
# ---------------------------------------------------------------------------

@app.get("/vendors/{group_id}/reports")
def get_vendor_reports(group_id: int):
    conn = create_db_server_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                cr.report_id,
                cr.contract,
                c.contract_name,
                cg.group_name,
                cr.created_at,
                c.uploaded_by AS analyst
            FROM compliance_reports cr
            JOIN contracts c ON cr.contract = c.contract_id
            JOIN contract_groups cg ON c.contract_group = cg.group_id
            WHERE c.contract_group = %s
            ORDER BY cr.created_at DESC
            """,
            (group_id,),
        )
        reports = cursor.fetchall()
        for r in reports:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return {"reports": reports}
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


# ---------------------------------------------------------------------------
# GET /contracts/directory
# ---------------------------------------------------------------------------

@app.get("/contracts/directory")
def get_contracts_directory():
    conn = create_db_server_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                cg.group_id,
                cg.group_name,
                c.contract_id,
                c.contract_name,
                c.uploaded_at,
                c.period_start,
                c.period_end
            FROM contract_groups cg
            LEFT JOIN contracts c ON c.contract_group = cg.group_id
            ORDER BY cg.group_name, c.uploaded_at DESC
            """
        )
        rows = cursor.fetchall()
    except Error as err:
        raise HTTPException(status_code=500, detail=str(err))
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    groups: Dict[int, Any] = {}
    for row in rows:
        gid = row["group_id"]
        if gid not in groups:
            groups[gid] = {
                "group_id":   gid,
                "group_name": row["group_name"],
                "contracts":  [],
            }
        if row["contract_id"] is not None:
            groups[gid]["contracts"].append({
                "contract_id":   row["contract_id"],
                "contract_name": row["contract_name"],
                "uploaded_at":   str(row["uploaded_at"])[:10] if row["uploaded_at"] else None,
                "period_start":  str(row["period_start"])[:10] if row["period_start"] else None,
                "period_end":    str(row["period_end"])[:10] if row["period_end"] else None,
            })

    # Deduplicate by group_name — keep the original (lowest group_id) per name,
    # merging contracts from any duplicate groups into that single card.
    name_to_gid: Dict[str, int] = {}
    for gid in groups:
        gname = groups[gid]["group_name"]
        if gname not in name_to_gid or gid < name_to_gid[gname]:
            name_to_gid[gname] = gid

    deduped: Dict[int, Any] = {keep: groups[keep] for keep in name_to_gid.values()}
    for gid, g in groups.items():
        keep = name_to_gid[g["group_name"]]
        if gid != keep:
            deduped[keep]["contracts"].extend(g["contracts"])

    return list(deduped.values())
