#!/usr/bin/env python3
"""
One-time seed of hand-verified leads (from current-leads.md, 2026-06-15)
into the Google Sheet Tracker tab. Deduplicates by (Company, Role).

Run: python seed_leads.py
Requires credentials.json in repo root (service account with Sheets access).
"""

import logging
from datetime import date
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config" / "profile.yaml"
CREDS_PATH = Path(__file__).parent / "credentials.json"

# Tracker columns:
# Company | Role | Bucket | Resume | Status | URL | Date Added |
# Date Applied | Follow-up Due | Why it fits | Fit Score
HEADER = [
    "Company", "Role", "Bucket", "Resume", "Status", "URL",
    "Date Added", "Date Applied", "Follow-up Due", "Why it fits", "Fit Score",
]

TODAY = date.today().isoformat()

# Hand-verified leads from the 2026-06-15 manual sweep.
# Each: (company, role, bucket, resume, url, why_it_fits, fit_score)
LEADS = [
    (
        "Hewlett Foundation",
        "Program Associate, Environment",
        "D",
        "Private Sector",
        "https://job.ceaconsulting.com/jobs/program-associate-environment-497",
        "VERIFIED LIVE 2026-06-15. Supports Environment Program's Climate Initiative, "
        "Multilateral & Climate Finance portfolio. Direct path into a target foundation; "
        "associate-level, posted 'until filled'.",
        8,
    ),
    (
        "Hewlett Foundation",
        "Program Officer, Economy and Society Initiative",
        "D",
        "Private Sector",
        "https://hewlett.org/careers/",
        "Grantmaking role on energy transition / economic policy. Title matches bucket "
        "exactly; focus broader than climate — adjacent fit. Get direct link before applying.",
        6,
    ),
    (
        "LA County Dept of Health Services",
        "Health Program Analyst I (Emergency Appointment — Homelessness)",
        "A",
        "Government",
        "https://www.governmentjobs.com/careers/lacounty",
        "Part of LA County homelessness emergency-hiring wave. Program-analyst title, "
        "government, LA — strong fit for Climate x Public Health bucket. Search title directly.",
        8,
    ),
    (
        "LA County",
        "Assistant Staff Analyst, Health Services (Emergency Appointment — Homelessness)",
        "A",
        "Government",
        "https://www.governmentjobs.com/careers/lacounty",
        "Companion posting in same emergency wave. Slightly more junior than Health Program "
        "Analyst I — compare levels before choosing.",
        7,
    ),
    (
        "LA County",
        "Management Analyst (Emergency Appointment — Homelessness)",
        "C",
        "Government",
        "https://www.governmentjobs.com/careers/lacounty",
        "County-wide emergency hiring under Civil Service Rule 13.04 (declared homelessness "
        "state of emergency). EM/resilience fit. Verify still accepting applications.",
        7,
    ),
    (
        "Climate Resolve",
        "Director of Resilience and Outreach",
        "C",
        "Private Sector",
        "https://climateresolve.org/careers/",
        "LA-based climate-resilience nonprofit. Director-level — likely above target seniority "
        "but possible stretch role if open to it.",
        5,
    ),
    (
        "Jupiter Intelligence",
        "Principal, Customer Success",
        "C",
        "Private Sector",
        "https://jobs.lever.co/jupiterintel/e949533a-02ef-4d41-939e-8020b6d7e469/apply",
        "Remote/US, senior. Customer-success rather than policy core, but Jupiter's customers "
        "include public-sector orgs and NGOs (Jupiter Promise) — gov/EM background relevant. "
        "'Worth a look,' not a bullseye.",
        5,
    ),
]


def main() -> None:
    cfg = yaml.safe_load(CONFIG_PATH.read_text())
    sheets_cfg = cfg.get("google_sheets", {})
    spreadsheet_id = sheets_cfg.get("spreadsheet_id", "")
    tracker_tab = sheets_cfg.get("tracker_tab", "Tracker")

    if not CREDS_PATH.exists():
        log.error("credentials.json not found — cannot write to sheet.")
        return

    import os
    import httplib2
    from google.oauth2 import service_account
    from google_auth_httplib2 import AuthorizedHttp
    from googleapiclient.discovery import build

    ca_bundle = os.environ.get("REQUESTS_CA_BUNDLE", "/etc/ssl/certs/ca-certificates.crt")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_file(str(CREDS_PATH), scopes=scopes)
    # httplib2 ignores SSL env vars — pass the CA bundle explicitly so it works
    # behind a TLS-intercepting egress proxy.
    base_http = httplib2.Http(ca_certs=ca_bundle)
    authed_http = AuthorizedHttp(creds, http=base_http)
    service = build("sheets", "v4", http=authed_http, cache_discovery=False)
    sheet = service.spreadsheets()

    # Read existing rows
    existing_keys = set()
    has_header = False
    try:
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id, range=f"{tracker_tab}!A:B"
        ).execute()
        rows = result.get("values", [])
        if rows and rows[0] and rows[0][0].strip().lower() == "company":
            has_header = True
        for row in rows[1:] if has_header else rows:
            if len(row) >= 2:
                existing_keys.add((row[0].strip().lower(), row[1].strip().lower()))
    except Exception as exc:
        log.warning("Could not read existing rows: %s", exc)

    new_rows = []
    if not has_header:
        new_rows.append(HEADER)
        log.info("Adding header row.")

    for company, role, bucket, resume, url, why, score in LEADS:
        key = (company.lower(), role.lower())
        if key in existing_keys:
            log.info("Skip dupe: %s — %s", company, role)
            continue
        new_rows.append([
            company, role, bucket, resume, "To Apply", url,
            TODAY, "", "", why, str(score),
        ])

    data_rows = len(new_rows) - (1 if not has_header else 0)
    if data_rows <= 0:
        log.info("Nothing new to add — all leads already present.")
        return

    sheet.values().append(
        spreadsheetId=spreadsheet_id,
        range=f"{tracker_tab}!A1",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": new_rows},
    ).execute()
    log.info("Seeded %d lead rows into '%s'.", data_rows, tracker_tab)


if __name__ == "__main__":
    main()
