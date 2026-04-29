# Stage311 REMEDA Trust Score URL + External Verification API

Stage311 turns REMEDA Trust Score results into shareable verification URLs and external API responses.

## Core Concept

Before Stage311:

```text
Trust Score can be viewed locally

After Stage311:

Trust Score can be shared by URL
Trust Score can be retrieved by external API
What Stage311 Adds
Public Trust Score URL
/trust/<id> visual verification page
/api/trust/<id> JSON verification result
/api/verify external verification API
accept / pending / reject decision
Trust Score breakdown
Evidence JSON
Fail-closed policy
Why This Matters

Stage310 made trust visible.

Stage311 makes trust shareable.

This is the first SaaS-like step where a verification result becomes a URL that can be sent to a customer, reviewer, partner, or external system.

Trust Model
Trust Score =
average(
  integrity,
  execution,
  identity,
  time,
  sigstore
)
Decision Policy
trust_score >= 0.85  → accept
trust_score >= 0.45  → pending
trust_score < 0.45   → reject

Fail-closed is enabled.

Run Locally
pip install -r requirements.txt
python app.py

Open:

http://127.0.0.1:3110
External API Example
curl -X POST http://127.0.0.1:3110/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "manifest": {
      "claims": {
        "execution": true,
        "identity": true,
        "integrity": true,
        "timestamp": true,
        "workflow": "github-actions",
        "sigstore": true,
        "policy_version": "v1"
      }
    }
  }'

The response includes:

share.trust_url
share.api_url
License

MIT License

Copyright (c) 2025 Motohiro Suzuki
