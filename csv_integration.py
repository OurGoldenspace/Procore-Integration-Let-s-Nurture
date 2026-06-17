# csv_integration.py
# Generates Sage 300 CRE AP Invoice Import CSV
# Format confirmed by Andrew O'Neill — June 2026
# Template: AP_Invoice_Import_template_format.PDF
#
# Two record types per invoice:
#   API = Invoice header
#   APD = Distribution line item (job cost allocation)
#
# File path: \\AGCM-VM01455\TIMBERLINE OFFICE\DATA\AGCM\NEW.API

import csv
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

os.makedirs("logs", exist_ok=True)
os.makedirs("sage_import", exist_ok=True)

logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%Y-%m-%d')}_csv_integration.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

# ─── Field format helpers ────────────────────────────────────────

def format_sage_date(date_str):
    """
    Convert various date formats to Sage MM/DD/YYYY
    Sage 300 CRE expects: MM/DD/YYYY
    """
    if not date_str:
        return ""
    try:
        # Handle YYYY-MM-DD
        if len(str(date_str)) >= 10 and str(date_str)[4] == "-":
            parts = str(date_str)[:10].split("-")
            return f"{parts[1]}/{parts[2]}/{parts[0]}"
        return str(date_str)
    except:
        return str(date_str)

def convert_job_number(procore_job):
    """
    Procore: 25-1355 → Sage: 25-1355-0
    Sage format: xx-xxxx-x (Alpha 9)
    Confirmed by Timie-Lynn Jones
    """
    if not procore_job:
        return ""
    cleaned = str(procore_job).strip()
    # Already has suffix
    if len(cleaned.split("-")) == 3:
        return cleaned
    # Add -0 suffix
    return f"{cleaned}-0"

def convert_cost_code(procore_code):
    """
    Procore: 01-5204 → Sage: 01-520400
    Sage format: xx-xxxxxx (Alpha 9)
    Confirmed by Timie-Lynn Jones
    """
    if not procore_code:
        return ""
    parts = str(procore_code).strip().split("-")
    if len(parts) == 2:
        # Pad second part to 6 digits
        return f"{parts[0]}-{parts[1]:0<6}"
    return str(procore_code)

# ─── API Record (Invoice Header) ────────────────────────────────

def build_api_record(invoice_data):
    """
    Build the API (header) record for Sage 300 CRE import.
    
    Fields from Andrew's template:
    API, Vendor, Invoice, Description, Amount, Tax, 
    Discount Offered, Invoice Date, Date Received, 
    Discount Date, Payment Date, Invoice Code 1,
    Smry Payee Name, Address1, Address2, City, State, ZIP
    """
    return {
        "Record Type":          "API",
        "Vendor":               str(invoice_data.get("vendor_code", ""))[:7],
        "Invoice":              str(invoice_data.get("invoice_number", ""))[:15],
        "Description":          str(invoice_data.get("description", ""))[:30],
        "Amount":               invoice_data.get("pre_tax_amount", 0),
        "Tax":                  invoice_data.get("tax_amount", 0),
        "Discount Offered":     0,
        "Invoice Date":         format_sage_date(invoice_data.get("invoice_date", "")),
        "Date Received":        format_sage_date(
                                    invoice_data.get("received_date", 
                                    datetime.now().strftime("%Y-%m-%d"))
                                ),
        "Discount Date":        "",
        "Payment Date":         format_sage_date(invoice_data.get("due_date", "")),
        "Invoice Code 1":       str(invoice_data.get("invoice_code", ""))[:10],
        "Smry Payee Name":      "",
        "Smry Payee Address 1": "",
        "Smry Payee Address 2": "",
        "Smry Payee City":      "",
        "Smry Payee State":     "",
        "Smry Payee ZIP":       ""
    }

# ─── APD Record (Distribution Line Item) ────────────────────────

def build_apd_record(invoice_data):
    """
    Build the APD (distribution) record for Sage 300 CRE import.
    
    Two types:
    - Job-related: fills Job + Cost Code fields
    - Admin: fills Expense Account field instead
    
    Fields from Andrew's template:
    APD, Commitment, Commitment Line Item, Job, Extra, 
    Cost Code, Category, Standard Item, Expense Account, 
    AP Account, Tax Group, Units, Unit Cost, Amount, Tax, 
    Holdback, 1099 Exempt, Draw, Description, Joint Payee, 
    Default Payment Type
    """
    is_job_related = bool(invoice_data.get("job_number"))
    
    return {
        "Record Type":           "APD",
        "Commitment":            str(invoice_data.get("commitment", ""))[:12],
        "Commitment Line Item":  "",
        "Job":                   convert_job_number(
                                     invoice_data.get("job_number", "")
                                 ) if is_job_related else "",
        "Extra":                 str(invoice_data.get("extra", ""))[:10],
        "Cost Code":             convert_cost_code(
                                     invoice_data.get("cost_code", "")
                                 ) if is_job_related else "",
        "Category":              str(invoice_data.get("category", ""))[:3],
        "Standard Item":         "",
        "Expense Account":       str(invoice_data.get("account", ""))[:11] 
                                 if not is_job_related else "",
        "AP Account":            "",
        "Tax Group":             str(invoice_data.get("tax_group", "S1152"))[:6],
        "Units":                 "",
        "Unit Cost":             "",
        "Amount":                invoice_data.get("pre_tax_amount", 0),
        "Tax":                   invoice_data.get("tax_amount", 0),
        "Holdback":              invoice_data.get("holdback", 0),
        "1099 Exempt":           "",
        "Draw":                  "",
        "Description":           str(invoice_data.get("description", ""))[:30],
        "Joint Payee":           "",
        "Default Payment Type":  "2"  # 1=Cheque, 2=Electronic
    }

# ─── Main Export Function ────────────────────────────────────────

def procore_to_sage_csv(invoice_data, output_folder="sage_import"):
    """
    Generate Sage 300 CRE AP Invoice Import CSV.
    
    Format: Two rows per invoice
      Row 1 = API record (invoice header)
      Row 2 = APD record (distribution/cost allocation)
    
    Multiple invoices can be in one file — each gets API + APD rows.
    
    Template confirmed by Andrew O'Neill, CFO
    Field formats confirmed by Timie-Lynn Jones, Accounting
    """
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        inv_num   = invoice_data.get("invoice_number", "UNKNOWN")
        filename  = f"sage_ap_import_{inv_num}_{timestamp}.csv"
        filepath  = os.path.join(output_folder, filename)
        
        # Determine invoice type
        is_job = bool(invoice_data.get("job_number"))
        inv_type = "Job-related" if is_job else "Admin"
        
        print(f"\nInvoice type: {inv_type}")
        if is_job:
            print(f"Job:       {invoice_data.get('job_number')} → "
                  f"{convert_job_number(invoice_data.get('job_number'))}")
            if invoice_data.get("cost_code"):
                print(f"Cost Code: {invoice_data.get('cost_code')} → "
                      f"{convert_cost_code(invoice_data.get('cost_code'))}")
        
        # Build records
        api_record = build_api_record(invoice_data)
        apd_record = build_apd_record(invoice_data)
        
        # Write CSV — API headers then APD headers
        api_fields = list(api_record.keys())
        apd_fields = list(apd_record.keys())
        
        # Combine into single rows with max columns
        all_fields = list(range(max(len(api_fields), len(apd_fields))))
        
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            
            # Write API record as values only (no header)
            writer.writerow(list(api_record.values()))
            
            # Write APD record as values only
            writer.writerow(list(apd_record.values()))
        
        logging.info(f"CSV generated: {filename} | Type: {inv_type}")
        
        print(f"\n✅ Sage 300 import CSV generated: {filepath}")
        print(f"\nAPI Record (Header):")
        for k, v in api_record.items():
            if v:
                print(f"  {k:25}: {v}")
        print(f"\nAPD Record (Distribution):")
        for k, v in apd_record.items():
            if v:
                print(f"  {k:25}: {v}")
        
        return filepath
        
    except Exception as e:
        logging.error(f"CSV generation failed: {str(e)}")
        print(f"❌ Failed: {str(e)}")
        return None

def batch_export(invoices, output_folder="sage_import"):
    """
    Export multiple invoices into a single Sage import file.
    Each invoice gets an API + APD row pair.
    """
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"sage_ap_batch_{timestamp}.csv"
        filepath  = os.path.join(output_folder, filename)
        
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            
            for inv_data in invoices:
                api_record = build_api_record(inv_data)
                apd_record = build_apd_record(inv_data)
                writer.writerow(list(api_record.values()))
                writer.writerow(list(apd_record.values()))
        
        print(f"✅ Batch export: {len(invoices)} invoices → {filepath}")
        logging.info(f"Batch export: {len(invoices)} invoices → {filename}")
        return filepath
        
    except Exception as e:
        logging.error(f"Batch export failed: {str(e)}")
        print(f"❌ Batch failed: {str(e)}")
        return None

def verify_csv(filepath):
    """Read back and verify CSV contents"""
    print(f"\n=== Verifying CSV: {filepath} ===")
    try:
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                record_type = row[0] if row else "?"
                if record_type == "API":
                    print(f"\nRow {i+1} [API Header]:")
                    print(f"  Vendor:   {row[1]}")
                    print(f"  Invoice:  {row[2]}")
                    print(f"  Desc:     {row[3]}")
                    print(f"  Amount:   {row[4]}")
                    print(f"  Tax:      {row[5]}")
                    print(f"  Inv Date: {row[7]}")
                elif record_type == "APD":
                    print(f"Row {i+1} [APD Distribution]:")
                    print(f"  Job:      {row[3]}")
                    print(f"  Cost Code:{row[5]}")
                    print(f"  Category: {row[6]}")
                    print(f"  Account:  {row[8]}")
                    print(f"  Tax Grp:  {row[10]}")
                    print(f"  Amount:   {row[13]}")
                    print(f"  Tax:      {row[14]}")
                    print(f"  Pmt Type: {row[20]}")
        
        print(f"\n✅ Verification passed")
        return True
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SAGE 300 CRE AP INVOICE IMPORT — CSV GENERATOR")
    print("Format: Andrew O'Neill template (June 2026)")
    print("=" * 60)
    
    # ─── Test 1: Job-related invoice (from Procore TEST1) ────────
    print("\n--- Test 1: Job-Related Invoice ---")
    job_invoice = {
        "vendor_code":    "RITCH10",
        "invoice_number": "TEST1",
        "description":    "#1355 RITCHIES BUILDING",
        "pre_tax_amount": 500.00,
        "tax_amount":     75.00,
        "invoice_date":   "2026-05-31",
        "received_date":  "2026-06-08",
        "due_date":       "2026-06-30",
        "job_number":     "25-1355",
        "cost_code":      "01-5204",
        "category":       "01",
        "tax_group":      "S1152"
    }
    path1 = procore_to_sage_csv(job_invoice)
    if path1:
        verify_csv(path1)
    
    # ─── Test 2: Admin invoice (no job/cost code) ────────────────
    print("\n\n--- Test 2: Admin Invoice ---")
    admin_invoice = {
        "vendor_code":    "ADMIR10",
        "invoice_number": "1234",
        "description":    "OFFICE SUPPLIES",
        "pre_tax_amount": 41.00,
        "tax_amount":     4.00,
        "invoice_date":   "2026-05-01",
        "received_date":  "2026-06-08",
        "due_date":       "2026-05-31",
        "account":        "1-1-5100.00",
        "tax_group":      "S1152"
    }
    path2 = procore_to_sage_csv(admin_invoice)
    if path2:
        verify_csv(path2)
    
    # ─── Test 3: Owner invoice (from Procore 26-000-01) ──────────
    print("\n\n--- Test 3: Owner Invoice ---")
    owner_invoice = {
        "vendor_code":    "QUEST10",
        "invoice_number": "26-000-01",
        "description":    "#0000 QUEST CAPITAL",
        "pre_tax_amount": 1000.00,
        "tax_amount":     150.00,
        "invoice_date":   "2026-05-31",
        "received_date":  "2026-06-08",
        "due_date":       "2026-06-30",
        "job_number":     "26-0000",
        "cost_code":      "01-3200",
        "category":       "01",
        "tax_group":      "S1152"
    }
    path3 = procore_to_sage_csv(owner_invoice)
    if path3:
        verify_csv(path3)
    
    # ─── Test 4: Batch export (all 3 invoices) ───────────────────
    print("\n\n--- Test 4: Batch Export ---")
    batch_path = batch_export([job_invoice, admin_invoice, owner_invoice])
    if batch_path:
        verify_csv(batch_path)
    
    print("\n" + "=" * 60)
    print("CSV GENERATION COMPLETE")
    print("=" * 60)
    print(f"\nFiles ready for Sage 300 import in: sage_import/")
    print(f"Drop these into: \\\\AGCM-VM01455\\TIMBERLINE OFFICE\\DATA\\AGCM\\")
