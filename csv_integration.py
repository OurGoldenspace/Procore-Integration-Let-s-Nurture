import csv
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='integration.log',
    level=logging.INFO,
    format='%(asctime)s — %(levelname)s — %(message)s'
)

def procore_to_sage_csv(invoice_data, output_folder="sage_import"):
    """
    Converts a Procore invoice dict into a Sage 300 CRE
    compatible CSV import file.
    
    In production:
    - invoice_data comes from Procore webhook payload
    - output_folder is Sage's watched import folder path
    - Sage picks up and imports automatically on schedule
    
    Right now:
    - invoice_data is hardcoded sample data
    - output_folder is local sage_import/ directory
    - Used to verify field mapping and file generation
    """
    try:
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename  = f"sage_import_{invoice_data['invoice_number']}_{timestamp}.csv"
        filepath  = os.path.join(output_folder, filename)
        
        # Transform — map Procore fields to Sage 300 format
        # Fields confirmed by accounting team in meeting
        sage_row = {
            "CUSTOMER":    invoice_data.get("customer_name"),
            "INVNUMBER":   invoice_data.get("invoice_number"),
            "INVDATE":     invoice_data.get("invoice_date", "").replace("-", ""),
            "DUEDATE":     invoice_data.get("due_date", "").replace("-", ""),
            "PRETAXAMT":   invoice_data.get("pre_tax_amount"),
            "TAXAMT":      invoice_data.get("tax_amount"),
            "TOTALAMT":    invoice_data.get("total"),
            "JOBNUMBER":   invoice_data.get("job_number"),
            "DESCRIPTION": "Auto-synced from Procore on approval",
            "SYNCED_AT":   datetime.now().isoformat()
        }
        
        # Validate all required fields are present
        missing = [k for k, v in sage_row.items() 
                   if v is None or v == ""]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        # Write CSV file
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sage_row.keys())
            writer.writeheader()
            writer.writerow(sage_row)
        
        # Log success
        logging.info(f"CSV generated successfully: {filename}")
        
        print(f"✅ CSV generated: {filepath}")
        print(f"\nField mapping applied:")
        for k, v in sage_row.items():
            print(f"  {k:12}: {v}")
        
        return filepath
        
    except Exception as e:
        logging.error(f"CSV generation failed: {str(e)}")
        print(f"❌ Failed: {str(e)}")
        return None


def verify_csv(filepath):
    """
    Reads back the generated CSV and prints contents
    Confirms file was written correctly
    """
    print(f"\n=== Verifying CSV Contents ===")
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"\nRow verified:")
                for k, v in row.items():
                    print(f"  {k:12}: {v}")
        print(f"\n✅ CSV verification passed")
        return True
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("=== Procore → Sage 300 CRE CSV Integration ===\n")
    
    # Sample invoice data
    # In production this comes from Procore webhook
    sample_invoice = {
        "customer_name":  "Benchmark Client Corp",
        "invoice_number": "INV-DEMO-001",
        "invoice_date":   "2026-05-26",
        "due_date":       "2026-06-26",
        "pre_tax_amount": 45000.00,
        "tax_amount":     5850.00,
        "total":          50850.00,
        "job_number":     "JOB-001"
    }
    
    print(f"Processing invoice: {sample_invoice['invoice_number']}")
    print(f"Customer: {sample_invoice['customer_name']}")
    print(f"Total: ${sample_invoice['total']:,.2f}\n")
    
    # Generate CSV
    filepath = procore_to_sage_csv(sample_invoice)
    
    if filepath:
        # Verify it was written correctly
        verify_csv(filepath)
        
        print(f"\n=== Integration Summary ===")
        print(f"✅ ETL Complete:")
        print(f"   Extract:   Sample Procore invoice data")
        print(f"   Transform: Mapped to Sage 300 field format")
        print(f"   Load:      CSV written to {filepath}")
        print(f"\nNext step in production:")
        print(f"   Drop {filepath} into Sage 300 watched folder")
        print(f"   Sage imports automatically on schedule")
    else:
        print("❌ CSV generation failed")