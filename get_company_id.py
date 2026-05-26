
import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL = os.getenv("PROCORE_BASE_URL")

def get_company_id():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/rest/v1.0/companies",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
        for company in data:
            if isinstance(company, dict):
                print(f"\nCompany Name: {company.get('name')}")
                print(f"Company ID: {company.get('id')}")
                print(f"\nAdd this to your .env:")
                print(f"PROCORE_COMPANY_ID={company.get('id')}")

if __name__ == "__main__":
    get_company_id()