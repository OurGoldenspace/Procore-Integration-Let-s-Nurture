# Benchmark Fabricators — Procore ↔ Sage 300 Integration

## Overview
Automated invoice sync from Procore to Sage 300 CRE.
Triggered by invoice approval in Procore — eliminates 
manual double entry across 30 active construction projects.

## Architecture
Procore (invoice approved)
  → Webhook trigger
    → Python on Teckels (extract + transform)
      → Sage 300 CRE (create invoice)

## Setup

### 1. Clone the repo
git clone https://github.com/yourusername/benchmark-procore-sage

### 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

### 3. Install dependencies
pip install requests python-dotenv

### 4. Configure credentials
cp .env.example .env
# Fill in your Procore credentials and IDs

### 5. Start Sage 300 mock
# Import mockoon/sage300-mock.json into Mockoon
# Click Play — runs on port 3001

### 6. Run scripts in order
python procore_auth.py      # Test authentication
python procore_test.py      # Verify Procore connection
python sage_test.py         # Verify Sage mock
python integration.py       # Run full P1 sync

## Scripts

| Script | Purpose |
|--------|---------|
| procore_auth.py | OAuth2 token generation |
| procore_test.py | Verify Procore sandbox connection |
| procore_invoices.py | Read invoices from Procore |
| get_company_id.py | Get your Procore company ID |
| get_project_id.py | Get your Procore project ID |
| get_invoice_id.py | Get your Procore invoice ID |
| sage_test.py | Verify Sage 300 mock connection |
| integration.py | Core P1 sync — Procore to Sage |
| debug_auth.py | Debug authentication issues |

## Current Status
- Procore OAuth2 authentication — in progress
- Sage 300 mock (Mockoon) — configured, all endpoints tested
- End-to-end integration — pending Procore auth fix

## Pending
- Procore credentials configuration (developers.procore.com)
- Real Sage 300 credentials from Prathmesh
- Procore Monthly Sandbox enablement (Prathmesh)

## Tech Stack
Python · Procore REST API · OAuth2 · Mockoon · 
Sage 300 CRE · ETL Pipeline · Webhook Architecture