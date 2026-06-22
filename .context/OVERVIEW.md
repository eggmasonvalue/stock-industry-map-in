# Project Overview: industry-data-in

`industry-data-in` is a tool designed to map Indian stock symbols (NSE and BSE) to their respective industry classifications (Macro, Sector, Industry, Basic Industry). This data is essential for investment analysis, portfolio categorization, and market visualization.

## Key Features

- **Comprehensive Coverage:** Supports both NSE (National Stock Exchange) and BSE (Bombay Stock Exchange).
  - NSE: Mainboard and SME (Small and Medium Enterprises) stocks.
  - BSE: All security groups (A, B, etc.) via iteration.
- **Robust Data Fetching:**
  - Uses `tenacity` for resilient retry logic with exponential backoff.
  - Handles API rate limits and temporary connection issues.
  - Skips invalid symbols (e.g., Rights Entitlements ending in `-RE`).
- **Data Persistence:** Stores mappings in a local JSON file (`out/industry_data.json`) for easy access and portability.
- **CLI Interface:** Provides command-line arguments for flexible execution:
  - `--refresh`: Updates missing or incomplete data.
  - `--full-refresh`: Rebuilds the database from scratch.
  - `--frequency`: Configures retry parameters based on run frequency (daily, weekly, monthly).
- **Environment Aware:** Detects execution in GitHub Actions to optimize network requests (using `httpx`/HTTP2).

## Core Dependencies

- `nse`: `NseIndiaApi` (custom library).
- `bse`: `BseIndiaApi` (custom library).
- `tenacity`: Retry logic.
- `httpx`: Async HTTP client.

## Consumer client (`industry_map_client`)

Beyond producing the dataset, this repo now ships the **consumer** as an
installable, zero-dependency package so sibling apps stop re-implementing the
ETag-cached fetch (it was copy-pasted in ~5 repos). See `README.md` -> "Consuming
the data". Producer and consumer live in one repo by design (single source of
truth for both the data and how to read it).

## Quick Start

1.  **Install Dependencies:**
    ```bash
    uv sync
    ```

2.  **Run a Full Refresh (Weekly):**
    ```bash
    python main.py --full-refresh --frequency weekly
    ```

3.  **Run a Quick Refresh (Daily):**
    ```bash
    python main.py --refresh --frequency daily
    ```
