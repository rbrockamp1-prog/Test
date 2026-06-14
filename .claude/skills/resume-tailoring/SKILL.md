# Skill: resume-tailoring

## Description
Given a job URL, fetch the JD, pick the right resume version, and produce a tailored resume emphasizing matching keywords — truthfully, no fabrication.

## Trigger
User says something like: "tailor resume for [URL]", "prep Elizabeth's resume for [company]", "which resume for this job", "help apply to [role]"

## Resume versions
- **Government** (`Weinlein_Resume_Government.pdf`) — for Buckets C, E, and federal contractor roles (ICF, Booz Allen, Guidehouse, Leidos, CACI, Peraton, Noblis, USAJobs)
- **Private Sector** (`Weinlein_Resume_PrivateSector.docx`) — for Buckets A, D, and health tech (foundations, NGOs, health tech operations)
- **Trust & Safety** (`Weinlein_Resume_TrustSafety.docx`) — for Bucket F ONLY (Persona, Plaid, Stripe, Coinbase, Discord, Snap, Meta, TikTok). **IMPORTANT: Remove the internal notes section at the bottom marked "REMOVE BEFORE SENDING" before any actual application.**

## Workflow

1. Fetch the job URL. If it 404s or redirects to a generic career page, stop and tell the user.
2. Read the full JD text.
3. Determine which bucket the role falls in using the keyword and company matching from `config/profile.yaml`.
4. Select the correct resume version per the table above.
5. Identify JD keywords that:
   - Are present in Elizabeth's actual experience (don't fabricate)
   - Should be emphasized or mirrored in the tailored version
6. Produce a tailored resume summary and bullets list showing:
   - Which existing bullet points to move to the top
   - Which keywords to weave in (with the exact existing context they fit)
   - Suggested rewordings (truthful only — no invented experience)
7. Generate a draft cover letter opening (2-3 sentences max) mirroring the JD language.
8. Note which resume file to use and remind user to review before sending.

## Rules
- No fabrication. Only reorder, reword, and emphasize what's already true.
- If Trust & Safety resume is selected, always remind about the "REMOVE BEFORE SENDING" section.
- If the role hits any hard-no (entry-level, DC-required, 5-day in-office, Mandarin-required), say so immediately and ask if the user wants to proceed anyway.
- Never submit or auto-apply anything. Output is always for Elizabeth's review.
