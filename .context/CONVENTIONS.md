# Conventions

This project follows specific conventions to ensure code quality, maintainability, and consistency.

## Technical Stack

- **Python Version:** 3.12+ (latest stable features).
- **Dependency Management:** `uv` (for fast, deterministic builds and virtual environments).
- **HTTP Client:** `httpx` (HTTP/2 support, especially for GitHub Actions).

## Coding Standards

### 1. Robustness & Retries

- **`tenacity` Library:** All network operations must be wrapped with `tenacity` retry logic.
- **Configurable Retries:** Retry settings (max attempts, max wait) are configurable via command-line arguments (e.g., `--frequency`).
- **Retryable Exceptions:**
  - Retry on `ConnectionError`, `TimeoutError`, and `requests.exceptions.RequestException`.
  - **Do NOT Retry:** 404 ConnectionErrors (specifically from the NSE library) to avoid infinite loops on missing data.
- **Backoff:** Use `wait_exponential` for polite retries.

### 2. Data Handling

- **JSON Storage:** All industry data is persisted in a simple JSON structure (`metadata` + `data` dictionary).
- **Precedence:** In `full_refresh` mode, BSE data takes precedence over NSE data for overlapping symbols.
- **SME Logic:** NSE SME fetching must attempt both `SM` and `ST` series if `SM` returns a 404.
- **Skipping Invalid:** Symbols ending in `-RE` (Rights Entitlements) are explicitly skipped.

### 3. Logging & Output

- **`logging` Module:** Use Python's built-in `logging` module for all output (info, warning, error).
- **Format:** `%(asctime)s - %(levelname)s - %(message)s`.
- **Progress:** Log progress periodically (e.g., every 50 records or for each significant step) to provide feedback during long-running operations.

### 4. Git & Workflow

- **Branching:** Use short, descriptive branch names.
- **Commits:** Follow conventional commit messages (e.g., `feat: add retry logic`, `fix: handle 404 in NSE`).
- **Artifacts:** Keep `.context/` documentation in sync with code changes. (See `GEMINI.md`).
