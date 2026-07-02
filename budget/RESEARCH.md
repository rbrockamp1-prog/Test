# Budget dashboard — research notes

Why this app is designed the way it is. Synthesized from budgeting-app reviews and
Reddit/personal-finance community sentiment (July 2026).

## Where budgeting apps fail

| # | Failure mode | What we do about it |
|---|---|---|
| 1 | **Friction kills it** — people quit in ~2 weeks. "The best system is the one you stick with; a free spreadsheet beats an unused app." | Add an expense in ~2 taps. Nothing is mandatory; falling behind never breaks the app. |
| 2 | **Bank sync breaks trust** — dropped connections, missing/duplicate/delayed transactions, endless re-auth. | No bank sync. CSV import instead, with **duplicate detection** on re-import. |
| 3 | **Miscategorization** — wrong auto-categories become a chore that makes people quit. | The app **remembers** each correction (payee → category) and auto-applies it to future imports. |
| 4 | **Subscription fatigue + privacy distrust** — $10–15/mo, and handing bank credentials to a third party. | Free, fully local, **zero credentials, zero cloud**. Data lives in your browser only. |
| 5 | **All-or-nothing rigidity** (YNAB) — steep learning curve, punishes you for falling behind. | Gentle. Track loosely or tightly; partial data still produces a useful picture. |
| 6 | **Forgotten annual/irregular bills** — car reg, insurance, gifts, holidays blow up the month. | **Sinking funds**: pre-save monthly toward big irregular expenses. |
| 7 | **No forward view** — "will I have enough by Friday?" Few apps forecast. | **"Safe to spend"** number + simple month-end projection. |
| 8 | **Couples handled badly** — apps assume fully-merged or fully-split; real couples have both. | Every expense tags **who** (You / Partner / Joint), with per-person and combined views. |

## Interesting avenues (backlog, not all in v1)

- Cash-flow calendar / projected daily balance (PocketSmith-style).
- Gentle nudges (category nearly spent) — notifications, not nagging.
- Month-over-month category-creep trends.
- "Fair share" settle-up for couples with separate accounts.
- Recurring-bill detection from imported history.

## Sources

- https://www.thepennyhoarder.com/budgeting/ynab-review/
- https://marriagekidsandmoney.com/ynab-review/
- https://getfinny.app/blog/best-budget-apps-reddit-recommends-2026
- https://www.financialaha.com/articles/mint-alternatives-after-shutdown/
- https://www.forbes.com/advisor/banking/best-budgeting-apps/
- https://www.quicken.com/blog/best-money-management-apps-for-cash-flow-reporting-in-2026/
- https://moneypatrol.com/moneytalk/budgeting/best-budget-management-apps-must-have-features-in-2026/
