# Sage 300 CRE Mock — Mockoon Setup

## What This Is
A local mock server simulating the Sage 300 CRE API for 
development and testing. Allows full integration testing 
without real Sage 300 credentials.

## Setup
1. Download Mockoon from mockoon.com (free)
2. Open Mockoon
3. Click File → Import → select mockoon/sage300-mock.json
4. Click Play — server starts on port 3001

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Check mock is running |
| GET | /ar-invoices | List all AR invoices |
| POST | /ar-invoices | Create new AR invoice |
| PUT | /ar-invoices/:id | Update existing invoice |
| DELETE | /ar-invoices/:id | Delete invoice |
| GET | /ap-invoices | List subcontractor invoices |

## Test It
curl http://localhost:3001/health

## Field Mapping — Procore to Sage 300

| Procore Field | Sage 300 Field | Notes |
|---------------|----------------|-------|
| contractor.name | customer_name | Client name |
| number | invoice_number | Invoice reference |
| subtotal | pre_tax_amount | Before tax |
| tax_amount | tax_amount | HST 13% |
| grand_total | total | Final amount |
| project_id | job_number | Confirm format with Prathmesh |

## Swap for Real Sage 300
When Prathmesh provides server access, update .env:
SAGE_BASE_URL=http://real-sage-server-url
Nothing else changes.