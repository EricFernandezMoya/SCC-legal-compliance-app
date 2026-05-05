import os
import tempfile
from typing import Any, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from mysql.connector import Error
from pydantic import BaseModel

from analysis import analyse_contract
from database import create_db_server_connection
from document_parser import parseDOC, parsePDF
from legislation_update import (
    analyse_legislation_update,
    apply_accepted_changes,
    save_reviewer_decisions,
)
from reports import save_report

app = FastAPI()


# ---------------------------------------------------------------------------
# POST /analyse
# ---------------------------------------------------------------------------

@app.post("/analyse")
async def analyse(
    file: UploadFile = File(...),
    contract_id: int = Form(...),
    prior_report_id: Optional[int] = Form(None),
):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".pdf", ".doc", ".docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        contract_text = parsePDF(tmp_path) if ext == ".pdf" else parseDOC(tmp_path)
    finally:
        os.unlink(tmp_path)

    findings = analyse_contract(contract_text)
    report_id = save_report(contract_id, findings, prior_report_id)

    if report_id is None:
        raise HTTPException(status_code=500, detail="Failed to save report to database.")

    return {"report_id": report_id, "findings": findings}


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
            SELECT report_id, contract_id, snapshot_id, prior_report_id,
                   compliance_status, created_at
            FROM compliance_reports
            WHERE contract_id = %s
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
            SELECT report_id, contract_id, snapshot_id, prior_report_id,
                   compliance_status, created_at
            FROM compliance_reports
            WHERE report_id = %s
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
            JOIN rules      r  ON cr.rule_id       = r.rule_id
            JOIN risk_levels rl ON cr.risk_level_id = rl.risk_level_id
            WHERE cr.report_id = %s
            """,
            (report_id,),
        )
        risks = cursor.fetchall()

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
