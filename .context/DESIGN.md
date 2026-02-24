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
  - [x] Fetch industry info (`fetch_symbol_data`)
  - [x] Retry logic (custom `tenacity` wrapper)
  - [x] GitHub Actions optimization (`httpx`)
- [x] **Data Fetching (BSE)**
  - [x] `BSEClient` implementation using `BseIndiaApi`
  - [x] Iterate all security groups
  - [x] Fetch industry metadata (`equityMetaInfo`)
  - [x] Retry logic
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

### 2. NSE SME Fetching
NSE SME symbols can be listed under the `SM` or `ST` series. The `NSEClient` explicitly tries `SM` first. If it receives a 404 (Not Found), it attempts `ST`.
- **Why:** Ensures complete coverage for SME stocks which may vary in their listing series.

### 3. Error Handling (404s)
The `NSEClient` specifically catches `ConnectionError` with "404" in the message (raised by the underlying library) and **does not retry** it.
- **Why:** 404 means the data is missing. Retrying will only waste time and potentially hit rate limits. All other `ConnectionError`s are retried.

### 4. GitHub Actions Support
When running in GitHub Actions (`GITHUB_ACTIONS=true`), `NSEClient` switches to `httpx` (HTTP/2) if supported by the underlying library or environment setup.
- **Why:** Improves performance and reliability in CI/CD environments.
