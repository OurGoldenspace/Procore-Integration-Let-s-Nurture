
from flask import Flask, request, jsonify
import os
import hmac
import hashlib
import logging
from datetime import datetime
from dotenv import load_dotenv
from integration import sync_invoice_procore_to_sage

load_dotenv()

app = Flask(__name__)

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=f"logs/{datetime.now().strftime('%Y-%m-%d')}_webhook.log",
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

COMPANY_ID     = os.getenv("PROCORE_COMPANY_ID")
WEBHOOK_SECRET = os.getenv("PROCORE_WEBHOOK_SECRET", "")

def verify_signature(payload, signature):
    """
    Verifies webhook is genuinely from Procore
    Prevents unauthorized triggers
    """
    if not WEBHOOK_SECRET:
        return True  # skip verification in development
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status":  "ok",
        "service": "Procore webhook handler",
        "version": "1.0"
    }), 200

@app.route("/webhook/procore", methods=["POST"])
def handle_webhook():
    """
    Receives Procore webhook when invoice is approved
    Automatically triggers Procore → Sage 300 sync
    
    In production Procore sends:
    {
        "event_type": "invoices.approve",
        "resource": { "id": 123 },
        "project_id": 456,
        "company_id": 789
    }
    """
    # Verify signature
    payload   = request.get_data()
    signature = request.headers.get("X-Procore-Signature", "")
    
    if not verify_signature(payload, signature):
        logging.warning("Invalid webhook signature rejected")
        return jsonify({"error": "Invalid signature"}), 401
    
    data       = request.json
    event_type = data.get("event_type", "")
    
    logging.info(f"Webhook received: {event_type}")
    print(f"\nWebhook received: {event_type}")
    
    # Only process invoice approval events
    if event_type in ["invoices.approve", "invoice.approved"]:
        resource   = data.get("resource", {})
        invoice_id = resource.get("id")
        project_id = data.get("project_id")
        company_id = data.get("company_id") or COMPANY_ID
        
        if not invoice_id or not project_id:
            logging.error("Missing invoice_id or project_id in webhook")
            return jsonify({"error": "Missing required fields"}), 400
        
        print(f"Invoice approved — ID: {invoice_id}")
        print(f"Project: {project_id}")
        print(f"Syncing to Sage 300...")
        
        success = sync_invoice_procore_to_sage(
            company_id=str(company_id),
            project_id=str(project_id),
            invoice_id=str(invoice_id)
        )
        
        if success:
            logging.info(f"Sync successful — invoice {invoice_id}")
            print(f"✅ Invoice {invoice_id} synced to Sage 300")
            return jsonify({
                "status":     "synced",
                "invoice_id": invoice_id
            }), 200
        else:
            logging.error(f"Sync failed — invoice {invoice_id}")
            return jsonify({
                "status":     "failed",
                "invoice_id": invoice_id
            }), 500
    
    # Ignore other event types
    logging.info(f"Event ignored: {event_type}")
    return jsonify({"status": "ignored", "event": event_type}), 200

@app.route("/webhook/test", methods=["POST"])
def test_webhook():
    """
    Test endpoint — simulate an invoice approval
    Use this to test without waiting for real Procore event
    
    Send: POST /webhook/test
    Body: { "invoice_id": "123", "project_id": "456" }
    """
    data       = request.json or {}
    invoice_id = data.get("invoice_id") or os.getenv("PROCORE_INVOICE_ID")
    project_id = data.get("project_id") or os.getenv("PROCORE_PROJECT_ID")
    
    if not invoice_id or not project_id:
        return jsonify({
            "error": "Provide invoice_id and project_id in request body"
        }), 400
    
    print(f"\nTest webhook triggered")
    print(f"Invoice: {invoice_id} | Project: {project_id}")
    
    success = sync_invoice_procore_to_sage(
        company_id=COMPANY_ID,
        project_id=str(project_id),
        invoice_id=str(invoice_id)
    )
    
    return jsonify({
        "status":     "synced" if success else "failed",
        "invoice_id": invoice_id,
        "project_id": project_id
    }), 200 if success else 500

if __name__ == "__main__":
    print("=== Procore Webhook Handler ===")
    print("Listening on http://localhost:5000")
    print("Endpoints:")
    print("  GET  /health         — health check")
    print("  POST /webhook/procore — real Procore events")
    print("  POST /webhook/test   — test trigger\n")
    app.run(port=5000, debug=True)