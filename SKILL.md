---
name: google-my-business
description: Manage and SEO-optimize any Google Business Profile (GBP / Google My Business) via two complementary surfaces — (a) the official GBP API (Business Information, Account Management, Performance, Q&A, v4 legacy for reviews/photos) once approved, and (b) Playwright bridge to business.google.com for immediate edits while the access form is pending. Covers OAuth bootstrap, the quota=0 gotcha, read-only audit via DataForSEO Maps, write operations for hours/address/website/categories/services/posts/reviews, multi-profile/duplicate handling. Validated 2026-05-27 on dr-meir.com clinic. Use when user says "GBP", "Google Business Profile", "Google My Business", "פרופיל גוגל", "עסק שלי בגוגל", "מאיפס Maps", "עדכן פרופיל GBP", "תקן שעות בגוגל", "ביקורות גוגל מפה", "מרפאה ב-Google Maps", or anything involving business.google.com or local.google.com/place.
---

# google-my-business — Google Business Profile Manager

End-to-end skill for managing a Google Business Profile. Built and validated 2026-05-27 on the Dr. Meir Babaev clinic in Holon (CID `9173893006157140215`). The workflow is robust to Google's two-tier gatekeeping: the official API is gated behind a manual access form (7-10 days), so the skill ships with a Playwright bridge that drives `business.google.com` directly for everything the API would do, plus a thin DataForSEO Maps wrapper for fast read-only audits that need no auth.

## When to invoke

- "Optimize my Google Business Profile" / "תעדכן את הפרופיל ב-Google"
- "Add services to GBP / לפי הקטגוריות שלי בגוגל"
- "Fix opening hours on Google Maps"
- "Why isn't my clinic showing for [keyword]?" (audit mode)
- "Add categories to my GBP"
- "Reply to reviews on Google Maps" (after API approval)
- "Upload photos to Google Business Profile"
- Anything mentioning `business.google.com`, `local.google.com/place`, GBP API, My Business API, Maps profile, or local SEO ranking on Maps

## When NOT to invoke

- General SEO of a website (use `dr-meir-content-update` or `claude-seo`)
- Listings on other platforms (Yelp, Tripadvisor — handle case-by-case)
- Local-pack ranking analysis alone (use DataForSEO Maps directly without this skill)
- Building a new clinic site (use `dr-meir_new_page`)

---

## Platform profile (memorize)

GBP has **three control surfaces** with different auth, latency, and capability profiles. The skill chooses the right one per task.

### 1. GBP API (write + structured read)
- **Hosts**: 5 separate APIs, all requiring `https://www.googleapis.com/auth/business.manage` scope:
  - `mybusinessbusinessinformation.googleapis.com/v1` — name, address, hours, categories, attributes, services
  - `mybusinessaccountmanagement.googleapis.com/v1` — list accounts (must call first)
  - `mybusinessqanda.googleapis.com/v1` — Q&A
  - `businessprofileperformance.googleapis.com/v1` — metrics (views, calls)
  - `mybusiness.googleapis.com/v4` — **LEGACY**, but still the only place for reviews replies, photos, posts
- **Auth**: OAuth Desktop client (`installed` type), refresh token cached. Service accounts DO NOT work for personal GBP.
- **GOTCHA**: Even after enabling an API and authenticating, **quota stays at 0 requests/min** until Google manually approves the "Application for basic API access" form. A single approval unlocks all 5 APIs. Without it, every call returns `429 RESOURCE_EXHAUSTED` with `quota_limit_value: "0"`.
- **Approval URL**: https://support.google.com/business/contact/api_default (choose "Application for basic API access")
- **ETA**: 7-10 working days

### 2. Playwright bridge (write fallback when API is gated)
- **URL**: `https://business.google.com/locations` (lists all profiles)
- **Profile editor**: Google has **moved most editing into the SERP**. Clicking "See your profile" or "Edit profile" opens an iframe-based edit dialog inside Google Search results (URL contains `#mpd=editprofile/...`). All edits happen inside that iframe.
- **Tabs in the editor**: About, Contact, Location, Hours, More.
- **Dedicated dialogs** (not inside Edit profile): Services, Products, Photos, Posts, Reviews.
- **Auth**: User logs in manually with the Google account that owns the GBP. Chrome saves the session in the MCP profile so subsequent runs skip login.
- **Concurrency**: Only one Playwright MCP session can hold the lock at `~/Library/Caches/ms-playwright/mcp-chrome-*/SingletonLock`. If another Claude session holds it, kill the Chrome process or close the other session.

### 3. DataForSEO Maps (read-only, no auth, instant)
- **Endpoint**: `mcp__dataforseo__business_data_business_listings_search`
- **Use for**: profile snapshot (rating, hours, photos count, attributes, work_time), competitor comparison, NAP verification, finding the CID/Place ID
- **Limit**: returns ~13 photos at most, no review text, no write capability
- **Cost**: ~$0.01 per call

---

## File layout

```
~/.claude/skills/google-my-business/
├── SKILL.md                  — this file
├── README.md                 — short user-facing intro
├── lib/
│   ├── gbp_client.py         — Python wrapper for the official APIs (OAuth, list/get/update)
│   ├── playwright_bridge.md  — recipes for every UI flow in business.google.com
│   ├── audit_dataforseo.md   — recipes for read-only audit via DataForSEO Maps
│   └── access_form.md        — exactly what to put in the Google approval form
└── examples/
    ├── dr-meir-2026-05-27.md — full case study used to validate the skill
    └── description-template.md — Hebrew + English description templates with keyword slots
```

---

## OAuth bootstrap (one-time per GCP project)

This is the slow part. Do it ONCE per business, then the wrapper is permanent.

1. **Create GCP project** at https://console.cloud.google.com — note the Project ID and Project Number.

2. **Enable these APIs** in the project (Library → search → Enable):
   - My Business Business Information API
   - My Business Account Management API
   - Business Profile Performance API
   - My Business Q&A API
   - Google My Business API (legacy, for reviews+photos)

3. **Create OAuth credentials** (APIs & Services → Credentials → Create Credentials → OAuth client ID):
   - Type: **Desktop app** (NOT Web app — Desktop is simpler, no redirect URI hassle)
   - On the "Which API are you using?" page: pick **My Business Business Information API** + **User data** (NOT Application data, since service accounts can't manage personal GBP)
   - Download the JSON, move to `~/.<business>/gbp/credentials.json`, chmod 600

4. **OAuth consent screen**: Add the owner's email as a Test User (otherwise the first login returns `access_denied`).

5. **Apply for API quota**:
   - Visit https://support.google.com/business/contact/api_default
   - Choose "Application for basic API access" → fill the form (see `lib/access_form.md` for exact text)
   - Save the Case ID Google emails back. ETA 7-10 working days.

6. **First-time auth**: run the Python wrapper once, browser pops for consent, refresh token saved to `~/.<business>/gbp/token.json` (chmod 600).

7. **Until approval lands**: every API call returns `429 RESOURCE_EXHAUSTED` with `quota_limit_value: "0"`. Use the **Playwright bridge** for any write during this window.

---

## Phase A: Audit (always do this first, no auth needed)

Pull the current profile snapshot via DataForSEO Maps. This is read-only, fast, and works without any setup. Use it to:
- Get the Place ID, CID, Maps URL
- See current rating, review count, **review distribution** (1-star bombing detection)
- Verify NAP consistency vs. site Schema
- Count photos (low photo count → SEO problem)
- Inspect attributes Google has auto-flagged

```js
mcp__dataforseo__business_data_business_listings_search({
  title: "<Hebrew or English business name>",
  location_coordinate: "<lat,lng,radius_km>",   // example: "32.0117,34.7740,30"
  limit: 10,
  is_claimed: false                              // false returns claimed AND unclaimed
})
```

Compare the result against the source of truth on the website (usually `<head>` Schema JSON-LD `MedicalClinic` → `address`, `openingHours`, `telephone`). Flag every drift.

**Tip**: search by location coordinates rather than just by title — Hebrew name spelling can vary (eg "בבייב" vs "באבאיב") and you'll miss the listing. Coordinates + city name catches it every time.

---

## Phase B: Setup the Python wrapper

Save `lib/gbp_client.py` to `~/.<business>/gbp/gbp_client.py`. It handles:
- OAuth refresh + token persistence
- `list_accounts()` → GET `mybusinessaccountmanagement.googleapis.com/v1/accounts`
- `list_locations(account_name, read_mask=...)` → GET `mybusinessbusinessinformation.googleapis.com/v1/{account}/locations`
- `get_location(name, read_mask)` and `update_location(name, body, update_mask)` → PATCH
- `list_reviews(location_name)` and `reply_review(review_name, comment)` → v4 legacy
- All HTTP via `google.auth.transport.requests.AuthorizedSession`

Install deps once:
```
pip3 install --user google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

After OAuth approval clears, this is your daily driver. Until then, the wrapper still authenticates fine but every call 429s — use that as the heartbeat to detect approval landing.

---

## Phase C: Playwright bridge — every UI flow

This is the active layer until API is unlocked. See `lib/playwright_bridge.md` for full ref selectors per dialog. Below are the high-level patterns.

### Open the editor
```
mcp__playwright__browser_navigate({ url: "https://business.google.com/locations" })
```
If the page returns "Browser is already in use", another MCP session holds the lock:
```bash
pkill -f "ms-playwright/mcp-chrome"   # or ask user to close the other Claude window
```

The locations page lists every profile the user manages. **Watch for "Duplicate" rows** — they share the same Place ID with the main profile and are auto-merged at the Maps level (clicking them redirects to the main profile). No UI removes them; user must contact Google support.

Click "See your profile" → opens the profile in Google Search SERP context. Click "Edit your business information" or "Edit profile" → opens the iframe edit dialog.

### Edit hours
Tab "Hours" → click "Edit Hours" (`button[name='Edit Hours']`). The dialog shows per-day rows with `Opens at` and `Closes at` comboboxes (both 30-min granularity, eg `09:00`, `09:30`, ..., `23:30`). Click combobox → select from listbox. Saturday is a special radio (Open vs Closed checkbox). Click Save.

### Edit address (including postcode)
Tab "Location" → "Edit Business location". Form has 4 fields: Country/Region (disabled), Street address, Town/City, Postcode. The Postcode field accepts only digits. Use `fill()` to replace value, not `type()`. Click Save.

### Edit website (HTTP → HTTPS)
Tab "Contact" → "Edit Website". Single textbox with URL. Use `fill('https://example.com/')`. Save.

### Edit Description (the big SEO lever)
Tab "About" → "Edit Description". 750-char limit. Lead with **clinic name + address city**, then list services using Hebrew keywords customers actually search (eg "שאיבת שומן בלייזר", not just "liposuction"). End with phone CTA. **Do not keyword-stuff** — Google rejects on review. Save → "pending review, up to one day".

### Add Categories (massive SEO impact)
Tab "About" → "Edit Business category". 1 primary + up to 9 additional. Primary should match the business owner's specialty (eg `Dermatologist`). Additional should reflect SERVICES offered (eg `Medical spa`, `Laser hair removal service`, `Skin care clinic`). Each combobox is a typeahead → wait 2s → click the suggestion from listbox. Save.

**Picking categories**: only add a category if it's a REAL service offered. Adding "Cosmetic surgeon" when you're a dermatologist is a guideline violation that risks suspension. When in doubt, skip it.

### Services catalog (highest SEO weight)
Main profile actions → "Edit services" (NOT inside the Edit Profile dialog — it's a separate button). The dialog shows one section per category. For Primary categories like Dermatologist, only `Add custom service` is offered (free text, 120 chars, no description/price field). For other categories like Medical spa, Google offers **preset services** (`Liposuction`, `Botox treatments`, `Body contouring`, `Lip fillers`, etc.) — **always prefer presets over custom** because Google's matching algorithm understands them natively.

Each preset for Medical spa appears as a clickable option in a listbox. Click to toggle. Common high-value presets for an aesthetic clinic:
- **Liposuction** (the big one for SEO)
- Body contouring
- Botox treatments
- Lip fillers
- JUVÉDERM treatments
- Laser hair removal
- IPL photo facial
- Microneedling
- PRP facial
- Chemical peels
- Spider vein treatments

Save → "pending review, up to one day". Same service can be added under multiple categories — Google uses the category match to pick which list to surface for a query. Worth duplicating high-value services across 2-3 categories.

### Service descriptions (per-item, hidden behind a click)
Click any service name in the Services dialog → opens "Edit service details" dialog with three fields: Service (name, 120 chars), Price (with ILS picker, default "No price"), and **Service description (300 chars)**. The description field is the hidden gem — most profiles leave it empty. Fill with technology/method explanation, body areas treated, results timeline, and phone CTA. Apply the **healthcare safety rules below** before saving.

### Posts — high risk for healthcare businesses ⚠️
Main profile actions → `button "Posts"` → `button "Add post"` → dialog `Add post` with:
- `listbox "Post type"`: Update / Offer / Event
- `textbox "Description"`: 1500 chars
- Image drag-drop or `Select images and videos`
- `Add link fields` button → expands to `Add a button (optional)` with menuitems: None, Book, Order online, Buy, Learn more, Sign up, Call now → adds `textbox "Link for your button*"`
- `Post` button (bottom)

After Post click, the new post shows `Pending` while Google reviews it.

**🚨 HEALTHCARE GOTCHA (Routing ID DPNB)**: Google enforces a much stricter content policy on "Your Money or Your Life" categories — Dermatologist, Medical spa, Skin care clinic, any medical service. A single rejected post can **disable posting for the entire profile** (not just block one post). Recovery requires submitting a support case via `support.google.com/business/gethelp` (NOT via reply email — the rejection notification is from `businessprofile-noreply@google.com`). Path: select profile → "Posts removed" category → Next → skip the case-in-progress prompt → Email channel → fill detailed appeal (acknowledge violation, commit to compliant content, request reinstatement). Returns a `2-XXXXXXXXXXXXX` case ID. Response in 1-3 business days via email.

Triggers that get medical posts rejected:
- **Outcome promises with timeframes** ("results within 2-6 months", "lasts X years")
- **Treatment area specificity** ("removes fat from belly, thighs, arms")
- **Comparative claims** ("better than", "no need for surgery", "instead of")
- **Aesthetic before/after implications** ("significant tightening", "smooths wrinkles")
- **Salesy emojis** + "new!" + sales-style framing
- Mentions of trademarked treatment brands without disclaimer

Safe medical post pattern (rarely rejected):
- Plain factual description ("X is a treatment for Y condition")
- Link to dedicated page on your website (where you have medical authority context)
- Optional Book/Call CTA
- No outcome claims, no timeframes, no comparisons
- One short paragraph, no bullets, no emoji

Example safe post: "מידע על שירות שאיבת שומן Quantum RF זמין באתר הקליניקה. תיאום ייעוץ אישי: 052-445-3107."

If posting is disabled, **service descriptions and the main profile Description are still editable** and carry more SEO weight anyway. Posts are mostly a freshness signal.

### Reviews (requires v4 API → blocked until form approval)
Once quota lands: `gbp_client.list_reviews(location_name)` returns 5-100 most recent reviews. `reply_review(review_name, comment)` posts a reply. **Until then**, replies must be typed manually in business.google.com → Reviews tab.

When auditing a profile with a bimodal rating distribution (eg 50× 5-star + 17× 1-star), assume review bombing or competitor attack. Pull review timestamps and look for clusters within 1-2 weeks — that's the smoking gun.

### Photos
v4 API only. Same gate as reviews. Until unlocked, drag-and-drop in the Photos dialog of business.google.com.

### Posts
v4 API only. Posts expire after 7 days (offers can last longer). Until unlocked, write manually in the Posts dialog.

### Q&A
`mybusinessqanda.googleapis.com/v1` — also gated by the same form approval. The owner can answer questions directly in the UI without API.

---

## Phase D: Maintenance (recurring)

- **Weekly**: check Reviews tab for new reviews. Reply to every one (5-star and 1-star both — patient signal).
- **Monthly**: review the "Google updates" feed in the editor — Google auto-suggests attribute changes (eg "Has wheelchair-accessible entrance") based on Street View/reviews. Approve or reject each one.
- **Quarterly**: re-audit via DataForSEO Maps and compare against the site's Schema JSON-LD. Phone numbers and hours drift surprisingly fast.

---

## Common pitfalls

1. **Service accounts don't work for personal GBP.** Only OAuth Desktop with user consent. If a service account looks tempting, it's because you're confusing this with Google Workspace setups, which need domain-wide delegation that personal GBP doesn't support.

2. **Quota=0 means "approval pending", not "API broken".** Don't waste time debugging the OAuth flow when you see `429 RESOURCE_EXHAUSTED` — the auth worked fine, you just need the form approved.

3. **Don't keyword-stuff the business name.** "Dr X — Best Liposuction Clinic Tel Aviv 24/7" gets flagged. Keep the legal name. Use the Description and Services for keywords.

4. **Friday hours in Israel** default to the same as weekdays in GBP. Always verify Friday isn't 09-17 when it should be 09-14 — this is a near-universal drift on Israeli clinics.

5. **The "Duplicate" row in the locations dashboard** isn't actionable from the UI when the duplicate shares the same Place ID. Contact Google support to remove it. Low priority — it's already dormant in search.

6. **Custom Hebrew service names** work but lose to preset Google service names in the SEO matching algorithm. When a preset exists for the same concept, prefer it. Eg use the preset "Liposuction" under Medical spa even if you also have a Hebrew custom "שאיבת שומן בלייזר" under Dermatologist — both can coexist.

7. **`type()` vs `fill()` in Playwright** — for the Postcode and Website fields, `fill()` replaces. `type()` may append. Always `fill()` for replace semantics, `type()` only when you need to trigger char-by-char handlers (eg autocomplete suggestions).

8. **Closing the iframe Save button** — Google's `Save` button is inside `iframe[2]` (the edit dialog). Always reference it via the iframe locator, not the top page.

---

## DR-MEIR CASE STUDY (validated 2026-05-27)

The canonical run. Used to build and verify this skill. Located at `examples/dr-meir-2026-05-27.md`. Key facts to memorize for future runs on this clinic:

- **GCP project**: `claude-495904` (number `553071705706`)
- **OAuth client**: `~/.dr-meir/gbp/credentials.json`, token at `~/.dr-meir/gbp/token.json`, scope `business.manage`
- **Support case**: `4-2468000040879` opened 2026-05-27, expected approval ~2026-06-10
- **Place ID**: `ChIJR5xFhpy3AhUR99BvbxU3UH8`, CID `9173893006157140215`
- **Account ID for the active profile**: `accounts/n/7827003086139493305`
- **Duplicate profile**: `accounts/n/11116513478108168589`, same fid, already auto-merged
- **Categories** (post-update): Dermatologist (primary) + Medical spa + Skin care clinic + Laser hair removal service
- **Services added**: 14 custom under Dermatologist + 11 preset under Medical spa (including the SEO-critical "Liposuction") + 1 auto under Laser hair removal service

When the user asks about this clinic specifically, skip the audit (we've done it) and jump straight to whatever they want. When the user asks about a different business, run Phase A (audit) first.
