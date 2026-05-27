# google-my-business

Optimize and maintain any Google Business Profile (GBP).

## What this is

A skill that ships three layers of control:

1. **GBP API wrapper** (`lib/gbp_client.py`) — Python module for the official Business Information, Account Management, Performance, Q&A, and v4 legacy APIs. OAuth Desktop flow, refresh token persistence, AuthorizedSession HTTP.
2. **Playwright bridge** (`lib/playwright_bridge.md`) — recipes for driving `business.google.com` directly when the API quota is gated (which is the default for new projects — Google requires manual approval, 7-10 days).
3. **DataForSEO Maps audit** (`lib/audit_dataforseo.md`) — read-only profile snapshot, no auth, instant. Used for first-pass audit before any writes.

## Trigger phrases

"GBP" / "Google Business Profile" / "Google My Business" / "פרופיל גוגל" / "עסק שלי בגוגל" / `business.google.com` / `local.google.com/place` / "Maps profile"

## Bootstrap (one-time per business)

1. Create GCP project, enable 5 GBP APIs, create OAuth Desktop credentials, save to `~/.<business>/gbp/credentials.json`.
2. Submit https://support.google.com/business/contact/api_default → "Application for basic API access". Save Case ID. ETA 7-10 days.
3. Until approved, every API call returns `429 quota=0` — use Playwright bridge for writes.

See `SKILL.md` for the complete workflow.
