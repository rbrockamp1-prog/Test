# Household Budget

A private, offline monthly budget dashboard for two people. One self-contained
`index.html` — no install, no build, no accounts, no bank logins, no cloud.
All data lives in your browser. Designed around [what makes people quit budgeting
apps](./RESEARCH.md).

## Use it

Open `index.html` in any browser (double-click it, or host it — see below).
That's it.

- **Add expense** — the button bottom-right. Amount, category, who paid, done.
- **Import bank CSV** — the ⬇ icon top-right. Export a transactions CSV from your
  bank and pick it. Negative/"debit" amounts become expenses, positives income.
  Re-importing an overlapping statement is safe — **duplicates are skipped**.
  Categorize a payee once and every future import of it is auto-categorized.
- **Budgets** — the ▦ icon. Set a monthly limit per category, add your own
  categories, and set the two people's names.
- **Sinking funds** — pre-save monthly for big irregular costs (car registration,
  insurance, holidays) so they never blow up a month.
- **Who paid** — every expense is tagged You / Partner / Joint; filter the whole
  dashboard by person or see both combined.
- **Safe to spend** — the hero number: budget left for the month, and a rough
  per-day figure for the days remaining.

## Backup & sharing (important)

Because data is local-only, use the ⋮ menu (top-right):

- **Export backup** regularly — downloads a `.json` you can keep safe.
- **Import backup** on a new device to move your data over.
- To share with your partner, both open the app and import the latest backup
  file. (A live shared version — Google Sheet or a small database — is the
  natural next step if you outgrow this; the app was built to make that swap
  easy.)

## Host it (optional, for phone access)

Any static host works, e.g. from this folder:

```bash
python3 -m http.server 8080   # then open http://localhost:8080/budget/
```

Or drop the `budget/` folder on Netlify, Vercel, GitHub Pages, etc.

## Design notes

- **Material Design 3**, implemented self-contained (tokens, elevation, shape,
  segmented buttons, dialogs, FAB) so it works with zero network access.
- Chart and budget-meter colors use a colorblind-safe, contrast-validated
  palette; light and dark mode both follow the system setting.
