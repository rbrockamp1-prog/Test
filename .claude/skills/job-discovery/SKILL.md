# Skill: job-discovery

## Description
Run the job discovery pipeline for Elizabeth. Fetches verified roles from Greenhouse, Lever, and USAJobs across all 5 buckets, applies the 3-check filter, and writes passing roles to the Google Sheet tracker.

## Trigger
User says something like: "run discovery", "find jobs", "check the buckets", "what's new this week", "run the pipeline"

## Workflow

1. Read `config/profile.yaml` to confirm bucket definitions and hard-nos are current.
2. Run `python discover.py` and capture stdout.
3. Parse the summary output:
   - How many roles pulled per source
   - How many passed Check 1 (URL live), Check 2 (keyword match), Check 3 (no hard-nos)
   - How many written to Google Sheet
4. Report results honestly:
   - If 0 roles passed for a bucket, say so. Do not pad.
   - For each role that passed, show: Company, Role, Bucket, Fit Score, and the specific JD sentence that proved Check 2.
   - If a source errored, say which one and why.
5. If Google Sheets write failed, report the error and tell the user to check credentials.

## Rules
- Never claim a role is verified without the script actually fetching and checking it.
- Never invent roles. All output comes from the script.
- Target: 2-5 verified roles per run. More is not better — quality only.
- If discover.py isn't runnable (missing deps, broken), fix it before reporting results.

## Output format
```
Discovery run — [date]

Source results:
  Greenhouse: X roles fetched, Y passed all checks
  Lever: X roles fetched, Y passed all checks
  USAJobs: X roles fetched, Y passed all checks (skipped if no API key)

Roles passing all 3 checks:
  1. [Company] — [Role Title]
     Bucket: [A/C/D/E/F]
     Fit score: [0-10]
     URL: [url]
     Why: "[exact sentence from JD that matched]"

Buckets with 0 results this week: [list]
Written to Google Sheet: [N] new rows
```
