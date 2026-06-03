# save as user_auth.py
import requests
import webbrowser
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("PROCORE_CLIENT_ID")
CLIENT_SECRET = os.getenv("PROCORE_CLIENT_SECRET")
REDIRECT_URI  = "http://localhost:3000/callback"
BASE_URL      = "https://login.procore.com"
API_URL       = "https://us02.procore.com"

class CallbackHandler(BaseHTTPRequestHandler):
    code = None
    
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        CallbackHandler.code = params.get("code", [None])[0]
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(
            b"Login successful! You can close this tab and return to the terminal."
        )
    
    def log_message(self, format, *args):
        pass

def get_user_token():
    """
    Authorization Code flow
    Opens browser for real user login
    Works with your new AGCM account access
    """
    
    # Step 1 — build auth URL
    auth_url = (
        f"https://login.procore.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    
    print("Opening browser for Procore login...")
    print(f"URL: {auth_url}\n")
    print("Log in with your AGCM Procore account credentials")
    print("Waiting for login...\n")
    
    webbrowser.open(auth_url)
    
    # Step 2 — wait for callback
    server = HTTPServer(("localhost", 3000), CallbackHandler)
    server.handle_request()
    
    code = CallbackHandler.code
    if not code:
        print("❌ No authorization code received")
        return None
    
    print(f"✅ Authorization code received")
    
    # Step 3 — exchange code for token
    r = requests.post(
        "https://login.procore.com/oauth/token",
        data={
            "grant_type":    "authorization_code",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri":  REDIRECT_URI,
            "code":          code
        }
    )
    
    if r.status_code == 200:
        data  = r.json()
        token = data.get("access_token")
        print(f"✅ Token obtained successfully")
        print(f"Token: {token[:20]}...")
        print(f"Expires in: {data.get('expires_in')} seconds")
        
        # Save to file for reuse
        with open(".access_token", "w") as f:
            f.write(token)
        print("Token saved to .access_token")
        
        return token
    else:
        print(f"❌ Token exchange failed: {r.json()}")
        return None

def test_with_token(token):
    """Test access to the real AGCM project"""
    
    COMPANY_ID = os.getenv("PROCORE_COMPANY_ID", "562949953425362")
    PROJECT_ID = os.getenv("PROCORE_PROJECT_ID", "562949955372419")
    
    headers = {
        "Authorization":      f"Bearer {token}",
        "Content-Type":       "application/json",
        "Procore-Company-Id": COMPANY_ID
    }
    
    print("\n=== Testing Real AGCM Project ===")
    
    # Test project
    print(f"\n[TEST 1] Project access...")
    r = requests.get(
        f"{API_URL}/rest/v1.0/projects/{PROJECT_ID}",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        p = r.json()
        print(f"✅ Project: {p.get('name')}")
        print(f"   ID: {p.get('id')}")
    else:
        print(f"❌ {r.text[:200]}")
    
    # Test invoices
    print(f"\n[TEST 2] Invoice access...")
    r = requests.get(
        f"{API_URL}/rest/v1.0/projects/{PROJECT_ID}/invoices",
        headers=headers,
        params={"company_id": COMPANY_ID}
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        invoices = r.json()
        if isinstance(invoices, list):
            print(f"✅ Invoices: {len(invoices)}")
            for inv in invoices:
                print(f"   #{inv.get('number')} | "
                      f"{inv.get('status')} | "
                      f"${inv.get('grand_total')}")
            if not invoices:
                print("   No invoices yet — ask Prathmesh to add one")
        else:
            print(f"Response: {invoices}")
    else:
        print(f"❌ {r.text[:200]}")

if __name__ == "__main__":
    token = get_user_token()
    if token:
        test_with_token(token)