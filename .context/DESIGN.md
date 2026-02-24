# Design & Feature Status

This document tracks the implementation status of key features and outlines the current design decisions.

## Feature Status

- [x] **Initial Repository Setup**
  - [x] Basic file structure (`main.py`, `src/`)
  - [x] CLI argument parsing (`argparse`)
  - [x] Logging configuration
- [x] **Data Fetching (NSE)**
  - [x] `NSEClient` implementation using `NseIndiaApi`
  - [x] Fetch Mainboard symbols (CSV)
  - [x] Fetch SME symbols (CSV)
  - [x] Fetch industry info (`getDetailedScripData`)
  - [x] Retry logic (strict predicate)
  - [x] Direct series extraction from CSV (SERIES column)
  - [x] GitHub Actions optimization (`httpx`)
- [x] **Data Fetching (BSE)**
  - [x] `BSEClient` implementation using `BseIndiaApi`
  - [x] Iterate all security groups
  - [x] Fetch industry metadata (`equityMetaInfo`)
  - [x] Retry logic (strict predicate)
- [x] **Orchestration & Logic**
  - [x] `Orchestrator` implementation
  - [x] `--full-refresh`: Clear store, BSE first (precedence), then fill gaps with NSE.
  - [x] `--refresh`: Update existing data (NSE first, then BSE), filling gaps.
  - [x] Batch saving (every 50 records)
  - [x] Configurable retry frequency (daily, weekly, monthly)
- [x] **Data Persistence**
  - [x] `Store` implementation (JSON load/save)
  - [x] Consistent schema (`Macro`, `Sector`, `Industry`, `Basic Industry`)

## Design Decisions

### 1. Precedence Logic (Full Refresh)
In `full_refresh` mode, **BSE data is fetched first**. NSE data is only fetched for symbols *not* found in the BSE dataset.
- **Why:** This ensures efficient processing and assumes BSE data covers most listed companies, potentially reducing NSE API load.
- **Trade-off:** If NSE has better industry classification for dual-listed stocks, it is currently ignored in this mode.

### 2. NSE Symbol Fetching
NSE symbols and their specific series (e.g., `EQ`, `BE`, `SM`, `ST`) are extracted directly from the source CSVs (`EQUITY_L.csv` and `SME_EQUITY_L.csv`).
- **Why:** This eliminates the need for guessing the series or trying multiple fallbacks, which reduces unnecessary API calls (404s) and improves reliability for symbols like `KAPSTON` (listed as `BE`).

### 3. Error Handling
Both NSE and BSE clients implement a strict retry policy.
- **Retries:** `TimeoutError` and `ConnectionError` with status codes 429, 503, 408, 502, 504.
- **No Retry:** `ConnectionError` with status codes 404 (Not Found), 400, 401, 403, 500.
- **Why:** Avoid unnecessary API calls for persistent errors and to respect API rate limits/errors.

### 4. GitHub Actions Support
When running in GitHub Actions (`GITHUB_ACTIONS=true`), `NSEClient` switches to `httpx` (HTTP/2) if supported by the underlying library or environment setup.
- **Why:** Improves performance and reliability in CI/CD environments.
