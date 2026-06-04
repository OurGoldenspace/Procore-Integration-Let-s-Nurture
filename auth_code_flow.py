# save as auth_code_flow.py
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

class Handler(BaseHTTPRequestHandler):
    code = None
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        Handler.code = params.get("code", [None])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Login successful - close this tab")
    def log_message(self, *args):
        pass

def get_token_via_browser():
    # Try both production and sandbox auth URLs
    for base in ["https://login.procore.com", "https://app.procore.com"]:
        auth_url = (
            f"{base}/oauth/authorize"
            f"?response_type=code"
            f"&client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
        )
        
        print(f"Opening browser: {base}")
        print("Log in with Kashyap's Procore credentials...")
        webbrowser.open(auth_url)
        
        server = HTTPServer(("localhost", 3000), Handler)
        server.handle_request()
        
        code = Handler.code
        if not code:
            print("No code received — trying next URL")
            continue
        
        print(f"Code received — exchanging for token...")
        
        r = requests.post(
            f"{base}/oauth/token",
            data={
                "grant_type":    "authorization_code",
                "client_id":     CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri":  REDIRECT_URI,
                "code":          code
            }
        )
        
        if r.status_code == 200:
            token = r.json().get("access_token")
            print(f"✅ Token obtained!")
            print(f"Token: {token[:20]}...")
            
            with open(".access_token", "w") as f:
                f.write(token)
            print("Saved to .access_token")
            return token
        else:
            print(f"❌ Token exchange failed: {r.json()}")
    
    return None

if __name__ == "__main__":
    get_token_via_browser()