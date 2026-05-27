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
    Production-ready CSV generator
    Converts Procore invoice → Sage 300 import file
    """
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        filename  = f"sage_import_{invoice_data['invoice_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath  = os.path.join(output_folder, filename)
        
        sage_row = {
            "CUSTOMER":    invoice_data.get("customer_name"),
            "INVNUMBER":   invoice_data.get("invoice_number"),
            "INVDATE":     invoice_data.get("invoice_date", "").replace("-", ""),
            "DUEDATE":     invoice_data.get("due_date", "").replace("-", ""),
            "PRETAXAMT":   invoice_data.get("pre_tax_amount"),
            "TAXAMT":      invoice_data.get("tax_amount"),
            "TOTALAMT":    invoice_data.get("total"),
            "JOBNUMBER":   invoice_data.get("job_number"),
            "DESCRIPTION": "Auto-synced from Procore"
        }
        
        # Validate required fields
        missing = [k for k, v in sage_row.items() if not v]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sage_row.keys())
            writer.writeheader()
            writer.writerow(sage_row)
        
        logging.info(f"✅ CSV generated: {filename}")
        print(f"✅ CSV generated: {filepath}")
        return filepath
        
    except Exception as e:
        logging.error(f"❌ CSV generation failed: {str(e)}")
        print(f"❌ Failed: {str(e)}")
        return None