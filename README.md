# PADRES 2026 Calendar

Generate a public ICS calendar from a Google Sheet and publish it to GitHub Pages.

## What it does

- Reads a single Google Sheet tab.
- Builds an ICS file with start/end times (4-hour duration) in Pacific time.
- Uses row `ID` as the ICS `UID`.
- Updates `docs/calendar.ics` only when content changes.

## Setup

1) Set the Sheet ID + tab name in `src/generate_calendar.py`:

- `SHEET_ID`
- `SHEET_TAB_NAME`

2) Create a Google Cloud service account with **Sheets API read** access.

- Share the sheet with the service account email.
- Store the service account JSON as a GitHub Secret named `SHEETS_SERVICE_ACCOUNT_JSON`.

3) Enable GitHub Pages

- In repo settings, Pages → **Build and deployment**.
- Source: **Deploy from a branch**.
- Branch: `main` (or your default branch), folder: `/docs`.

Your calendar will be served at:

```
https://<your-username>.github.io/<repo-name>/calendar.ics
```

## Local run

```
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
export SHEETS_SERVICE_ACCOUNT_JSON='{"type": "service_account", ... }'
python src/generate_calendar.py
```

## Sheet schema

Required columns (header names can vary in case/punctuation):

- `ID`
- `Date` (MM-DD, assumed year 2026)
- `Time` (HH:MM AM/PM)
- `team`
- `Going?` (checkbox)

Optional column:

- `Giveaway`
- `#Tix`

Summary format:

```
{PP/TV}: {vs/@} {team name}
```

- `PP` if Going is checked, otherwise `TV`.
- If `#Tix` is present, it is included after the prefix as e.g. `PP (2)`.
- `vs` if ID < 82, `@` if ID >= 82.
- Giveaway is appended to `DESCRIPTION` as `Giveaway: <value>` when present.

## GitHub Actions

A scheduled workflow runs every 6 hours and updates the ICS file if content changes.
You can also run it manually via **Actions → Publish ICS → Run workflow**.
