# save as find_sandbox_company.py
import requests
from procore_auth import get_token

def find_company():
    token = get_token()
    if not token:
        return
    
    # Try without company ID header first
    headers = {"Authorization": f"Bearer {token}"}
    
    r = requests.get(
        "https://sandbox.procore.com/rest/v1.0/companies",
        headers=headers
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:300]}")

if __name__ == "__main__":
    find_company()