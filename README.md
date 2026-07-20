# Procore-to-Sage 300 CRE Integration Documentation

**Project:** LetsNurture AI Automation for AGCM (Benchmark Fabricators)  
**Component:** P1 - Procore ↔ Sage 300 AP Invoice Sync  
**Client:** AGCM (Avant Garde Construction and Management)  
**Status:** Active Development  
**Last Updated:** July 2026  

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Setup & Configuration](#setup--configuration)
5. [Field Mapping](#field-mapping)
6. [Data Flow](#data-flow)
7. [CSV Format Specification](#csv-format-specification)
8. [Running Tests](#running-tests)
9. [Deployment & Usage](#deployment--usage)
10. [Troubleshooting](#troubleshooting)
11. [Contacts & Support](#contacts--support)

---

## Overview

### What This Does

The Procore-to-Sage 300 integration **automatically syncs invoices from Procore to Sage 300 CRE's Accounts Payable module**. It:

- ✅ Fetches approved owner invoices (payment applications) from Procore
- ✅ Fetches approved subcontractor invoices (requisitions) from Procore
- ✅ Transforms invoice data using AGCM-specific field mappings
- ✅ Generates Sage 300-compatible CSV files
- ✅ Enables one-click import into Sage AP without manual data entry

### Business Value

| Before Integration | After Integration |
|---|---|
| Manual copy-paste of invoices | Automated invoice pull |
| 20-30 min per invoice | <1 min per invoice |
| High error rate | Validation before import |
| Duplicate entry risk | Single source of truth |

### Scope

**In Scope:**
- Procore payment applications (owner invoices)
- Procore requisitions (subcontractor invoices)
- CSV generation for Sage 300 AP import
- Field mapping & validation
- Error logging & diagnostics

**Out of Scope:**
- Sage 300 vendor creation (vendors must exist first)
- Two-way sync (read-only from Procore)
- Automatic posting in Sage (manual review + post required)
- Attachments (future phase)

---

## Architecture

### System Components

```
┌─────────────┐
│   Procore   │
│  (Production│
│  + Sandbox) │
└──────┬──────┘
       │ OAuth2 + REST API
       │
       v
┌─────────────────────────────────────┐
│  Procore Integration Layer          │
│  ├─ user_token_auth.py             │
│  ├─ procore_oauth.py               │
│  └─ get_invoice_id.py              │
└──────┬──────────────────────────────┘
       │
       v
┌─────────────────────────────────────┐
│  ETL Transform Layer                │
│  ├─ Field Extraction                │
│  ├─ Sage Field Conversion           │
│  └─ Validation Rules                │
└──────┬──────────────────────────────┘
       │
       v
┌─────────────────────────────────────┐
│  CSV Generation                     │
│  └─ CSV Format: API + APD Records   │
└──────┬──────────────────────────────┘
       │
       v
┌──────────────────────────────────────┐
│   Sage 300 Import                    │
│   ├─ AP > Enter Invoices > Import    │
│   └─ Review + Post                   │
└──────────────────────────────────────┘
```

### Data Sources

| Source | Type | Contains |
|--------|------|----------|
| **Procore Payment Applications** | Owner Invoices | G.702 forms, builder invoices, payment requests |
| **Procore Requisitions** | Sub Invoices | Subcontractor payment requests |
| **Sage 300 Vendor Master** | Reference | Valid vendor codes for lookup |
| **Sage 300 Job Master** | Reference | Valid job numbers (format: YY-XXXX-0) |
| **Sage 300 Cost Codes** | Reference | Valid cost codes (format: XX-XXXXXX) |

---

## Prerequisites

### Technical Requirements

- **Python 3.8+**
- **Virtual Environment** (venv)
- **Required Packages:**
  ```
  requests==2.31.0
  python-dotenv==1.0.0
  ```

### Procore Requirements

- ✅ Active Procore account with AP/Requisitions access
- ✅ OAuth2 Client ID + Secret (from Procore admin)
- ✅ Company ID (visible in Procore URL or settings)
- ✅ Project ID (test project: LETS NURTURE TEST)
- ✅ At least one approved invoice in Procore

### Sage 300 Requirements

- ✅ Sage 300 CRE installed (sandbox or production)
- ✅ All vendors pre-created in vendor master
- ✅ All job numbers created (format: YY-XXXX-0)
- ✅ All cost codes created (format: XX-XXXXXX)
- ✅ Tax group S1152 configured (HST 15%)
- ✅ AP module access for import

### AGCM-Specific Data

**Known Vendors:**
- Ritches building and flooring (Vendor Code: TBD)
- M6 Electric Ltd (Vendor Code: TBD)
- [Add more as needed]

**Sample Job Number:** 25-1355-0 (Year-Code-Suffix)  
**Sample Cost Code:** 01-520400 (Division-Item format)  
**Tax Group:** S1152 (15% HST)

---

## Setup & Configuration

### Step 1: Clone/Download Project

```bash
cd C:\Users\shrey\Documents\Projects\Procore-integration\Procore-Integration-Let-s-Nurture
```

### Step 2: Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

**requirements.txt:**
```
requests==2.31.0
python-dotenv==1.0.0
```

### Step 4: Configure .env File

Create `.env` in project root:

```env
# Procore OAuth
PROCORE_CLIENT_ID=your_client_id
PROCORE_CLIENT_SECRET=your_client_secret
PROCORE_BASE_URL=https://us02.procore.com
PROCORE_REDIRECT_URI=http://localhost:8000/oauth/callback

# Procore Sandbox/Production
PROCORE_COMPANY_ID=562949953425362
PROCORE_PROJECT_ID=562949955372419

# Sage 300 (if using API)
SAGE_BASE_URL=http://localhost:3001
SAGE_USERNAME=sage_user
SAGE_PASSWORD=sage_password

# AGCM-Specific Mappings
SAGE_VENDOR_CODE=
SAGE_JOB_NUMBER=25-1355-0
SAGE_COST_CODE=01-520400
SAGE_TAX_GROUP=S1152
```

### Step 5: Test Authentication

```powershell
python -c "from user_token_auth import get_token; print(get_token())"
```

Expected output: `Bearer eyJ0eXAi...` (OAuth token)

---

## Field Mapping

### Procore → Sage 300 Transformation Rules

#### Invoice-Level Fields

| Procore Field | Data Type | Sage Field | Transform Rule |
|---|---|---|---|
| `invoice_number` | String | Invoice # | Direct pass-through |
| `formatted_contract_company` (owner) or `vendor_name` (sub) | String | Vendor | Direct pass-through; must exist in vendor master |
| `g702.current_payment_due` (owner) or `summary.current_payment_due` (sub) | Float | Pre-Tax Amount | Parse float; may include tax |
| `g702.tax_applicable_to_this_payment` or `summary.tax_applicable_to_this_payment` | Float | Tax Amount | Parse float; default 0 if omitted |
| `billing_date` | ISO Date | Invoice Date | Format: MM/DD/YYYY |
| `due_date` | ISO Date | Due Date | Format: MM/DD/YYYY |
| `id` | Integer | Vendor Code (fallback) | Use only if vendor code not provided |

#### Line-Item-Level Fields

| Procore Field | Sage Field | Transform Rule |
|---|---|---|
| Project ID | Job Number | Append "-0" suffix if missing (e.g., 25-1355 → 25-1355-0) |
| Default Cost Code | Cost Code | Append "00" if last segment is 4 digits (e.g., 01-5204 → 01-520400) |
| Commitment ID (sub invoices) | Reference | Stored for audit trail |
| N/A | Tax Group | Always S1152 (15% HST) |
| N/A | Description | Format: `#{Job} {Vendor}` (e.g., #25-1355 M6 Electric Ltd) |
| N/A | Payment Type | Always "Electronic" |

### Validation Rules

| Field | Rule | Error Handling |
|---|---|---|
| Vendor Code | Must exist in Sage 300 vendor master | Warning logged; import continues with lookup |
| Job Number | Must match pattern `YY-XXXX-0` | Auto-corrected if missing -0 |
| Cost Code | Must match pattern `XX-XXXXXX` | Auto-corrected if last segment < 6 chars |
| Invoice Amount | Must be > 0 | Skipped; logged as validation error |
| Tax Group | Must be S1152 | Hardcoded; no override |

---

## Data Flow

### End-to-End Invoice Sync Flow

```
1. USER TRIGGERS TEST
   python ready_to_test.py

2. AUTHENTICATION
   ├─ Load .env credentials
   ├─ Call Procore OAuth endpoint
   └─ Receive Bearer token

3. FETCH APPROVED INVOICES
   ├─ GET /rest/v1.0/payment_applications (owner invoices)
   │   └─ Filter: status in [approved, approved_as_noted]
   ├─ GET /rest/v1.0/requisitions (sub invoices)
   │   └─ Filter: status in [approved, approved_as_noted]
   └─ Combine results into single list

4. EXTRACT FIELDS
   For each approved invoice:
   ├─ Extract vendor name, invoice #, amounts, dates
   ├─ Parse G.702 or summary section
   ├─ Determine invoice type (owner vs sub)
   └─ Store in Python dict

5. APPLY SAGE TRANSFORMS
   For each extracted invoice:
   ├─ Append -0 to job number if missing
   ├─ Append 00 to cost code if needed
   ├─ Set tax group to S1152
   ├─ Format dates to MM/DD/YYYY
   ├─ Generate description
   └─ Store in transformed dict

6. GENERATE CSV
   ├─ For each transformed invoice:
   │   ├─ Create API record (header)
   │   └─ Create APD record (line item)
   ├─ Write to file: ./output/sage_invoices_procore_YYYYMMDD_HHMMSS.csv
   └─ Return filepath

7. VALIDATE CSV
   ├─ Count API records
   ├─ Count APD records
   ├─ Check 1:1 pairing
   └─ Log warnings if issues

8. USER IMPORTS TO SAGE
   ├─ Open Sage 300 > AP > Enter Invoices
   ├─ Click List...
   ├─ File > Import
   ├─ Select CSV file
   ├─ Review field mapping
   ├─ Click Import
   └─ Click Accept Invoice to post
```

### Error Handling Flow

```
If step fails:
├─ Log error with context (invoice #, field, value)
├─ Add to error summary
├─ Continue with next invoice (non-blocking)
└─ Display summary at end with retry instructions
```

---

## CSV Format Specification

### Sage 300 CSV Record Types

Sage 300 CRE accepts two record types for AP import: **API** and **APD**.

#### API Record (Invoice Header)

**Purpose:** Define the invoice header (vendor, amount, dates)

**Format:**
```
API,{filler},{invoice_num},{description},{pretax},{tax},{discount},{inv_date},{due_date},{filler},{gl_date}
```

**Example:**
```
API,,TEST1,#25-1355-0 Ritches Building & Flooring,500.00,0.00,0,05/31/2026,06/03/2026,,05/31/2026
```

**Field Descriptions:**

| Position | Field Name | Data Type | Length | Required | Example | Notes |
|----------|-----------|-----------|--------|----------|---------|-------|
| 1 | Record Type | String | 3 | Yes | API | Always "API" |
| 2 | Filler | String | - | No | (blank) | Leave empty |
| 3 | Invoice Number | String | 20 | Yes | TEST1 | Unique per vendor |
| 4 | Description | String | 60 | Yes | #25-1355-0 Ritches Building & Flooring | Job + Vendor |
| 5 | Pre-Tax Amount | Float | 12,2 | Yes | 500.00 | Decimal format |
| 6 | Tax Amount | Float | 12,2 | Yes | 0.00 | HST/Other tax |
| 7 | Discount | Float | 12,2 | No | 0 | Default 0 |
| 8 | Invoice Date | Date | - | Yes | 05/31/2026 | MM/DD/YYYY |
| 9 | Due Date | Date | - | Yes | 06/03/2026 | MM/DD/YYYY |
| 10 | Filler | String | - | No | (blank) | Leave empty |
| 11 | GL Date | Date | - | Yes | 05/31/2026 | MM/DD/YYYY; usually = Invoice Date |

#### APD Record (Invoice Detail/Line Item)

**Purpose:** Define the invoice line item (job, cost code, amount, tax group)

**Format:**
```
APD,{filler},{filler},{cost_code},{filler},{filler},{filler},{filler},{filler},{tax_group},{filler},{filler},{pretax},{tax},{discount},{filler},{filler},{filler},{description},{filler},{line_seq}
```

**Example:**
```
APD,,,01-520400,,,,,S1152,,,500.00,0.00,0,,,#25-1355-0 Ritches Building & Flooring,,2
```

**Field Descriptions:**

| Position | Field Name | Data Type | Notes |
|----------|-----------|-----------|-------|
| 1 | Record Type | String | Always "APD" |
| 2-3 | Filler | String | Leave empty |
| 4 | Cost Code | String | Format: XX-XXXXXX (e.g., 01-520400) |
| 5-9 | Filler | String | Leave empty |
| 10 | Tax Group | String | Always S1152 for AGCM (15% HST) |
| 11-12 | Filler | String | Leave empty |
| 13 | Amount (Pre-Tax) | Float | Decimal format |
| 14 | Tax Amount | Float | Decimal format |
| 15 | Discount | Float | Default 0 |
| 16-18 | Filler | String | Leave empty |
| 19 | Description | String | Job + Vendor for audit trail |
| 20 | Filler | String | Leave empty |
| 21 | Line Sequence | Integer | Always 2 (1 header + 2 line item) |

### Complete CSV Example

```csv
API,,TEST1,#562949955372419-0 Ritches Building & Flooring,500.00,0.00,0,2026-05-31,2026-05-31,,2026-05-31
APD,,,01-520400,,,,,S1152,,,500.00,0.00,0,,,#562949955372419-0 Ritches Building & Flooring,,2
API,,TEST2,#562949955372419-0 M6 Electric Ltd,300.00,0.00,0,2026-05-31,2026-05-31,,2026-05-31
APD,,,01-520400,,,,,S1152,,,300.00,0.00,0,,,#562949955372419-0 M6 Electric Ltd,,2
```

### Validation Rules

- ✅ Each API record **must** have exactly one APD record following it
- ✅ Column count must be consistent (21 fields per record)
- ✅ No blank lines between records
- ✅ Amounts must be decimals (e.g., 500.00, not 500 or $500)
- ✅ Dates must be MM/DD/YYYY format
- ✅ Tax Group must always be S1152

---

## Running Tests

### Test 1: Full End-to-End (All Invoices)

**Purpose:** Validate entire pipeline from Procore fetch to CSV generation

```powershell
python ready_to_test.py
```

**Expected Output:**
```
======================================================================
PROCORE → SAGE 300 INTEGRATION TEST (END-TO-END)
======================================================================
[1/6] AUTHENTICATION
----------------------------------------------------------------------
✅ Authenticated with Procore

[2/6] PROJECT ACCESS
----------------------------------------------------------------------
✅ Project: LETS NURTURE TEST
   ID: 562949955372419

[3/6] FETCHING APPROVED INVOICES
----------------------------------------------------------------------
✓ Owner invoices: N total, M approved
✓ Subcontractor invoices: X total, Y approved
✅ Total approved invoices found: N

[4/6] ETL TRANSFORM
----------------------------------------------------------------------
✓ Invoice #TEST1
  Vendor: Ritches Building & Flooring
  Amount: $500.00 ...
✅ Transformed 2 invoices

[5/6] GENERATING SAGE CSV
----------------------------------------------------------------------
✅ CSV generated: ./output/sage_invoices_procore_20260715_101451.csv

[6/6] VALIDATING CSV FORMAT
----------------------------------------------------------------------
✓ Record pairs balanced: 2 API + 2 APD
✅ CSV format validated

======================================================================
TEST SUMMARY
======================================================================
  Authentication:    ✅
  Project Access:    ✅
  Invoice Fetch:     ✅
  ETL Transform:     ✅
  CSV Generation:    ✅
  CSV Validation:    ✅

✅ ALL TESTS PASSED
```

### Test 2: Limit to N Invoices

**Purpose:** Test with specific number of invoices

```powershell
python ready_to_test.py 1
```

This will process only the first 1 approved invoice.

### Test 3: Manual CSV Inspection

**Purpose:** Verify CSV format before Sage import

```powershell
# Open CSV in Excel
.\output\sage_invoices_procore_20260715_101451.csv

# Or view in PowerShell
Get-Content .\output\sage_invoices_procore_20260715_101451.csv | Select-Object -First 5
```

**Checklist:**
- [ ] API and APD records alternate
- [ ] Invoice numbers are correct
- [ ] Vendor names match Procore
- [ ] Amounts match (pre-tax + tax = total)
- [ ] Dates in MM/DD/YYYY format
- [ ] Job numbers have -0 suffix
- [ ] Cost codes have 6-digit format

---

## Deployment & Usage

### Production Workflow

**Step 1: Prepare Sage 300**

1. Ensure all vendors exist in vendor master
2. Ensure all job numbers are created
3. Ensure all cost codes are created
4. Verify tax group S1152 is configured

**Step 2: Run Integration Test**

```powershell
cd C:\Users\shrey\Documents\Projects\Procore-integration\Procore-Integration-Let-s-Nurture
.\venv\Scripts\Activate
python ready_to_test.py
```

**Step 3: Download CSV**

```
File location: ./output/sage_invoices_procore_YYYYMMDD_HHMMSS.csv
```

**Step 4: Import to Sage 300**

1. Open **Sage 300 > Accounts Payable > Enter Invoices**
2. Click **List...** button (bottom left)
3. Click **File > Import**
4. Select your CSV file
5. Review the **field mapping** popup:
   - Invoice # → matches CSV column 3 (TEST1, TEST2, etc.)
   - Vendor → matches CSV column 4 description
   - Pre-Tax Amount → matches CSV column 5
   - Tax → matches CSV column 6
   - Invoice Date → matches CSV column 8
   - Due Date → matches CSV column 9
6. Click **Import**
7. Review invoices in the dialog
8. (Optional) Attach documents using **Attachments** button
9. Click **Accept Invoice** to post to AP

**Step 5: Verify in Sage**

1. Go to **AP > Inquiry > Vendor Invoices**
2. Search for invoices by vendor name
3. Verify amounts, dates, cost codes match Procore
4. Check GL posting if required

### Automated Scheduling (Future)

```powershell
# Run daily at 9 AM
Task Scheduler > Create Task
Program: python.exe
Arguments: ready_to_test.py
Schedule: Daily 9:00 AM
Log: C:\path\to\procore_integration.log
```

---

## Troubleshooting

### Issue 1: Authentication Fails

**Error:** `Client ID: xxxxx... ❌ Auth failed — check credentials in .env`

**Cause:** Invalid OAuth credentials or network issue

**Solutions:**
1. Verify `.env` has correct `PROCORE_CLIENT_ID` and `PROCORE_CLIENT_SECRET`
2. Check Procore admin panel for current credentials
3. Verify internet connection
4. Check if OAuth app is still active in Procore

**Debug:**
```powershell
python -c "from user_token_auth import get_token; print(get_token())"
```

---

### Issue 2: Project Access Denied

**Error:** `❌ Project access failed: 403` or `❌ Project access failed: 404`

**Cause:** Invalid project ID or insufficient permissions

**Solutions:**
1. Verify `PROCORE_PROJECT_ID` in `.env` is correct
2. Check that user has access to this project in Procore
3. Ensure project is in the correct company

**Debug:**
```powershell
# Verify project ID
# Go to Procore > Project Settings > copy Project ID
# Paste into .env as PROCORE_PROJECT_ID
```

---

### Issue 3: No Approved Invoices Found

**Error:** `⚠️ NO APPROVED INVOICES FOUND`

**Cause:** No invoices in Procore are marked as "Approved"

**Solutions:**
1. Create test invoices in Procore:
   - Go to **Accounts Payable > Invoices**
   - Create new payment application (owner) or requisition (sub)
   - Fill in vendor, amount, date
   - Submit for approval
   - Approve the invoice
2. Check invoice status: must be "Approved" or "Approved as Noted"
3. Wait 1-2 minutes for Procore API to sync

---

### Issue 4: CSV Generation Fails - `'int' object has no attribute 'strip'`

**Error:** `AttributeError: 'int' object has no attribute 'strip'`

**Cause:** Vendor code is integer (Procore ID) instead of string

**Solution:** Ensure `vendor_code` is converted to string before `.strip()`

**Code Fix:**
```python
vendor_code = str(inv.get("vendor_code", "")).strip() or "VENDOR"
```

---

### Issue 5: CSV Validation Warns About Mismatched Records

**Error:** `⚠️ WARNING: API records (2) != APD records (1)`

**Cause:** Unequal number of headers and line items

**Solutions:**
1. Each API record must have exactly 1 APD record
2. Check that CSV generation loop creates both for each invoice
3. Manually inspect CSV in Excel

**Example Valid Structure:**
```
API,...   (header)
APD,...   (line item)
API,...   (header)
APD,...   (line item)
```

---

### Issue 6: Sage Import Fails - "Vendor Not Found"

**Error:** `Vendor not found: Ritches building and flooring`

**Cause:** Vendor does not exist in Sage 300 vendor master

**Solutions:**
1. In Sage 300, go to **AP > Vendors**
2. Create vendor:
   - Vendor Code: (e.g., RITCH001)
   - Vendor Name: Ritches building and flooring
   - Address, contact info as needed
3. Re-run integration with updated vendor code

**Alternative:**
- Update `.env` to specify correct vendor code:
  ```env
  SAGE_VENDOR_CODE=RITCH001
  ```

---

### Issue 7: Sage Import Fails - "Job Not Found"

**Error:** `Job not found: 25-1355-0`

**Cause:** Job number does not exist in Sage 300 job master

**Solutions:**
1. In Sage 300, go to **Project Management > Job Master**
2. Create job:
   - Job Number: 25-1355-0 (must include -0)
   - Job Name: (e.g., "Project Name")
   - Other details as needed
3. Re-run integration

---

### Issue 8: Sage Import Fails - "Cost Code Not Found"

**Error:** `Cost code not found: 01-520400`

**Cause:** Cost code does not exist in Sage 300

**Solutions:**
1. In Sage 300, go to **AP > Codes > Cost Codes**
2. Create cost code:
   - Code: 01-520400 (format: XX-XXXXXX)
   - Description: (e.g., "Labor")
3. Re-run integration

---

### Issue 9: Sage Import Succeeds But Amounts Don't Match

**Error:** Invoice appears in Sage but pre-tax or tax amounts are wrong

**Cause:** 
- Procore rounding/formatting issue
- Tax calculation mismatch
- CSV decimal formatting

**Solutions:**
1. Verify in Procore that amounts are exactly as expected
2. Check if invoice includes embedded tax
3. Inspect CSV file to confirm values before import
4. Manually adjust in Sage if small discrepancy

---

### Issue 10: Connection Timeout to Procore

**Error:** `Connection to us02.procore.com timed out. (connect timeout=10)`

**Cause:** Network connectivity issue or Procore API slow

**Solutions:**
1. Check internet connection
2. Wait 1-2 minutes and retry
3. Check Procore system status: https://status.procore.com
4. If VPN required, ensure connected

---

## Contacts & Support

### AGCM Stakeholders

| Role | Name | Contact | Notes |
|------|------|---------|-------|
| CFO / Sage Expert | Andrew O'Neill | andrew@agcm.ca | Oversees AP, can create jobs/vendors |
| AP User | Timie-Lynn Jones | timie@agcm.ca | Day-to-day Sage user |
| AP User | Stephanie McArdle | stephanie@agcm.ca | Accounting contact |
| Procore Admin | Prathmesh | prathmesh@agcm.ca | Manages Procore users/permissions | 
| Procurement | Keith Flynn | keith@agcm.ca | Sales/estimation, requisition approver |

### LetsNurture Team

| Role | Name | Contact | Notes |
|------|------|---------|-------|
| Project Lead | Kashyap | kashyap@letsnurture.in | Primary contact for integration |
| Tech Lead | Eduardo Hahn | eduardo@letsnurture.in | Architecture & debugging |
| Developer | Shreyas Varma | shreyas.varma@unb.ca | Builds integration code |

### Getting Help

**For Procore issues:**
- Contact Prathmesh (Procore admin)
- Check Procore documentation: https://developers.procore.com

**For Sage 300 issues:**
- Contact Andrew O'Neill or Timie-Lynn Jones
- Check Sage 300 CRE documentation
- Contact Sage support if needed

**For integration bugs:**
- Contact Shreyas Varma with error message + .env (redacted)
- Include CSV file and Sage 300 screenshot if applicable
- Check troubleshooting section first

---

## Appendix

### A. Field Mapping Reference

**AGCM Sage 300 Configuration:**

```
Tax Group: S1152 (15% HST)
Default Job: 25-1355-0
Default Cost Code: 01-520400
Payment Type: Electronic
```

**Known Vendors:**

| Vendor Name | Sage Code | Procore Name | Status |
|---|---|---|---|
| Ritches building and flooring | (TBD) | Ritches Building & Flooring | Test |
| M6 Electric Ltd | (TBD) | M6 Electric Ltd | Test |

### B. Sample Data

**Test Invoice 1:**
- Invoice #: TEST1
- Vendor: Ritches Building & Flooring
- Amount: $500.00
- Date: 05/31/2026
- Job: 25-1355-0
- Cost Code: 01-520400

**Test Invoice 2:**
- Invoice #: TEST2
- Vendor: M6 Electric Ltd
- Amount: $300.00
- Date: 05/31/2026
- Job: 25-1355-0
- Cost Code: 01-520400

### C. Important URLs

| System | URL |
|--------|-----|
| Procore OAuth | https://login.procore.com/oauth/token |
| Procore API | https://us02.procore.com/rest/v1.0 |
| Procore Docs | https://developers.procore.com |
| Sage Status | https://status.procore.com |

### D. Common CSV Issues & Fixes

| Issue | Example | Fix |
|-------|---------|-----|
| Amount with $ sign | $500.00 | Remove $ and parse as float |
| Amount with comma | 1,500.00 | Remove comma before parsing |
| ISO date format | 2026-05-31T00:00:00Z | Convert to MM/DD/YYYY |
| Missing -0 on job | 25-1355 | Append -0: 25-1355-0 |
| Short cost code | 01-5204 | Append 00: 01-520400 |

### E. Script Files Overview

| File | Purpose | Key Functions |
|------|---------|----------------|
| `ready_to_test.py` | Main integration test script | run_full_test() |
| `user_token_auth.py` | OAuth token retrieval | get_token() |
| `procore_oauth.py` | Procore API wrapper | ProCoreOAuth class |
| `get_invoice_id.py` | Invoice ID lookup | get_invoice_id() |
| `csv_integration.py` | CSV generation | procore_to_sage_csv() |
| `.env` | Configuration (secrets) | PROCORE_* keys, SAGE_* keys |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-15 | Initial documentation + CSV format spec |
| 1.1 | (Planned) | Add vendor code lookup, improve tax handling |
| 2.0 | (Planned) | Two-way sync, attachment support |

---

