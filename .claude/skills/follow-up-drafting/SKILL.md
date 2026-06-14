# Skill: follow-up-drafting

## Description
Read Elizabeth's tracker in the Google Sheet. For any role where Status = "Applied", Date Applied is 7+ days ago, and no Follow-up Due date is set, draft a polite follow-up email for review.

## Trigger
User says something like: "draft follow-ups", "check who needs a follow-up", "any follow-ups due", "write follow-up emails"

## Workflow

1. Read the Tracker tab from the Google Sheet (ID in `config/profile.yaml`).
2. Filter rows where:
   - Status = "Applied"
   - Date Applied is 7 or more days before today
   - Follow-up Due column is empty
3. For each matching row, draft a follow-up email:
   - Subject: `Following up — [Role Title] at [Company]`
   - Body: 3 sentences max. Professional, warm, not pushy. Reference the role and when she applied. Express continued interest. Ask if there's any additional info they need.
   - Do NOT mention salary, other applications, or deadlines.
4. Present all drafts to the user for review before anything is sent.
5. Ask the user which ones to mark as "Follow-up Sent" in the tracker.
6. Update the Follow-up Due column for sent ones to today + 7 days.

## Rules
- Elizabeth sends all emails herself. Never auto-send.
- Never draft more than 3 follow-ups in one session — if more are due, prioritize by oldest application date.
- If a role has already been followed up once (Follow-up Due is set), do not draft a second one unless the user specifically asks.
- Keep tone professional and brief. Recruiters read hundreds of emails.

## Draft template
```
Subject: Following up — [Role] at [Company]

Hi [Name if known, otherwise "there"],

I wanted to follow up on my application for the [Role Title] position, which I submitted on [Date Applied]. I remain very interested in this opportunity and would love to learn more about next steps.

Please let me know if there's any additional information I can provide.

Thank you,
Elizabeth Weinlein
```
