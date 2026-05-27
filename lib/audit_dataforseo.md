# Read-only GBP audit via DataForSEO Maps

No auth, no API approval needed. Use this for first-pass audit on any GBP before touching writes.

## Find the listing

Hebrew clinic name spelling varies (eg `בבייב` vs `באבאיב`). Always search by **coordinates + city** instead of just name:

```js
mcp__dataforseo__business_data_business_listings_search({
  title: "Dr X clinic",
  location_coordinate: "32.0117,34.7740,30",   // lat,lng,radius_km
  limit: 10,
  is_claimed: false                              // false = both claimed and unclaimed
})
```

If you don't know the coordinates, geocode the street address via Google Maps URL trick or set a wide radius around the city center.

## What you get back

Each item in `items[]` includes (relevant fields only):

```json
{
  "title": "...",
  "category": "Dermatologist",
  "category_ids": ["dermatologist"],
  "cid": "9173893006157140215",
  "feature_id": "0x1502b79c86459c47:0x7f5037156f6fd0f7",
  "place_id": "ChIJ...",
  "address": "Harokmim St 26, Holon, 5885849",
  "phone": "+972...",
  "url": "http://dr-meir.com/",
  "domain": "dr-meir.com",
  "logo": "https://lh.../photo.jpg",
  "main_image": "...",
  "total_photos": 13,
  "rating": { "value": 4, "votes_count": 68 },
  "rating_distribution": { "1": 17, "2": 0, "3": 1, "4": 0, "5": 50 },
  "work_time": { "work_hours": { "timetable": { "friday": [{...}] } } },
  "is_claimed": true,
  "attributes": { ... },
  "contact_info": [ { "type": "telephone", "value": "...", "source": "..." } ],
  "place_topics": { "modern equipment": 7, "personal attention": 3 },
  "people_also_search": [ ... ],
  "check_url": "https://www.google.com/maps?cid=..."
}
```

## What to flag (audit checklist)

1. **NAP consistency** — compare `address`, `phone`, `url` against the website's Schema JSON-LD. Drift is common after office moves.
2. **`url` starts with `http://`** — should be `https://`. Easy fix.
3. **Postcode** in `address` vs the website's `addressLocality`+postalCode Schema fields. Differences happen when GBP was created years ago.
4. **`total_photos` < 20** → low, hurts CTR. Aim for 30+.
5. **`rating_distribution`** bimodal (eg 50 five-stars and 17 one-stars with nothing in between) → assume review bombing. Look at review timestamps later.
6. **Friday hours in Israel** in `work_time.work_hours.timetable.friday` — if equal to weekdays, almost certainly wrong (Israeli businesses typically close earlier on Friday).
7. **Saturday status** — should be "Closed" for most Israeli businesses; missing entry usually means "Closed" by default but it's better to set it explicitly.
8. **`contact_info` entries from `source: "backlinks"`** that don't match `source: "google_business"` → indicate old phone numbers still floating in the web. Find and fix those external citations.
9. **`is_claimed: false`** → claim the profile before doing anything else.
10. **`place_topics`** gives you the language customers actually use about you in reviews — pull these phrases into the Description and Services for better keyword matching.

## Performance limits

- ~$0.01 per call
- Returns up to ~13 photos URLs (not 50), no review text
- 1-2 second response time
- Works for any business worldwide

## Cross-checking with the Place ID

The `place_id` returned here is the canonical Google Maps Place ID. Use it to:
- Build the canonical Maps URL: `https://www.google.com/maps?cid=<cid>`
- Match against the GBP API `locations.metadata.placeId` once you have API access
- Detect duplicate listings — same `place_id` across different account names = auto-merged duplicate
