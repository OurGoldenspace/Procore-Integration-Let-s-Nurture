# save as check_project_tools.py
import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL   = os.getenv("PROCORE_BASE_URL")
COMPANY_ID = os.getenv("PROCORE_COMPANY_ID")
PROJECT_ID = os.getenv("PROCORE_PROJECT_ID")

def check_tools():
    token = get_token()
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": COMPANY_ID
    }
    
    # Get project details including enabled tools
    r = requests.get(
        f"{BASE_URL}/rest/v1.0/projects/{PROJECT_ID}",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    
    if r.status_code == 200:
        project = r.json()
        print(f"Project: {project.get('name')}")
        print(f"All fields:")
        for k, v in project.items():
            print(f"  {k}: {v}")
    else:
        print(f"❌ {r.text[:200]}")

if __name__ == "__main__":
    check_tools()