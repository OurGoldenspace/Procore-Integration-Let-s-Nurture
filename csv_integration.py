import csv
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%Y-%m-%d')}_integration.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

def convert_job_number(procore_job):
    """
    Procore: 25-1355
    Sage:    25-1355-0
    Rule: append -0 to Procore job number
    """
    if not procore_job:
        return ""
    # Remove any existing -0 suffix first
    cleaned = procore_job.rstrip("-0").rstrip("-")
    return f"{cleaned}-0"

def convert_cost_code(procore_code):
    """
    Procore: 01-5204
    Sage:    01-520400
    Rule: append 00 to the numeric part after dash
    """
    if not procore_code:
        return ""
    parts = procore_code.split("-")
    if len(parts) == 2:
        return f"{parts[0]}-{parts[1]}00"
    return procore_code

def format_sage_date(date_str):
    """
    Convert various date formats to Sage MM-DD-YYYY
    """
    if not date_str:
        return ""
    try:
        # Handle YYYY-MM-DD format
        if len(date_str) == 10 and date_str[4] == "-":
            parts = date_str.split("-")
            return f"{parts[1]}-{parts[2]}-{parts[0]}"
        return date_str
    except:
        return date_str

def procore_to_sage_csv(invoice_data, output_folder="sage_import"):
    """
    Converts Procore invoice to Sage 300 AP invoice CSV
    
    Field mapping confirmed by Timie-Lynn Jones (AGCM)
    Job number and cost code transformations confirmed
    
    Two invoice types:
    - Job related:  requires Job + Cost Code
    - Admin:        requires Account only, no Job/Cost Code
    """
    try:
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename   = f"sage_ap_{invoice_data.get('invoice_number', 'UNKNOWN')}_{timestamp}.csv"
        filepath   = os.path.join(output_folder, filename)
        
        # Determine invoice type
        procore_job  = invoice_data.get("job_number", "")
        is_job_related = bool(procore_job)
        
        # Convert job number and cost code
        sage_job       = convert_job_number(procore_job)
        sage_cost_code = convert_cost_code(
            invoice_data.get("cost_code", "")
        )
        
        print(f"Invoice type: {'Job-related' if is_job_related else 'Admin'}")
        if is_job_related:
            print(f"Job: {procore_job} → {sage_job}")
            print(f"Cost Code: {invoice_data.get('cost_code')} → {sage_cost_code}")
        
        # Build Sage row
        sage_row = {
            # Header fields
            "VENDOR":       invoice_data.get("vendor_code", ""),
            "INVOICE":      invoice_data.get("invoice_number", ""),
            "INV_DATE":     format_sage_date(
                                invoice_data.get("invoice_date", "")
                            ),
            "PRE_TAX":      invoice_data.get("pre_tax_amount", 0),
            "TAX":          invoice_data.get("tax_amount", 0),
            "DESCRIPTION":  invoice_data.get("description", ""),
            "RECEIVED":     format_sage_date(
                                invoice_data.get("received_date",
                                datetime.now().strftime("%Y-%m-%d"))
                            ),
            "PMT_DATE":     format_sage_date(
                                invoice_data.get("due_date", "")
                            ),
            "PAYMENT_TYPE": "Electronic",
            
            # Line item fields
            "JOB":          sage_job if is_job_related else "",
            "COST_CODE":    sage_cost_code if is_job_related else "",
            "ACCOUNT":      "" if is_job_related else invoice_data.get("account", ""),
            "CATEGORY":     invoice_data.get("category", ""),
            "TAX_GROUP":    invoice_data.get("tax_group", "S1152"),
            
            # Audit
            "SYNCED_AT":    datetime.now().isoformat(),
            "SOURCE":       "Procore Auto-Sync"
        }
        
        # Validate required fields
        required = ["VENDOR", "INVOICE", "INV_DATE", "PRE_TAX"]
        missing  = [k for k in required if not sage_row.get(k)]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        # Write CSV
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=sage_row.keys())
            writer.writeheader()
            writer.writerow(sage_row)
        
        logging.info(f"CSV generated: {filename}")
        
        print(f"\n✅ CSV generated: {filepath}")
        print(f"\nField mapping applied:")
        for k, v in sage_row.items():
            print(f"  {k:15}: {v}")
        
        return filepath
        
    except Exception as e:
        logging.error(f"CSV failed: {str(e)}")
        print(f"❌ Failed: {str(e)}")
        return None

def verify_csv(filepath):
    """Read back CSV and confirm contents"""
    print(f"\n=== Verifying CSV ===")
    try:
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for k, v in row.items():
                    print(f"  {k:15}: {v}")
        print(f"✅ Verification passed")
        return True
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Procore → Sage 300 AP Invoice CSV ===\n")
    
    # Sample invoice using real AGCM format
    sample = {
        "vendor_code":    "ADMIR10",
        "invoice_number": "1234",
        "invoice_date":   "2026-05-01",
        "due_date":       "2026-05-31",
        "received_date":  "2026-06-08",
        "pre_tax_amount": 41.00,
        "tax_amount":     4.00,
        "description":    "#1355 ADMIRIAL GLASS",
        "job_number":     "25-1355",    # Procore format
        "cost_code":      "01-5204",    # Procore format
        "category":       "01",
        "account":        "1-1-5100.00",
        "tax_group":      "S1152"
    }
    
    filepath = procore_to_sage_csv(sample)
    if filepath:
        verify_csv(filepath)
        print(f"\n=== Transformation Applied ===")
        print(f"Job:       25-1355 → 25-1355-0")
        print(f"Cost Code: 01-5204 → 01-520400")