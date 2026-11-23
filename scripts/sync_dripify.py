#!/usr/bin/env python3
"""Fetch only approved, aggregate Dripify campaign statistics for a public dashboard."""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

BASE = "https://api.dripify.com/v1/open-api"
CAMPAIGNS = {
    2161184: "Materials",
    2151502: "AUMMIS Referrals",
    2151441: "AUMMIS Candidates",
}
OUTPUT = Path("data/dripify-summary.json")
FIELDS = (
    "totalLeads", "contactedLeads", "acceptanceRate", "acceptanceRateLeads",
    "replyRate", "replyRateLeads", "leadListsCount", "active",
)
BREAKDOWN_FIELDS = (
    "inProgress", "finished", "failed", "blacklisted", "gettingReady",
    "waiting", "paused", "uploading", "transferred",
)


def request_statistics(campaign_id, key):
    url = f"{BASE}/campaigns/{campaign_id}/statistics"
    for attempt in range(4):
        req = urllib.request.Request(
            url,
            headers={"X-Api-Key": key, "Accept": "application/json", "User-Agent": "collider-dashboard/1.0"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 3:
                value = exc.headers.get("Retry-After", "5")
                try:
                    delay = min(60, max(1, int(value)))
                except ValueError:
                    delay = 5
                time.sleep(delay)
                continue
            # Never print response bodies, URLs with tokens, or other API data.
            raise RuntimeError(f"Dripify campaign {campaign_id} returned HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Dripify campaign {campaign_id} could not be reached") from None
    raise RuntimeError("Dripify request retry limit reached")


def sanitized(stats, campaign_id, label):
    if not isinstance(stats, dict) or stats.get("campaignId") != campaign_id:
        raise ValueError(f"Unexpected response for campaign {campaign_id}")
    result = {"id": campaign_id, "label": label}
    for field in FIELDS:
        val = stats.get(field)
        if isinstance(val, bool) and field == "active":
            result[field] = val
        elif field != "active" and type(val) in (int, float) and val >= 0:
            result[field] = val
        else:
            raise ValueError(f"Invalid {field} for campaign {campaign_id}")
    breakdown = stats.get("leadStatusBreakdown", {})
    if not isinstance(breakdown, dict):
        raise ValueError("Invalid leadStatusBreakdown")
    result["leadStatusBreakdown"] = {}
    for field in BREAKDOWN_FIELDS:
        value = breakdown.get(field)
        if type(value) not in (int, float) or value < 0:
            raise ValueError(f"Invalid breakdown: {field}")
        result["leadStatusBreakdown"][field] = value
    return result


def main():
    key = os.environ.get("DRIPIFY_API_KEY", "")
    if not key:
        print("DRIPIFY_API_KEY is missing", file=sys.stderr)
        return 1
    campaigns = []
    try:
        for campaign_id, label in CAMPAIGNS.items():
            raw = request_statistics(campaign_id, key)
            campaigns.append(sanitized(raw, campaign_id, label))
    except (ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1  # Preserve previous successful snapshot on any error.
    payload = {
        "schemaVersion": 1,
        "updatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source": "Dripify Open API (aggregate campaign statistics)",
        "campaigns": campaigns,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(OUTPUT)
    print(f"Updated aggregate statistics for {len(campaigns)} approved campaigns.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
