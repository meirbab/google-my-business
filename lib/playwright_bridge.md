# Playwright bridge for business.google.com

Active-control layer while the GBP API quota is gated (the default for new projects). Drives the same UI a human would use. Selectors verified 2026-05-27 on the post-2024 SERP-embedded editor.

## Pre-flight

The MCP Playwright profile lives at `~/Library/Caches/ms-playwright/mcp-chrome-*/`. Only one MCP-driven session can hold the lock at a time.

If `mcp__playwright__browser_navigate` returns `Browser is already in use`:
```bash
pkill -f "ms-playwright/mcp-chrome"
```
Or close the other Claude window holding it. After kill, the lock file (`SingletonLock` symlink) clears automatically.

## Login

The first call to `business.google.com/locations` redirects to `accounts.google.com` if not logged in. Have the user log in manually (the browser is visible). Chrome saves the session for subsequent runs.

## Navigation map

```
business.google.com/locations
  └─ Row per profile
      ├─ "See your profile"  →  Google SERP with editor sidebar (URL contains #mpd=...)
      └─ "Manage profile"     →  same as above
```

When a profile is marked **Duplicate** (column 2 = "Duplicate"), clicking it redirects to the active profile (same fid). Cannot remove via UI — needs Google support form.

## The SERP-embedded editor

After clicking "See your profile", URL becomes something like:
```
google.com/search?q=...&stick=...#mpd=
```

The editor itself lives inside `iframe[ref=e2133]` (third iframe in the page). **All Playwright selectors must use the iframe locator**:

```js
// Wrong — selector won't be found:
mcp__playwright__browser_click({ target: "f5e236" })

// Right — Playwright tools auto-handle the iframe when the snapshot returned the ref from inside it:
// (the f5* refs are iframe-internal, the e* refs are top-page)
```

The Playwright MCP `browser_snapshot` returns both top-page and iframe refs. The `f5e*` / `f9e*` prefix indicates iframe-internal refs. Just pass them as-is.

## Editor dialog: structure

`button "Edit your business information"` (or `"Edit profile"`) → opens `dialog "Business information"` with:

- `tab "About"` (selected by default)
- `tab "Contact"`
- `tab "Location"`
- `tab "Hours"`
- `tab "More"`

Each tab scrolls within the same dialog. Don't close-reopen between tabs — just click the next tab.

## Recipe: fix Friday hours

```
tab "Hours" → button "Edit Hours" →
  combobox "Closes at: Time range 1 for Friday" → listbox → option "14:00" →
  button "Save"
```

Combobox values are pre-formatted strings: `"09:00"`, `"09:30"`, ..., `"23:30"`. Options are visible only after clicking the combobox.

Each day has:
- `checkbox "Closed"` (toggles whole-day closure)
- `combobox "Opens at: Time range 1 for {Day}"`
- `combobox "Closes at: Time range 1 for {Day}"`
- `button "Add hours for {Day}"` for split shifts (eg lunch break)

## Recipe: fix postcode

```
tab "Location" → button "Edit Business location" →
  textbox "Postcode" → click + Meta+a + type new value → button "Save"
```

Use `fill()` semantics (replace) not `type()` (append). Pure digits only.

## Recipe: HTTP → HTTPS website

```
tab "Contact" → button "Edit Website" →
  textbox "Website" → fill("https://example.com/") → button "Save"
```

## Recipe: Description (the big SEO lever)

```
tab "About" → button "Edit Description" →
  textbox "X of 750 characters entered" → fill("Hebrew text...") → button "Save"
```

Hebrew works fine, including RTL. The label `"X of 750 characters entered"` updates live; current value shows in the textbox.

### Description writing guide

Maximize the 750-char budget. Structure:
1. Open with clinic/business name + city (anchors local entity)
2. Owner credibility line (years of experience, specialization)
3. List ALL services using the Hebrew terms customers search (eg `שאיבת שומן בלייזר`, not `liposuction`)
4. Mention top-of-mind technologies/brand names (eg `Quantum RF`, `Botox`, `JUVÉDERM`) — these are entity-level signals
5. Close with phone CTA

Keep it natural prose, not a keyword soup. Google rejects on review.

## Recipe: Categories

```
tab "About" → button "Edit Business category" →
  combobox "Primary category"     // 1 required
  combobox "Additional category 1" // optional, up to 9
  ... button "Add another category" ...
  button "Save"
```

Each additional combobox is a typeahead. Type 3-4 chars → wait 2s → listbox appears with `option "..."` items → click the right one.

**Don't add a category for a service you don't actually offer** — Google guideline violation, can trigger suspension. When in doubt, skip it.

Common safe additions for aesthetic medical clinics:
- `Skin care clinic`
- `Medical spa`
- `Laser hair removal service`

Avoid: `Cosmetic surgeon` (only if board-certified plastic surgeon), `Beauty salon` (dilutes medical brand).

## Recipe: Services catalog (highest SEO weight)

NOT inside the Edit Profile dialog. From the main profile actions row:
```
button "Edit services" → dialog "Add services" with one region per category
```

Each `region "{Category}"` has a `button "Add more services for {Category}"` (or `Add custom service` for primary categories that lack presets).

### Two modes

**Mode A: Preset services (Medical spa, Beauty salon, etc. get this)**
- Click the Add button → listbox with preset options
- Click each option to toggle (add ✓)
- Click `button "Save"` when done
- These match Google's internal entity catalog → strongest SEO signal

**Mode B: Custom services (Dermatologist + many other categories only get this)**
- Click "Add custom service" → combobox appears (120 char limit)
- Type the service name → click "Add custom service" again to add another row
- Click `button "Save"` when done
- Use Hebrew terms customers actually search

### High-value preset names for aesthetic clinics (verified 2026)

Under **Medical spa**:
- Liposuction *(the big SEO one)*
- Body contouring
- Botox treatments
- Cellulite reduction
- Chemical peels
- Dermaplaning
- Dysport treatment
- HydraFacial
- IPL photo facial
- JUVÉDERM treatments
- Laser hair removal
- Lip fillers
- Microneedling
- PRP facial
- Sculptra treatments
- Spider vein treatments
- Ultherapy

Under **Laser hair removal service**: auto-includes "Laser hair removal".

After Save, Google shows: `"Your edit is pending review. It may take up to one day to be published."` Services typically clear within a few hours.

## Recipe: Photos (legacy v4 API, but UI works without approval)

Main profile actions → `button "Photos"` (or `link "Add photo"` in the locations table). UI accepts drag-and-drop of JPG/PNG up to 5 MB each.

Categories: Logo, Cover, Interior, Exterior, At work, Team, Identity, Food & drink, Common areas, Rooms.

For aesthetic clinics, prioritize: Logo (1), Cover (1 wide hero), Interior (4-6 of reception/treatment rooms), Team (1-2 of staff), At work (4-6 process shots of treatments).

## Recipe: Posts (manual until API approval)

Main profile actions → `button "Posts"`. Three types:
- Standard ("What's new") — expires after 7 days
- Offers — has explicit start/end date
- Events — has date/time

Posts have weak SEO weight but signal activity to Google. Worth one weekly post.

## Recipe: Replying to reviews (manual until API approval)

Main profile actions → `button "Reviews"` (or "Read reviews" link).

Reply to every review, positive and negative:
- 5-star: short thanks + invite back (3-4 lines)
- 1-2 star: empathy + factual response + invite to take it offline (5-8 lines, no defensiveness)

Patient privacy in healthcare: NEVER confirm someone was actually a patient, never disclose treatment specifics. Keep replies generic.

## Detecting Google's auto-changes

While the editor is open, Google shows diffs in side panels like:
```
"Has wheelchair-accessible entrance has been updated"   ← insertion
"Has gender-neutral toilets has been removed"           ← deletion
```

These are attribute changes Google detected from Street View, reviews, or other signals. Review each one — the auto-detected values aren't always accurate.

## Console errors to ignore

The SERP-embedded editor logs 2-4 console errors per page load. These are non-fatal CSP and FedCM warnings from Google's own SDK. Don't treat them as failures.

## Snapshot size

The full page snapshot can exceed 50k tokens and trip MCP's response cap. When that happens, save the snapshot to a file:
```js
mcp__playwright__browser_snapshot({ filename: "step.yml" })
```
Then grep the local YAML for the refs you need (`button "Edit ..."` patterns are stable).
