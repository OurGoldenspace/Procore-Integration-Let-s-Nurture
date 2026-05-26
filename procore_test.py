import requests
import os
from dotenv import load_dotenv
from procore_auth import get_token

load_dotenv()

BASE_URL = os.getenv("PROCORE_BASE_URL")

def test_connection():
    token = get_token()
    if not token:
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test 1 — confirm who you are
    me = requests.get(
        f"{BASE_URL}/rest/v1.0/me", 
        headers=headers
    )
    me_data = me.json()
    print(f"\nRaw /me response: {me_data}")
    print(f"Connected as: {me_data.get('login') or me_data.get('email') or 'check raw response'}")
    
    # Test 2 — list companies
    companies = requests.get(
        f"{BASE_URL}/rest/v1.0/companies",
        headers=headers
    )
    
    companies_data = companies.json()
    print(f"\nRaw companies response: {companies_data}")
    print(f"Type: {type(companies_data)}")
    
    # Handle both list and dict response
    if isinstance(companies_data, list):
        print(f"Companies found: {len(companies_data)}")
        for c in companies_data:
            if isinstance(c, dict):
                print(f"  - {c.get('name')} | ID: {c.get('id')}")
            else:
                print(f"  - {c}")
    elif isinstance(companies_data, dict):
        print(f"Companies response is a dict: {companies_data}")
    
    return companies_data

if __name__ == "__main__":
    result = test_connection()