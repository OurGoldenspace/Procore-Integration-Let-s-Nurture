"""
api_server.py
=============
FastAPI server that exposes the Procore → Sage CSV integration
as a downloadable endpoint for the x platform.

Endpoints:
  GET  /health              — health check
  GET  /invoices            — list all approved invoices from Procore
  POST /sync                — pull invoices, generate CSV, return for download
  GET  /sync/batch          — pull ALL invoices, return batch CSV download
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import io
import csv
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL", "https://us02.procore.com")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID", "562949953425362")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID", "562949955372419")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="P1 — Procore to Sage Integration API",
    description="Pulls approved invoices from Procore and returns Sage 300 AP import CSV",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_token() -> str:
    r = requests.post(
        f"https://login.procore.com/oauth/token",
        data={
            "grant_type":    "client_credentials",
            "client_id":     os.getenv("PROCORE_CLIENT_ID"),
            "client_secret": os.getenv("PROCORE_CLIENT_SECRET"),
        }
    )
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Procore authentication failed")
    return r.json()["access_token"]

def get_headers(token: str) -> dict:
    return {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": str(COMPANY_ID),
    }

# ── Procore extraction ─────────────────────────────────────────────────────────

def fetch_approved_invoices(token: str, project_id: str = None) -> list:
    headers = get_headers(token)
    pid = project_id or PROJECT_ID
    params = {"project_id": pid, "company_id": COMPANY_ID}
    approved = []

    # Owner invoices
    r = requests.get(f"{BASE_URL}/rest/v1.0/payment_applications", headers=headers, params=params)
    if r.status_code == 200:
        for inv in r.json():
            if str(inv.get("status", "")).lower() in ["approved", "approved_as_noted"]:
                inv["_type"] = "owner"
                approved.append(inv)

    # Subcontractor invoices
    r = requests.get(f"{BASE_URL}/rest/v1.0/requisitions", headers=headers, params=params)
    if r.status_code == 200:
        for inv in r.json():
            if str(inv.get("status", "")).lower() in ["approved", "approved_as_noted"]:
                inv["_type"] = "subcontractor"
                approved.append(inv)

    return approved

# ── Transformation ─────────────────────────────────────────────────────────────

def safe_float(val):
    try:
        return float(str(val).replace(",", "").replace("$", ""))
    except:
        return 0.0

def transform_invoice(inv: dict) -> dict:
    inv_type = inv.get("_type", "owner")

    if inv_type == "owner":
        g702      = inv.get("g702", {})
        vendor    = inv.get("formatted_contract_company", "Unknown")
        pre_tax   = safe_float(g702.get("current_payment_due", 0))
        tax       = safe_float(g702.get("tax_applicable_to_this_payment", 0))
        inv_num   = inv.get("invoice_number") or str(inv.get("number", ""))
    else:
        summary   = inv.get("summary", {})
        vendor    = inv.get("vendor_name", "Unknown")
        pre_tax   = safe_float(summary.get("current_payment_due", 0))
        tax       = safe_float(summary.get("tax_applicable_to_this_payment", 0))
        inv_num   = inv.get("invoice_number") or str(inv.get("number", ""))

    # AGCM Sage transformation rules
    raw_job   = str(inv.get("project_id", PROJECT_ID))
    sage_job  = raw_job + "-0" if not raw_job.endswith("-0") else raw_job
    raw_cost  = "01-5204"
    parts     = raw_cost.split("-")
    sage_cost = raw_cost + "00" if len(parts[-1]) == 4 else raw_cost
    invoice_date = inv.get("billing_date", "")
    if invoice_date:
        try:
            d = datetime.strptime(invoice_date, "%Y-%m-%d")
            invoice_date = d.strftime("%m/%d/%Y")
        except:
            pass

    return {
        "vendor":         vendor,
        "invoice_number": inv_num,
        "description":    f"#{raw_job} {vendor}",
        "pre_tax":        pre_tax,
        "tax":            tax,
        "total":          pre_tax + tax,
        "discount":       0.00,
        "invoice_date":   invoice_date,
        "date_received":  datetime.now().strftime("%m/%d/%Y"),
        "payment_date":   inv.get("payment_date", ""),
        "job":            sage_job,
        "cost_code":      sage_cost,
        "category":       sage_cost.split("-")[0] if "-" in sage_cost else "01",
        "account":        "1-1-5100.00",
        "tax_group":      "S1152",
        "holdback":       0.00,
        "payment_type":   "Electronic",
        "invoice_type":   "Job-related" if inv_type in ["owner", "subcontractor"] else "Admin",
        "procore_id":     inv.get("id"),
        "_type":          inv_type,
    }

# ── CSV generation ─────────────────────────────────────────────────────────────

def generate_csv_bytes(invoices: list) -> bytes:
    """Generate Sage 300 AP import CSV as bytes (for streaming download)."""
    output = io.StringIO()
    writer = csv.writer(output)

    for inv in invoices:
        t = transform_invoice(inv)
        # API header record
        writer.writerow([
            "API",
            t["vendor"],
            t["invoice_number"],
            t["description"],
            f"{t['pre_tax']:.2f}",
            f"{t['tax']:.2f}",
            f"{t['discount']:.2f}",
            t["invoice_date"],
            t["date_received"],
            "",  # discount date
            t["payment_date"],
        ])
        # APD distribution record
        writer.writerow([
            "APD",
            "",  # commitment
            t["job"],
            "",
            t["cost_code"],
            t["category"],
            t["account"],
            t["tax_group"],
            "",
            "",
            f"{t['pre_tax']:.2f}",
            f"{t['tax']:.2f}",
            f"{t['holdback']:.2f}",
            "",
            t["description"],
            t["payment_type"],
        ])

    return output.getvalue().encode("utf-8")

# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "P1 Procore-Sage Integration", "version": "1.0.0"}


@app.get("/invoices")
def list_invoices(project_id: str = Query(None, description="Procore project ID (optional, defaults to .env)")):
    """List all approved invoices from Procore — no CSV, just JSON."""
    token = get_token()
    invoices = fetch_approved_invoices(token, project_id)
    if not invoices:
        return {"count": 0, "invoices": []}
    transformed = [transform_invoice(inv) for inv in invoices]
    return {
        "count":    len(transformed),
        "invoices": transformed,
    }


@app.post("/sync")
def sync_and_download(project_id: str = Query(None, description="Procore project ID (optional)")):
    """
    Pull approved invoices from Procore, generate Sage 300 CSV, return as download.
    x calls this → gets a CSV file back immediately.
    """
    token    = get_token()
    invoices = fetch_approved_invoices(token, project_id)

    if not invoices:
        raise HTTPException(status_code=404, detail="No approved invoices found in Procore")

    csv_bytes = generate_csv_bytes(invoices)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"sage_ap_batch_{timestamp}.csv"

    logger.info(f"Sync: {len(invoices)} invoices → {filename}")

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/sync/batch")
def sync_batch_download(project_id: str = Query(None)):
    """
    Same as POST /sync but via GET — easier to trigger from a browser or button.
    """
    token    = get_token()
    invoices = fetch_approved_invoices(token, project_id)

    if not invoices:
        raise HTTPException(status_code=404, detail="No approved invoices found in Procore")

    csv_bytes = generate_csv_bytes(invoices)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"sage_ap_batch_{timestamp}.csv"

    logger.info(f"Batch sync: {len(invoices)} invoices → {filename}")

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )