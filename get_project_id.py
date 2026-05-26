
import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")

def get_projects():
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Procore-Company-Id": str(COMPANY_ID)
    }
    
    response = requests.get(
        f"{BASE_URL}/rest/v1.0/projects",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    
    if isinstance(data, list):
        print(f"\nProjects found: {len(data)}")
        for p in data:
            print(f"  Name: {p.get('name')}")
            print(f"  ID: {p.get('id')}")
            print(f"  Add to .env: PROCORE_PROJECT_ID={p.get('id')}")
            print()
    else:
        print(f"Response: {data}")

if __name__ == "__main__":
    get_projects()