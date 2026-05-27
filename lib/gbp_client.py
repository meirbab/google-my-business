"""Google Business Profile API client.

Reusable wrapper for any GBP. Place credentials at <project_dir>/credentials.json
(OAuth Desktop client downloaded from GCP Console). Token cached at
<project_dir>/token.json and auto-refreshed.

Usage:
    from gbp_client import GBP
    g = GBP("/path/to/business/gbp/")   # or default to script dir
    accounts = g.list_accounts()
    locations = g.list_locations(accounts[0]["name"])
    g.update_location(loc_name, body={"regularHours": ...}, update_mask="regularHours")
    reviews = g.list_reviews(loc_name)
    g.reply_review(review_name, "Thank you...")

Run directly to perform OAuth + dump accounts/locations:
    python3 gbp_client.py [project_dir]

Quota=0 gotcha: every call returns 429 RESOURCE_EXHAUSTED with quota_limit_value="0"
until the "Application for basic API access" form is approved by Google
(7-10 working days). See lib/access_form.md.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/business.manage"]

ACCOUNT_MGMT = "https://mybusinessaccountmanagement.googleapis.com/v1"
BUSINESS_INFO = "https://mybusinessbusinessinformation.googleapis.com/v1"
MY_BUSINESS_V4 = "https://mybusiness.googleapis.com/v4"
QA = "https://mybusinessqanda.googleapis.com/v1"
PERFORMANCE = "https://businessprofileperformance.googleapis.com/v1"

DEFAULT_LOCATION_READ_MASK = (
    "name,title,storefrontAddress,phoneNumbers,websiteUri,regularHours,"
    "categories,metadata,profile,labels,openInfo,serviceArea"
)


class GBP:
    def __init__(self, project_dir: str | Path | None = None) -> None:
        self.dir = Path(project_dir or Path(__file__).resolve().parent)
        self.cred_path = self.dir / "credentials.json"
        self.token_path = self.dir / "token.json"
        if not self.cred_path.exists():
            raise FileNotFoundError(
                f"OAuth credentials missing at {self.cred_path}. "
                "Download from GCP Console → Credentials → OAuth client ID (Desktop)."
            )
        self.creds = self._load_creds()
        self.session = AuthorizedSession(self.creds)

    def _load_creds(self) -> Credentials:
        creds: Credentials | None = None
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.cred_path), SCOPES
                )
                creds = flow.run_local_server(
                    port=0, prompt="consent", access_type="offline"
                )
            self.token_path.write_text(creds.to_json())
            os.chmod(self.token_path, 0o600)
        return creds

    def _get(self, url: str, params: dict | None = None) -> dict:
        r = self.session.get(url, params=params)
        return self._unwrap(r, url)

    def _patch(self, url: str, body: dict, params: dict | None = None) -> dict:
        r = self.session.patch(url, json=body, params=params)
        return self._unwrap(r, url)

    def _put(self, url: str, body: dict) -> dict:
        return self._unwrap(self.session.put(url, json=body), url)

    def _post(self, url: str, body: dict) -> dict:
        return self._unwrap(self.session.post(url, json=body), url)

    def _delete(self, url: str) -> dict:
        return self._unwrap(self.session.delete(url), url)

    @staticmethod
    def _unwrap(r, url):
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code} on {url}: {r.text}")
        return r.json() if r.text else {}

    # --- Accounts -------------------------------------------------------
    def list_accounts(self) -> list[dict]:
        out, page = [], None
        while True:
            params = {"pageSize": 50}
            if page:
                params["pageToken"] = page
            data = self._get(f"{ACCOUNT_MGMT}/accounts", params)
            out.extend(data.get("accounts", []))
            page = data.get("nextPageToken")
            if not page:
                return out

    # --- Locations ------------------------------------------------------
    def list_locations(
        self, account_name: str, read_mask: str = DEFAULT_LOCATION_READ_MASK
    ) -> list[dict]:
        out, page = [], None
        while True:
            params = {"pageSize": 100, "readMask": read_mask}
            if page:
                params["pageToken"] = page
            data = self._get(f"{BUSINESS_INFO}/{account_name}/locations", params)
            out.extend(data.get("locations", []))
            page = data.get("nextPageToken")
            if not page:
                return out

    def get_location(self, location_name: str, read_mask: str = DEFAULT_LOCATION_READ_MASK) -> dict:
        return self._get(f"{BUSINESS_INFO}/{location_name}", {"readMask": read_mask})

    def update_location(self, location_name: str, body: dict, update_mask: str) -> dict:
        return self._patch(
            f"{BUSINESS_INFO}/{location_name}", body, {"updateMask": update_mask}
        )

    # --- Categories ----------------------------------------------------
    def list_categories(self, region_code: str = "IL", language_code: str = "en") -> dict:
        return self._get(
            f"{BUSINESS_INFO}/categories",
            {"regionCode": region_code, "languageCode": language_code, "view": "BASIC"},
        )

    def search_categories(self, query: str, region_code: str = "IL", language_code: str = "en") -> dict:
        return self._get(
            f"{BUSINESS_INFO}/categories:search",
            {
                "regionCode": region_code,
                "languageCode": language_code,
                "searchTerm": query,
            },
        )

    # --- Reviews (legacy v4) -------------------------------------------
    def list_reviews(self, location_name: str) -> list[dict]:
        out, page = [], None
        while True:
            params = {"pageSize": 50}
            if page:
                params["pageToken"] = page
            data = self._get(f"{MY_BUSINESS_V4}/{location_name}/reviews", params)
            out.extend(data.get("reviews", []))
            page = data.get("nextPageToken")
            if not page:
                return out

    def reply_review(self, review_name: str, comment: str) -> dict:
        return self._put(f"{MY_BUSINESS_V4}/{review_name}/reply", {"comment": comment})

    def delete_review_reply(self, review_name: str) -> dict:
        return self._delete(f"{MY_BUSINESS_V4}/{review_name}/reply")

    # --- Photos (legacy v4) --------------------------------------------
    def list_media(self, location_name: str) -> list[dict]:
        out, page = [], None
        while True:
            params = {"pageSize": 100}
            if page:
                params["pageToken"] = page
            data = self._get(f"{MY_BUSINESS_V4}/{location_name}/media", params)
            out.extend(data.get("mediaItems", []))
            page = data.get("nextPageToken")
            if not page:
                return out

    # --- Performance ---------------------------------------------------
    def fetch_performance(
        self,
        location_name: str,
        start_date: str,  # YYYY-MM-DD
        end_date: str,
        metrics: list[str] | None = None,
    ) -> dict:
        metrics = metrics or [
            "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
            "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
            "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
            "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
            "BUSINESS_CONVERSATIONS",
            "BUSINESS_DIRECTION_REQUESTS",
            "CALL_CLICKS",
            "WEBSITE_CLICKS",
        ]
        s_y, s_m, s_d = start_date.split("-")
        e_y, e_m, e_d = end_date.split("-")
        params = {
            "dailyMetrics": metrics,
            "dailyRange.startDate.year": s_y,
            "dailyRange.startDate.month": s_m,
            "dailyRange.startDate.day": s_d,
            "dailyRange.endDate.year": e_y,
            "dailyRange.endDate.month": e_m,
            "dailyRange.endDate.day": e_d,
        }
        return self._get(
            f"{PERFORMANCE}/{location_name}:fetchMultiDailyMetricsTimeSeries", params
        )


def _main() -> int:
    project_dir = sys.argv[1] if len(sys.argv) > 1 else None
    g = GBP(project_dir)
    print("[ok] authenticated, loading accounts...", file=sys.stderr)
    accounts = g.list_accounts()
    print(f"[ok] {len(accounts)} account(s) found")
    for a in accounts:
        print(f"\n=== ACCOUNT: {a.get('accountName') or a.get('name')} ===")
        print(json.dumps(a, ensure_ascii=False, indent=2))
        try:
            locs = g.list_locations(a["name"])
        except Exception as e:
            print(f"  [warn] could not list locations: {e}")
            continue
        print(f"  → {len(locs)} location(s)")
        for loc in locs:
            print(json.dumps(loc, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
