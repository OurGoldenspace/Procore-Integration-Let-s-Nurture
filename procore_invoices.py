import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL = os.getenv("PROCORE_BASE_URL")

def get_projects(company_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/rest/v1.0/projects",
        headers=headers,
        params={"company_id": company_id}
    )
    if response.status_code == 200:
        projects = response.json()
        print(f"\nProjects found: {len(projects)}")
        for p in projects[:5]:
            print(f"  - {p['name']} | ID: {p['id']}")
        return projects
    else:
        print(f"Error: {response.status_code} — {response.text}")
        return []

def get_invoices(company_id, project_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/rest/v1.0/projects/{project_id}/invoices",
        headers=headers,
        params={"company_id": company_id}
    )
    if response.status_code == 200:
        invoices = response.json()
        print(f"\nInvoices found: {len(invoices)}")
        for inv in invoices[:5]:
            print(f"  - #{inv.get('number')} | "
                  f"Amount: ${inv.get('grand_total')} | "
                  f"Status: {inv.get('status')}")
        return invoices
    else:
        print(f"Error: {response.status_code} — {response.text}")
        return []

def get_headers(token, company_id):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Procore-Company-Id": str(company_id)  # Required on every call
    }

if __name__ == "__main__":
    token = get_token()
    # Replace with real IDs from procore_test.py output
    COMPANY_ID = "your_company_id"
    PROJECT_ID = "your_project_id"
    
    projects = get_projects(COMPANY_ID, token)
    if projects:
        get_invoices(COMPANY_ID, projects[0]['id'], token)