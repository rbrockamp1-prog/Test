#!/usr/bin/env python3
"""
Job search discovery pipeline for Elizabeth Weinlein.
Pulls roles from Greenhouse, Lever, and USAJobs; filters, scores,
deduplicates, writes to CSV and optionally to Google Sheets.
"""

import csv
import logging
import os
import re
import sys
import warnings
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import requests
import yaml

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONFIG_PATH = Path(__file__).parent / "config" / "profile.yaml"
OUTPUT_DIR = Path(__file__).parent / "output"
SESSION_TIMEOUT = 10  # seconds for content fetches
HEAD_TIMEOUT = 5       # seconds for URL liveness check
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; JobDiscoveryBot/1.0; +https://github.com/elizabeth)"
    )
}

RESUME_MAP = {
    "E": "Government",
    "C": "Government",
    "F": "Trust & Safety",
    "A": "Private Sector",
    "D": "Private Sector",
}

CSV_COLUMNS = [
    "Company",
    "Role",
    "Bucket",
    "Resume",
    "Status",
    "URL",
    "Date Added",
    "Date Applied",
    "Follow-up Due",
    "Why it fits",
    "Fit Score",
]

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(path: Path) -> dict:
    with open(path, "r") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class JobPosting:
    """Normalised job posting before filtering."""

    def __init__(
        self,
        company: str,
        title: str,
        url: str,
        location: str = "",
        content: str = "",
        source: str = "",
    ):
        self.company = company.strip()
        self.title = title.strip()
        self.url = url.strip()
        self.location = location.strip()
        self.content = content.strip()
        self.source = source

    def searchable_text(self) -> str:
        return f"{self.title} {self.content} {self.location}".lower()

    def __repr__(self) -> str:
        return f"<JobPosting company={self.company!r} title={self.title!r}>"


class DiscoveredRole:
    """A posting that passed all 3 checks."""

    def __init__(
        self,
        posting: JobPosting,
        bucket_key: str,
        bucket_name: str,
        matched_keywords: list[str],
        fit_score: int,
    ):
        self.posting = posting
        self.bucket_key = bucket_key
        self.bucket_name = bucket_name
        self.matched_keywords = matched_keywords
        self.fit_score = fit_score

    @property
    def resume(self) -> str:
        return RESUME_MAP.get(self.bucket_key, "Private Sector")

    def to_row(self, today: str) -> list[str]:
        return [
            self.posting.company,
            self.posting.title,
            self.bucket_name,
            self.resume,
            "To Apply",
            self.posting.url,
            today,
            "",  # Date Applied
            "",  # Follow-up Due
            ", ".join(self.matched_keywords),
            str(self.fit_score),
        ]


# ---------------------------------------------------------------------------
# Source: Greenhouse
# ---------------------------------------------------------------------------

def fetch_greenhouse(slug: str) -> list[JobPosting]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=SESSION_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("Greenhouse fetch failed for slug %r: %s", slug, exc)
        return []

    try:
        data = resp.json()
    except ValueError as exc:
        log.warning("Greenhouse JSON parse error for slug %r: %s", slug, exc)
        return []

    postings: list[JobPosting] = []
    for job in data.get("jobs", []):
        title = job.get("title", "")
        job_url = job.get("absolute_url", "")
        location_obj = job.get("location", {})
        location = location_obj.get("name", "") if isinstance(location_obj, dict) else str(location_obj)
        content = job.get("content", "") or ""
        # Strip HTML tags from content
        content = re.sub(r"<[^>]+>", " ", content)
        postings.append(
            JobPosting(
                company=slug.replace("-", " ").title(),
                title=title,
                url=job_url,
                location=location,
                content=content,
                source="greenhouse",
            )
        )

    log.info("Greenhouse [%s]: %d postings fetched", slug, len(postings))
    return postings


# ---------------------------------------------------------------------------
# Source: Lever
# ---------------------------------------------------------------------------

def fetch_lever(slug: str) -> list[JobPosting]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=SESSION_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("Lever fetch failed for slug %r: %s", slug, exc)
        return []

    try:
        data = resp.json()
    except ValueError as exc:
        log.warning("Lever JSON parse error for slug %r: %s", slug, exc)
        return []

    postings: list[JobPosting] = []
    # Lever returns a list of postings directly
    items = data if isinstance(data, list) else data.get("data", [])
    for job in items:
        title = job.get("text", "")
        job_url = job.get("hostedUrl", "") or job.get("applyUrl", "")
        location_obj = job.get("categories", {})
        location = ""
        if isinstance(location_obj, dict):
            location = location_obj.get("location", "")

        # Build content from lists block
        content_parts: list[str] = []
        for block in job.get("lists", []):
            content_parts.append(block.get("text", ""))
            for item in block.get("content", "").split("</li>"):
                clean = re.sub(r"<[^>]+>", " ", item).strip()
                if clean:
                    content_parts.append(clean)
        description = job.get("description", "") or job.get("descriptionPlain", "") or ""
        description = re.sub(r"<[^>]+>", " ", description)
        content_parts.append(description)
        content = " ".join(content_parts)

        postings.append(
            JobPosting(
                company=slug.replace("-", " ").title(),
                title=title,
                url=job_url,
                location=location,
                content=content,
                source="lever",
            )
        )

    log.info("Lever [%s]: %d postings fetched", slug, len(postings))
    return postings


# ---------------------------------------------------------------------------
# Source: USAJobs
# ---------------------------------------------------------------------------

def fetch_usajobs(cfg: dict) -> list[JobPosting]:
    email = os.environ.get("USAJOBS_EMAIL", "").strip()
    api_key = os.environ.get("USAJOBS_API_KEY", "").strip()

    if not email or not api_key:
        log.warning(
            "Skipping USAJobs — USAJOBS_EMAIL and/or USAJOBS_API_KEY env vars not set."
        )
        return []

    usa_cfg = cfg.get("usajobs", {})
    series_list = usa_cfg.get("series", [])
    keyword = usa_cfg.get("keyword", "program analyst")
    remote_only = usa_cfg.get("remote_only", True)

    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": email,
        "Authorization-Key": api_key,
    }

    postings: list[JobPosting] = []

    for series_code in series_list:
        params: dict[str, Any] = {
            "Keyword": keyword,
            "JobCategoryCode": series_code,
            "ResultsPerPage": 50,
            "PageNumber": 1,
        }
        if remote_only:
            params["RemoteIndicator"] = "True"

        page = 1
        while True:
            params["PageNumber"] = page
            try:
                resp = requests.get(
                    "https://data.usajobs.gov/api/search",
                    headers=headers,
                    params=params,
                    timeout=SESSION_TIMEOUT,
                )
                resp.raise_for_status()
            except requests.RequestException as exc:
                log.warning("USAJobs fetch failed for series %s (page %d): %s", series_code, page, exc)
                break

            try:
                data = resp.json()
            except ValueError as exc:
                log.warning("USAJobs JSON parse error for series %s: %s", series_code, exc)
                break

            search_result = data.get("SearchResult", {})
            items = search_result.get("SearchResultItems", [])
            if not items:
                break

            for item in items:
                matched = item.get("MatchedObjectDescriptor", {})
                title = matched.get("PositionTitle", "")
                org = matched.get("OrganizationName", "")
                dept = matched.get("DepartmentName", "")
                company = org or dept or "Federal Agency"

                url_obj = matched.get("ApplyURI", [])
                job_url = url_obj[0] if url_obj else matched.get("PositionURI", "")

                location_list = matched.get("PositionLocation", [])
                if location_list:
                    loc = location_list[0]
                    location = f"{loc.get('CityName', '')}, {loc.get('CountrySubDivisionCode', '')}".strip(", ")
                else:
                    location = ""

                qual_summary = matched.get("QualificationSummary", "")
                user_area = matched.get("UserArea", {})
                details = user_area.get("Details", {}) if isinstance(user_area, dict) else {}
                job_summary = details.get("JobSummary", "") if isinstance(details, dict) else ""
                content = f"{qual_summary} {job_summary}"

                postings.append(
                    JobPosting(
                        company=company,
                        title=title,
                        url=job_url,
                        location=location,
                        content=content,
                        source="usajobs",
                    )
                )

            total_count = int(search_result.get("SearchResultCountAll", 0))
            fetched_so_far = page * params["ResultsPerPage"]
            if fetched_so_far >= total_count:
                break
            page += 1

        log.info("USAJobs [series %s]: %d postings fetched", series_code, len(postings))

    log.info("USAJobs total: %d postings fetched across all series", len(postings))
    return postings


# ---------------------------------------------------------------------------
# Check 1: URL liveness
# ---------------------------------------------------------------------------

def check_url_live(url: str) -> bool:
    """Return True if URL is well-formed and responds with a non-4xx/5xx status."""
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    try:
        resp = requests.head(
            url,
            headers=REQUEST_HEADERS,
            timeout=HEAD_TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code >= 400:
            # Some servers reject HEAD; try GET with stream
            resp = requests.get(
                url,
                headers=REQUEST_HEADERS,
                timeout=HEAD_TIMEOUT,
                stream=True,
            )
        return resp.status_code < 400
    except requests.RequestException:
        return False


# ---------------------------------------------------------------------------
# Check 2: Keyword matching and scoring
# ---------------------------------------------------------------------------

def check_keywords(
    posting: JobPosting, buckets: dict
) -> tuple[Optional[str], Optional[str], list[str], int]:
    """
    Find which bucket best matches the posting.
    Returns (bucket_key, bucket_name, matched_keywords, score) or (None, None, [], 0).
    Requires at least 2 keyword matches in title or JD text.
    """
    text = posting.searchable_text()
    best_bucket_key = None
    best_bucket_name = None
    best_matched: list[str] = []
    best_score = 0

    for bucket_key, bucket in buckets.items():
        keywords: list[str] = [kw.lower() for kw in bucket.get("keywords", [])]
        titles: list[str] = [t.lower() for t in bucket.get("titles", [])]

        matched_kw = [kw for kw in keywords if kw in text]

        # Also count title matches as keyword hits
        title_lower = posting.title.lower()
        matched_titles = [t for t in titles if t in title_lower]

        all_matched = list(dict.fromkeys(matched_kw + matched_titles))  # deduplicate, preserve order

        if len(all_matched) < 2:
            continue

        # Score: keyword density relative to total keywords available, scaled 0-10
        total_signals = len(keywords) + len(titles)
        score = min(10, round((len(all_matched) / max(total_signals, 1)) * 10 * 1.5))

        if score > best_score:
            best_score = score
            best_bucket_key = bucket_key
            best_bucket_name = bucket.get("name", bucket_key)
            best_matched = all_matched

    return best_bucket_key, best_bucket_name, best_matched, best_score


# ---------------------------------------------------------------------------
# Check 3: Hard-no filter
# ---------------------------------------------------------------------------

YEARS_PATTERN = re.compile(
    r"(\d+)\+?\s*(?:or more\s*)?years?\s+(?:of\s+)?(?:experience|exp\.?)",
    re.IGNORECASE,
)


def check_hard_nos(posting: JobPosting, hard_nos: dict) -> tuple[bool, str]:
    """
    Return (passes, reason). passes=True means the posting is clean.
    """
    text = posting.searchable_text()

    for kw in hard_nos.get("keywords", []):
        if kw.lower() in text:
            return False, f"hard-no keyword: {kw!r}"

    max_years = hard_nos.get("min_years_required", 8)
    for match in YEARS_PATTERN.finditer(text):
        years_required = int(match.group(1))
        if years_required > max_years:
            return False, f"requires {years_required}+ years experience"

    for loc in hard_nos.get("excluded_locations", []):
        if loc.lower() in text or loc.lower() in posting.location.lower():
            return False, f"excluded location: {loc!r}"

    return True, ""


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline() -> None:
    cfg = load_config(CONFIG_PATH)
    buckets: dict = cfg.get("buckets", {})
    hard_nos: dict = cfg.get("hard_nos", {})

    today_str = date.today().isoformat()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_csv = OUTPUT_DIR / f"discovered_{today_str}.csv"

    # -----------------------------------------------------------------------
    # Gather all slugs per source across buckets
    # -----------------------------------------------------------------------
    greenhouse_slug_to_buckets: dict[str, list[str]] = {}
    lever_slug_to_buckets: dict[str, list[str]] = {}

    for bucket_key, bucket in buckets.items():
        for slug in bucket.get("greenhouse_slugs", []):
            greenhouse_slug_to_buckets.setdefault(slug, []).append(bucket_key)
        for slug in bucket.get("lever_slugs", []):
            lever_slug_to_buckets.setdefault(slug, []).append(bucket_key)

    # -----------------------------------------------------------------------
    # Fetch from all sources
    # -----------------------------------------------------------------------
    log.info("=== Fetching from Greenhouse ===")
    all_postings: list[JobPosting] = []
    source_counts: dict[str, int] = {"greenhouse": 0, "lever": 0, "usajobs": 0}

    for slug in greenhouse_slug_to_buckets:
        fetched = fetch_greenhouse(slug)
        source_counts["greenhouse"] += len(fetched)
        all_postings.extend(fetched)

    log.info("=== Fetching from Lever ===")
    for slug in lever_slug_to_buckets:
        fetched = fetch_lever(slug)
        source_counts["lever"] += len(fetched)
        all_postings.extend(fetched)

    log.info("=== Fetching from USAJobs ===")
    usa_postings = fetch_usajobs(cfg)
    source_counts["usajobs"] += len(usa_postings)
    all_postings.extend(usa_postings)

    log.info(
        "Total fetched — Greenhouse: %d, Lever: %d, USAJobs: %d",
        source_counts["greenhouse"],
        source_counts["lever"],
        source_counts["usajobs"],
    )

    # -----------------------------------------------------------------------
    # 3-check filter + deduplication
    # -----------------------------------------------------------------------
    seen: set[tuple[str, str]] = set()
    check1_passed = 0
    check2_passed = 0
    check3_passed = 0
    discovered: list[DiscoveredRole] = []

    for posting in all_postings:
        # Deduplication
        dedup_key = (posting.company.lower(), posting.title.lower())
        if dedup_key in seen:
            log.debug("Duplicate skipped: %s — %s", posting.company, posting.title)
            continue
        seen.add(dedup_key)

        # Check 1: URL liveness
        if not check_url_live(posting.url):
            log.debug("Check 1 failed (dead URL): %s", posting.url)
            continue
        check1_passed += 1

        # Check 2: Keyword matching
        bucket_key, bucket_name, matched_kw, score = check_keywords(posting, buckets)
        if bucket_key is None:
            log.debug("Check 2 failed (no keyword match): %s — %s", posting.company, posting.title)
            continue
        check2_passed += 1

        # Check 3: Hard-no filter
        passes, reason = check_hard_nos(posting, hard_nos)
        if not passes:
            log.debug("Check 3 failed (%s): %s — %s", reason, posting.company, posting.title)
            continue
        check3_passed += 1

        discovered.append(
            DiscoveredRole(
                posting=posting,
                bucket_key=bucket_key,
                bucket_name=bucket_name,
                matched_keywords=matched_kw,
                fit_score=score,
            )
        )

    # Sort by fit score descending, then bucket priority
    bucket_priority = {k: v.get("priority", 99) for k, v in buckets.items()}
    discovered.sort(key=lambda r: (-r.fit_score, bucket_priority.get(r.bucket_key, 99)))

    log.info(
        "Filtering results — Check 1 (URL live): %d, Check 2 (keywords): %d, Check 3 (hard-nos): %d",
        check1_passed,
        check2_passed,
        check3_passed,
    )
    log.info("Total roles passing all checks: %d", len(discovered))

    # -----------------------------------------------------------------------
    # Write CSV
    # -----------------------------------------------------------------------
    rows = [role.to_row(today_str) for role in discovered]
    with open(output_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(CSV_COLUMNS)
        writer.writerows(rows)
    log.info("CSV written: %s (%d roles)", output_csv, len(rows))

    # -----------------------------------------------------------------------
    # Write to Google Sheets (optional)
    # -----------------------------------------------------------------------
    sheets_cfg = cfg.get("google_sheets", {})
    creds_file = sheets_cfg.get("credentials_file", "credentials.json")
    creds_path = Path(creds_file)

    if not creds_path.exists():
        log.info("Skipping Google Sheets write — no credentials.json found")
    else:
        write_to_google_sheets(cfg, discovered, today_str, creds_path)

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("DISCOVERY SUMMARY")
    print("=" * 60)
    print(f"Roles pulled — Greenhouse: {source_counts['greenhouse']}, "
          f"Lever: {source_counts['lever']}, USAJobs: {source_counts['usajobs']}")
    print(f"Unique postings evaluated: {len(seen)}")
    print(f"Passed Check 1 (URL live):        {check1_passed}")
    print(f"Passed Check 2 (keyword match):   {check2_passed}")
    print(f"Passed Check 3 (no hard-nos):     {check3_passed}")
    print(f"Roles in output CSV:              {len(discovered)}")
    print(f"Output CSV: {output_csv}")

    if discovered:
        print("\nTop 10 matches:")
        for role in discovered[:10]:
            print(
                f"  [{role.bucket_key}] {role.posting.company} — {role.posting.title} "
                f"(score: {role.fit_score}, keywords: {', '.join(role.matched_keywords[:3])})"
            )
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Google Sheets integration
# ---------------------------------------------------------------------------

def write_to_google_sheets(
    cfg: dict,
    discovered: list[DiscoveredRole],
    today_str: str,
    creds_path: Path,
) -> None:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        log.error("Google API libraries not installed: %s", exc)
        return

    sheets_cfg = cfg.get("google_sheets", {})
    spreadsheet_id = sheets_cfg.get("spreadsheet_id", "")
    tracker_tab = sheets_cfg.get("tracker_tab", "Tracker")

    if not spreadsheet_id:
        log.warning("No spreadsheet_id configured — skipping Sheets write.")
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    try:
        creds = service_account.Credentials.from_service_account_file(
            str(creds_path), scopes=scopes
        )
        service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        sheet = service.spreadsheets()
    except Exception as exc:
        log.error("Failed to initialise Google Sheets client: %s", exc)
        return

    # Fetch existing rows for deduplication
    existing_keys: set[tuple[str, str]] = set()
    try:
        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{tracker_tab}!A:B",
        ).execute()
        existing_values = result.get("values", [])
        # Skip header row
        for row in existing_values[1:]:
            if len(row) >= 2:
                existing_keys.add((row[0].strip().lower(), row[1].strip().lower()))
    except Exception as exc:
        log.warning("Could not read existing sheet rows for deduplication: %s", exc)

    new_rows = []
    for role in discovered:
        key = (role.posting.company.lower(), role.posting.title.lower())
        if key in existing_keys:
            log.debug("Sheet dupe skipped: %s — %s", role.posting.company, role.posting.title)
            continue
        new_rows.append(role.to_row(today_str))

    if not new_rows:
        log.info("No new roles to append to Google Sheets (all already present).")
        return

    try:
        body = {"values": new_rows}
        sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{tracker_tab}!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()
        log.info("Google Sheets: appended %d new rows to tab %r", len(new_rows), tracker_tab)
        print(f"Google Sheets: {len(new_rows)} new roles written to tab '{tracker_tab}'.")
    except Exception as exc:
        log.error("Failed to append to Google Sheets: %s", exc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        log.info("Pipeline interrupted by user.")
        sys.exit(0)
    except Exception as exc:
        log.exception("Unhandled error in pipeline: %s", exc)
        sys.exit(1)
