# GBP API Access Form — exact answers

**URL**: https://support.google.com/business/contact/api_default
**Choose**: "Application for basic API access"

Before clicking the button, **sign in as the owner of the GBP** (top-right Google account selector). Otherwise the form blocks.

## Form fields (typical 2026 layout)

| Field | What to write |
|---|---|
| **GCP Project ID** | the actual project ID, eg `claude-495904` |
| **GCP Project Number** | numeric, eg `553071705706` |
| **Business name** | legal name in Hebrew/English |
| **Email** | the same Gmail that owns the GBP |
| **Website** | https://... |
| **Phone** | full international, eg `+972524453107` |
| **Region(s)** | Israel |
| **Use case description** | see template below |
| **Expected QPS** | "Low — single location, <100 calls/day" for one clinic |
| **Acting on behalf of others?** | No (unless it's a true agency) |

## Use case template (proven to pass review)

> I am a single business owner managing my own Google Business Profile for my [INDUSTRY] in [CITY]. I need API access to automate:
> (1) responding to patient/customer reviews promptly,
> (2) uploading new photos in bulk,
> (3) keeping business hours and attributes in sync with my website ([DOMAIN]),
> (4) publishing Google Posts about new services.
> This is for my own single location only, not a third-party platform.

## Why this wording works

- "Single business" + "my own" + "not a third-party platform" — defuses the platform/aggregator suspicion that triggers most rejections
- Concrete list of 4 use cases shows you've thought about it
- No vague phrases like "improve marketing" or "automate everything"

## Avoid

- "We manage clients' profiles" → flagged as agency, requires different scope
- "Bulk export reviews" → flagged as scraping
- "AI" / "GPT" / "automation platform" in the description → flagged as bot

## After submission

- Case ID emailed within minutes (eg `4-2468000040879`)
- ETA: **7-10 working days** per the form's own confirmation text
- Sometimes Google emails back asking for clarification — answer concisely, single paragraph
- Once approved, ALL 5 GBP APIs unlock at once (not just v4 legacy)

## Verifying approval landed

Run `python3 gbp_client.py`. If it returns accounts/locations JSON instead of `429 RESOURCE_EXHAUSTED`, you're in.
