# Repository Guidelines

## Project Structure & Module Organization

- `src/` contains the Python generator (`src/generate_calendar.py`) and its dependencies list (`src/requirements.txt`).
- `docs/` is the published output for GitHub Pages, including `docs/calendar.ics`.
- `.github/workflows/publish.yml` runs the scheduled update job that regenerates the calendar.
- Local virtual environments (e.g., `.venv/`) are for development only and should not be committed.

## Build, Test, and Development Commands

- `python -m venv .venv` creates a local virtual environment.
- `source .venv/bin/activate` activates the environment.
- `pip install -r src/requirements.txt` installs runtime dependencies.
- `export SHEETS_SERVICE_ACCOUNT_JSON='{"type": "service_account", ...}'` sets credentials for the Google Sheets API.
- `python src/generate_calendar.py` regenerates `docs/calendar.ics` from the Google Sheet.

## Coding Style & Naming Conventions

- Use 4-space indentation and follow standard PEP 8 conventions for Python.
- Prefer `snake_case` for functions and variables; keep constants in `UPPER_SNAKE_CASE`.
- Keep functions small and focused; minimize side effects outside `docs/` updates.
- No formatter or linter is configured—keep diffs clean and readable.

## Testing Guidelines

- No automated tests are currently defined.
- If you add logic that is non-trivial or error-prone, add tests alongside it and document how to run them.
- Validate output by inspecting `docs/calendar.ics` after running the generator.

## Commit & Pull Request Guidelines

- Git history is not available in this workspace; no enforced commit message convention is documented.
- Use short, imperative commit messages (e.g., `Update calendar parsing`).
- PRs should describe changes, reference the relevant issue (if any), and note whether `docs/calendar.ics` was updated.

## Configuration & Secrets

- The Google service account JSON must be stored in the `SHEETS_SERVICE_ACCOUNT_JSON` GitHub secret.
- Never commit service account files or raw JSON secrets to the repo.
