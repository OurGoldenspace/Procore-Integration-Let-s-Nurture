import requests
import os
from dotenv import load_dotenv

load_dotenv()

SAGE_URL = os.getenv("SAGE_BASE_URL")

def test_sage_connection():
    # Health check
    health = requests.get(f"{SAGE_URL}/health")
    print(f"Sage 300 mock status: {health.json()['status']}")
    
    # Get invoices
    invoices = requests.get(f"{SAGE_URL}/ar-invoices")
    print(f"AR Invoices: {len(invoices.json()['invoices'])} found")
    
    # Create test invoice
    new_invoice = requests.post(
        f"{SAGE_URL}/ar-invoices",
        json={
            "customer_name": "Test Client",
            "invoice_number": "TEST-001",
            "pre_tax_amount": 10000.00,
            "tax_amount": 1300.00,
            "total": 11300.00,
            "job_number": "JOB-TEST"
        }
    )
    print(f"Invoice created: {new_invoice.json()['status']}")

if __name__ == "__main__":
    test_sage_connection()