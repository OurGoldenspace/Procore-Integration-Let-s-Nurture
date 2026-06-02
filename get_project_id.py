import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")

def get_projects():
    token = get_token()
    if not token:
        return
    
    if not COMPANY_ID:
        print("❌ Set PROCORE_COMPANY_ID in .env first")
        return
    
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": str(COMPANY_ID)
    }
    
    response = requests.get(
        f"{BASE_URL}/rest/v1.0/projects",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        projects = response.json()
        if not projects:
            print("⚠️  No projects found — Prathmesh needs to create test project")
            return
        print(f"\n✅ Projects found: {len(projects)}")
        for p in projects:
            print(f"\n  Name:   {p.get('name')}")
            print(f"  ID:     {p.get('id')}")
            print(f"  Status: {p.get('status')}")
            print(f"  → Add to .env: PROCORE_PROJECT_ID={p.get('id')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text[:200]}")

if __name__ == "__main__":
    get_projects()